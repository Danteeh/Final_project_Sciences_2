class Grafo:
    def __init__(self):
 
        self.nodos = {}

        self.aristas = {}


    def cargar_desde_json(self, data: dict):
        nodos = data.get("nodos", {})
        aristas = data.get("aristas", {})


        for nid, info in nodos.items():
            self.nodos[nid] = {
                "lat": info["lat"],
                "lng": info["lng"],
                "tipo": info["tipo"],
                "capacidad": info["capacidad"]
            }


            if nid not in self.aristas:
                self.aristas[nid] = []


        for origen, lista in aristas.items():
            if origen not in self.aristas:
                self.aristas[origen] = []

            for edge in lista:
                self.aristas[origen].append({
                    "to": edge["to"],
                    "peso": edge["peso"],
                    "coordinates": edge.get("coordinates", [])
                })


    def info(self):
        return {
            "nodos": len(self.nodos),
            "aristas": sum(len(v) for v in self.aristas.values())
        }


    def imprimir_nodos(self):
        print("Nodos")
        for nid, info in self.nodos.items():
            print(f"{nid}: tipo={info['tipo']}, capacidad={info['capacidad']}, "
                  f"lat={info['lat']}, lng={info['lng']}")
        print()


    def imprimir_aristas(self):
        print("aristas")
        for origen, edges in self.aristas.items():
            for edge in edges:
                print(f"{origen} -> {edge['to']} | peso={edge['peso']}")
        print()

    def imprimir_grafo(self):
        print("Grafo")
        print("NODOS:")
        for nid, info in self.nodos.items():
            print(f"   {nid} ({info['tipo']} / cap={info['capacidad']})")
        print("\nARISTAS:")
        for origen, edges in self.aristas.items():
            if not edges:
                print(f"   {origen} -> (sin conexiones)")
            else:
                for e in edges:
                    print(f"   {origen} -> {e['to']} (peso {e['peso']})")
