## Descripción del proyecto

Este proyecto implementa una herramienta para visualizar, analizar y modelar el sistema de transporte público de Bogotá utilizando datos reales obtenidos a partir de conjuntos de datos GTFS o equivalentes. El sistema permite cargar estaciones y rutas, reconstruir recorridos basados en información de secuencias de paraderos y generar archivos GeoJSON que pueden visualizarse en un mapa interactivo con Leaflet.

El propósito del proyecto es proporcionar una base para:

- Visualización de rutas del sistema de transporte.
- Reconstrucción de trayectorias mediante datos GTFS.
- Análisis posterior mediante grafos, algoritmos de optimización y simulaciones.
- Documentación y exploración de rutas específicas como H15, 6-2, 10-5, entre otras.

El proyecto está pensado como soporte para investigación académica y trabajos universitarios relacionados con movilidad urbana y optimización.

## Datos utilizados

Los datos sin procesar no están incluidos en el repositorio por su tamaño y por posibles restricciones de redistribución. El usuario debe descargar los archivos GTFS o las capas equivalentes desde fuentes oficiales.

Archivos requeridos (GTFS):

- `routes.txt`
- `stops.txt`
- `trips.txt`
- `stop_times.txt`

Estos datos pueden descargarse desde el portal ArcGIS:

https://www.arcgis.com

Se recomienda usar capas oficiales de movilidad o datasets publicados por entidades distritales.


## Generación de archivos GeoJSON

El script principal se encuentra en `src/generar_geojson.py`. Sus responsabilidades principales son:

1. Cargar los archivos GTFS (`routes.txt`, `stops.txt`, `trips.txt`, `stop_times.txt`).
2. Limpiar y validar las secuencias de paraderos (`stop_times`).
3. Seleccionar para cada `route_id` un `trip_id` representativo (por ejemplo, el trip más largo o el que cumpla criterios de validez).
4. Construir las geometrías (LineString) usando las coordenadas de `stops.txt`.
5. Exportar `estaciones.geojson` y `rutas.geojson` en formato GeoJSON compatible con Leaflet.

### Ejecutar el script

Coloque los archivos GTFS en una carpeta accesible para el script (por ejemplo `data/raw_gtfs/`) y ajuste las rutas en `src/generar_geojson.py` si es necesario.

Ejemplo básico (desde la raíz del proyecto):

```bash
python -m venv .venv
.venv/bin/activate      # Linux/macOS
.venv\Scripts\activate   # Windows PowerShell

pip install -r requirements.txt

python src/generar_geojson.py


