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

class CaminoRequest(BaseModel):
    grafo: dict
    origen: str
    destino: str


@app.post("/camino_optimo")
def camino_optimo(data: CaminoRequest):
    g = Grafo()
    g.cargar_desde_json(data.grafo)

    resultado = calcular_camino_optimo(g, data.origen, data.destino)
    return resultado
