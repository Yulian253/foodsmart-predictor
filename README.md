# FoodSmart Predictor — Restaurante La 22

Sistema de Predicción de Ventas con Machine Learning  
Streamlit + Python + Random Forest + MySQL (Laragon)

---

## Instalación Paso a Paso

### Prerrequisitos
- **Laragon** instalado con MySQL corriendo (botón verde)
- **Python 3.10+** instalado

### Paso 1: Copiar el proyecto
Copia la carpeta `foodsmart_predictor` a:
```
C:\laragon\www\foodsmart_predictor
```

### Paso 2: Instalar dependencias
Abre la terminal de Laragon y ejecuta:
```bash
cd C:\laragon\www\foodsmart_predictor
pip install -r requirements.txt
```

### Paso 3: Configurar la base de datos MySQL
```bash
python setup_db.py
```
Esto crea la base de datos `foodsmart_la22` en MySQL, las 5 tablas, e importa los 10,753 registros del CSV.

**Si tu MySQL tiene contraseña**, edita `utils/database.py` y cambia:
```python
"password": ""  →  "password": "tu_contraseña"
```

### Paso 4: Ejecutar la aplicación
```bash
streamlit run app.py
```
Se abre en `http://localhost:8501`

### Paso 5: Entrenar el modelo
En la app, ve a **Modelo ML** → **Entrenar Modelo Ahora**

---

## Flujo de Datos

```
CSV (una sola vez) → MySQL (ventas_historicas)
                         ↓
                    pd.read_sql() → DataFrame
                         ↓
                    Random Forest → modelo_rf.pkl
                         ↓
                    Predicciones → MySQL (predicciones)
                         ↓
                    Registro ventas → MySQL (ventas_historicas)
                         ↓
                    Reentrenar → modelo_rf.pkl actualizado
```

Los datos siempre viven en MySQL. El CSV solo se usa para la carga inicial.
