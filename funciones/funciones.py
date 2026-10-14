from pathlib import Path

import folium
import numpy as np
import pandas as pd
from folium.plugins import HeatMap

# ==========================================
# 1. PUNTOS DE INTERÉS TURÍSTICO (MADRID)
# ==========================================
# Pesos: 10 (Hitos mundiales / núcleos primarios), 8-9 (Atracciones top), 5-7 (Interés medio/alto)
MADRID_POIS = [
    {"poi": "Puerta del Sol", "lat": 40.4169, "lon": -3.7035, "peso": 10},
    {"poi": "Plaza Mayor", "lat": 40.4155, "lon": -3.7074, "peso": 10},
    {"poi": "Museo Nacional del Prado", "lat": 40.4138, "lon": -3.6922, "peso": 10},
    {"poi": "Palacio Real de Madrid", "lat": 40.4179, "lon": -3.7143, "peso": 9},
    {"poi": "Parque del Buen Retiro", "lat": 40.4153, "lon": -3.6845, "peso": 9},
    {"poi": "Gran Vía / Callao", "lat": 40.4200, "lon": -3.7058, "peso": 9},
    {"poi": "Museo Reina Sofía", "lat": 40.4080, "lon": -3.6946, "peso": 8},
    {"poi": "Museo Thyssen-Bornemisza", "lat": 40.4161, "lon": -3.6949, "peso": 8},
    {"poi": "Plaza de Cibeles", "lat": 40.4196, "lon": -3.6934, "peso": 8},
    {"poi": "Plaza de España", "lat": 40.4234, "lon": -3.7122, "peso": 8},
    {"poi": "Catedral de la Almudena", "lat": 40.4157, "lon": -3.7146, "peso": 8},
    {"poi": "Estadio Santiago Bernabéu", "lat": 40.4530, "lon": -3.6883, "peso": 8},
    {"poi": "Puerta de Alcalá", "lat": 40.4200, "lon": -3.6887, "peso": 7},
    {"poi": "Templo de Debod", "lat": 40.4240, "lon": -3.7178, "peso": 7},
    {"poi": "Mercado de San Miguel", "lat": 40.4154, "lon": -3.7089, "peso": 7},
    {"poi": "El Rastro (La Latina)", "lat": 40.4105, "lon": -3.7075, "peso": 6},
    {"poi": "Matadero Madrid", "lat": 40.3926, "lon": -3.6978, "peso": 6},
    {"poi": "Madrid Río (Puente de Segovia)", "lat": 40.4140, "lon": -3.7225, "peso": 6},
    {"poi": "Estadio Cívitas Metropolitano", "lat": 40.4362, "lon": -3.5996, "peso": 6},
    {"poi": "Casa de Campo (Teleférico)", "lat": 40.4244, "lon": -3.7431, "peso": 5}
]

df_pois = pd.DataFrame(MADRID_POIS)


# ==========================================
# 2. FUNCIONES DE CÁLCULO ESPACIAL Y SCORE
# ==========================================
def calcular_matriz_haversine(lat1_series, lon1_series, lat2_series, lon2_series):
    """
    Calcula la distancia Haversine en km entre dos conjuntos de coordenadas vectorialmente.
    Retorna una matriz de dimensiones (N_inmuebles, M_pois).
    """
    RADIO_TIERRA_KM = 6371.0088

    lat1 = np.radians(lat1_series.to_numpy())[:, np.newaxis]  # Shape: (N, 1)
    lon1 = np.radians(lon1_series.to_numpy())[:, np.newaxis]
    lat2 = np.radians(lat2_series.to_numpy())[np.newaxis, :]  # Shape: (1, M)
    lon2 = np.radians(lon2_series.to_numpy())[np.newaxis, :]

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))

    return RADIO_TIERRA_KM * c


def calcular_score_turistico(df_propiedades, df_pois, d_max_km=5.0, col_lat='lat', col_lon='lon'):
    """
    Aplica decaimiento lineal ponderado y devuelve la serie de scores entre 0 y 100.
    """
    # 1. Matriz de distancias (N, M)
    distancias = calcular_matriz_haversine(
        df_propiedades[col_lat], df_propiedades[col_lon],
        df_pois['lat'], df_pois['lon']
    )

    # 2. Decaimiento lineal: max(0, 1 - d / d_max)
    factor_lineal = np.maximum(0.0, 1.0 - (distancias / d_max_km))

    # 3. Suma ponderada por el peso del POI (Producto matricial: N x M dot M -> N)
    pesos = df_pois['peso'].to_numpy()
    score_crudo = np.dot(factor_lineal, pesos)

    # 4. Normalización Min-Max a escala 0 - 100
    min_score = score_crudo.min()
    max_score = score_crudo.max()

    if max_score == min_score:
        score_100 = np.zeros_like(score_crudo)
    else:
        score_100 = ((score_crudo - min_score) / (max_score - min_score)) * 100.0

    return score_crudo, np.round(score_100, 2)


def crear_mapa_calor_score(df, ruta_salida=None, col_lat='latitude', col_lon='longitude',
                           col_score='score_turistico', centro=(40.4168, -3.7038), zoom=12):
    """
    Crea un mapa de calor folium ponderado por el score turístico (rojo = mayor, azul = menor).
    Si se indica ruta_salida, lo guarda como HTML. Devuelve el mapa.
    """
    df_mapa = df[[col_lat, col_lon, col_score]].dropna()
    puntos = np.column_stack([
        df_mapa[col_lat].to_numpy(),
        df_mapa[col_lon].to_numpy(),
        df_mapa[col_score].to_numpy() / 100,
    ]).tolist()

    mapa = folium.Map(location=list(centro), zoom_start=zoom, tiles='OpenStreetMap')

    HeatMap(
        puntos,
        radius=12,
        blur=15,
        min_opacity=0.3,
        gradient={0.0: 'blue', 0.4: 'cyan', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'},
    ).add_to(mapa)

    if ruta_salida is not None:
        ruta_salida = Path(ruta_salida)
        mapa.save(ruta_salida)
        print(f"Mapa guardado en: {ruta_salida.resolve()}")

    return mapa