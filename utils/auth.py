# -*- coding: utf-8 -*-
"""
Módulo de Autenticación y Roles — FoodSmart Predictor
Gestiona login, sesiones, roles y permisos.
"""
import streamlit as st
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Roles y permisos ─────────────────────────────────────────────────────
ROLES = {
    "administrador": {
        "label": "Administrador",
        "color": "#e9c46a",
        "icon": "👑",
        "descripcion": "Acceso total al sistema",
        "permisos": [
            "dashboard_financiero",   # ver ingresos y montos
            "predicciones",           # predicciones diaria/semanal/mensual
            "registro_ventas",        # registrar ventas del día
            "modelo_ml",              # entrenar/reentrenar el modelo
            "reportes",               # todos los reportes
            "alertas",                # ver y gestionar alertas
            "inventario",             # gestión de stock y compras
            "gestion_usuarios",       # crear/editar/eliminar usuarios
        ],
    },
    "cocina": {
        "label": "Jefe de Cocina",
        "color": "#2a9d8f",
        "icon": "👨‍🍳",
        "descripcion": "Acceso operativo de producción",
        "permisos": [
            "dashboard_basico",       # solo cantidades, sin montos
            "predicciones",           # ver predicciones para planificar
            "registro_ventas",        # registrar lo vendido al cierre
            "alertas_produccion",     # solo alertas de sobreproducción
        ],
    },
}

# Páginas que cada rol puede ver en el sidebar
PAGINAS_POR_ROL = {
    "administrador": [
        "1_Predicciones",
        "2_Registro_Ventas",
        "3_Modelo_ML",
        "4_Reportes",
        "5_Alertas",
        "6_Inventario",
        "7_Usuarios",
    ],
    "cocina": [
        "1_Predicciones",
        "2_Registro_Ventas",
        "5_Alertas",
    ],
}


def hash_password(password: str) -> str:
    """Hashea la contraseña con SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def tiene_permiso(permiso: str) -> bool:
    """Verifica si el usuario actual tiene un permiso específico."""
    if "usuario" not in st.session_state:
        return False
    rol = st.session_state["usuario"]["rol"]
    return permiso in ROLES.get(rol, {}).get("permisos", [])


def get_usuario_actual():
    """Retorna el usuario de la sesión actual o None."""
    return st.session_state.get("usuario", None)


def is_admin() -> bool:
    u = get_usuario_actual()
    return u is not None and u["rol"] == "administrador"


def is_cocina() -> bool:
    u = get_usuario_actual()
    return u is not None and u["rol"] == "cocina"


def cerrar_sesion():
    """Cierra la sesión del usuario actual."""
    for key in ["usuario", "autenticado"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def verificar_sesion(permisos_requeridos: list = None):
    """
    Verifica que haya sesión activa y que el usuario tenga los permisos.
    Si no, muestra error y detiene la página.
    """
    if not st.session_state.get("autenticado", False):
        st.error("⚠️ Debes iniciar sesión para acceder a esta página.")
        st.stop()

    if permisos_requeridos:
        u = get_usuario_actual()
        rol = u["rol"]
        permisos_usuario = ROLES.get(rol, {}).get("permisos", [])
        for p in permisos_requeridos:
            if p not in permisos_usuario:
                st.error(f"🚫 No tienes permiso para acceder a esta sección.")
                st.info(f"Esta funcionalidad está disponible solo para **Administradores**.")
                st.stop()


def sidebar_usuario():
    """Muestra la info del usuario y botón de cerrar sesión en el sidebar."""
    u = get_usuario_actual()
    if not u:
        return

    rol_info = ROLES.get(u["rol"], {})
    with st.sidebar:
        st.markdown(f"""
        <div style="background:#21262d; border:1px solid #30363d; border-radius:8px;
                    padding:0.8rem; margin-bottom:1rem;">
            <div style="font-size:1.2rem;">{rol_info.get('icon','👤')}
                <strong style="color:#e6edf3;">{u['nombre']}</strong>
            </div>
            <div style="margin-top:0.3rem;">
                <span style="background:{rol_info.get('color','#8b949e')}22;
                      color:{rol_info.get('color','#8b949e')};
                      border:1px solid {rol_info.get('color','#8b949e')};
                      padding:0.15rem 0.6rem; border-radius:10px; font-size:0.78rem;
                      font-weight:600;">
                    {rol_info.get('label','Sin rol')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            cerrar_sesion()
