from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Grafo_Respose import Grafo
from dkistra import calcular_camino_optimo
from btree_storage import recuperar_subgrafo, BTreeStore
from planificacion import planificar_recursos


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




@app.get("/rutas_guardadas")
def rutas_guardadas():
    bt = BTreeStore.load_or_create("btree_store.json")
    rutas = []

    def recorrer(nodo):
        if nodo is None:
            return

        for k, v in zip(nodo.keys, nodo.values):
            rutas.append({
                "clave": k,
                "camino": v.get("camino", []),
                "flujo_maximo": v.get("flujo_maximo", None)
            })
 
        if not nodo.leaf:
            for c in nodo.children:
                recorrer(c)

    recorrer(bt.root)
    return {"ok": True, "rutas": rutas}


@app.get("/ruta_guardada/{clave}")
def ruta_guardada(clave: str):
    sub = recuperar_subgrafo(clave)
    if sub is None:
        return {"ok": False, "error": "No existe esa ruta en el Árbol B"}
    return {"ok": True, "ruta": sub}

@app.get("/planificacion_recursos")
def planificacion_recursos():
    return planificar_recursos()
