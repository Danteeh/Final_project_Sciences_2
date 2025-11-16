import pandas as pd
import json


routes = pd.read_csv(".venv\\ETF\\Data_whitout_Process\\routes.txt")
stops = pd.read_csv(".venv\\ETF\\Data_whitout_Process\\stops.txt")
trips = pd.read_csv(".venv\\ETF\\Data_whitout_Process\\trips.txt")
stop_times = pd.read_csv(".venv\\ETF\\Data_whitout_Process\\stop_times.txt")


def crear_estaciones_geojson():
    features = []

    for _, row in stops.iterrows():
        features.append({
            "type": "Feature",
            "properties": {
                "id": str(row["stop_id"]),
                "nombre": row["stop_name"],
                "tipo": row.get("stop_desc", "")
            },
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["stop_lon"]), float(row["stop_lat"])]
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open("estaciones.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=4, ensure_ascii=False)






def crear_rutas_geojson():

    features = []

    for route_id in routes["route_id"].unique():

        trips_ruta = trips[trips["route_id"] == route_id]["trip_id"].unique()

        secuencia_final = None

        for trip in trips_ruta:
            secuencia = stop_times[stop_times["trip_id"] == trip]
            if len(secuencia) > 5:
                secuencia_final = secuencia.sort_values("stop_sequence")
                break

        if secuencia_final is None:
            continue

        coords = []

        for _, row in secuencia_final.iterrows():
            stop_id = row["stop_id"]
            stop_info = stops[stops["stop_id"] == stop_id]

            if len(stop_info) == 0:
                continue

            lat = float(stop_info.iloc[0]["stop_lat"])
            lon = float(stop_info.iloc[0]["stop_lon"])
            coords.append([lon, lat])

        info_ruta = routes[routes["route_id"] == route_id].iloc[0]

        features.append({
            "type": "Feature",
            "properties": {
                "route_id": route_id,
                "short_name": info_ruta["route_short_name"],
                "long_name": info_ruta["route_long_name"],
                "tipo": info_ruta["route_desc"]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open("rutas.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=4, ensure_ascii=False)

    print("✔ rutas.geojson generado correctamente.")


crear_estaciones_geojson()
crear_rutas_geojson()

