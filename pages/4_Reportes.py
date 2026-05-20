# -*- coding: utf-8 -*-
"""
Módulo de Reportes y Análisis Comparativo
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.database import (
    obtener_ventas_historicas, obtener_predicciones
)


from utils.auth import verificar_sesion, sidebar_usuario, get_usuario_actual, ROLES

st.set_page_config(page_title="Reportes — La 22", page_icon="📄", menu_items={}, layout="wide")

from utils.theme import DARK_THEME_CSS, apply_plotly_dark, CHART_COLORS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

verificar_sesion(permisos_requeridos=["reportes"])

# (CSS handled by theme.py)

st.markdown("""
<div class="page-header">
    <h2>📄 Reportes y Análisis</h2>
    <p>Reportes de ventas, análisis comparativo predicción vs. realidad, y tendencias del negocio</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Reporte de Ventas", "📈 Predicción vs. Real", "📉 Tendencias"])

# ── Tab 1: Reporte de Ventas ─────────────────────────────────────────────
with tab1:
    st.markdown("### Reporte de Ventas por Período")

    col1, col2 = st.columns(2)
    with col1:
        fecha_ini = st.date_input("Fecha inicio", value=date.today() - timedelta(days=30), key="rep_ini")
    with col2:
        fecha_fin_rep = st.date_input("Fecha fin", value=date.today(), key="rep_fin")

    df = obtener_ventas_historicas(fecha_inicio=fecha_ini, fecha_fin=fecha_fin_rep)

    if len(df) > 0:
        df["fecha_venta"] = pd.to_datetime(df["fecha_venta"])
        df["ingreso"] = df["cantidad_vendida"] * df["precio_unitario"]

        # KPIs del período
        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        with col_k1:
            st.metric("Total Unidades", f"{df['cantidad_vendida'].sum():,}")
        with col_k2:
            st.metric("Ingreso Total", f"${df['ingreso'].sum():,.0f}")
        with col_k3:
            st.metric("Promedio Diario", f"{df.groupby('fecha_venta')['cantidad_vendida'].sum().mean():.0f} uds")
        with col_k4:
            st.metric("Días con Datos", f"{df['fecha_venta'].nunique()}")

        st.divider()

        # Ventas por plato
        st.markdown("#### Ventas por Plato")
        df_plato = df.groupby(["nombre_plato", "categoria_plato"]).agg(
            total_uds=("cantidad_vendida", "sum"),
            ingreso_total=("ingreso", "sum"),
        ).reset_index().sort_values("total_uds", ascending=False)

        fig = px.bar(
            df_plato,
            x="total_uds",
            y="nombre_plato",
            orientation="h",
            color="categoria_plato",
            color_discrete_map={
                "Sopas": "#264653", "Carnes": "#2a9d8f",
                "Pescados": "#e9c46a", "Arroces": "#e76f51",
                "Corrientes": "#1a5632",
            },
        )
        fig.update_layout(
            plot_bgcolor="#161b22", paper_bgcolor="#161b22",
            xaxis_title="Unidades Vendidas", yaxis_title="",
            height=500, margin=dict(l=20, r=20, t=10, b=20),
            yaxis=dict(autorange="reversed"),
        )
        fig = apply_plotly_dark(fig)
        st.plotly_chart(fig, use_container_width=True)

        # Tabla resumen
        st.markdown("#### Tabla Resumen")
        df_plato_display = df_plato.copy()
        df_plato_display.columns = ["Plato", "Categoría", "Unidades Vendidas", "Ingreso Total"]
        df_plato_display["Ingreso Total"] = df_plato_display["Ingreso Total"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(df_plato_display, use_container_width=True, hide_index=True)

        # Descargar CSV
        csv = df_plato.to_csv(index=False)
        st.download_button("📥 Descargar Reporte CSV", csv, "reporte_ventas.csv", "text/csv")
    else:
        st.info("No hay datos de ventas para el período seleccionado.")

# ── Tab 2: Predicción vs Real ────────────────────────────────────────────
with tab2:
    st.markdown("### Análisis Comparativo: Predicción vs. Venta Real")

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        fecha_comp_ini = st.date_input("Desde", value=date.today() - timedelta(days=14), key="comp_ini")
    with col_c2:
        fecha_comp_fin = st.date_input("Hasta", value=date.today(), key="comp_fin")

    pred_df = obtener_predicciones(fecha_inicio=fecha_comp_ini, fecha_fin=fecha_comp_fin)
    ventas_df = obtener_ventas_historicas(fecha_inicio=fecha_comp_ini, fecha_fin=fecha_comp_fin)

    if len(pred_df) > 0 and len(ventas_df) > 0:
        # Agregar ventas reales por fecha + plato
        ventas_agg = ventas_df.groupby(["fecha_venta", "nombre_plato"])["cantidad_vendida"].sum().reset_index()
        ventas_agg.rename(columns={"fecha_venta": "fecha_prediccion", "cantidad_vendida": "venta_real"}, inplace=True)

        # Merge
        comp = pred_df.merge(ventas_agg, on=["fecha_prediccion", "nombre_plato"], how="inner")

        if len(comp) > 0:
            comp["error_abs"] = abs(comp["cantidad_predicha"] - comp["venta_real"])
            comp["error_pct"] = (comp["error_abs"] / comp["venta_real"].clip(lower=1)) * 100

            # KPIs
            mae = comp["error_abs"].mean()
            mape = comp["error_pct"].mean()
            r2 = 1 - (((comp["venta_real"] - comp["cantidad_predicha"]) ** 2).sum() /
                       ((comp["venta_real"] - comp["venta_real"].mean()) ** 2).sum()) if len(comp) > 1 else 0

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("MAE del período", f"{mae:.2f} uds")
            with col_m2:
                st.metric("MAPE del período", f"{mape:.1f}%")
            with col_m3:
                st.metric("R² del período", f"{r2:.4f}")

            # Gráfico comparativo por día
            comp_diario = comp.groupby("fecha_prediccion").agg(
                predicho=("cantidad_predicha", "sum"),
                real=("venta_real", "sum"),
            ).reset_index()

            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(
                x=comp_diario["fecha_prediccion"],
                y=comp_diario["predicho"],
                mode="lines+markers",
                name="Predicción",
                line=dict(color="#2a9d8f", width=2),
            ))
            fig_comp.add_trace(go.Scatter(
                x=comp_diario["fecha_prediccion"],
                y=comp_diario["real"],
                mode="lines+markers",
                name="Venta Real",
                line=dict(color="#e76f51", width=2),
            ))
            fig_comp.update_layout(
                plot_bgcolor="#161b22", paper_bgcolor="#161b22",
                xaxis_title="Fecha", yaxis_title="Unidades Totales",
                height=400, margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            fig_comp.update_xaxes(gridcolor="#21262d")
            fig_comp.update_yaxes(gridcolor="#21262d")
            fig_comp = apply_plotly_dark(fig_comp)
            st.plotly_chart(fig_comp, use_container_width=True)

            # Tabla comparativa
            st.markdown("#### Detalle por Plato")
            comp_plato = comp.groupby("nombre_plato").agg(
                predicho_total=("cantidad_predicha", "sum"),
                real_total=("venta_real", "sum"),
                error_medio=("error_abs", "mean"),
                mape_plato=("error_pct", "mean"),
            ).reset_index().sort_values("real_total", ascending=False)

            comp_plato.columns = ["Plato", "Total Predicho", "Total Real", "Error Medio", "MAPE %"]
            comp_plato["Total Predicho"] = comp_plato["Total Predicho"].round(0).astype(int)
            comp_plato["Error Medio"] = comp_plato["Error Medio"].round(1)
            comp_plato["MAPE %"] = comp_plato["MAPE %"].round(1)
            st.dataframe(comp_plato, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos coincidentes entre predicciones y ventas reales para este período.")
    else:
        st.info("Se necesitan tanto predicciones como ventas reales registradas para el mismo período. "
                "Genera predicciones y luego registra las ventas reales para ver la comparación.")

# ── Tab 3: Tendencias ────────────────────────────────────────────────────
with tab3:
    st.markdown("### Tendencias de Ventas")

    df_all = obtener_ventas_historicas()
    if len(df_all) > 0:
        df_all["fecha_venta"] = pd.to_datetime(df_all["fecha_venta"])
        df_all["mes"] = df_all["fecha_venta"].dt.to_period("M").astype(str)

        # Tendencia mensual
        st.markdown("#### Evolución Mensual de Ventas")
        df_mensual = df_all.groupby("mes")["cantidad_vendida"].sum().reset_index()
        fig_mes = px.line(
            df_mensual, x="mes", y="cantidad_vendida",
            markers=True, color_discrete_sequence=["#1a5632"],
        )
        fig_mes.update_layout(
            plot_bgcolor="#161b22", paper_bgcolor="#161b22",
            xaxis_title="Mes", yaxis_title="Unidades Totales",
            height=350, margin=dict(l=20, r=20, t=10, b=20),
        )
        fig_mes.update_xaxes(gridcolor="#21262d")
        fig_mes.update_yaxes(gridcolor="#21262d")
        fig_mes = apply_plotly_dark(fig_mes)
        st.plotly_chart(fig_mes, use_container_width=True)

        # Patrón semanal
        st.markdown("#### Patrón por Día de la Semana")
        orden_dias = ["Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        df_dia = df_all.groupby("dia_semana")["cantidad_vendida"].mean().reset_index()
        df_dia["dia_semana"] = pd.Categorical(df_dia["dia_semana"], categories=orden_dias, ordered=True)
        df_dia = df_dia.sort_values("dia_semana")

        fig_dia = px.bar(
            df_dia, x="dia_semana", y="cantidad_vendida",
            color_discrete_sequence=["#2a9d8f"],
        )
        fig_dia.update_layout(
            plot_bgcolor="#161b22", paper_bgcolor="#161b22",
            xaxis_title="", yaxis_title="Promedio Unidades/Día",
            height=350, margin=dict(l=20, r=20, t=10, b=20),
        )
        fig_dia = apply_plotly_dark(fig_dia)
        st.plotly_chart(fig_dia, use_container_width=True)
    else:
        st.info("No hay datos históricos para analizar.")
