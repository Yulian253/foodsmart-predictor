# -*- coding: utf-8 -*-
"""
Módulo de Inventario y Recomendaciones de Compra
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.database import (
    get_connection, obtener_predicciones, crear_alerta
)
from utils.database import obtener_ventas_df_completo
from utils.ml_model import predecir_rango, modelo_existe


from utils.auth import verificar_sesion, sidebar_usuario, get_usuario_actual, ROLES

st.set_page_config(page_title="Inventario — La 22", page_icon="📦", menu_items={}, layout="wide")

from utils.theme import DARK_THEME_CSS, apply_plotly_dark, CHART_COLORS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

verificar_sesion(permisos_requeridos=["inventario"])

# (CSS handled by theme.py)

st.markdown("""
<div class="page-header">
    <h2>📦 Inventario y Compras</h2>
    <p>Control de insumos, stock mínimo y recomendaciones de compra basadas en predicciones</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📦 Gestión de Inventario", "🛒 Recomendaciones de Compra"])

# ── Insumos base del restaurante ─────────────────────────────────────────
INSUMOS_BASE = [
    {"nombre": "Carne de res", "categoria": "Proteínas", "unidad": "kg", "stock_minimo": 20},
    {"nombre": "Pollo", "categoria": "Proteínas", "unidad": "kg", "stock_minimo": 15},
    {"nombre": "Cerdo", "categoria": "Proteínas", "unidad": "kg", "stock_minimo": 15},
    {"nombre": "Pescado (mojarra)", "categoria": "Proteínas", "unidad": "kg", "stock_minimo": 10},
    {"nombre": "Trucha", "categoria": "Proteínas", "unidad": "kg", "stock_minimo": 5},
    {"nombre": "Mariscos", "categoria": "Proteínas", "unidad": "kg", "stock_minimo": 5},
    {"nombre": "Lengua de res", "categoria": "Proteínas", "unidad": "kg", "stock_minimo": 8},
    {"nombre": "Cola de buey", "categoria": "Proteínas", "unidad": "kg", "stock_minimo": 8},
    {"nombre": "Cabro", "categoria": "Proteínas", "unidad": "kg", "stock_minimo": 10},
    {"nombre": "Arroz", "categoria": "Granos", "unidad": "kg", "stock_minimo": 30},
    {"nombre": "Frijoles", "categoria": "Granos", "unidad": "kg", "stock_minimo": 15},
    {"nombre": "Papa", "categoria": "Verduras", "unidad": "kg", "stock_minimo": 25},
    {"nombre": "Yuca", "categoria": "Verduras", "unidad": "kg", "stock_minimo": 15},
    {"nombre": "Plátano", "categoria": "Verduras", "unidad": "kg", "stock_minimo": 15},
    {"nombre": "Cebolla", "categoria": "Verduras", "unidad": "kg", "stock_minimo": 10},
    {"nombre": "Tomate", "categoria": "Verduras", "unidad": "kg", "stock_minimo": 10},
    {"nombre": "Aceite", "categoria": "Otros", "unidad": "litros", "stock_minimo": 10},
    {"nombre": "Gas", "categoria": "Otros", "unidad": "pipeta", "stock_minimo": 2},
    {"nombre": "Bebidas", "categoria": "Otros", "unidad": "unidades", "stock_minimo": 100},
]


def obtener_inventario():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM inventario ORDER BY categoria, nombre_insumo")
        rows = cursor.fetchall()
    conn.close()
    return rows


def inicializar_inventario():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as total FROM inventario")
        count = cursor.fetchone()["total"]
        if count == 0:
            for insumo in INSUMOS_BASE:
                cursor.execute(
                    """INSERT INTO inventario (nombre_insumo, categoria, cantidad_actual, unidad, stock_minimo)
                       VALUES (%s, %s, 0, %s, %s)""",
                    (insumo["nombre"], insumo["categoria"], insumo["unidad"], insumo["stock_minimo"]),
                )
    conn.commit()
    conn.close()


inicializar_inventario()

with tab1:
    st.markdown("### Control de Stock Actual")

    inventario = obtener_inventario()
    if not inventario:
        st.info("Inventario vacío. Se inicializará con los insumos base.")
        st.rerun()

    # Agrupar por categoría
    inv_df = pd.DataFrame(inventario)
    categorias = inv_df["categoria"].unique()

    cambios = {}

    for cat in categorias:
        st.markdown(f"#### {cat}")
        cat_items = inv_df[inv_df["categoria"] == cat]

        cols = st.columns(min(4, len(cat_items)))
        for i, (_, item) in enumerate(cat_items.iterrows()):
            with cols[i % len(cols)]:
                # Determinar estado del stock
                ratio = item["cantidad_actual"] / max(item["stock_minimo"], 1)
                if ratio < 0.3:
                    status = "🔴"
                    status_text = "Crítico"
                elif ratio < 0.7:
                    status = "🟡"
                    status_text = "Bajo"
                else:
                    status = "🟢"
                    status_text = "OK"

                nueva_cant = st.number_input(
                    f"{status} {item['nombre_insumo']} ({item['unidad']})",
                    min_value=0.0,
                    value=float(item["cantidad_actual"]),
                    step=0.5,
                    key=f"inv_{item['id']}",
                    help=f"Stock mínimo: {item['stock_minimo']} {item['unidad']} | Estado: {status_text}",
                )
                if nueva_cant != item["cantidad_actual"]:
                    cambios[item["id"]] = nueva_cant

    st.divider()

    if cambios:
        st.info(f"Hay {len(cambios)} cambios pendientes.")
        if st.button("💾 Guardar Cambios de Inventario", type="primary"):
            conn = get_connection()
            with conn.cursor() as cursor:
                for inv_id, nueva_cant in cambios.items():
                    cursor.execute(
                        "UPDATE inventario SET cantidad_actual = %s WHERE id = %s",
                        (nueva_cant, inv_id),
                    )
            conn.commit()
            conn.close()

            # Verificar stock bajo
            inventario_nuevo = obtener_inventario()
            for item in inventario_nuevo:
                if item["cantidad_actual"] < item["stock_minimo"] * 0.3:
                    crear_alerta(
                        "stock_bajo",
                        f"🔴 Stock crítico de {item['nombre_insumo']}: "
                        f"{item['cantidad_actual']} {item['unidad']} "
                        f"(mínimo: {item['stock_minimo']})",
                        "danger",
                    )

            st.success("✅ Inventario actualizado correctamente.")
            st.rerun()

with tab2:
    st.markdown("### Recomendaciones de Compra")
    st.markdown(
        "Basado en las predicciones de ventas y el inventario actual, "
        "el sistema sugiere qué insumos comprar."
    )

    if not modelo_existe():
        st.warning("Entrena el modelo ML primero para generar recomendaciones basadas en predicciones.")
        st.stop()

    periodo = st.selectbox("Período de planificación", ["3 días", "5 días", "7 días"])
    dias = int(periodo.split()[0])

    if st.button("📊 Generar Recomendaciones", type="primary"):
        with st.spinner("Calculando demanda esperada..."):
            df_hist = obtener_ventas_df_completo()
            hoy = date.today()
            pred = predecir_rango(hoy, hoy + timedelta(days=dias - 1), df_hist)

        if len(pred) > 0:
            total_por_plato = pred.groupby("nombre_plato")["cantidad_predicha"].sum().to_dict()

            st.markdown(f"#### Demanda Proyectada ({dias} días)")
            pred_resumen = pred.groupby(["nombre_plato", "categoria_plato"])["cantidad_predicha"].sum().reset_index()
            pred_resumen.columns = ["Plato", "Categoría", "Unidades Estimadas"]
            pred_resumen = pred_resumen.sort_values("Unidades Estimadas", ascending=False)
            pred_resumen["Unidades Estimadas"] = pred_resumen["Unidades Estimadas"].round(0).astype(int)
            st.dataframe(pred_resumen, use_container_width=True, hide_index=True)

            st.markdown("#### 🛒 Lista de Compras Sugerida")
            st.markdown(
                "A continuación se muestra una estimación de insumos basada en la demanda proyectada. "
                "Los valores son aproximados y deben ajustarse según las recetas específicas."
            )

            total_unidades = sum(total_por_plato.values())

            # Estimaciones básicas de insumos por unidad vendida (aproximado)
            inventario_actual = {i["nombre_insumo"]: i for i in obtener_inventario()}

            recomendaciones = []
            for insumo in INSUMOS_BASE:
                actual = inventario_actual.get(insumo["nombre"], {}).get("cantidad_actual", 0)
                minimo = insumo["stock_minimo"]

                # Estimación simple: stock mínimo * factor de días
                necesario = minimo * (dias / 7) * 1.2  # 20% margen
                comprar = max(0, necesario - actual)

                if comprar > 0:
                    recomendaciones.append({
                        "Insumo": insumo["nombre"],
                        "Stock Actual": f"{actual:.1f} {insumo['unidad']}",
                        "Necesario (est.)": f"{necesario:.1f} {insumo['unidad']}",
                        "Comprar": f"{comprar:.1f} {insumo['unidad']}",
                        "Urgencia": "🔴 Alta" if actual < minimo * 0.3 else ("🟡 Media" if actual < minimo else "🟢 Baja"),
                    })

            if recomendaciones:
                st.dataframe(pd.DataFrame(recomendaciones), use_container_width=True, hide_index=True)

                csv = pd.DataFrame(recomendaciones).to_csv(index=False)
                st.download_button("📥 Descargar Lista de Compras", csv, "lista_compras.csv", "text/csv")
            else:
                st.success("El inventario actual cubre la demanda proyectada. No se necesitan compras urgentes.")
        else:
            st.error("No se pudieron generar predicciones.")
