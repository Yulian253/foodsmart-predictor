# -*- coding: utf-8 -*-
"""
Base de datos MySQL para FoodSmart Predictor.
Conexión a MySQL (Laragon) usando SQLAlchemy + PyMySQL.
"""
import pandas as pd
import pymysql
from sqlalchemy import create_engine, text
from datetime import datetime, date
import os

# ── Datos de conexión MySQL (Laragon) ────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("FS_HOST", "localhost"),
    "port":     int(os.getenv("FS_PORT", 3306)),
    "user":     os.getenv("FS_USER", "root"),
    "password": os.getenv("FS_PASSWORD", ""),
    "database": os.getenv("FS_DATABASE", "foodsmart_la22"),
    "charset":  "utf8mb4",
}

# SQLAlchemy engine (para pd.read_sql)
_engine = None


def get_engine():
    """Retorna el engine de SQLAlchemy (singleton)."""
    global _engine
    if _engine is None:
        url = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            f"?charset={DB_CONFIG['charset']}"
        )
        _engine = create_engine(url, pool_recycle=3600, pool_pre_ping=True)
    return _engine


def get_connection():
    """Retorna una conexión directa PyMySQL."""
    return pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        charset=DB_CONFIG["charset"],
        cursorclass=pymysql.cursors.DictCursor,
    )


def crear_base_de_datos():
    """En Railway la BD ya existe, no necesita crearse."""
    pass


def init_database():
    """Crea la base de datos y todas las tablas si no existen."""
    crear_base_de_datos()

    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas_historicas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fecha_venta DATE NOT NULL,
                nombre_plato VARCHAR(100) NOT NULL,
                categoria_plato VARCHAR(50) NOT NULL,
                cantidad_vendida INT NOT NULL,
                tipo_venta VARCHAR(20) NOT NULL DEFAULT 'total',
                precio_unitario INT NOT NULL DEFAULT 0,
                dia_semana VARCHAR(20) NOT NULL,
                tipo_dia VARCHAR(30) NOT NULL,
                registrado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_fecha (fecha_venta),
                INDEX idx_plato (nombre_plato)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predicciones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fecha_prediccion DATE NOT NULL,
                nombre_plato VARCHAR(100) NOT NULL,
                categoria_plato VARCHAR(50) NOT NULL,
                cantidad_predicha FLOAT NOT NULL,
                tipo_dia VARCHAR(30) NOT NULL,
                dia_semana VARCHAR(20) NOT NULL,
                generado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_pred_fecha (fecha_prediccion)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS modelos_ml (
                id INT AUTO_INCREMENT PRIMARY KEY,
                version VARCHAR(50) NOT NULL,
                mae FLOAT,
                rmse FLOAT,
                mape FLOAT,
                r2 FLOAT,
                n_registros INT,
                estado VARCHAR(20) DEFAULT 'activo',
                entrenado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre_insumo VARCHAR(100) NOT NULL UNIQUE,
                categoria VARCHAR(50) NOT NULL,
                cantidad_actual FLOAT NOT NULL DEFAULT 0,
                unidad VARCHAR(20) NOT NULL DEFAULT 'kg',
                stock_minimo FLOAT NOT NULL DEFAULT 0,
                actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alertas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tipo VARCHAR(30) NOT NULL,
                mensaje TEXT NOT NULL,
                nivel VARCHAR(20) NOT NULL DEFAULT 'info',
                leida TINYINT DEFAULT 0,
                creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(64) NOT NULL,
                rol VARCHAR(20) NOT NULL DEFAULT 'cocina',
                activo TINYINT DEFAULT 1,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_acceso TIMESTAMP NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Crear usuario admin por defecto si no existe
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE username = 'admin'")
        if cursor.fetchone()["total"] == 0:
            import hashlib
            pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute(
                """INSERT INTO usuarios (nombre, username, password_hash, rol)
                   VALUES ('Administrador Principal', 'admin', %s, 'administrador')""",
                (pwd_hash,)
            )
            # Usuario de cocina por defecto
            pwd_chef = hashlib.sha256("cocina123".encode()).hexdigest()
            cursor.execute(
                """INSERT INTO usuarios (nombre, username, password_hash, rol)
                   VALUES ('Jefe de Cocina', 'cocina', %s, 'cocina')""",
                (pwd_chef,)
            )

    conn.commit()
    conn.close()


def cargar_csv_inicial(csv_path: str):
    """Carga el CSV histórico en MySQL si la tabla está vacía."""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as total FROM ventas_historicas")
        count = cursor.fetchone()["total"]

    if count > 0:
        conn.close()
        return count

    # Leer CSV con pandas y cargar a MySQL
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    engine = get_engine()
    df.to_sql("ventas_historicas", engine, if_exists="append", index=False)

    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as total FROM ventas_historicas")
        total = cursor.fetchone()["total"]
    conn.close()
    return total


def obtener_ventas_historicas(fecha_inicio=None, fecha_fin=None):
    """Retorna DataFrame con ventas históricas filtradas."""
    query = "SELECT * FROM ventas_historicas WHERE 1=1"
    params = {}
    if fecha_inicio:
        query += " AND fecha_venta >= %(fecha_inicio)s"
        params["fecha_inicio"] = str(fecha_inicio)
    if fecha_fin:
        query += " AND fecha_venta <= %(fecha_fin)s"
        params["fecha_fin"] = str(fecha_fin)
    query += " ORDER BY fecha_venta DESC"

    engine = get_engine()
    df = pd.read_sql(query, engine, params=params)
    return df


def obtener_ventas_df_completo():
    """Retorna DataFrame completo para entrenamiento del modelo."""
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM ventas_historicas ORDER BY fecha_venta", engine)
    return df


def registrar_ventas_dia(fecha, ventas: dict, tipo_dia: str, dia_semana: str):
    """
    Registra las ventas del día en MySQL.
    ventas = {nombre_plato: {cantidad, precio, categoria}, ...}
    """
    conn = get_connection()
    with conn.cursor() as cursor:
        # Eliminar registros previos de esa fecha tipo 'total' (por si se corrige)
        cursor.execute(
            "DELETE FROM ventas_historicas WHERE fecha_venta = %s AND tipo_venta = 'total'",
            (str(fecha),),
        )

        for plato, info in ventas.items():
            if info["cantidad"] > 0:
                cursor.execute(
                    """INSERT INTO ventas_historicas 
                       (fecha_venta, nombre_plato, categoria_plato, cantidad_vendida,
                        tipo_venta, precio_unitario, dia_semana, tipo_dia)
                       VALUES (%s, %s, %s, %s, 'total', %s, %s, %s)""",
                    (
                        str(fecha),
                        plato,
                        info["categoria"],
                        info["cantidad"],
                        info["precio"],
                        dia_semana,
                        tipo_dia,
                    ),
                )

    conn.commit()
    conn.close()

    crear_alerta(
        "registro",
        f"Ventas del {fecha.strftime('%d/%m/%Y')} registradas correctamente.",
        "success",
    )


def obtener_predicciones(fecha_inicio=None, fecha_fin=None):
    query = "SELECT * FROM predicciones WHERE 1=1"
    params = {}
    if fecha_inicio:
        query += " AND fecha_prediccion >= %(fi)s"
        params["fi"] = str(fecha_inicio)
    if fecha_fin:
        query += " AND fecha_prediccion <= %(ff)s"
        params["ff"] = str(fecha_fin)
    query += " ORDER BY fecha_prediccion, nombre_plato"

    engine = get_engine()
    return pd.read_sql(query, engine, params=params)


def guardar_predicciones(predicciones_df: pd.DataFrame):
    """Guarda predicciones en MySQL."""
    conn = get_connection()
    with conn.cursor() as cursor:
        for _, row in predicciones_df.iterrows():
            cursor.execute(
                "DELETE FROM predicciones WHERE fecha_prediccion = %s AND nombre_plato = %s",
                (str(row["fecha_prediccion"]), row["nombre_plato"]),
            )
            cursor.execute(
                """INSERT INTO predicciones 
                   (fecha_prediccion, nombre_plato, categoria_plato, 
                    cantidad_predicha, tipo_dia, dia_semana)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    str(row["fecha_prediccion"]),
                    row["nombre_plato"],
                    row["categoria_plato"],
                    float(row["cantidad_predicha"]),
                    row["tipo_dia"],
                    row["dia_semana"],
                ),
            )
    conn.commit()
    conn.close()


def guardar_modelo_info(version, mae, rmse, mape, r2, n_registros):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE modelos_ml SET estado = 'archivado' WHERE estado = 'activo'")
        cursor.execute(
            """INSERT INTO modelos_ml (version, mae, rmse, mape, r2, n_registros, estado)
               VALUES (%s, %s, %s, %s, %s, %s, 'activo')""",
            (version, mae, rmse, mape, r2, n_registros),
        )
    conn.commit()
    conn.close()


def obtener_modelo_activo():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM modelos_ml WHERE estado = 'activo' ORDER BY entrenado_en DESC LIMIT 1"
        )
        row = cursor.fetchone()
    conn.close()
    return row


def crear_alerta(tipo, mensaje, nivel="info"):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO alertas (tipo, mensaje, nivel) VALUES (%s, %s, %s)",
            (tipo, mensaje, nivel),
        )
    conn.commit()
    conn.close()


def obtener_alertas(solo_no_leidas=False, limite=50):
    conn = get_connection()
    with conn.cursor() as cursor:
        query = "SELECT * FROM alertas"
        if solo_no_leidas:
            query += " WHERE leida = 0"
        query += f" ORDER BY creada_en DESC LIMIT {limite}"
        cursor.execute(query)
        rows = cursor.fetchall()
    conn.close()
    return rows


def marcar_alerta_leida(alerta_id):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE alertas SET leida = 1 WHERE id = %s", (alerta_id,))
    conn.commit()
    conn.close()


def obtener_resumen_ventas_periodo(dias=7):
    engine = get_engine()
    df = pd.read_sql(
        f"""SELECT fecha_venta, nombre_plato, categoria_plato, 
                   SUM(cantidad_vendida) as total_vendido,
                   SUM(cantidad_vendida * precio_unitario) as ingreso_total
            FROM ventas_historicas 
            WHERE fecha_venta >= DATE_SUB(CURDATE(), INTERVAL {dias} DAY)
            GROUP BY fecha_venta, nombre_plato, categoria_plato
            ORDER BY fecha_venta DESC""",
        engine,
    )
    return df


# ── Funciones de Usuarios ────────────────────────────────────────────────

def login_usuario(username: str, password: str):
    """
    Verifica credenciales. Retorna el dict del usuario si OK, None si falla.
    """
    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT id, nombre, username, rol, activo
               FROM usuarios
               WHERE username = %s AND password_hash = %s AND activo = 1""",
            (username, pwd_hash),
        )
        user = cursor.fetchone()
        if user:
            cursor.execute(
                "UPDATE usuarios SET ultimo_acceso = NOW() WHERE id = %s",
                (user["id"],),
            )
    conn.commit()
    conn.close()
    return user


def obtener_usuarios():
    """Retorna lista de todos los usuarios."""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, nombre, username, rol, activo, creado_en, ultimo_acceso "
            "FROM usuarios ORDER BY rol, nombre"
        )
        rows = cursor.fetchall()
    conn.close()
    return rows


def crear_usuario(nombre: str, username: str, password: str, rol: str):
    """Crea un nuevo usuario. Retorna True si OK, False si username duplicado."""
    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO usuarios (nombre, username, password_hash, rol) VALUES (%s, %s, %s, %s)",
                (nombre, username, pwd_hash, rol),
            )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def editar_usuario(user_id: int, nombre: str, rol: str, activo: int, nueva_password: str = None):
    """Edita nombre, rol y estado de un usuario. Opcionalmente cambia contraseña."""
    import hashlib
    conn = get_connection()
    with conn.cursor() as cursor:
        if nueva_password:
            pwd_hash = hashlib.sha256(nueva_password.encode()).hexdigest()
            cursor.execute(
                "UPDATE usuarios SET nombre=%s, rol=%s, activo=%s, password_hash=%s WHERE id=%s",
                (nombre, rol, activo, pwd_hash, user_id),
            )
        else:
            cursor.execute(
                "UPDATE usuarios SET nombre=%s, rol=%s, activo=%s WHERE id=%s",
                (nombre, rol, activo, user_id),
            )
    conn.commit()
    conn.close()


def eliminar_usuario(user_id: int):
    """Desactiva (baja lógica) un usuario. No elimina físicamente."""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE usuarios SET activo = 0 WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
