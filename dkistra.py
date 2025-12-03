import math
import heapq
from typing import List, Dict, Any, Tuple, Optional
import networkx as nx
from btree_storage import guardar_subgrafo


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def build_nx_from_grafo(grafo) -> nx.DiGraph:

    G = nx.DiGraph()

    for nid, info in grafo.nodos.items():
        attrs = {}
        if 'lat' in info and 'lng' in info:
            try:
                attrs['lat'] = float(info['lat'])
                attrs['lng'] = float(info['lng'])
            except:
                pass
        G.add_node(nid, **attrs)
    for origen, edges in grafo.aristas.items():
        for e in edges:
            to = e.get('to')
            if to is None:
                continue
            # capacity
            cap = e.get('peso', e.get('weight', e.get('capacity', 1.0)))
            try:
                cap = float(cap)
            except:
                cap = 1.0
            # length
            length = None
            if 'length' in e:
                try:
                    length = float(e['length'])
                except:
                    length = None
            if length is None and 'dist' in e:
                try:
                    length = float(e['dist'])
                except:
                    length = None
            if length is None:
                # intentar calcular por lat/lng de nodos
                src = grafo.nodos.get(origen, {})
                dst = grafo.nodos.get(to, {})
                if 'lat' in src and 'lng' in src and 'lat' in dst and 'lng' in dst:
                    try:
                        length = haversine(float(src['lat']), float(src['lng']),
                                           float(dst['lat']), float(dst['lng']))
                    except:
                        length = 1.0
                else:
                    length = 1.0
            G.add_edge(origen, to, capacity=cap, length=length, raw=e)
    return G

def widest_path(G: nx.DiGraph, source: str, target: str, capacity_attr: str = 'capacity') -> Tuple[float, List[str]]:

    if source not in G or target not in G:
        return 0.0, []
    best = {n: 0.0 for n in G.nodes()}
    prev: Dict[str, str] = {}
    best[source] = float('inf')
    heap = [(-best[source], source)]
    while heap:
        negb, u = heapq.heappop(heap)
        b = -negb
        if b < best[u]:
            continue
        if u == target:
            break
        for v in G.successors(u):
            cap = float(G[u][v].get(capacity_attr, 0.0))
            bott = min(b, cap)
            if bott > best[v]:
                best[v] = bott
                prev[v] = u
                heapq.heappush(heap, (-bott, v))
    if best[target] == 0.0:
        return 0.0, []

    path = []
    cur = target
    while cur != source:
        path.append(cur)
        cur = prev.get(cur)
        if cur is None:
            return 0.0, []
    path.append(source)
    path.reverse()
    return best[target], path

def shortest_path_with_capacity_threshold(G: nx.DiGraph, source: str, target: str, min_capacity: float,
                                          capacity_attr: str = 'capacity', length_attr: str = 'length') -> Tuple[Optional[float], Optional[List[str]]]:

    H = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        if float(d.get(capacity_attr, 0.0)) >= float(min_capacity):
            H.add_edge(u, v, length=float(d.get(length_attr, 1.0)), capacity=d.get(capacity_attr), raw=d.get('raw'))
    if source not in H or target not in H:
        return None, None
    try:
        path = nx.shortest_path(H, source=source, target=target, weight='length')
        total_length = sum(H[u][v]['length'] for u, v in zip(path[:-1], path[1:]))
        return total_length, path
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None, None

def export_path_subgraph(G: nx.DiGraph, path: List[str]) -> Dict[str, Any]:

    nodes = []
    edges = []
    for n in path:
        node_info = dict(G.nodes[n])
        node_info['id'] = n
        nodes.append(node_info)
    for u, v in zip(path[:-1], path[1:]):
        data = G.get_edge_data(u, v, default={})
        edge_out = {'from': u, 'to': v, 'capacity': data.get('capacity'), 'length': data.get('length')}
        if 'raw' in data:
            edge_out['raw'] = data['raw']
        edges.append(edge_out)
    return {"nodes": nodes, "edges": edges}

def calcular_camino_optimo(grafo, origen: str, destino: str) -> Dict[str, Any]:


    if origen not in grafo.nodos or destino not in grafo.nodos:
        return {"ok": False, "error": "Origen o destino no existen en el grafo."}


    Gnx = build_nx_from_grafo(grafo)


    bottleneck, path_widest = widest_path(Gnx, origen, destino)
    if bottleneck == 0.0 or not path_widest:
        return {"ok": False, "error": "No existe camino entre origen y destino."}


    length, path_short = shortest_path_with_capacity_threshold(
        Gnx, origen, destino, bottleneck
    )

    if path_short is None:
        path_short = path_widest
        length = sum(float(Gnx[u][v].get('length', 1.0)) 
                     for u, v in zip(path_short[:-1], path_short[1:]))


    sub = export_path_subgraph(Gnx, path_short)


    resultado = {
        "ok": True,
        "flujo_maximo": bottleneck,
        "camino": path_short,
        "capacidad_total": bottleneck,
        "longitud_metros": length,
        "subgrafo": sub
    }


    clave = f"{origen}->{destino}"
    guardar_subgrafo(clave, resultado, store_path="btree_store.json", t=2)

    print(f"[B-TREE] Subgrafo para {clave} guardado exitosamente.")

    return resultado
