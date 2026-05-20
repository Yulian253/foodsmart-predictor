# -*- coding: utf-8 -*-
"""
Gestión de Usuarios — Solo Administradores
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.theme import DARK_THEME_CSS
from utils.auth import verificar_sesion, sidebar_usuario, ROLES, get_usuario_actual
from utils.database import obtener_usuarios, crear_usuario, editar_usuario, eliminar_usuario, obtener_modelo_activo, obtener_alertas
from utils.ml_model import modelo_existe

st.set_page_config(page_title="Usuarios — La 22", page_icon="👥", layout="wide")
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# Guard: solo administradores
verificar_sesion(permisos_requeridos=["gestion_usuarios"])

usuario_actual = get_usuario_actual()

with st.sidebar:
    st.markdown('<div class="sidebar-brand"><h2>🍽️ PredictaVentas</h2><p>Restaurante La 22</p></div>', unsafe_allow_html=True)
    modelo_info = obtener_modelo_activo()
    if modelo_existe() and modelo_info:
        st.markdown(f'<span class="model-badge model-active">● MAPE {modelo_info["mape"]:.1f}%</span>', unsafe_allow_html=True)
    st.divider()
    sidebar_usuario()

st.markdown("""
<div class="page-header">
    <div><h2>👥 Gestión de Usuarios</h2>
    <p>Crea, edita y administra los accesos al sistema</p></div>
</div>
""", unsafe_allow_html=True)

tab_lista, tab_nuevo = st.tabs(["👥 Usuarios Registrados", "➕ Crear Usuario"])

# ── Tab 1: Lista de usuarios ─────────────────────────────────────────────
with tab_lista:
    usuarios = obtener_usuarios()

    if not usuarios:
        st.info("No hay usuarios registrados.")
    else:
        # Separar por rol
        admins  = [u for u in usuarios if u["rol"] == "administrador"]
        cocinas = [u for u in usuarios if u["rol"] == "cocina"]

        for grupo, titulo, color, icono in [
            (admins,  "Administradores", "#e9c46a", "👑"),
            (cocinas, "Jefes de Cocina", "#2a9d8f", "👨‍🍳"),
        ]:
            st.markdown(f'<div class="cat-header">{icono} {titulo} ({len(grupo)})</div>', unsafe_allow_html=True)

            if not grupo:
                st.caption("No hay usuarios en este rol.")
                continue

            for u in grupo:
                estado_color = "#3fb950" if u["activo"] else "#e63946"
                estado_txt   = "Activo" if u["activo"] else "Inactivo"
                ultimo = str(u["ultimo_acceso"])[:16] if u["ultimo_acceso"] else "Nunca"

                with st.expander(f"{icono} {u['nombre']} — @{u['username']} · {estado_txt}"):
                    col_i, col_f = st.columns([1, 2])

                    with col_i:
                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-label">Usuario</div>
                            <div style="color:#e6edf3;font-weight:700;font-size:1.1rem;">@{u['username']}</div>
                            <div class="kpi-sub">ID #{u['id']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="kpi-card" style="margin-top:.5rem;">
                            <div class="kpi-label">Último Acceso</div>
                            <div style="color:#c9d1d9;font-size:.95rem;font-weight:600;">{ultimo}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_f:
                        with st.form(f"edit_{u['id']}"):
                            nuevo_nombre = st.text_input("Nombre completo", value=u["nombre"])
                            nuevo_rol    = st.selectbox("Rol", ["administrador", "cocina"],
                                                        index=0 if u["rol"]=="administrador" else 1)
                            nuevo_estado = st.selectbox("Estado", ["Activo", "Inactivo"],
                                                        index=0 if u["activo"] else 1)
                            nueva_pwd    = st.text_input("Nueva contraseña (dejar vacío para no cambiar)",
                                                          type="password", placeholder="••••••••")

                            col_s, col_d = st.columns(2)
                            with col_s:
                                guardar = st.form_submit_button("💾 Guardar", type="primary", use_container_width=True)
                            with col_d:
                                # No permitir eliminar al propio usuario
                                deshabilitar = (u["id"] == usuario_actual["id"])
                                eliminar = st.form_submit_button("🗑️ Desactivar",
                                                                  use_container_width=True,
                                                                  disabled=deshabilitar)

                        if guardar:
                            editar_usuario(
                                u["id"], nuevo_nombre, nuevo_rol,
                                1 if nuevo_estado == "Activo" else 0,
                                nueva_pwd if nueva_pwd else None,
                            )
                            st.success(f"✅ Usuario @{u['username']} actualizado.")
                            st.rerun()

                        if eliminar:
                            eliminar_usuario(u["id"])
                            st.warning(f"⚠️ Usuario @{u['username']} desactivado.")
                            st.rerun()

            st.markdown("---")

# ── Tab 2: Crear usuario ─────────────────────────────────────────────────
with tab_nuevo:
    st.markdown('<div class="section-card"><h4>➕ Nuevo Usuario</h4></div>', unsafe_allow_html=True)

    col_form, col_info = st.columns([1, 1])

    with col_form:
        with st.form("crear_usuario"):
            nombre   = st.text_input("Nombre completo *", placeholder="Ej: María López")
            username = st.text_input("Usuario *", placeholder="Ej: maria.lopez")
            password = st.text_input("Contraseña *", type="password", placeholder="Mínimo 6 caracteres")
            rol_nuevo = st.selectbox("Rol *", ["administrador", "cocina"],
                                     format_func=lambda r: "👑 Administrador" if r=="administrador" else "👨‍🍳 Jefe de Cocina")

            crear = st.form_submit_button("➕ Crear Usuario", type="primary", use_container_width=True)

        if crear:
            if not nombre or not username or not password:
                st.error("Todos los campos marcados con * son obligatorios.")
            elif len(password) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres.")
            elif " " in username:
                st.error("El nombre de usuario no puede tener espacios.")
            else:
                ok = crear_usuario(nombre.strip(), username.strip().lower(), password, rol_nuevo)
                if ok:
                    st.success(f"✅ Usuario **@{username.strip().lower()}** creado exitosamente con rol **{rol_nuevo}**.")
                    st.rerun()
                else:
                    st.error(f"El nombre de usuario '@{username.strip().lower()}' ya existe. Elige otro.")

    with col_info:
        st.markdown("""
        <div class="section-card">
            <h4>👑 Administrador</h4>
            <p>Tiene acceso completo al sistema:</p>
            <ul style="color:#c9d1d9;padding-left:1.2rem;">
                <li>Dashboard con datos financieros</li>
                <li>Predicciones (diaria, semanal, mensual)</li>
                <li>Registro de ventas</li>
                <li>Modelo ML (entrenar/reentrenar)</li>
                <li>Reportes completos</li>
                <li>Alertas y control de desperdicio</li>
                <li>Inventario y compras</li>
                <li>Gestión de usuarios</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="section-card" style="margin-top:.5rem;">
            <h4>👨‍🍳 Jefe de Cocina</h4>
            <p>Acceso operativo para producción:</p>
            <ul style="color:#c9d1d9;padding-left:1.2rem;">
                <li>Dashboard (sin datos financieros)</li>
                <li>Predicciones (planificar producción)</li>
                <li>Registro de ventas del día</li>
                <li>Alertas de sobreproducción</li>
            </ul>
            <p style="color:#e76f51;margin-top:.5rem;">
                ❌ Sin acceso a: Modelo ML, Reportes financieros, Inventario/Compras, Usuarios
            </p>
        </div>
        """, unsafe_allow_html=True)
