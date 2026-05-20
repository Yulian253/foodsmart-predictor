# -*- coding: utf-8 -*-
"""
Módulo de Machine Learning para FoodSmart Predictor.
Random Forest Regressor para predicción de ventas por plato.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib
import os
from datetime import datetime, date, timedelta

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MODEL_PATH = os.path.join(MODEL_DIR, "modelo_rf.pkl")
ENCODERS_PATH = os.path.join(MODEL_DIR, "encoders.pkl")

# ── Carta completa del Restaurante La 22 ──────────────────────────────────
MENU_LA22 = {
    "Sopas": [
        {"nombre": "Lengua en salsa", "precio": 60000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Mute", "precio": 30000, "disponible": ["Sáb", "Dom"]},
        {"nombre": "Sancocho de Gallina", "precio": 60000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Frijoles con Pezuña", "precio": 50000, "disponible": ["L-V", "Sáb"]},
        {"nombre": "Pata", "precio": 27000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Cola de Buey", "precio": 60000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Cazuela de Mariscos", "precio": 53000, "disponible": ["L-V", "Sáb", "Dom"]},
    ],
    "Carnes": [
        {"nombre": "Carne Asada (Chatas)", "precio": 62000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Carne Oreada", "precio": 62000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Cabro con Pepitoria", "precio": 62000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Costillas de Cerdo", "precio": 60000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Lomo de Cerdo", "precio": 60000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Sobrebarriga", "precio": 60000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Pechuga Asada", "precio": 52000, "disponible": ["L-V", "Sáb", "Dom"]},
    ],
    "Pescados": [
        {"nombre": "Mojarra 2en1", "precio": 58000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Trucha 2en1", "precio": 58000, "disponible": ["L-V", "Sáb", "Dom"]},
        {"nombre": "Tierra Aire Mar", "precio": 90000, "disponible": ["L-V", "Sáb", "Dom"]},
    ],
    "Arroces": [
        {"nombre": "Arroz con Pollo", "precio": 52000, "disponible": ["L-V", "Sáb", "Dom"]},
    ],
    "Corrientes": [
        {"nombre": "Almuerzo Ejecutivo", "precio": 25000, "disponible": ["L-V", "Sáb"]},
    ],
}

DIAS_SEMANA_MAP = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo",
}


def obtener_platos_disponibles(fecha: date) -> dict:
    """Retorna los platos disponibles para un día específico."""
    dia_idx = fecha.weekday()
    dia_nombre = DIAS_SEMANA_MAP[dia_idx]

    if dia_idx == 6:
        tipo_disp = "Dom"
    elif dia_idx == 5:
        tipo_disp = "Sáb"
    else:
        tipo_disp = "L-V"

    disponibles = {}
    for categoria, platos in MENU_LA22.items():
        platos_dia = []
        for plato in platos:
            if tipo_disp in plato["disponible"]:
                platos_dia.append(plato)
        if platos_dia:
            disponibles[categoria] = platos_dia

    return disponibles


def clasificar_tipo_dia(fecha: date) -> str:
    """Clasifica el tipo de día."""
    dia_idx = fecha.weekday()
    if dia_idx == 6:
        return "domingo"
    elif dia_idx == 5:
        return "sabado"
    else:
        return "entre_semana"


def obtener_dia_semana(fecha: date) -> str:
    return DIAS_SEMANA_MAP[fecha.weekday()]


def preparar_features(df: pd.DataFrame) -> tuple:
    """
    Feature engineering para el modelo.
    Retorna (X, y, encoders).
    """
    df = df.copy()
    df["fecha_venta"] = pd.to_datetime(df["fecha_venta"])

    # Agregar por fecha + plato (sumar mesa + domicilio)
    df_agg = df.groupby(
        ["fecha_venta", "nombre_plato", "categoria_plato", "dia_semana", "tipo_dia"]
    ).agg({"cantidad_vendida": "sum", "precio_unitario": "first"}).reset_index()

    df_agg = df_agg.sort_values("fecha_venta").reset_index(drop=True)

    # Features temporales
    df_agg["mes"] = df_agg["fecha_venta"].dt.month
    df_agg["dia_mes"] = df_agg["fecha_venta"].dt.day
    df_agg["semana_anio"] = df_agg["fecha_venta"].dt.isocalendar().week.astype(int)

    # Encoding tipo_dia numérico (variable más importante: correlación 0.847)
    tipo_dia_map = {"entre_semana": 0, "sabado": 1, "domingo": 2, "festivo": 1, "festivo_especial": 2}
    df_agg["tipo_dia_cod"] = df_agg["tipo_dia"].map(tipo_dia_map).fillna(0).astype(int)

    # Encoding dia_semana
    dia_map = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
    df_agg["dia_semana_cod"] = df_agg["dia_semana"].map(dia_map).fillna(0).astype(int)

    # Encoding platos y categorías
    le_plato = LabelEncoder()
    le_categoria = LabelEncoder()
    df_agg["plato_cod"] = le_plato.fit_transform(df_agg["nombre_plato"])
    df_agg["categoria_cod"] = le_categoria.fit_transform(df_agg["categoria_plato"])

    # Features de rezago por plato (lag_7 y promedio móvil 7 días)
    df_agg = df_agg.sort_values(["nombre_plato", "fecha_venta"])
    df_agg["lag_7"] = df_agg.groupby("nombre_plato")["cantidad_vendida"].shift(7).fillna(
        df_agg.groupby("nombre_plato")["cantidad_vendida"].transform("mean")
    )
    df_agg["prom_mov_7"] = (
        df_agg.groupby("nombre_plato")["cantidad_vendida"]
        .transform(lambda x: x.rolling(7, min_periods=1).mean().shift(1))
        .fillna(df_agg.groupby("nombre_plato")["cantidad_vendida"].transform("mean"))
    )

    # Features de interacción
    df_agg["plato_x_tipoDia"] = df_agg["plato_cod"] * df_agg["tipo_dia_cod"]

    feature_cols = [
        "plato_cod", "categoria_cod", "tipo_dia_cod", "dia_semana_cod",
        "mes", "dia_mes", "semana_anio", "precio_unitario",
        "lag_7", "prom_mov_7", "plato_x_tipoDia",
    ]

    X = df_agg[feature_cols].values
    y = df_agg["cantidad_vendida"].values

    encoders = {
        "le_plato": le_plato,
        "le_categoria": le_categoria,
        "tipo_dia_map": tipo_dia_map,
        "dia_map": dia_map,
        "feature_cols": feature_cols,
        "promedios_plato": df_agg.groupby("nombre_plato")["cantidad_vendida"].mean().to_dict(),
    }

    return X, y, encoders, df_agg


def entrenar_modelo(df: pd.DataFrame):
    """
    Entrena Random Forest con el dataset completo.
    Retorna métricas y guarda modelo.
    """
    X, y, encoders, df_prep = preparar_features(df)

    # TimeSeriesSplit para validación
    tscv = TimeSeriesSplit(n_splits=5)
    mae_scores, rmse_scores, r2_scores = [], [], []

    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        rf = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
        rf.fit(X_train, y_train)
        y_pred = rf.predict(X_test)

        mae_scores.append(mean_absolute_error(y_test, y_pred))
        rmse_scores.append(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2_scores.append(r2_score(y_test, y_pred))

    # Entrenar modelo final con todos los datos
    modelo_final = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    modelo_final.fit(X, y)

    # Calcular MAPE
    y_pred_full = modelo_final.predict(X)
    mask = y > 0
    mape = np.mean(np.abs((y[mask] - y_pred_full[mask]) / y[mask])) * 100

    # Guardar modelo y encoders
    joblib.dump(modelo_final, MODEL_PATH)
    joblib.dump(encoders, ENCODERS_PATH)

    metricas = {
        "mae": np.mean(mae_scores),
        "rmse": np.mean(rmse_scores),
        "r2": np.mean(r2_scores),
        "mape": mape,
        "n_registros": len(df),
        "feature_importance": dict(
            zip(encoders["feature_cols"], modelo_final.feature_importances_)
        ),
    }

    return metricas


def cargar_modelo():
    """Carga modelo y encoders guardados."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODERS_PATH):
        return None, None
    modelo = joblib.load(MODEL_PATH)
    encoders = joblib.load(ENCODERS_PATH)
    return modelo, encoders


def predecir_dia(fecha: date, df_historico: pd.DataFrame = None) -> pd.DataFrame:
    """
    Genera predicciones para un día específico.
    Retorna DataFrame con predicción por plato.
    """
    modelo, encoders = cargar_modelo()
    if modelo is None:
        return pd.DataFrame()

    tipo_dia = clasificar_tipo_dia(fecha)
    dia_semana = obtener_dia_semana(fecha)
    platos_disponibles = obtener_platos_disponibles(fecha)

    le_plato = encoders["le_plato"]
    le_categoria = encoders["le_categoria"]
    tipo_dia_map = encoders["tipo_dia_map"]
    dia_map = encoders["dia_map"]
    promedios = encoders["promedios_plato"]

    predicciones = []

    for categoria, platos in platos_disponibles.items():
        for plato_info in platos:
            nombre = plato_info["nombre"]
            precio = plato_info["precio"]

            # Encoding
            try:
                plato_cod = le_plato.transform([nombre])[0]
            except ValueError:
                continue
            try:
                cat_cod = le_categoria.transform([categoria])[0]
            except ValueError:
                continue

            tipo_dia_cod = tipo_dia_map.get(tipo_dia, 0)
            dia_cod = dia_map.get(dia_semana, 0)

            fecha_dt = pd.Timestamp(fecha)
            mes = fecha_dt.month
            dia_mes = fecha_dt.day
            semana = fecha_dt.isocalendar()[1]

            # Lag features: usar promedio histórico como proxy
            promedio = promedios.get(nombre, 5)
            lag_7 = promedio
            prom_mov_7 = promedio

            # Si tenemos datos históricos, calcular lag real
            if df_historico is not None and len(df_historico) > 0:
                df_h = df_historico.copy()
                df_h["fecha_venta"] = pd.to_datetime(df_h["fecha_venta"])
                plato_hist = df_h[df_h["nombre_plato"] == nombre].sort_values("fecha_venta")
                if len(plato_hist) > 0:
                    # Agregar por fecha
                    plato_agg = plato_hist.groupby("fecha_venta")["cantidad_vendida"].sum()
                    if len(plato_agg) >= 7:
                        lag_7 = plato_agg.iloc[-7]
                        prom_mov_7 = plato_agg.iloc[-7:].mean()
                    elif len(plato_agg) > 0:
                        lag_7 = plato_agg.iloc[-1]
                        prom_mov_7 = plato_agg.mean()

            plato_x_tipoDia = plato_cod * tipo_dia_cod

            features = np.array([[
                plato_cod, cat_cod, tipo_dia_cod, dia_cod,
                mes, dia_mes, semana, precio,
                lag_7, prom_mov_7, plato_x_tipoDia,
            ]])

            cantidad = max(0, round(modelo.predict(features)[0]))

            predicciones.append({
                "fecha_prediccion": fecha,
                "nombre_plato": nombre,
                "categoria_plato": categoria,
                "cantidad_predicha": cantidad,
                "tipo_dia": tipo_dia,
                "dia_semana": dia_semana,
                "precio_unitario": precio,
                "ingreso_estimado": cantidad * precio,
            })

    return pd.DataFrame(predicciones)


def predecir_rango(fecha_inicio: date, fecha_fin: date, df_historico=None) -> pd.DataFrame:
    """Genera predicciones para un rango de fechas."""
    todas = []
    fecha = fecha_inicio
    while fecha <= fecha_fin:
        pred_dia = predecir_dia(fecha, df_historico)
        if len(pred_dia) > 0:
            todas.append(pred_dia)
        fecha += timedelta(days=1)

    if todas:
        return pd.concat(todas, ignore_index=True)
    return pd.DataFrame()


def modelo_existe() -> bool:
    return os.path.exists(MODEL_PATH) and os.path.exists(ENCODERS_PATH)
