from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Grafo_Respose import Grafo
from dkistra import calcular_camino_optimo

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GrafoInput(BaseModel):
    nodos: dict
    aristas: dict


g = Grafo()



@app.post("/cargar_grafo")
def cargar_grafo(data: GrafoInput):
    global g
    g = Grafo()
    g.cargar_desde_json(data.dict())

    return {
        "ok": True,
        "nodos": len(g.nodos),
        "aristas": sum(len(v) for v in g.aristas.values())
    }


@app.get("/info_grafo")
def info_grafo():
    return g.info()



@app.get("/camino/{origen}/{destino}")
def camino(origen: str, destino: str):
    """
    Luego aquí implementamos Dijkstra 
    """
    if not g.nodos:
        return {"ok": False, "error": "Grafo no cargado. Use /cargar_grafo primero."}

    if origen not in g.nodos:
        return {"ok": False, "error": f"Origen '{origen}' no existe en el grafo."}

    if destino not in g.nodos:
        return {"ok": False, "error": f"Destino '{destino}' no existe en el grafo."}

    # Ejecutar el cálculo principal 
    result = calcular_camino_optimo(g, origen, destino)

    # Pasamos directamente el resultado de la función;
    return result
