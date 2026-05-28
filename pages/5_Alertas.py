# -*- coding: utf-8 -*-
"""
Módulo de Alertas — Reducción de desperdicio y notificaciones del sistema
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.database import (
    obtener_alertas, marcar_alerta_leida, obtener_predicciones,
    obtener_ventas_historicas, crear_alerta
)
from utils.database import obtener_ventas_df_completo
from utils.ml_model import predecir_dia, modelo_existe

from utils.auth import verificar_sesion, sidebar_usuario, get_usuario_actual, ROLES

st.set_page_config(page_title="Alertas — La 22", page_icon="⚠️", menu_items={}, layout="wide")

from utils.theme import DARK_THEME_CSS, apply_plotly_dark, CHART_COLORS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

verificar_sesion()


def cop(valor):
    """Formatea un número como pesos colombianos."""
    return f"${int(valor):,} COP".replace(",", ".")


st.markdown("""
<div class="page-header">
    <h2>⚠️ Alertas y Control de Desperdicio</h2>
    <p>Monitoreo de desviaciones, alertas de sobreproducción y notificaciones del sistema</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔔 Alertas del Sistema", "📊 Análisis de Desperdicio"])

with tab1:
    # ── Generar alertas automáticas ──────────────────────────────────
    if modelo_existe():
        if st.button("🔄 Analizar y generar alertas", type="primary"):
            with st.spinner("Analizando datos..."):
                hoy    = date.today()
                hace_7 = hoy - timedelta(days=7)
                pred   = obtener_predicciones(fecha_inicio=hace_7, fecha_fin=hoy)
                ventas = obtener_ventas_historicas(fecha_inicio=hace_7, fecha_fin=hoy)

                if len(pred) > 0 and len(ventas) > 0:
                    # Normalizar tipos antes del merge
                    pred["fecha_prediccion"] = pd.to_datetime(pred["fecha_prediccion"]).dt.date.astype(str)

                    ventas_agg = ventas.groupby(["fecha_venta", "nombre_plato"])["cantidad_vendida"].sum().reset_index()
                    ventas_agg.rename(columns={"fecha_venta": "fecha_prediccion"}, inplace=True)
                    ventas_agg["fecha_prediccion"] = pd.to_datetime(ventas_agg["fecha_prediccion"]).dt.date.astype(str)

                    comp = pred.merge(ventas_agg, on=["fecha_prediccion", "nombre_plato"], how="inner")

                    alertas_generadas = 0
                    for _, row in comp.iterrows():
                        diff = row["cantidad_vendida"] - row["cantidad_predicha"]
                        if diff < -10:
                            crear_alerta(
                                "desperdicio",
                                f"⚠️ Posible desperdicio en {row['nombre_plato']} "
                                f"({row['fecha_prediccion']}): se predijeron {int(row['cantidad_predicha'])} "
                                f"pero se vendieron {int(row['cantidad_vendida'])} ({int(diff)} uds sobrantes).",
                                "warning",
                            )
                            alertas_generadas += 1
                        elif diff > 15:
                            crear_alerta(
                                "demanda_alta",
                                f"📈 Demanda superior a lo esperado en {row['nombre_plato']} "
                                f"({row['fecha_prediccion']}): predicho {int(row['cantidad_predicha'])}, "
                                f"vendido {int(row['cantidad_vendida'])} (+{int(diff)} uds).",
                                "info",
                            )
                            alertas_generadas += 1

                st.success(f"Análisis completado. {alertas_generadas} alertas generadas.")
                st.rerun()

    st.divider()

    # ── Mostrar alertas ──────────────────────────────────────────────
    filtro = st.radio("Filtrar", ["Todas", "No leídas", "Leídas"], horizontal=True)

    if filtro == "No leídas":
        alertas = obtener_alertas(solo_no_leidas=True, limite=100)
    else:
        alertas = obtener_alertas(solo_no_leidas=False, limite=100)
        if filtro == "Leídas":
            alertas = [a for a in alertas if a["leida"] == 1]

    if alertas:
        st.markdown(f"**{len(alertas)} alertas encontradas**")

        for alerta in alertas:
            badge_class = f"badge-{alerta['nivel']}"
            card_class  = "unread" if not alerta["leida"] else "read"
            tipo_label  = alerta["tipo"].replace("_", " ").title()

            # Reemplazar $ por COP en el mensaje si aplica
            mensaje = alerta["mensaje"]

            col_a, col_btn = st.columns([5, 1])
            with col_a:
                st.markdown(f"""
                <div class="alert-card {card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="alert-badge {badge_class}">{tipo_label}</span>
                        <span style="color: #8b949e; font-size: 0.8rem;">{alerta['creada_en']}</span>
                    </div>
                    <p style="margin: 0.5rem 0 0; color: #c9d1d9;">{mensaje}</p>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if not alerta["leida"]:
                    if st.button("✓", key=f"mark_{alerta['id']}", help="Marcar como leída"):
                        marcar_alerta_leida(alerta["id"])
                        st.rerun()
    else:
        st.info("No hay alertas para mostrar.")

with tab2:
    st.markdown("### Análisis de Sobreproducción y Desperdicio")
    st.markdown(
        "Este análisis compara las predicciones con las ventas reales para identificar "
        "días y platos donde hubo sobreproducción (posible desperdicio de alimentos)."
    )

    pred_all   = obtener_predicciones()
    ventas_all = obtener_ventas_historicas()

    if len(pred_all) > 0 and len(ventas_all) > 0:
        # Normalizar tipos antes del merge
        pred_all["fecha_prediccion"] = pd.to_datetime(pred_all["fecha_prediccion"]).dt.date.astype(str)

        ventas_agg2 = ventas_all.groupby(["fecha_venta", "nombre_plato"])["cantidad_vendida"].sum().reset_index()
        ventas_agg2.rename(columns={"fecha_venta": "fecha_prediccion"}, inplace=True)
        ventas_agg2["fecha_prediccion"] = pd.to_datetime(ventas_agg2["fecha_prediccion"]).dt.date.astype(str)

        comp2 = pred_all.merge(ventas_agg2, on=["fecha_prediccion", "nombre_plato"], how="inner")
        comp2["excedente"]             = comp2["cantidad_predicha"] - comp2["cantidad_vendida"]
        comp2["desperdicio_potencial"] = comp2["excedente"].clip(lower=0)

        if comp2["desperdicio_potencial"].sum() > 0:
            desp_plato = comp2.groupby("nombre_plato")["desperdicio_potencial"].sum().nlargest(10).reset_index()
            desp_plato.columns = ["Plato", "Unidades Excedentes"]

            st.markdown("#### Platos con Mayor Excedente Acumulado")
            st.bar_chart(desp_plato.set_index("Plato"))
            st.dataframe(desp_plato, use_container_width=True, hide_index=True)

            total_desp = int(comp2["desperdicio_potencial"].sum())
            st.metric("Total Unidades Excedentes (período)", f"{total_desp:,}")
            st.caption(
                "El excedente no necesariamente es desperdicio — algunos platos pueden conservarse. "
                "Use este dato para ajustar la producción futura."
            )
        else:
            st.success("No se detectó excedente significativo en el período analizado.")
    else:
        st.info(
            "Para generar este análisis necesitas tener predicciones guardadas y ventas reales "
            "registradas para los mismos días."
        )