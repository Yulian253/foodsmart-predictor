# -*- coding: utf-8 -*-
"""
Módulo de Reportes y Análisis Comparativo — con exportación a PDF
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import sys, os, io
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.database import (
    obtener_ventas_historicas, obtener_predicciones, obtener_modelo_activo
)

from utils.auth import verificar_sesion, sidebar_usuario, get_usuario_actual, ROLES

st.set_page_config(page_title="Reportes — La 22", page_icon="📄", menu_items={}, layout="wide")

from utils.theme import DARK_THEME_CSS, apply_plotly_dark, CHART_COLORS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

verificar_sesion(permisos_requeridos=["reportes"])

st.markdown("""
<div class="page-header">
    <h2>📄 Reportes y Análisis</h2>
    <p>Reportes de ventas, análisis comparativo predicción vs. realidad, y tendencias del negocio</p>
</div>
""", unsafe_allow_html=True)

# ── Función generadora de PDF ─────────────────────────────────────────────
def generar_pdf(df, fecha_ini, fecha_fin, modelo_info=None, comp_data=None):
    """
    Genera un PDF profesional con el reporte de ventas.
    Lenguaje amigable para personas no técnicas.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    # ── Colores ──────────────────────────────────────────────────────────
    VERDE_OSCURO  = colors.HexColor("#1A5632")
    VERDE_CLARO   = colors.HexColor("#2A9D8F")
    FONDO_GRIS    = colors.HexColor("#F4F6F5")
    GRIS_LINEA    = colors.HexColor("#DEE2E6")
    NARANJA       = colors.HexColor("#E76F51")
    TEXTO_OSCURO  = colors.HexColor("#2D3436")
    BLANCO        = colors.white

    # ── Estilos ──────────────────────────────────────────────────────────
    estilos = getSampleStyleSheet()

    titulo_principal = ParagraphStyle(
        "titulo_principal", parent=estilos["Normal"],
        fontSize=22, textColor=BLANCO, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=4,
    )
    subtitulo = ParagraphStyle(
        "subtitulo", parent=estilos["Normal"],
        fontSize=11, textColor=BLANCO, fontName="Helvetica",
        alignment=TA_CENTER, spaceAfter=2,
    )
    seccion_titulo = ParagraphStyle(
        "seccion_titulo", parent=estilos["Normal"],
        fontSize=14, textColor=VERDE_OSCURO, fontName="Helvetica-Bold",
        spaceBefore=14, spaceAfter=6,
    )
    cuerpo = ParagraphStyle(
        "cuerpo", parent=estilos["Normal"],
        fontSize=10, textColor=TEXTO_OSCURO, fontName="Helvetica",
        leading=14, spaceAfter=4,
    )
    nota_tecnica = ParagraphStyle(
        "nota_tecnica", parent=estilos["Normal"],
        fontSize=8, textColor=colors.HexColor("#8B949E"),
        fontName="Helvetica-Oblique", spaceAfter=4,
    )
    pie_pagina = ParagraphStyle(
        "pie_pagina", parent=estilos["Normal"],
        fontSize=8, textColor=colors.HexColor("#8B949E"),
        fontName="Helvetica", alignment=TA_CENTER,
    )

    contenido = []

    # ── ENCABEZADO ───────────────────────────────────────────────────────
    encabezado_data = [[
        Paragraph("🍽️  Restaurante La 22", titulo_principal),
    ]]
    encabezado_sub = [[
        Paragraph("Reporte de Ventas y Desempeño del Negocio", subtitulo),
        Paragraph(
            f"Período: {fecha_ini.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}  ·  "
            f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
            subtitulo,
        ),
    ]]

    t_enc = Table([[Paragraph("Restaurante La 22 — Reporte de Ventas", titulo_principal)]], colWidths=[17*cm])
    t_enc.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), VERDE_OSCURO),
        ("ROWPADDING",   (0, 0), (-1, -1), 18),
        ("TOPPADDING",   (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 18),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))

    t_sub = Table([[
        Paragraph(f"Período: {fecha_ini.strftime('%d/%m/%Y')} — {fecha_fin.strftime('%d/%m/%Y')}", subtitulo),
        Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitulo),
    ]], colWidths=[8.5*cm, 8.5*cm])
    t_sub.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), VERDE_CLARO),
        ("ROWPADDING", (0, 0), (-1, -1), 8),
    ]))

    contenido.append(t_enc)
    contenido.append(Spacer(1, 0.3*cm))
    contenido.append(t_sub)
    contenido.append(Spacer(1, 0.5*cm))

    # ── SECCIÓN 1: RESUMEN EJECUTIVO ─────────────────────────────────────
    contenido.append(Paragraph("1. Resumen del Período", seccion_titulo))
    contenido.append(HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8))

    df["ingreso"] = df["cantidad_vendida"] * df["precio_unitario"]
    total_uds     = int(df["cantidad_vendida"].sum())
    total_ingreso = int(df["ingreso"].sum())
    dias_datos    = df["fecha_venta"].nunique()
    promedio_dia  = total_uds / max(dias_datos, 1)
    plato_top     = df.groupby("nombre_plato")["cantidad_vendida"].sum().idxmax()
    plato_menor   = df.groupby("nombre_plato")["cantidad_vendida"].sum().idxmin()
    cat_top       = df.groupby("categoria_plato")["cantidad_vendida"].sum().idxmax()

    kpi_data = [
        ["✔  Total de platos servidos", f"{total_uds:,} unidades"],
        ["✔  Ingresos generados en el período", f"${total_ingreso:,} COP"],
        ["✔  Días con ventas registradas", f"{dias_datos} días"],
        ["✔  Promedio de platos por día", f"{promedio_dia:.0f} unidades/día"],
        ["✔  Plato más vendido", plato_top],
        ["✔  Plato menos vendido", plato_menor],
        ["✔  Categoría más popular", cat_top],
    ]

    t_kpi = Table(kpi_data, colWidths=[9*cm, 8*cm])
    t_kpi.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("FONTNAME",    (1, 0), (1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",   (0, 0), (0, -1), TEXTO_OSCURO),
        ("TEXTCOLOR",   (1, 0), (1, -1), VERDE_OSCURO),
        ("BACKGROUND",  (0, 0), (-1, 0), FONDO_GRIS),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BLANCO, FONDO_GRIS]),
        ("GRID",        (0, 0), (-1, -1), 0.5, GRIS_LINEA),
        ("ROWPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    contenido.append(KeepTogether([t_kpi]))
    contenido.append(Spacer(1, 0.5*cm))

    # ── SECCIÓN 2: DETALLE POR PLATO ─────────────────────────────────────
    contenido.append(KeepTogether([
        Paragraph("2. Detalle de Ventas por Plato", seccion_titulo),
        HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8),
    ]))

    df_plato = df.groupby(["nombre_plato", "categoria_plato"]).agg(
        total_uds=("cantidad_vendida", "sum"),
        ingreso_total=("ingreso", "sum"),
    ).reset_index().sort_values("total_uds", ascending=False)

    df_plato["pct"] = (df_plato["total_uds"] / total_uds * 100).round(1)

    plato_tabla = [["Plato", "Categoría", "Unidades", "Ingresos (COP)", "% del Total"]]
    for _, row in df_plato.iterrows():
        plato_tabla.append([
            row["nombre_plato"],
            row["categoria_plato"],
            f"{int(row['total_uds']):,}",
            f"${int(row['ingreso_total']):,}",
            f"{row['pct']}%",
        ])

    t_plato = Table(plato_tabla, colWidths=[5.5*cm, 3*cm, 2.2*cm, 3.5*cm, 2.8*cm])
    t_plato.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), VERDE_OSCURO),
        ("TEXTCOLOR",   (0, 0), (-1, 0), BLANCO),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, FONDO_GRIS]),
        ("GRID",        (0, 0), (-1, -1), 0.5, GRIS_LINEA),
        ("ROWPADDING",  (0, 0), (-1, -1), 6),
        ("ALIGN",       (2, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    contenido.append(KeepTogether([t_plato]))
    contenido.append(Spacer(1, 0.5*cm))

    # ── SECCIÓN 3: POR CATEGORÍA ─────────────────────────────────────────
    contenido.append(KeepTogether([
        Paragraph("3. Ventas por Categoría", seccion_titulo),
        HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8),
    ]))

    df_cat = df.groupby("categoria_plato").agg(
        total_uds=("cantidad_vendida", "sum"),
        ingreso_total=("ingreso", "sum"),
    ).reset_index().sort_values("total_uds", ascending=False)

    emojis_cat = {"Sopas": "🍲", "Carnes": "🥩", "Pescados": "🐟", "Arroces": "🍚", "Corrientes": "🍱"}

    cat_tabla = [["Categoría", "Platos vendidos", "Ingresos (COP)", "% del Total"]]
    for _, row in df_cat.iterrows():
        emoji = emojis_cat.get(row["categoria_plato"], "🍽️")
        pct   = row["total_uds"] / total_uds * 100
        cat_tabla.append([
            f"{emoji}  {row['categoria_plato']}",
            f"{int(row['total_uds']):,}",
            f"${int(row['ingreso_total']):,}",
            f"{pct:.1f}%",
        ])

    t_cat = Table(cat_tabla, colWidths=[5*cm, 3.5*cm, 4.5*cm, 4*cm])
    t_cat.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), VERDE_OSCURO),
        ("TEXTCOLOR",   (0, 0), (-1, 0), BLANCO),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, FONDO_GRIS]),
        ("GRID",        (0, 0), (-1, -1), 0.5, GRIS_LINEA),
        ("ROWPADDING",  (0, 0), (-1, -1), 8),
        ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    contenido.append(KeepTogether([t_cat]))
    contenido.append(Spacer(1, 0.5*cm))

    # ── SECCIÓN 4: COMPORTAMIENTO POR DÍA ───────────────────────────────
    contenido.append(KeepTogether([
        Paragraph("4. ¿Qué días se vende más?", seccion_titulo),
        HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8),
    ]))

    tipo_labels = {
        "entre_semana": "Lunes a Viernes",
        "sabado":       "Sábado",
        "domingo":      "Domingo",
        "festivo":      "Festivo",
        "festivo_especial": "Festivo Especial",
    }

    df_tipo = df.copy()
    df_tipo["fecha_venta"] = pd.to_datetime(df_tipo["fecha_venta"])
    df_tipo_avg = df_tipo.groupby(["fecha_venta", "tipo_dia"])["cantidad_vendida"].sum().reset_index()
    df_tipo_avg = df_tipo_avg.groupby("tipo_dia")["cantidad_vendida"].mean().reset_index()

    dia_tabla = [["Tipo de Día", "Promedio de Platos Vendidos", "Comparación"]]
    base = df_tipo_avg.loc[df_tipo_avg["tipo_dia"] == "entre_semana", "cantidad_vendida"].values
    base_val = float(base[0]) if len(base) > 0 else 1.0

    orden_tipo = ["entre_semana", "sabado", "festivo", "domingo", "festivo_especial"]
    df_tipo_avg["tipo_dia"] = pd.Categorical(df_tipo_avg["tipo_dia"], categories=orden_tipo, ordered=True)
    df_tipo_avg = df_tipo_avg.sort_values("tipo_dia")

    for _, row in df_tipo_avg.iterrows():
        label    = tipo_labels.get(row["tipo_dia"], row["tipo_dia"])
        promedio = row["cantidad_vendida"]
        ratio    = promedio / base_val if base_val > 0 else 1.0
        if row["tipo_dia"] == "entre_semana":
            comparacion = "Base de referencia"
        else:
            comparacion = f"{ratio:.1f}x más que entre semana"
        dia_tabla.append([label, f"{promedio:.0f} unidades", comparacion])

    t_dia = Table(dia_tabla, colWidths=[5*cm, 5.5*cm, 6.5*cm])
    t_dia.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), VERDE_OSCURO),
        ("TEXTCOLOR",   (0, 0), (-1, 0), BLANCO),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, FONDO_GRIS]),
        ("GRID",        (0, 0), (-1, -1), 0.5, GRIS_LINEA),
        ("ROWPADDING",  (0, 0), (-1, -1), 8),
        ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    contenido.append(KeepTogether([t_dia]))
    contenido.append(
        Paragraph(
            "Los domingos el restaurante suele vender aproximadamente 3 veces más que un día entre semana. "
            "Esto es fundamental para planificar la producción y las compras de insumos.",
            cuerpo,
        )
    )
    contenido.append(Spacer(1, 0.5*cm))

    # ── SECCIÓN 5: QUÉ TAN PRECISAS SON LAS PREDICCIONES ────────────────
    if comp_data is not None and len(comp_data) > 0:
        contenido.append(KeepTogether([
            Paragraph("5. ¿Qué tan bien predijo el sistema?", seccion_titulo),
            HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8),
        ]))

        mape_periodo = comp_data["error_pct"].mean()
        acierto      = max(0, 100 - mape_periodo)

        contenido.append(
            Paragraph(
                f"Durante este período, el sistema acertó en aproximadamente el "
                f"<b>{acierto:.0f}%</b> de sus predicciones de ventas. "
                f"En promedio, la diferencia entre lo que se predijo y lo que realmente se vendió fue de "
                f"<b>{comp_data['error_abs'].mean():.1f} unidades por plato</b>.",
                cuerpo,
            )
        )
        contenido.append(
            Paragraph(
                f"Nota técnica: MAPE del período = {mape_periodo:.1f}%  ·  "
                f"MAE = {comp_data['error_abs'].mean():.2f}  ·  "
                f"Comparaciones realizadas = {len(comp_data)}",
                nota_tecnica,
            )
        )

        comp_tabla = [["Plato", "Lo que se predijo", "Lo que se vendió", "Diferencia"]]
        comp_resumen = comp_data.groupby("nombre_plato").agg(
            predicho=("cantidad_predicha", "sum"),
            real=("venta_real", "sum"),
        ).reset_index()
        comp_resumen["diff"] = comp_resumen["real"] - comp_resumen["predicho"]

        for _, row in comp_resumen.iterrows():
            diff_str = f"+{int(row['diff'])}" if row["diff"] >= 0 else str(int(row["diff"]))
            comp_tabla.append([
                row["nombre_plato"],
                f"{int(row['predicho']):,}",
                f"{int(row['real']):,}",
                diff_str,
            ])

        t_comp = Table(comp_tabla, colWidths=[6*cm, 3.5*cm, 3.5*cm, 4*cm])
        t_comp.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), VERDE_OSCURO),
            ("TEXTCOLOR",   (0, 0), (-1, 0), BLANCO),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, FONDO_GRIS]),
            ("GRID",        (0, 0), (-1, -1), 0.5, GRIS_LINEA),
            ("ROWPADDING",  (0, 0), (-1, -1), 6),
            ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ]))
        contenido.append(KeepTogether([t_comp]))
        contenido.append(Spacer(1, 0.5*cm))

    # ── SECCIÓN 6: ESTADO DEL MODELO (solo si hay info) ──────────────────
    if modelo_info:
        contenido.append(KeepTogether([
            Paragraph("6. Estado del Sistema de Predicción", seccion_titulo),
            HRFlowable(width="100%", thickness=1, color=VERDE_CLARO, spaceAfter=8),
        ]))

        mape_m  = modelo_info["mape"]
        r2_m    = modelo_info["r2"]
        acierto_m = max(0, 100 - mape_m)

        contenido.append(
            Paragraph(
                f"El sistema de inteligencia artificial está funcionando correctamente. "
                f"Fue entrenado con <b>{modelo_info.get('n_registros', 0):,} registros</b> históricos del restaurante "
                f"y tiene una precisión del <b>{acierto_m:.0f}%</b> en sus predicciones.",
                cuerpo,
            )
        )

        estado_data = [
            ["✔  Precisión del sistema", f"{acierto_m:.0f}% de acierto en promedio"],
            ["✔  Error promedio por predicción", f"{modelo_info['mae']:.1f} unidades"],
            ["✔  Versión del modelo", modelo_info.get("version", "N/A")],
            ["✔  Último entrenamiento", str(modelo_info.get("entrenado_en", "N/A"))[:16]],
            ["✔  Registros de entrenamiento", f"{modelo_info.get('n_registros', 0):,}"],
        ]
        contenido.append(Spacer(1, 0.2*cm))

        nota_str = (
            f"Nota técnica: MAPE = {mape_m:.1f}%  ·  R² = {r2_m:.4f}  ·  "
            f"RMSE = {modelo_info['rmse']:.2f}  ·  Algoritmo: Random Forest Regressor (200 árboles)"
        )

        t_estado = Table(estado_data, colWidths=[7*cm, 10*cm])
        t_estado.setStyle(TableStyle([
            ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 0), (-1, -1), 10),
            ("FONTNAME",    (1, 0), (1, -1), "Helvetica-Bold"),
            ("TEXTCOLOR",   (1, 0), (1, -1), VERDE_OSCURO),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BLANCO, FONDO_GRIS]),
            ("GRID",        (0, 0), (-1, -1), 0.5, GRIS_LINEA),
            ("ROWPADDING",  (0, 0), (-1, -1), 7),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ]))
        contenido.append(KeepTogether([t_estado]))
        contenido.append(Paragraph(nota_str, nota_tecnica))
        contenido.append(Spacer(1, 0.5*cm))

    # ── PIE DE PÁGINA ────────────────────────────────────────────────────
    contenido.append(HRFlowable(width="100%", thickness=1, color=GRIS_LINEA, spaceAfter=6))
    contenido.append(
        Paragraph(
            f"FoodSmart Predictor · Restaurante La 22 · Bucaramanga, Colombia  ·  "
            f"Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
            pie_pagina,
        )
    )

    doc.build(contenido)
    buffer.seek(0)
    return buffer.getvalue()


# ── TABS ─────────────────────────────────────────────────────────────────
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
        df["ingreso"]     = df["cantidad_vendida"] * df["precio_unitario"]

        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        with col_k1:
            st.metric("Total Unidades",  f"{df['cantidad_vendida'].sum():,}")
        with col_k2:
            st.metric("Ingreso Total",   f"${df['ingreso'].sum():,.0f}")
        with col_k3:
            st.metric("Promedio Diario", f"{df.groupby('fecha_venta')['cantidad_vendida'].sum().mean():.0f} uds")
        with col_k4:
            st.metric("Días con Datos",  f"{df['fecha_venta'].nunique()}")

        st.divider()

        # Ventas por plato
        st.markdown("#### Ventas por Plato")
        df_plato = df.groupby(["nombre_plato", "categoria_plato"]).agg(
            total_uds=("cantidad_vendida", "sum"),
            ingreso_total=("ingreso", "sum"),
        ).reset_index().sort_values("total_uds", ascending=False)

        fig = px.bar(
            df_plato, x="total_uds", y="nombre_plato", orientation="h",
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

        st.markdown("#### Tabla Resumen")
        df_plato_display = df_plato.copy()
        df_plato_display.columns = ["Plato", "Categoría", "Unidades Vendidas", "Ingreso Total"]
        df_plato_display["Ingreso Total"] = df_plato_display["Ingreso Total"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(df_plato_display, use_container_width=True, hide_index=True)

        # ── Botones de descarga ──────────────────────────────────────────
        st.markdown("#### 📥 Exportar Reporte")
        col_csv, col_pdf = st.columns(2)

        with col_csv:
            csv = df_plato.to_csv(index=False)
            st.download_button(
                "📥 Descargar CSV",
                csv,
                f"reporte_ventas_{fecha_ini}_{fecha_fin_rep}.csv",
                "text/csv",
                use_container_width=True,
            )

        with col_pdf:
            # Intentar obtener comparación si existe
            pred_df_t1   = obtener_predicciones(fecha_inicio=fecha_ini, fecha_fin=fecha_fin_rep)
            ventas_df_t1 = df.copy()
            comp_data_pdf = None

            if len(pred_df_t1) > 0:
                ventas_agg_t1 = ventas_df_t1.groupby(["fecha_venta", "nombre_plato"])["cantidad_vendida"].sum().reset_index()
                ventas_agg_t1.rename(columns={"fecha_venta": "fecha_prediccion", "cantidad_vendida": "venta_real"}, inplace=True)
                # Convertir ambas columnas al mismo tipo antes del merge
                pred_df_t1["fecha_prediccion"]    = pd.to_datetime(pred_df_t1["fecha_prediccion"]).dt.date.astype(str)
                ventas_agg_t1["fecha_prediccion"] = pd.to_datetime(ventas_agg_t1["fecha_prediccion"]).dt.date.astype(str)
                merged = pred_df_t1.merge(ventas_agg_t1, on=["fecha_prediccion", "nombre_plato"], how="inner")
                if len(merged) > 0:
                    merged["error_abs"] = abs(merged["cantidad_predicha"] - merged["venta_real"])
                    merged["error_pct"] = (merged["error_abs"] / merged["venta_real"].clip(lower=1)) * 100
                    comp_data_pdf = merged

            modelo_info_pdf = obtener_modelo_activo()

            # Generar PDF directamente al hacer clic
            try:
                pdf_bytes = generar_pdf(
                    df.copy(), fecha_ini, fecha_fin_rep,
                    modelo_info=modelo_info_pdf,
                    comp_data=comp_data_pdf,
                )
                st.download_button(
                    label="📄 Descargar Reporte PDF",
                    data=pdf_bytes,
                    file_name=f"reporte_la22_{fecha_ini}_{fecha_fin_rep}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
            except Exception as e:
                st.error(f"Error al generar el PDF: {str(e)}")
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

    pred_df  = obtener_predicciones(fecha_inicio=fecha_comp_ini, fecha_fin=fecha_comp_fin)
    ventas_df = obtener_ventas_historicas(fecha_inicio=fecha_comp_ini, fecha_fin=fecha_comp_fin)

    if len(pred_df) > 0 and len(ventas_df) > 0:
        ventas_agg = ventas_df.groupby(["fecha_venta", "nombre_plato"])["cantidad_vendida"].sum().reset_index()
        ventas_agg.rename(columns={"fecha_venta": "fecha_prediccion", "cantidad_vendida": "venta_real"}, inplace=True)

        comp = pred_df.merge(ventas_agg, on=["fecha_prediccion", "nombre_plato"], how="inner")

        if len(comp) > 0:
            comp["error_abs"] = abs(comp["cantidad_predicha"] - comp["venta_real"])
            comp["error_pct"] = (comp["error_abs"] / comp["venta_real"].clip(lower=1)) * 100

            mae  = comp["error_abs"].mean()
            mape = comp["error_pct"].mean()
            r2   = 1 - (((comp["venta_real"] - comp["cantidad_predicha"]) ** 2).sum() /
                        ((comp["venta_real"] - comp["venta_real"].mean()) ** 2).sum()) if len(comp) > 1 else 0

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("MAE del período",  f"{mae:.2f} uds")
            with col_m2:
                st.metric("MAPE del período", f"{mape:.1f}%")
            with col_m3:
                st.metric("R² del período",   f"{r2:.4f}")

            comp_diario = comp.groupby("fecha_prediccion").agg(
                predicho=("cantidad_predicha", "sum"),
                real=("venta_real", "sum"),
            ).reset_index()

            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(
                x=comp_diario["fecha_prediccion"], y=comp_diario["predicho"],
                mode="lines+markers", name="Predicción",
                line=dict(color="#2a9d8f", width=2),
            ))
            fig_comp.add_trace(go.Scatter(
                x=comp_diario["fecha_prediccion"], y=comp_diario["real"],
                mode="lines+markers", name="Venta Real",
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

            st.markdown("#### Detalle por Plato")
            comp_plato = comp.groupby("nombre_plato").agg(
                predicho_total=("cantidad_predicha", "sum"),
                real_total=("venta_real", "sum"),
                error_medio=("error_abs", "mean"),
                mape_plato=("error_pct", "mean"),
            ).reset_index().sort_values("real_total", ascending=False)

            comp_plato.columns = ["Plato", "Total Predicho", "Total Real", "Error Medio", "MAPE %"]
            comp_plato["Total Predicho"] = comp_plato["Total Predicho"].round(0).astype(int)
            comp_plato["Error Medio"]    = comp_plato["Error Medio"].round(1)
            comp_plato["MAPE %"]         = comp_plato["MAPE %"].round(1)
            st.dataframe(comp_plato, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos coincidentes entre predicciones y ventas reales para este período.")
    else:
        st.info("Se necesitan tanto predicciones como ventas reales registradas para el mismo período.")

# ── Tab 3: Tendencias ────────────────────────────────────────────────────
with tab3:
    st.markdown("### Tendencias de Ventas")

    df_all = obtener_ventas_historicas()
    if len(df_all) > 0:
        df_all["fecha_venta"] = pd.to_datetime(df_all["fecha_venta"])
        df_all["mes"] = df_all["fecha_venta"].dt.to_period("M").astype(str)

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