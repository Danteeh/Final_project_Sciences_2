from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Grafo_Respose import Grafo

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
    Luego aquí implementamos Dijkstra o BFS.
    Por ahora solo devolvemos la estructura base.
    """
    if origen not in g.nodos or destino not in g.nodos:
        return {"ok": False, "error": "Nodo no existe"}

    return {
        "ok": True,
        "mensaje": f"Procesando camino entre {origen} → {destino}",
        "nodos_totales": len(g.nodos),
    }
