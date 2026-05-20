# -*- coding: utf-8 -*-
"""
Módulo de Predicción de Ventas Diarias y Semanales
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import sys, os

from utils.database import (
    obtener_ventas_df_completo, guardar_predicciones, obtener_predicciones,
    obtener_ventas_historicas, crear_alerta
)
from utils.ml_model import (
    predecir_dia, predecir_rango, modelo_existe, cargar_modelo,
    clasificar_tipo_dia, obtener_dia_semana, MENU_LA22
)


from utils.auth import verificar_sesion, sidebar_usuario, get_usuario_actual, ROLES

st.set_page_config(page_title="Predicciones — La 22", page_icon="🔮", menu_items={}, layout="wide")

from utils.theme import DARK_THEME_CSS, apply_plotly_dark, CHART_COLORS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

verificar_sesion(permisos_requeridos=["predicciones"])

# (CSS handled by theme.py)

st.markdown("""
<div class="page-header">
    <h2>🔮 Predicción de Ventas</h2>
    <p>Genera predicciones diarias, semanales y mensuales por plato usando el modelo de Machine Learning</p>
</div>
""", unsafe_allow_html=True)

# ── Verificar modelo ─────────────────────────────────────────────────────
if not modelo_existe():
    st.error("⚠️ **No hay un modelo entrenado.** Ve a la página **Modelo ML** para entrenar el modelo primero.")
    st.stop()

# ── Selector de modo ─────────────────────────────────────────────────────
modo = st.radio(
    "Tipo de predicción",
    ["📅 Predicción Diaria", "📆 Predicción Semanal", "📊 Predicción Mensual"],
    horizontal=True,
)

st.divider()

if modo == "📅 Predicción Diaria":
    col_fecha, col_info = st.columns([1, 2])

    with col_fecha:
        fecha_pred = st.date_input(
            "Selecciona la fecha",
            value=date.today(),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=30),
        )
        tipo_dia = clasificar_tipo_dia(fecha_pred)
        dia_semana = obtener_dia_semana(fecha_pred)

        st.markdown(f"""
        **Día:** {dia_semana}  
        **Tipo:** {tipo_dia.replace('_', ' ').title()}  
        **Fecha:** {fecha_pred.strftime('%d/%m/%Y')}
        """)

        generar = st.button("🚀 Generar Predicción", type="primary", use_container_width=True)

    with col_info:
        st.info(
            "El modelo analiza patrones históricos de ventas, tipo de día y tendencias "
            "para predecir cuántas unidades de cada plato se venderán."
        )

    if generar:
        with st.spinner("Generando predicción..."):
            df_hist = obtener_ventas_df_completo()
            pred = predecir_dia(fecha_pred, df_hist)

        if len(pred) == 0:
            st.error("No se pudieron generar predicciones. Verifica que el modelo esté entrenado.")
        else:
            # Guardar en BD
            guardar_predicciones(pred)
            crear_alerta(
                "prediccion",
                f"Predicción generada para {fecha_pred.strftime('%d/%m/%Y')} ({dia_semana}): "
                f"{int(pred['cantidad_predicha'].sum())} unidades totales.",
                "success",
            )

            # ── Resumen ──────────────────────────────────────────────
            total_uds = int(pred["cantidad_predicha"].sum())
            total_ingreso = int(pred["ingreso_estimado"].sum())

            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                st.markdown(f"""
                <div class="total-card"><div class="total-label">TOTAL UNIDADES PREDICHAS</div>
                    <div class="total-value">{total_uds}</div>
                    <div class="total-label">{dia_semana} {fecha_pred.strftime('%d/%m/%Y')}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_t2:
                st.markdown(f"""
                <div class="total-card"><div class="total-label">INGRESO ESTIMADO</div>
                    <div class="total-value">${total_ingreso:,.0f}</div>
                    <div class="total-label">COP</div>
                </div>
                """, unsafe_allow_html=True)
            with col_t3:
                st.markdown(f"""
                <div class="total-card"><div class="total-label">PLATOS DISPONIBLES</div>
                    <div class="total-value">{len(pred)}</div>
                    <div class="total-label">para este día</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("###")

            # ── Detalle por categoría ────────────────────────────────
            col_detail, col_chart = st.columns([3, 2])

            with col_detail:
                st.markdown("#### 📋 Detalle por Plato")
                for cat in ["Sopas", "Carnes", "Pescados", "Arroces", "Corrientes"]:
                    cat_data = pred[pred["categoria_plato"] == cat]
                    if len(cat_data) > 0:
                        emoji_map = {"Sopas": "🍲", "Carnes": "🥩", "Pescados": "🐟", "Arroces": "🍚", "Corrientes": "🍱"}
                        st.markdown(f'<div class="cat-header">{emoji_map.get(cat, "🍽️")} {cat}</div>', unsafe_allow_html=True)
                        for _, row in cat_data.iterrows():
                            cant = int(row["cantidad_predicha"])
                            ingreso = f"${int(row['ingreso_estimado']):,}"
                            st.markdown(f"""
                            <div class="plato-row">
                                <div>
                                    <span class="plato-name">{row['nombre_plato']}</span>
                                    <span style="color:#999; font-size:0.8rem; margin-left:8px">${int(row['precio_unitario']):,} c/u</span>
                                </div>
                                <div>
                                    <span style="color:#666; font-size:0.85rem; margin-right:12px">{ingreso}</span>
                                    <span class="plato-qty">{cant} uds</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

            with col_chart:
                st.markdown("#### 📊 Distribución por Categoría")
                df_cat = pred.groupby("categoria_plato")["cantidad_predicha"].sum().reset_index()
                fig = px.pie(
                    df_cat,
                    values="cantidad_predicha",
                    names="categoria_plato",
                    color_discrete_sequence=["#1a5632", "#2a9d8f", "#e9c46a", "#e76f51", "#264653"],
                    hole=0.45,
                )
                fig.update_layout(
                    paper_bgcolor="#161b22",
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=300,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                )
                fig = apply_plotly_dark(fig)
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("#### 📊 Top Platos")
                top_platos = pred.nlargest(8, "cantidad_predicha")
                fig_bar = px.bar(
                    top_platos,
                    x="cantidad_predicha",
                    y="nombre_plato",
                    orientation="h",
                    color="categoria_plato",
                    color_discrete_map={
                        "Sopas": "#264653", "Carnes": "#2a9d8f",
                        "Pescados": "#e9c46a", "Arroces": "#e76f51",
                        "Corrientes": "#1a5632",
                    },
                )
                fig_bar.update_layout(
                    plot_bgcolor="#161b22",
                    paper_bgcolor="#161b22",
                    xaxis_title="Unidades",
                    yaxis_title="",
                    showlegend=False,
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=300,
                    yaxis=dict(autorange="reversed"),
                )
                fig_bar = apply_plotly_dark(fig_bar)
                st.plotly_chart(fig_bar, use_container_width=True)

elif modo == "📆 Predicción Semanal":
    # ── Predicción Semanal ───────────────────────────────────────────
    col_sem1, col_sem2 = st.columns([1, 2])

    with col_sem1:
        fecha_inicio = st.date_input(
            "Fecha inicio de semana",
            value=date.today(),
            min_value=date.today(),
        )
        fecha_fin = fecha_inicio + timedelta(days=6)
        st.markdown(f"**Rango:** {fecha_inicio.strftime('%d/%m')} al {fecha_fin.strftime('%d/%m/%Y')}")
        generar_sem = st.button("🚀 Generar Predicción Semanal", type="primary", use_container_width=True)

    with col_sem2:
        st.info("La predicción semanal genera estimaciones para 7 días consecutivos, "
                "mostrando tendencias y los días de mayor y menor demanda.")

    if generar_sem:
        with st.spinner("Generando predicción para 7 días..."):
            df_hist = obtener_ventas_df_completo()
            pred_sem = predecir_rango(fecha_inicio, fecha_fin, df_hist)

        if len(pred_sem) == 0:
            st.error("No se pudieron generar predicciones.")
        else:
            guardar_predicciones(pred_sem)

            # Resumen por día
            pred_por_dia = pred_sem.groupby(["fecha_prediccion", "dia_semana"]).agg(
                total_uds=("cantidad_predicha", "sum"),
                ingreso=("ingreso_estimado", "sum"),
            ).reset_index()

            total_semana = int(pred_por_dia["total_uds"].sum())
            ingreso_semana = int(pred_por_dia["ingreso"].sum())
            dia_max = pred_por_dia.loc[pred_por_dia["total_uds"].idxmax()]

            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("Total Unidades Semana", f"{total_semana:,}")
            with col_s2:
                st.metric("Ingreso Estimado", f"${ingreso_semana:,.0f}")
            with col_s3:
                st.metric("Día Mayor Demanda", f"{dia_max['dia_semana']} ({int(dia_max['total_uds'])} uds)")

            st.markdown("###")

            # Gráfico semanal
            st.markdown("#### 📊 Predicción Diaria — Vista Semanal")
            fig_sem = px.bar(
                pred_por_dia,
                x="dia_semana",
                y="total_uds",
                text="total_uds",
                color_discrete_sequence=["#2a9d8f"],
            )
            fig_sem.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            fig_sem.update_layout(
                plot_bgcolor="#161b22",
                paper_bgcolor="#161b22",
                xaxis_title="",
                yaxis_title="Unidades Totales",
                height=400,
                margin=dict(l=20, r=20, t=30, b=20),
            )
            fig_sem.update_xaxes(gridcolor="#21262d")
            fig_sem.update_yaxes(gridcolor="#21262d")
            fig_sem = apply_plotly_dark(fig_sem)
            st.plotly_chart(fig_sem, use_container_width=True)

            # Tabla detallada
            st.markdown("#### 📋 Detalle por Plato y Día")
            pivot = pred_sem.pivot_table(
                index=["categoria_plato", "nombre_plato"],
                columns="dia_semana",
                values="cantidad_predicha",
                aggfunc="sum",
                fill_value=0,
            ).reset_index()
            pivot.columns.name = None
            st.dataframe(pivot, use_container_width=True, hide_index=True)

elif modo == "📊 Predicción Mensual":
    # ── Predicción Mensual ───────────────────────────────────────────
    import calendar

    col_mes1, col_mes2 = st.columns([1, 2])

    with col_mes1:
        anio = st.selectbox("Año", [2026, 2027], index=0)
        mes = st.selectbox("Mes", list(range(1, 13)),
                           index=date.today().month - 1,
                           format_func=lambda m: [
                               "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                               "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
                           ][m - 1])

        dias_en_mes = calendar.monthrange(anio, mes)[1]
        fecha_ini_mes = date(anio, mes, 1)
        fecha_fin_mes = date(anio, mes, dias_en_mes)

        nombre_mes = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][mes - 1]

        st.markdown(f"**Período:** {nombre_mes} {anio} ({dias_en_mes} días)")
        generar_mes = st.button("🚀 Generar Predicción Mensual", type="primary", use_container_width=True)

    with col_mes2:
        st.info(
            f"La predicción mensual genera estimaciones para los {dias_en_mes} días de {nombre_mes} {anio}. "
            "Muestra el total por semana, el detalle por plato y categoría, "
            "y los días de mayor y menor demanda del mes."
        )

    if generar_mes:
        with st.spinner(f"Generando predicción para {dias_en_mes} días de {nombre_mes}..."):
            df_hist = obtener_ventas_df_completo()
            pred_mes = predecir_rango(fecha_ini_mes, fecha_fin_mes, df_hist)

        if len(pred_mes) == 0:
            st.error("No se pudieron generar predicciones.")
        else:
            guardar_predicciones(pred_mes)
            crear_alerta(
                "prediccion",
                f"Predicción mensual generada para {nombre_mes} {anio}: "
                f"{int(pred_mes['cantidad_predicha'].sum())} unidades totales.",
                "success",
            )

            # ── KPIs del mes ─────────────────────────────────────────
            total_mes_uds = int(pred_mes["cantidad_predicha"].sum())
            total_mes_ingreso = int(pred_mes["ingreso_estimado"].sum())
            promedio_diario = int(total_mes_uds / dias_en_mes)

            pred_por_dia = pred_mes.groupby(["fecha_prediccion", "dia_semana", "tipo_dia"]).agg(
                total_uds=("cantidad_predicha", "sum"),
                ingreso=("ingreso_estimado", "sum"),
            ).reset_index()

            dia_max = pred_por_dia.loc[pred_por_dia["total_uds"].idxmax()]
            dia_min = pred_por_dia.loc[pred_por_dia["total_uds"].idxmin()]

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.markdown(f"""
                <div class="total-card">
                    <div class="total-label">TOTAL UNIDADES</div>
                    <div class="total-value">{total_mes_uds:,}</div>
                    <div class="total-sub">{nombre_mes} {anio}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_m2:
                st.markdown(f"""
                <div class="total-card alt">
                    <div class="total-label">INGRESO ESTIMADO</div>
                    <div class="total-value">${total_mes_ingreso:,.0f}</div>
                    <div class="total-sub">COP</div>
                </div>
                """, unsafe_allow_html=True)
            with col_m3:
                st.markdown(f"""
                <div class="total-card warn">
                    <div class="total-label">PROMEDIO DIARIO</div>
                    <div class="total-value">{promedio_diario}</div>
                    <div class="total-sub">unidades/día</div>
                </div>
                """, unsafe_allow_html=True)
            with col_m4:
                st.markdown(f"""
                <div class="total-card">
                    <div class="total-label">DÍA MAYOR DEMANDA</div>
                    <div class="total-value" style="font-size:1.3rem;">{dia_max['dia_semana']}</div>
                    <div class="total-sub">{int(dia_max['total_uds'])} uds — {str(dia_max['fecha_prediccion'])[:10]}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("###")

            # ── Gráfico diario del mes ───────────────────────────────
            st.markdown(f"#### 📊 Predicción Diaria — {nombre_mes} {anio}")

            pred_por_dia["fecha_str"] = pd.to_datetime(pred_por_dia["fecha_prediccion"]).dt.strftime("%d")
            pred_por_dia["total_uds_int"] = pred_por_dia["total_uds"].astype(int)

            color_tipo = {
                "entre_semana": "#58a6ff",
                "sabado": "#3fb950",
                "domingo": "#e76f51",
                "festivo": "#e9c46a",
                "festivo_especial": "#e63946",
            }
            pred_por_dia["color"] = pred_por_dia["tipo_dia"].map(color_tipo).fillna("#58a6ff")

            fig_mes_bar = px.bar(
                pred_por_dia,
                x="fecha_str",
                y="total_uds_int",
                color="tipo_dia",
                color_discrete_map=color_tipo,
                text="total_uds_int",
            )
            fig_mes_bar.update_traces(texttemplate="%{text}", textposition="outside", textfont=dict(size=9, color="#c9d1d9"))
            fig_mes_bar = apply_plotly_dark(fig_mes_bar)
            fig_mes_bar.update_layout(
                height=420,
                xaxis_title=f"Día de {nombre_mes}",
                yaxis_title="Unidades Totales",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=""),
                bargap=0.15,
            )
            st.plotly_chart(fig_mes_bar, use_container_width=True)

            # ── Resumen por semana del mes ───────────────────────────
            st.markdown("#### 📅 Resumen por Semana")
            pred_por_dia["fecha_dt"] = pd.to_datetime(pred_por_dia["fecha_prediccion"])
            pred_por_dia["semana"] = pred_por_dia["fecha_dt"].dt.isocalendar().week.astype(int)

            resumen_semana = pred_por_dia.groupby("semana").agg(
                dias=("fecha_prediccion", "count"),
                total_uds=("total_uds", "sum"),
                ingreso=("ingreso", "sum"),
            ).reset_index()
            resumen_semana["semana_label"] = [f"Semana {i+1}" for i in range(len(resumen_semana))]
            resumen_semana["total_uds"] = resumen_semana["total_uds"].astype(int)
            resumen_semana["ingreso"] = resumen_semana["ingreso"].apply(lambda x: f"${int(x):,}")

            fig_sem_mes = px.bar(
                resumen_semana,
                x="semana_label",
                y="total_uds",
                text="total_uds",
                color_discrete_sequence=["#2a9d8f"],
            )
            fig_sem_mes.update_traces(texttemplate="%{text:,}", textposition="outside", textfont=dict(color="#c9d1d9"))
            fig_sem_mes = apply_plotly_dark(fig_sem_mes)
            fig_sem_mes.update_layout(height=350, xaxis_title="", yaxis_title="Unidades Totales", showlegend=False)
            st.plotly_chart(fig_sem_mes, use_container_width=True)

            # ── Top platos del mes ───────────────────────────────────
            col_top, col_cat = st.columns(2)

            with col_top:
                st.markdown("#### 🥇 Top 10 Platos del Mes")
                top_mes = pred_mes.groupby("nombre_plato")["cantidad_predicha"].sum().nlargest(10).reset_index()
                top_mes["cantidad_predicha"] = top_mes["cantidad_predicha"].astype(int)
                fig_top_mes = px.bar(
                    top_mes, x="cantidad_predicha", y="nombre_plato", orientation="h",
                    color_discrete_sequence=["#2a9d8f"], text=top_mes["cantidad_predicha"],
                )
                fig_top_mes.update_traces(textposition="outside", textfont=dict(color="#c9d1d9"))
                fig_top_mes = apply_plotly_dark(fig_top_mes)
                fig_top_mes.update_layout(height=400, showlegend=False, xaxis_title="Unidades", yaxis_title="", yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_top_mes, use_container_width=True)

            with col_cat:
                st.markdown("#### 🍽️ Distribución por Categoría")
                cat_mes = pred_mes.groupby("categoria_plato")["cantidad_predicha"].sum().reset_index()
                fig_cat_mes = px.pie(
                    cat_mes, values="cantidad_predicha", names="categoria_plato",
                    color_discrete_sequence=CHART_COLORS, hole=0.45,
                )
                fig_cat_mes = apply_plotly_dark(fig_cat_mes)
                fig_cat_mes.update_layout(height=400)
                st.plotly_chart(fig_cat_mes, use_container_width=True)

            # ── Tabla detallada mensual ──────────────────────────────
            st.markdown("#### 📋 Detalle Mensual por Plato")
            detalle_mes = pred_mes.groupby(["categoria_plato", "nombre_plato"]).agg(
                total_uds=("cantidad_predicha", "sum"),
                ingreso_total=("ingreso_estimado", "sum"),
                promedio_diario=("cantidad_predicha", "mean"),
            ).reset_index()
            detalle_mes["total_uds"] = detalle_mes["total_uds"].astype(int)
            detalle_mes["ingreso_total"] = detalle_mes["ingreso_total"].apply(lambda x: f"${int(x):,}")
            detalle_mes["promedio_diario"] = detalle_mes["promedio_diario"].round(1)
            detalle_mes.columns = ["Categoría", "Plato", "Total Unidades", "Ingreso Estimado", "Promedio Diario"]
            detalle_mes = detalle_mes.sort_values("Total Unidades", ascending=False)

            st.dataframe(detalle_mes, use_container_width=True, hide_index=True)

            csv_mes = detalle_mes.to_csv(index=False)
            st.download_button(
                "📥 Descargar Reporte Mensual CSV",
                csv_mes,
                f"prediccion_{nombre_mes}_{anio}.csv",
                "text/csv",
            )
