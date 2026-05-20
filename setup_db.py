# -*- coding: utf-8 -*-
"""
Script de configuración inicial de FoodSmart Predictor.
Ejecutar UNA SOLA VEZ para:
1. Crear la base de datos 'foodsmart_la22' en MySQL
2. Crear todas las tablas
3. Importar el CSV histórico en la tabla ventas_historicas

Uso:
    python setup_db.py

Requisitos:
    - MySQL corriendo en Laragon (puerto 3306)
    - pip install pymysql sqlalchemy pandas
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("=" * 60)
    print("  FoodSmart Predictor — Configuración de Base de Datos")
    print("  Restaurante La 22 — MySQL (Laragon)")
    print("=" * 60)
    print()

    # 1. Verificar conexión a MySQL
    print("[1/4] Verificando conexión a MySQL...")
    try:
        import pymysql
        conn = pymysql.connect(
            host="localhost", port=3306,
            user="root", password="",
            charset="utf8mb4",
        )
        conn.close()
        print("  ✅ Conexión a MySQL exitosa (root@localhost:3306)")
    except Exception as e:
        print(f"  ❌ ERROR: No se pudo conectar a MySQL: {e}")
        print()
        print("  Verifica que:")
        print("  - Laragon esté abierto y MySQL esté corriendo (botón verde)")
        print("  - El usuario sea 'root' y la contraseña esté vacía")
        print("  - El puerto sea 3306")
        print()
        print("  Si tu MySQL tiene contraseña, edita utils/database.py")
        print('  y cambia: "password": "" → "password": "tu_contraseña"')
        sys.exit(1)

    # 2. Crear base de datos y tablas
    print("[2/4] Creando base de datos y tablas...")
    try:
        from utils.database import init_database
        init_database()
        print("  ✅ Base de datos 'foodsmart_la22' creada")
        print("  ✅ Tablas creadas: ventas_historicas, predicciones,")
        print("     modelos_ml, inventario, alertas")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        sys.exit(1)

    # 3. Importar CSV
    print("[3/4] Importando CSV histórico...")
    csv_path = os.path.join(os.path.dirname(__file__), "data", "ventas_la22_5.csv")
    if not os.path.exists(csv_path):
        print(f"  ❌ No se encontró: {csv_path}")
        sys.exit(1)

    try:
        from utils.database import cargar_csv_inicial
        n = cargar_csv_inicial(csv_path)
        print(f"  ✅ {n:,} registros cargados en ventas_historicas")
    except Exception as e:
        print(f"  ❌ ERROR al importar CSV: {e}")
        sys.exit(1)

    # 4. Verificar datos
    print("[4/4] Verificando datos en MySQL...")
    try:
        from utils.database import obtener_ventas_df_completo
        df = obtener_ventas_df_completo()
        print(f"  ✅ DataFrame creado exitosamente: {len(df)} registros")
        print(f"  ✅ Platos únicos: {df['nombre_plato'].nunique()}")
        print(f"  ✅ Rango: {df['fecha_venta'].min()} a {df['fecha_venta'].max()}")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  ✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print()
    print("  Ahora puedes ejecutar la aplicación:")
    print("  streamlit run app.py")
    print()
    print("  Los datos ya están en MySQL, no necesitas el CSV.")
    print("  Puedes verificar en phpMyAdmin o HeidiSQL:")
    print("  Base de datos: foodsmart_la22")
    print("  Tabla: ventas_historicas")
    print()


if __name__ == "__main__":
    main()
