# Análisis de rentabilidad del alquiler turístico en Madrid

Proyecto de **Business Analytics** realizado durante mi especialización en Data Science en Madrid. Responde a una pregunta de negocio: **¿dónde y qué tipo de inmueble comprar para maximizar la rentabilidad del alquiler turístico?**

📊 **Informe interactivo:** https://kacs97.github.io/1.-ANALISIS-AIRBNB-ALQUILER-TURISTICO/informe/

## Resultados principales

| Hallazgo | Resultado |
|---|---|
| Rentabilidad alta con poca inversión | 62 apartamentos con rentabilidad bruta ≥ 15% y menos de 150.000 € de inversión (Puente de Vallecas, Carabanchel y Usera) |
| Barrios destacados | Comillas (Carabanchel) con 10,6% de rentabilidad mediana y coste mediano de 186.664 €, frente al 5,1% de Madrid |
| Perfil que mejor rinde | Apartamento entero de 2 habitaciones y 4+ personas en Latina, Carabanchel, Arganzuela y Centro: 7,5% mediano (+48% sobre la mediana de Madrid) |
| Riesgo de elegir mal | La habitación privada o compartida rinde 1,7% frente al 5,6% del apartamento entero |

**Recomendación:** priorizar apartamentos enteros de 2 habitaciones en Latina, Carabanchel, Arganzuela y Centro, con Puente de Vallecas y Ciudad Lineal como segunda línea.

## Metodología

- **Margen bruto (%)** = ingresos anuales ÷ coste de adquisición × 100.
  - Ingresos anuales = precio por noche × ocupación estimada de 365 días.
  - Coste de adquisición = m² estimados × precio €/m² del distrito (Idealista) × 0,75.
- **Minicubos:** métricas precalculadas (mediana) para cada dimensión (distrito, barrio, tipo, habitaciones, capacidad). Ver [docs/metodologia_minicubos.md](docs/metodologia_minicubos.md).
- **Score turístico:** cercanía a 20 puntos de interés de Madrid ponderados por importancia (0–100).
- **Mediana** en lugar de media y **mínimo de 30 registros** por distrito para que las comparaciones sean fiables.

## Estructura del repositorio

```
├── notebooks/
│   ├── 01.Importacion_Datos.ipynb      # Carga, limpieza y base de datos SQLite
│   ├── 02.Creacion_Variables.ipynb     # Variables de negocio y tablón analítico
│   └── 03. Analisis.ipynb              # Minicubo, gráficos, insights y mapas
├── funciones/
│   ├── funciones.py                    # Score turístico y mapa de calor
│   ├── scraping_idealista.py           # Extracción del precio/m² por distrito
│   ├── construir_informe.py            # Genera el informe HTML
│   └── plantilla_informe.html          # Plantilla del informe
├── docs/
│   ├── informe/                        # Informe publicado (GitHub Pages)
│   ├── mapa_*.html                     # Mapas interactivos
│   └── metodologia_minicubos.md
└── requirements.txt
```

## Cómo reproducirlo

1. Instalar las dependencias: `pip install -r requirements.txt`
2. Datos: solo se incluye el CSV pequeño de Idealista; el resto se genera o se descarga:
   - Airbnb: `01.Importacion_Datos.ipynb` los descarga desde [Inside Airbnb](https://insideairbnb.com/get-the-data/).
   - Idealista: el precio medio del m² por distrito ya está en `datos/brutos/precio_m2_distritos_madrid.csv` (se generó con `funciones/scraping_idealista.py`).
   - La base SQLite `datos/intermedios/mercado_inmobiliario.db` se incluye ya generada (el notebook 01 la vuelve a crear); permite ejecutar directamente los notebooks 02 y 03.
3. Ejecutar los notebooks en orden: 01, 02 y 03.
4. Regenerar el informe: `python funciones/construir_informe.py`

## Tecnologías

Python · pandas · NumPy · matplotlib · seaborn · folium · SQLite · Jupyter

## Fuentes y limitaciones

- Datos de [Inside Airbnb](https://insideairbnb.com) (según su política de datos) y precios de Idealista.
- La ocupación y el coste de adquisición son **estimaciones**. El margen bruto no incluye gastos operativos, impuestos, reforma ni financiación.
- Hay distritos con pocos anuncios (Vicálvaro, Moratalaz, Barajas), por lo que sus resultados no son concluyentes.

---

Elaborado por **Kelvin Carrero**.
