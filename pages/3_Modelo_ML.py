# -*- coding: utf-8 -*-
"""
Módulo de Entrenamiento y Gestión del Modelo de Machine Learning
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.database import (
    obtener_ventas_df_completo, guardar_modelo_info, obtener_modelo_activo,
    crear_alerta
)
from utils.ml_model import entrenar_modelo, modelo_existe, cargar_modelo

from utils.auth import verificar_sesion, sidebar_usuario, get_usuario_actual, ROLES

st.set_page_config(page_title="Modelo ML — La 22", page_icon="🤖", menu_items={}, layout="wide")

from utils.theme import DARK_THEME_CSS, apply_plotly_dark, CHART_COLORS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

verificar_sesion(permisos_requeridos=["modelo_ml"])

st.markdown("""
<div class="page-header">
    <h2>🤖 Modelo de Machine Learning</h2>
    <p>Entrena, evalúa y gestiona el modelo Random Forest para predicción de ventas</p>
</div>
""", unsafe_allow_html=True)

# ── Estado actual del modelo ─────────────────────────────────────────────
modelo_info = obtener_modelo_activo()

if modelo_info:
    st.markdown("### 📊 Modelo Activo")

    mape = modelo_info["mape"]
    r2   = modelo_info["r2"]
    mae  = modelo_info["mae"]
    rmse = modelo_info["rmse"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status = "status-ok" if mape < 10 else ("status-warn" if mape < 15 else "status-bad")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">MAPE</div>
            <div class="metric-value {status}">{mape:.1f}%</div>
            <div class="metric-label">{'✅ Objetivo ≤15%' if mape <= 15 else '❌ Sobre el objetivo'}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        status_r2 = "status-ok" if r2 > 0.9 else ("status-warn" if r2 > 0.7 else "status-bad")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">R² (Bondad de ajuste)</div>
            <div class="metric-value {status_r2}">{r2:.4f}</div>
            <div class="metric-label">{'Excelente' if r2 > 0.9 else 'Aceptable'}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">MAE</div>
            <div class="metric-value" style="color: #58a6ff;">{mae:.2f}</div>
            <div class="metric-label">Error Absoluto Medio</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">RMSE</div>
            <div class="metric-value" style="color: #58a6ff;">{rmse:.2f}</div>
            <div class="metric-label">Raíz Error Cuadrático</div>
        </div>
        """, unsafe_allow_html=True)

    st.caption(
        f"Versión: {modelo_info['version']} | "
        f"Entrenado: {modelo_info['entrenado_en']} | "
        f"Registros: {modelo_info['n_registros']:,}"
    )
    st.divider()

elif modelo_existe():
    st.info("Hay un modelo entrenado pero no está registrado en la base de datos.")
else:
    st.warning("⚠️ **No hay un modelo entrenado.** Entrena el modelo para poder generar predicciones.")

# ── Entrenamiento ────────────────────────────────────────────────────────
st.markdown("### 🚀 Entrenar / Reentrenar Modelo")

df_ventas = obtener_ventas_df_completo()

if len(df_ventas) == 0:
    st.error("No hay datos de ventas en la base de datos. Carga datos primero.")
    st.stop()

col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    st.metric("Registros en MySQL", f"{len(df_ventas):,}")
with col_info2:
    st.metric("Platos únicos", df_ventas["nombre_plato"].nunique())
with col_info3:
    rango = f"{df_ventas['fecha_venta'].min()} a {df_ventas['fecha_venta'].max()}"
    st.metric("Rango de fechas", rango)

# ── Evidencia de autoalimentación ────────────────────────────────────────
modelo_previo = obtener_modelo_activo()
if modelo_previo:
    registros_modelo = modelo_previo.get("n_registros", 0)
    registros_actual = len(df_ventas)
    nuevos = registros_actual - registros_modelo

    if nuevos > 0:
        st.markdown(f"""
        <div class="section-card" style="border-left: 4px solid #e9c46a;">
            <h4>📢 Hay {nuevos:,} registros nuevos desde el último entrenamiento</h4>
            <p style="margin-top:-0.3rem;">
                El modelo actual fue entrenado con <strong>{registros_modelo:,}</strong> registros.
                Ahora la base de datos tiene <strong>{registros_actual:,}</strong> registros.
                Al reentrenar, el modelo usará todos los {registros_actual:,} registros (incluidos los nuevos).
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="section-card" style="border-left: 4px solid #3fb950;">
            <h4>✅ El modelo está actualizado</h4>
            <p style="margin-top:-0.3rem;">
                Entrenado con <strong>{registros_modelo:,}</strong> registros.
                No hay datos nuevos pendientes. Registra ventas de nuevos días para seguir alimentando el modelo.
            </p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

st.markdown("""
<div class="section-card">
    <h4>⚙️ Configuración del Entrenamiento</h4>
    <p style="margin-top:-0.3rem;">
        <strong>Algoritmo:</strong> Random Forest Regressor (200 árboles)<br>
        <strong>Validación:</strong> TimeSeriesSplit (5 folds, respeta orden cronológico)<br>
        <strong>Features:</strong> plato, categoría, tipo de día, día semana, mes, lag_7, promedio móvil 7<br>
        <strong>Fuente de datos:</strong> MySQL → pd.read_sql() → DataFrame
    </p>
</div>
""", unsafe_allow_html=True)

if len(df_ventas) < 100:
    st.error(f"Se necesitan al menos 100 registros para entrenar. Actualmente hay {len(df_ventas)}.")
    st.stop()

entrenar = st.button("🧠 Entrenar Modelo Ahora", type="primary", use_container_width=True)

if entrenar:
    progress    = st.progress(0, text="Preparando datos...")
    status_text = st.empty()

    try:
        status_text.text("📊 Cargando y preparando features...")
        progress.progress(10, text="Preparando features...")
        time.sleep(0.5)

        progress.progress(30, text="Entrenando Random Forest (200 árboles)...")
        status_text.text("🌲 Entrenando Random Forest con validación cruzada temporal...")

        metricas = entrenar_modelo(df_ventas)

        progress.progress(80, text="Guardando modelo...")
        status_text.text("💾 Guardando modelo y encoders...")

        version = f"RF_v{datetime.now().strftime('%Y%m%d_%H%M')}"
        guardar_modelo_info(
            version=version,
            mae=metricas["mae"],
            rmse=metricas["rmse"],
            mape=metricas["mape"],
            r2=metricas["r2"],
            n_registros=metricas["n_registros"],
        )

        crear_alerta(
            "modelo",
            f"Modelo {version} entrenado exitosamente. "
            f"MAPE: {metricas['mape']:.1f}%, R²: {metricas['r2']:.4f}",
            "success",
        )

        progress.progress(100, text="¡Modelo entrenado!")
        status_text.empty()

        st.success("✅ **Modelo entrenado exitosamente.**")
        st.toast("✅ Modelo actualizado correctamente", icon="🤖")

        st.markdown(f"""
        <div class="section-card" style="border-left: 4px solid #3fb950;">
            <h4>📋 Resumen del Entrenamiento</h4>
            <p>
                <strong>Fuente de datos:</strong> MySQL (ventas_historicas) vía pd.read_sql()<br>
                <strong>Registros utilizados:</strong> {metricas['n_registros']:,}<br>
                <strong>Versión:</strong> {version}<br>
                <strong>Modelo guardado:</strong> data/modelo_rf.pkl
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        with col_r1:
            st.metric("MAPE", f"{metricas['mape']:.1f}%",
                      delta="✅ Cumple" if metricas["mape"] <= 15 else "❌ No cumple")
        with col_r2:
            st.metric("R²", f"{metricas['r2']:.4f}")
        with col_r3:
            st.metric("MAE", f"{metricas['mae']:.2f}")
        with col_r4:
            st.metric("RMSE", f"{metricas['rmse']:.2f}")

        st.markdown("### 📊 Importancia de Variables")
        fi    = metricas["feature_importance"]
        fi_df = pd.DataFrame(
            {"Variable": list(fi.keys()), "Importancia": list(fi.values())}
        ).sort_values("Importancia", ascending=True)

        fig_fi = px.bar(
            fi_df, x="Importancia", y="Variable",
            orientation="h", color_discrete_sequence=["#2a9d8f"],
        )
        fig_fi.update_layout(
            plot_bgcolor="#161b22", paper_bgcolor="#161b22",
            height=400, margin=dict(l=20, r=20, t=10, b=20),
            yaxis=dict(autorange="reversed"),
        )
        fig_fi = apply_plotly_dark(fig_fi)
        st.plotly_chart(fig_fi, use_container_width=True)

    except Exception as e:
        progress.empty()
        status_text.empty()
        st.error(f"❌ Error durante el entrenamiento: {str(e)}")
        st.exception(e)

# ── Información del modelo ───────────────────────────────────────────────
st.divider()
st.markdown("### ℹ️ Sobre el Modelo")
st.markdown("""
**Random Forest Regressor** es un algoritmo de ensamble que construye múltiples árboles de decisión
y promedia sus predicciones. Es robusto frente a outliers y maneja bien variables categóricas.

**Variables más importantes del modelo:**
- **tipo_dia** (correlación 0.847): La demanda varía en proporción 1:1.5:3 (semana:sábado:domingo)
- **lag_7** y **prom_mov_7**: Las ventas de la misma semana anterior son fuertes predictores
- **plato_cod**: Cada plato tiene su propio patrón de demanda
- **precio_unitario**: Correlación negativa con demanda (-0.473)

**Objetivo:** MAPE ≤ 15% (Error Absoluto Porcentual Medio)
""")