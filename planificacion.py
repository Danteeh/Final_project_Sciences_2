from btree_storage import BTreeStore


def construir_grafo_conflictos(bt: BTreeStore):
    rutas = []

    def rec(n):
        if n is None:
            return
        for k, v in zip(n.keys, n.values):
            rutas.append((k, v["subgrafo"]))
        if not n.leaf:
            for c in n.children:
                rec(c)

    rec(bt.root)

    conflictos = {clave: set() for clave, _ in rutas}

    for i in range(len(rutas)):
        clave1, sub1 = rutas[i]
        nodos1 = {n['id'] for n in sub1["nodes"]}

        for j in range(i + 1, len(rutas)):
            clave2, sub2 = rutas[j]
            nodos2 = {n['id'] for n in sub2["nodes"]}

            if nodos1 & nodos2:  # comparten al menos 1 nodo
                conflictos[clave1].add(clave2)
                conflictos[clave2].add(clave1)

    return conflictos



def colorear_grafo(conflictos: dict) -> dict:
    colores = {}

    for ruta in sorted(conflictos.keys()):
        usados = {colores[r] for r in conflictos[ruta] if r in colores}
        color = 0
        while color in usados:
            color += 1
        colores[ruta] = color

    return colores



FRECUENCIAS = {
    0: "cada 3 minutos",
    1: "cada 4 minutos",
    2: "cada 5 minutos",
    3: "cada 6 minutos",
    4: "cada 8 minutos"
}

def asignar_frecuencias(colores):
    return {
        ruta: FRECUENCIAS.get(c, "cada 10 minutos")
        for ruta, c in colores.items()
    }


def planificar_recursos():
    bt = BTreeStore.load_or_create("btree_store.json")

    conflictos = construir_grafo_conflictos(bt)
    colores = colorear_grafo(conflictos)
    frecuencias = asignar_frecuencias(colores)

    return {
        "ok": True,
        "conflictos": {k: list(v) for k, v in conflictos.items()},
        "colores": colores,
        "frecuencias": frecuencias
    }

