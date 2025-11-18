"""
generar_geojson_y_grafo.py

Entrada (carpeta actual):
 - routes.txt
 - shapes.txt
 - trips.txt
 - stop_times.txt
 - stops.txt

Salida:
 - rutas.geojson
 - estaciones.geojson
 - grafo_bipartito.json
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from shapely.geometry import LineString, Point, mapping
import networkx as nx
from tqdm import tqdm

# ------------ Config ------------
INPUT_DIR = Path('.venv\ETF\Data_whitout_Process') 
OUT_RUTAS = Path('rutas.geojson')
OUT_ESTACIONES = Path('estaciones.geojson')
OUT_GRAFO = Path('grafo_bipartito.json')

# Nombres de archivos GTFS
F_ROUTES = INPUT_DIR / 'routes.txt'
F_SHAPES = INPUT_DIR / 'shapes.txt'
F_TRIPS = INPUT_DIR / 'trips.txt'
F_STOP_TIMES = INPUT_DIR / 'stop_times.txt'
F_STOPS = INPUT_DIR / 'stops.txt'
# ---------------------------------

# ---------- Utilidades ----------
def save_geojson_featurecollection(features, path):
    fc = {"type": "FeatureCollection", "features": features}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {path} ({len(features)} features)")

def route_type_normalize(s):
    if s is None:
        return None
    st = str(s).strip().upper()
    if 'TRONCAL' in st: return 'TRONCAL'
    if 'ALIMENT' in st or 'ALIM' in st: return 'ALIMENTADOR'
    if 'URB' in st: return 'URBANO'
    # fallback common GTFS numeric codes
    try:
        n = int(st)
        if n in (0,1,3,11,5):  # bus/tram/... heuristic
            return 'URBANO'
    except:
        pass
    return st

# --------------------------------

def main():
    # Cargar archivos (pandas)
    print("Cargando archivos GTFS (esto puede tardar si son grandes)...")
    routes = pd.read_csv(F_ROUTES, dtype=str)
    shapes = pd.read_csv(F_SHAPES, dtype=str)
    trips = pd.read_csv(F_TRIPS, dtype=str)
    stop_times = pd.read_csv(F_STOP_TIMES, dtype=str)
    stops = pd.read_csv(F_STOPS, dtype=str)

    # Normalizaciones de columnas (por si hay espacios u otros nombres)
    # asumimos que las columnas vienen como el estándar: route_id, shape_id, stop_id, etc.
    # ---------- PREPROCESADO ----------
    shapes['shape_pt_sequence'] = pd.to_numeric(shapes['shape_pt_sequence'], errors='coerce')
    shapes['shape_pt_lat'] = pd.to_numeric(shapes['shape_pt_lat'], errors='coerce')
    shapes['shape_pt_lon'] = pd.to_numeric(shapes['shape_pt_lon'], errors='coerce')

    # Convertir stop_sequence a num para contar largos de trips
    if 'stop_sequence' in stop_times.columns:
        stop_times['stop_sequence'] = pd.to_numeric(stop_times['stop_sequence'], errors='coerce')

    # ---------- Elegir shape representativo por route ----------
    print("Elegiendo shape representativo por route_id...")
    # trips: route_id, trip_id, shape_id
    # Para cada route_id, escoger shape_id más frecuente entre sus trips
    trips_group = trips[['route_id', 'trip_id', 'shape_id']].fillna('')
    route_to_shapecount = defaultdict(Counter)

    for idx, row in trips_group.iterrows():
        route = row['route_id']
        shape = row['shape_id'] if pd.notna(row['shape_id']) and row['shape_id'] != '' else None
        if shape:
            route_to_shapecount[route][shape] += 1

    # fallback: si no existe shape para route, elegimos el trip con más stop_times
    # contar stops por trip
    trip_stop_counts = stop_times.groupby('trip_id').size().to_dict() if 'trip_id' in stop_times.columns else {}

    route_to_shape = {}
    for route in routes['route_id'].unique():
        shape_counter = route_to_shapecount.get(route, None)
        chosen_shape = None
        if shape_counter and len(shape_counter) > 0:
            chosen_shape = shape_counter.most_common(1)[0][0]
        else:
            # buscar trips de esta ruta y elegir trip con mayor stop_times y usar su shape_id
            candidate_trips = trips[trips['route_id'] == route]
            if not candidate_trips.empty:
                # calcular sizes
                best_trip_id = None
                best_count = -1
                best_shape = None
                for _, trow in candidate_trips.iterrows():
                    tid = trow['trip_id']
                    cnt = int(trip_stop_counts.get(tid, 0))
                    if cnt > best_count:
                        best_count = cnt
                        best_trip_id = tid
                        best_shape = trow.get('shape_id', None)
                chosen_shape = best_shape if pd.notna(best_shape) and best_shape != '' else None

        route_to_shape[route] = chosen_shape

    # ---------- Construir rutas.geojson desde shapes ----------
    print("Construyendo rutas.geojson desde shapes...")
    # Pre-agrupamos shapes por shape_id y ordenamos por sequence
    shapes_grouped = {}
    for shape_id, grp in shapes.groupby('shape_id'):
        grp_sorted = grp.sort_values('shape_pt_sequence')
        coords = list(zip(grp_sorted['shape_pt_lon'].astype(float), grp_sorted['shape_pt_lat'].astype(float)))
        shapes_grouped[shape_id] = coords
 
 
    rutas_features = []
    for idx, r in tqdm(routes.iterrows(), total=len(routes), desc="rutas"):
        route_id = r['route_id']
        short_name = r.get('route_short_name', '') if 'route_short_name' in r else ''
        long_name = r.get('route_long_name', '') if 'route_long_name' in r else ''
        tipo_raw = r.get('route_desc', r.get('route_type', ''))
        tipo = route_type_normalize(tipo_raw)
        shape_id = route_to_shape.get(route_id)

        coords = shapes_grouped.get(shape_id)
        if coords and len(coords) >= 2:
            feature = {
                "type": "Feature",
                "properties": {
                    "route_id": route_id,
                    "short_name": short_name,
                    "long_name": long_name,
                    "tipo": tipo,
                    "shape_id": shape_id
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                }
            }
            rutas_features.append(feature)
        else:
            # Si no hay shape, intentar construir una línea usando stops del trip mas largo
            # obtener trips de la route
            candidate_trips = trips[trips['route_id'] == route_id]
            best_trip = None
            best_count = -1
            for _, trow in candidate_trips.iterrows():
                tid = trow['trip_id']
                cnt = int(trip_stop_counts.get(tid, 0))
                if cnt > best_count:
                    best_count = cnt
                    best_trip = tid
            if best_trip and best_count >= 2:
                st = stop_times[stop_times['trip_id'] == best_trip].sort_values('stop_sequence')
                coords2 = []
                for _, srow in st.iterrows():
                    sid = srow['stop_id']
                    stoprow = stops[stops['stop_id'] == sid]
                    if not stoprow.empty:
                        lon = float(stoprow.iloc[0]['stop_lon'])
                        lat = float(stoprow.iloc[0]['stop_lat'])
                        coords2.append([lon, lat])
                if len(coords2) >= 2:
                    rutas_features.append({
                        "type": "Feature",
                        "properties": {
                            "route_id": route_id,
                            "short_name": short_name,
                            "long_name": long_name,
                            "tipo": tipo,
                            "shape_id": shape_id or f"trip_{best_trip}"
                        },
                        "geometry": {
                            "type": "LineString",
                            "coordinates": coords2
                        }
                    })
                else:
                    # no coordinates -> saltar
                    pass

    save_geojson_featurecollection(rutas_features, OUT_RUTAS)

    # ---------- Construir estaciones.geojson tipificadas ----------
    print("Construyendo estaciones.geojson y clasificando por tipo (segun rutas que pasan)...")
    # Primero, para cada stop_id, averiguar los route_ids que lo usan
    # stop_times: trip_id -> stop_id ; trips: trip_id -> route_id
    trip_to_route = trips.set_index('trip_id')['route_id'].to_dict()
    stop_to_routes = defaultdict(set)

    for idx, row in tqdm(stop_times.iterrows(), total=len(stop_times), desc="stop_times"):
        trip_id = row['trip_id']
        stop_id = row['stop_id']
        route_id = trip_to_route.get(trip_id)
        if route_id:
            stop_to_routes[stop_id].add(route_id)

    # Mapear route_id -> tipo (normalizado)
    route_tipo = {}
    for _, r in routes.iterrows():
        route_tipo[r['route_id']] = route_type_normalize(r.get('route_desc', r.get('route_type', '')))

    estaciones_features = []
    stop_type_counts = {"TRONCAL":0, "ALIMENTADOR":0, "URBANO":0, "MIXTO":0, "UNKNOWN":0}
    for _, s in tqdm(stops.iterrows(), total=len(stops), desc="stops"):
        sid = s['stop_id']
        name = s.get('stop_name', '')
        lat = float(s['stop_lat'])
        lon = float(s['stop_lon'])
        location_type = s.get('location_type', '')

        # tipos de rutas que pasan por este stop
        rutas_que_pasan = stop_to_routes.get(sid, set())
        tipos = set()
        for rid in rutas_que_pasan:
            t = route_tipo.get(rid)
            if t:
                tipos.add(t)
        # decidir tipo final del stop
        if len(tipos) == 0:
            final_type = 'UNKNOWN'
            stop_type_counts['UNKNOWN'] += 1
        elif len(tipos) == 1:
            final_type = list(tipos)[0]
            stop_type_counts[final_type] = stop_type_counts.get(final_type,0) + 1
        else:
            # si contiene TRONCAL y alimentador -> MIXTO; si contiene TRONCAL + urbano -> MIXTO, etc.
            final_type = 'MIXTO'
            stop_type_counts['MIXTO'] += 1

        feature = {
            "type": "Feature",
            "properties": {
                "stop_id": sid,
                "stop_name": name,
                "location_type": location_type,
                "tipo": final_type,
                "routes": list(rutas_que_pasan)
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }
        estaciones_features.append(feature)

    save_geojson_featurecollection(estaciones_features, OUT_ESTACIONES)
    print("Conteo de tipos de paraderos:", stop_type_counts)

    # ---------- Construir grafo bipartito route <-> stop ----------
    print("Construyendo grafo bipartito (route <-> stop) con pesos (apariciones)...")
    G = nx.Graph()
    # Añadir nodos (prefijados para distinguir tipos)
    for _, r in routes.iterrows():
        rid = r['route_id']
        G.add_node(f"R_{rid}", bipartite='route', route_id=rid,
                   short_name=r.get('route_short_name', ''), tipo=route_tipo.get(rid))
    for _, s in stops.iterrows():
        sid = s['stop_id']
        G.add_node(f"S_{sid}", bipartite='stop', stop_id=sid, stop_name=s.get('stop_name',''))

    # Añadir aristas con peso = apariciones en stop_times (conteo de trips que unen route-stop)
    edge_counts = defaultdict(int)
    # Para cada stop_time row, obtenemos route via trip_to_route -> incrementamos edge (route,stop)
    for _, row in tqdm(stop_times.iterrows(), total=len(stop_times), desc="armando aristas"):
        trip_id = row['trip_id']
        stop_id = row['stop_id']
        route_id = trip_to_route.get(trip_id)
        if route_id and stop_id:
            edge_counts[(route_id, stop_id)] += 1

    for (rid, sid), weight in edge_counts.items():
        G.add_edge(f"R_{rid}", f"S_{sid}", weight=weight)

    # Exportar grafo a JSON simple (nodos + aristas con atributos)
    out_graph = {
        "nodes": [],
        "edges": []
    }
    for n, d in G.nodes(data=True):
        out_graph['nodes'].append({"id": n, **d})
    for u, v, data in G.edges(data=True):
        out_graph['edges'].append({"u": u, "v": v, **data})

    with open(OUT_GRAFO, 'w', encoding='utf-8') as f:
        json.dump(out_graph, f, ensure_ascii=False, indent=2)

    print(f"Guardado: {OUT_GRAFO}")
    print("Proceso finalizado.")

if __name__ == '__main__':
    main()
