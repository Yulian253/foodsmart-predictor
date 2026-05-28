# -*- coding: utf-8 -*-
"""
FoodSmart Predictor — Restaurante La 22
Login + Dashboard con roles
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from utils.database import init_database, cargar_csv_inicial, obtener_ventas_historicas, obtener_modelo_activo, obtener_alertas, login_usuario, get_connection
from utils.ml_model import modelo_existe
from utils.theme import DARK_THEME_CSS, CHART_COLORS, apply_plotly_dark
from utils.auth import ROLES, sidebar_usuario, get_usuario_actual

st.set_page_config(
    page_title="FoodSmart Predictor — La 22",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
.login-wrap{max-width:420px;margin:3rem auto 0;background:#161b22;border:1px solid #21262d;border-radius:14px;padding:2.5rem 2rem 2rem;box-shadow:0 8px 32px rgba(0,0,0,.4)}
.login-logo{text-align:center;margin-bottom:1.5rem}
.login-logo h1{color:#e6edf3;font-size:1.8rem;margin:.3rem 0 0}
.login-logo p{color:#8b949e;font-size:.9rem;margin:.2rem 0 0}
.login-logo .logo-icon{font-size:3rem}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def inicializar_sistema():
    init_database()
    csv_path = os.path.join(os.path.dirname(__file__), "data", "ventas_la22_5.csv")
    if os.path.exists(csv_path): return cargar_csv_inicial(csv_path)
    return 0

n_registros = inicializar_sistema()

# ── LOGIN ────────────────────────────────────────────────────────────────
if not st.session_state.get("autenticado", False):
    # Ocultar completamente el sidebar en la pantalla de login
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        .stAppDeployButton { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    col_c, col_f, col_c2 = st.columns([1, 1.5, 1])
    with col_f:
        st.markdown("""
        <div class="login-wrap">
            <div class="login-logo">
                <div class="logo-icon">🍽️</div>
                <h1>FoodSmart Predictor</h1>
                <p>Restaurante La 22 — Bucaramanga</p>
            </div>
        </div>""", unsafe_allow_html=True)
        st.markdown("####")
        username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
        if st.button("🔐 Ingresar", type="primary", use_container_width=True):
            if not username or not password:
                st.error("Ingresa usuario y contraseña.")
            else:
                usuario = login_usuario(username.strip(), password.strip())
                if usuario:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario"] = {
                        "id": usuario["id"],
                        "nombre": usuario["nombre"],
                        "username": usuario["username"],
                        "rol": usuario["rol"],
                    }
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos, o cuenta inactiva.")
        st.markdown('<div style="text-align:center;color:#8b949e;font-size:.82rem;margin-top:1rem;">admin / admin123 &nbsp;·&nbsp; cocina / cocina123</div>', unsafe_allow_html=True)
    st.stop()

# ── DASHBOARD ────────────────────────────────────────────────────────────
usuario  = get_usuario_actual()
rol      = usuario["rol"]
rol_info = ROLES.get(rol, {})

with st.sidebar:
    st.markdown('<div class="sidebar-brand"><h2>🍽️ PredictaVentas</h2><p>Restaurante La 22</p></div>', unsafe_allow_html=True)
    modelo_info = obtener_modelo_activo()
    if modelo_existe() and modelo_info:
        st.markdown(f'<span class="model-badge model-active">● MAPE {modelo_info["mape"]:.1f}% · R² {modelo_info["r2"]:.3f}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="model-badge model-inactive">⚠ Sin Modelo</span>', unsafe_allow_html=True)
    st.divider()

    if rol == "administrador":
        alertas = obtener_alertas(solo_no_leidas=True, limite=3)
    else:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM alertas WHERE leida=0 AND tipo IN ('desperdicio','desvio','demanda_alta') ORDER BY creada_en DESC LIMIT 3")
            alertas = cur.fetchall()
        conn.close()

    if alertas:
        st.markdown(f"**🔔 Alertas ({len(alertas)})**")
        for a in alertas[:3]:
            cls = "success-a" if a['nivel'] == 'success' else ("warning-a" if a['nivel'] == 'warning' else "info-a")
            msg = a["mensaje"][:70] + "..." if len(a["mensaje"]) > 70 else a["mensaje"]
            st.markdown(f'<div class="alert-item {cls}" style="font-size:.82rem;">{msg}</div>', unsafe_allow_html=True)

    st.divider()
    sidebar_usuario()
    st.caption(f"📊 {n_registros:,} registros · v0.1.0")

st.markdown(f'<div class="page-header"><div><h2>Dashboard</h2><p>{rol_info.get("icon","")} {rol_info.get("label","")} — {usuario["nombre"]}</p></div></div>', unsafe_allow_html=True)

df_ventas = obtener_ventas_historicas()
if len(df_ventas) == 0:
    st.warning("No hay datos cargados.")
    st.stop()

df_ventas["fecha_venta"] = pd.to_datetime(df_ventas["fecha_venta"])
f_min     = df_ventas["fecha_venta"].min().strftime("%Y-%m-%d")
f_max     = df_ventas["fecha_venta"].max().strftime("%Y-%m-%d")
n_dias    = df_ventas["fecha_venta"].nunique()
total_uds = int(df_ventas["cantidad_vendida"].sum())

st.markdown(f'<div class="status-bar"><div><span class="status-dot"></span>ventas_la22 · MySQL (foodsmart_la22) <span class="status-badge">{n_registros:,} registros</span></div><div class="status-info">{f_min} → {f_max} · {n_dias} días</div></div>', unsafe_allow_html=True)

if modelo_info:
    st.markdown('<div class="section-card"><h4>🧠 Métricas del Modelo ML (Random Forest)</h4></div>', unsafe_allow_html=True)
    st.markdown(f'''<div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-label">MAPE</div><div class="kpi-value green">{modelo_info["mape"]:.0f}%</div><div class="kpi-sub">Objetivo ≤15% ✅</div></div>
        <div class="kpi-card"><div class="kpi-label">MAE</div><div class="kpi-value teal">{modelo_info["mae"]:.2f}</div><div class="kpi-sub">Unidades · error promedio</div></div>
        <div class="kpi-card"><div class="kpi-label">R²</div><div class="kpi-value blue">{modelo_info["r2"]:.3f}</div><div class="kpi-sub">{modelo_info["r2"]*100:.1f}% variabilidad explicada</div></div>
        <div class="kpi-card"><div class="kpi-label">Algoritmo</div><div class="kpi-value green" style="font-size:1.4rem;">Random Forest</div><div class="kpi-sub">{modelo_info.get("n_registros", n_registros):,} registros</div></div>
    </div>''', unsafe_allow_html=True)

# KPIs según rol
if rol == "administrador":
    total_mesa    = df_ventas[df_ventas["tipo_venta"] == "mesa"]["cantidad_vendida"].sum()
    total_domi    = df_ventas[df_ventas["tipo_venta"] == "domicilio"]["cantidad_vendida"].sum()
    pct_mesa      = (total_mesa / max(total_uds, 1)) * 100
    pct_domi      = (total_domi / max(total_uds, 1)) * 100
    ingreso_total = (df_ventas["cantidad_vendida"] * df_ventas["precio_unitario"]).sum()
    st.markdown(f'''<div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-label">Total Registros</div><div class="kpi-value teal">{n_registros:,}</div><div class="kpi-sub">{n_dias} días de historial</div></div>
        <div class="kpi-card"><div class="kpi-label">Ingreso Total Histórico</div><div class="kpi-value orange">${ingreso_total:,.0f} COP</div><div class="kpi-sub">Pesos colombianos</div></div>
        <div class="kpi-card"><div class="kpi-label">Ventas en Mesa</div><div class="kpi-value gold">{pct_mesa:.0f}%</div><div class="kpi-sub">{int(total_mesa):,} uds</div></div>
        <div class="kpi-card"><div class="kpi-label">Domicilios</div><div class="kpi-value red">{pct_domi:.0f}%</div><div class="kpi-sub">{int(total_domi):,} uds</div></div>
    </div>''', unsafe_allow_html=True)
else:
    ultima_fecha = df_ventas["fecha_venta"].max()
    df_7d        = df_ventas[df_ventas["fecha_venta"] >= ultima_fecha - timedelta(days=7)]
    uds_7d       = int(df_7d["cantidad_vendida"].sum())
    platos_top   = df_ventas.groupby("nombre_plato")["cantidad_vendida"].sum().idxmax()
    promedio_dia = int(df_ventas.groupby("fecha_venta")["cantidad_vendida"].sum().mean())
    st.markdown(f'''<div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-label">Unidades Últimos 7 Días</div><div class="kpi-value teal">{uds_7d:,}</div><div class="kpi-sub">unidades vendidas</div></div>
        <div class="kpi-card"><div class="kpi-label">Promedio Diario</div><div class="kpi-value orange">{promedio_dia:,}</div><div class="kpi-sub">unidades por día</div></div>
        <div class="kpi-card"><div class="kpi-label">Plato Más Vendido</div><div class="kpi-value green" style="font-size:1rem;">{platos_top}</div><div class="kpi-sub">historial completo</div></div>
        <div class="kpi-card"><div class="kpi-label">Días con Datos</div><div class="kpi-value blue">{n_dias}</div><div class="kpi-sub">días registrados</div></div>
    </div>''', unsafe_allow_html=True)

# Gráficas
st.markdown('<div class="section-card"><h4>📊 Promedio de Ventas por Tipo de Día · Ratio 1 : 1.5 : 3</h4></div>', unsafe_allow_html=True)
df_tipo     = df_ventas.groupby(["fecha_venta", "tipo_dia"])["cantidad_vendida"].sum().reset_index()
df_tipo_avg = df_tipo.groupby("tipo_dia")["cantidad_vendida"].mean().reset_index()
orden       = ["entre_semana", "sabado", "festivo", "domingo", "festivo_especial"]
labels_map  = {"entre_semana": "Entre Semana", "sabado": "Sábado", "festivo": "Festivo", "domingo": "Domingo", "festivo_especial": "Festivo Esp."}
color_map   = {"Entre Semana": "#58a6ff", "Sábado": "#3fb950", "Festivo": "#e9c46a", "Domingo": "#e76f51", "Festivo Esp.": "#e63946"}
df_tipo_avg["tipo_dia"] = pd.Categorical(df_tipo_avg["tipo_dia"], categories=orden, ordered=True)
df_tipo_avg = df_tipo_avg.sort_values("tipo_dia")
df_tipo_avg["label"] = df_tipo_avg["tipo_dia"].map(labels_map)
fig_tipo = px.bar(df_tipo_avg, x="label", y="cantidad_vendida", color="label", color_discrete_map=color_map, text=df_tipo_avg["cantidad_vendida"].round(0).astype(int))
fig_tipo.update_traces(textposition="outside", textfont=dict(color="#c9d1d9"))
fig_tipo = apply_plotly_dark(fig_tipo)
fig_tipo.update_layout(height=380, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), xaxis_title="", yaxis_title="Promedio Uds/Día")
st.plotly_chart(fig_tipo, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="section-card"><h4>🥇 Top 10 Platos Más Vendidos</h4></div>', unsafe_allow_html=True)
    df_top  = df_ventas.groupby("nombre_plato")["cantidad_vendida"].sum().nlargest(10).reset_index()
    fig_top = px.bar(df_top, x="cantidad_vendida", y="nombre_plato", orientation="h", color_discrete_sequence=["#2a9d8f"], text=df_top["cantidad_vendida"])
    fig_top.update_traces(textposition="outside", textfont=dict(color="#c9d1d9"))
    fig_top = apply_plotly_dark(fig_top)
    fig_top.update_layout(height=380, showlegend=False, xaxis_title="Unidades", yaxis_title="", yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_top, use_container_width=True)
with col2:
    st.markdown('<div class="section-card"><h4>🍽️ Distribución por Categoría</h4></div>', unsafe_allow_html=True)
    df_cat  = df_ventas.groupby("categoria_plato")["cantidad_vendida"].sum().reset_index()
    fig_cat = px.pie(df_cat, values="cantidad_vendida", names="categoria_plato", color_discrete_sequence=CHART_COLORS, hole=0.45)
    fig_cat = apply_plotly_dark(fig_cat)
    fig_cat.update_layout(height=380)
    st.plotly_chart(fig_cat, use_container_width=True)