# -*- coding: utf-8 -*-
"""
Módulo de Registro de Ventas Diarias
Formulario organizado por categoría para registrar lo vendido cada día.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.database import (
    registrar_ventas_dia, obtener_ventas_historicas, obtener_predicciones,
    crear_alerta
)
from utils.ml_model import (
    obtener_platos_disponibles, clasificar_tipo_dia, obtener_dia_semana,
    MENU_LA22
)


from utils.auth import verificar_sesion, sidebar_usuario, get_usuario_actual, ROLES

st.set_page_config(page_title="Registro de Ventas — La 22", page_icon="📝", menu_items={}, layout="wide")

from utils.theme import DARK_THEME_CSS, apply_plotly_dark, CHART_COLORS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

verificar_sesion(permisos_requeridos=["registro_ventas"])

# (CSS handled by theme.py)

st.markdown("""
<div class="page-header">
    <h2>📝 Registro de Ventas del Día</h2>
    <p>Ingresa las cantidades vendidas de cada plato. El sistema usará estos datos para mejorar sus predicciones.</p>
</div>
""", unsafe_allow_html=True)

# ── Selector de fecha ────────────────────────────────────────────────────
col_fecha, col_info_dia = st.columns([1, 2])

with col_fecha:
    fecha_registro = st.date_input(
        "📅 Fecha de las ventas",
        value=date.today(),
        max_value=date.today(),
        help="Selecciona el día de las ventas que quieres registrar"
    )

tipo_dia = clasificar_tipo_dia(fecha_registro)
dia_semana = obtener_dia_semana(fecha_registro)

with col_info_dia:
    st.markdown(f"""
    <div class="info-dia">
        <strong>📅 {dia_semana} {fecha_registro.strftime('%d de %B de %Y')}</strong><br>
        <span style="color: #8b949e;">Tipo de día: <strong>{tipo_dia.replace('_', ' ').title()}</strong></span>
    </div>
    """, unsafe_allow_html=True)

# ── Verificar si hay predicción para comparar ────────────────────────────
pred_df = obtener_predicciones(fecha_inicio=fecha_registro, fecha_fin=fecha_registro)
pred_dict = {}
if len(pred_df) > 0:
    pred_dict = dict(zip(pred_df["nombre_plato"], pred_df["cantidad_predicha"]))
    st.success(f"✅ Hay predicción disponible para este día. Se mostrará la comparación al registrar.")

st.divider()

# ── Verificar ventas existentes para ese día ─────────────────────────────
ventas_existentes = obtener_ventas_historicas(fecha_inicio=fecha_registro, fecha_fin=fecha_registro)
ventas_exist_dict = {}
if len(ventas_existentes) > 0:
    # Filtrar solo registros tipo 'total' (registrados por el usuario)
    vt = ventas_existentes[ventas_existentes["tipo_venta"] == "total"]
    if len(vt) > 0:
        ventas_exist_dict = dict(zip(vt["nombre_plato"], vt["cantidad_vendida"]))
        st.warning(f"⚠️ Ya hay ventas registradas para este día ({len(vt)} platos). "
                   "Si registras de nuevo, se reemplazarán los datos anteriores.")

# ── Formulario de registro ───────────────────────────────────────────────
platos_disponibles = obtener_platos_disponibles(fecha_registro)

emoji_categorias = {
    "Sopas": "🍲",
    "Carnes": "🥩",
    "Pescados": "🐟",
    "Arroces": "🍚",
    "Corrientes": "🍱",
}

ventas_input = {}
total_preview = 0
ingreso_preview = 0

st.markdown("### Ingresa las cantidades vendidas")
st.caption("Escribe la cantidad vendida de cada plato. Deja en 0 los que no se vendieron.")

for categoria, platos in platos_disponibles.items():
    emoji = emoji_categorias.get(categoria, "🍽️")
    st.markdown(f'<div class="cat-header">{emoji} {categoria} ({len(platos)} platos)</div>', unsafe_allow_html=True)

    # Siempre 3 columnas por fila, crear nuevas filas cada 3 platos
    COLS_PER_ROW = 3
    for row_start in range(0, len(platos), COLS_PER_ROW):
        row_platos = platos[row_start:row_start + COLS_PER_ROW]
        cols = st.columns(COLS_PER_ROW)  # Siempre 3 columnas (las vacías quedan en blanco limpio)

        for col_idx, plato in enumerate(row_platos):
            with cols[col_idx]:
                default_val = ventas_exist_dict.get(plato["nombre"], 0)
                pred_val = pred_dict.get(plato["nombre"], None)

                help_text = f"${plato['precio']:,} COP"
                if pred_val is not None:
                    help_text += f" | Predicción: {int(pred_val)} uds"

                cantidad = st.number_input(
                    plato["nombre"],
                    min_value=0,
                    max_value=500,
                    value=int(default_val),
                    step=1,
                    key=f"venta_{plato['nombre']}",
                    help=help_text,
                )

                if pred_val is not None and cantidad > 0:
                    diff = cantidad - int(pred_val)
                    st.caption(f"Pred: {int(pred_val)} | Dif: {diff:+d}")

                ventas_input[plato["nombre"]] = {
                    "cantidad": cantidad,
                    "precio": plato["precio"],
                    "categoria": categoria,
                }
                total_preview += cantidad
                ingreso_preview += cantidad * plato["precio"]

    st.markdown("---")

# ── Resumen antes de guardar ─────────────────────────────────────────────
st.markdown("### 📊 Resumen del Registro")

col_res1, col_res2, col_res3 = st.columns(3)

with col_res1:
    st.markdown(f"""
    <div class="total-card">
        <div class="total-label">TOTAL UNIDADES</div>
        <div class="total-value">{total_preview:,}</div>
        <div class="total-sub">{dia_semana}</div>
    </div>
    """, unsafe_allow_html=True)

with col_res2:
    st.markdown(f"""
    <div class="total-card alt">
        <div class="total-label">INGRESO TOTAL</div>
        <div class="total-value">${ingreso_preview:,.0f}</div>
        <div class="total-sub">COP</div>
    </div>
    """, unsafe_allow_html=True)

with col_res3:
    platos_vendidos = sum(1 for v in ventas_input.values() if v["cantidad"] > 0)
    st.markdown(f"""
    <div class="total-card warn">
        <div class="total-label">PLATOS VENDIDOS</div>
        <div class="total-value">{platos_vendidos}</div>
        <div class="total-sub">de {len(ventas_input)} disponibles</div>
    </div>
    """, unsafe_allow_html=True)

# ── Comparación con predicción ───────────────────────────────────────────
if pred_dict:
    st.markdown("### 📈 Comparación: Predicción vs. Venta Real")
    comp_data = []
    for plato_nombre, info in ventas_input.items():
        if plato_nombre in pred_dict and info["cantidad"] > 0:
            pred_v = int(pred_dict[plato_nombre])
            real_v = info["cantidad"]
            error = abs(real_v - pred_v)
            error_pct = (error / max(pred_v, 1)) * 100
            comp_data.append({
                "Plato": plato_nombre,
                "Predicción": pred_v,
                "Venta Real": real_v,
                "Diferencia": real_v - pred_v,
                "Error %": f"{error_pct:.1f}%",
            })
    if comp_data:
        st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

# ── Botón guardar ────────────────────────────────────────────────────────
st.markdown("###")

col_btn1, col_btn2 = st.columns([1, 3])

with col_btn1:
    guardar = st.button(
        "💾 Guardar Ventas del Día",
        type="primary",
        use_container_width=True,
        disabled=total_preview == 0,
    )

with col_btn2:
    if total_preview == 0:
        st.caption("⚠️ No hay ventas para registrar. Ingresa al menos la cantidad de un plato.")

if guardar:
    if total_preview > 0:
        registrar_ventas_dia(fecha_registro, ventas_input, tipo_dia, dia_semana)
        st.success(f"✅ **Ventas registradas exitosamente** para {dia_semana} {fecha_registro.strftime('%d/%m/%Y')}")
        st.balloons()

        # Alerta si hay mucha diferencia con predicción
        if pred_dict:
            total_pred = sum(pred_dict.values())
            diff_total = abs(total_preview - total_pred)
            if diff_total > total_pred * 0.3:
                crear_alerta(
                    "desvio",
                    f"Desviación significativa el {fecha_registro.strftime('%d/%m')}: "
                    f"predicho {int(total_pred)} vs real {total_preview} ({diff_total:+.0f} uds).",
                    "warning",
                )

        st.info("💡 Los nuevos datos ya están disponibles para reentrenar el modelo y mejorar las predicciones futuras.")
    else:
        st.error("No se registraron ventas porque todas las cantidades están en 0.")
