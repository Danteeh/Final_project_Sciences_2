from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict


@dataclass
class BTreeNode:
    keys: List[str] = field(default_factory=list)
    values: List[Any] = field(default_factory=list)#sub grafos asociados a las llaves
    children: List["BTreeNode"] = field(default_factory=list)
    leaf: bool = True #No tiene hijos


    #Convierte el nodo a un diccionario serializable en JSON.
    def to_dict(self) -> Dict[str, Any]:
        return {
            "keys": self.keys,
            "values": self.values,
            "children": [c.to_dict() for c in self.children],
            "leaf": self.leaf,
        }

    #Reconstruccion de un nodo a partir de un diccionario cargado desde JSON.
    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "BTreeNode":
        node = BTreeNode(
            keys=d.get("keys", []),
            values=d.get("values", []),
            children=[],
            leaf=bool(d.get("leaf", True)),
        )
        # Se reconstruyen recursivamente todos los hijos
        node.children = [BTreeNode.from_dict(cd) for cd in d.get("children", [])]
        return node
    
class BTreeStore:
    def __init__(self, t: int = 2, file_path: str = "btree_store.json"):
        if t < 2:
            raise ValueError("t must be >= 2")
        self.t = int(t)
        self.root: Optional[BTreeNode] = None
        self.file_path = file_path    

         # SEARCH (Busca una clave dentro del arbol)
    def search(self, key: str) -> Optional[Any]:
        if self.root is None:
            return None
        return self._search_node(self.root, key)

    #Busca dentro de un nodo especifico
    def _search_node(self, node: BTreeNode, key: str) -> Optional[Any]:
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            return node.values[i]
        if node.leaf:
            return None
        return self._search_node(node.children[i], key)
    

    
    def insert(self, key: str, value: Any) -> None:
        """
        Inserto (key, value) en el Árbol B.
        Casos:
        - Si root no existe → se crea un nodo hoja nuevo.
        - Si la clave ya existe → actualiza el valor.
        - Si la raíz está llena → la divide antes de insertar.
        """
        if self.root is None:
            self.root = BTreeNode(keys=[key], values=[value], leaf=True)
            self.save()
            return
        # if key exists, replace value
        if self.search(key) is not None:
            self._replace(self.root, key, value)
            self.save()
            return

        max_keys = 2 * self.t - 1
        if len(self.root.keys) == max_keys:
            s = BTreeNode(leaf=False, children=[self.root])
            self._split_child(s, 0)
            self.root = s
        self._insert_non_full(self.root, key, value)
        self.save()

    #Reemplaza el valor asociado a una clave ya existente.
    def _replace(self, node: BTreeNode, key: str, value: Any) -> bool:
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            node.values[i] = value
            return True
        if node.leaf:
            return False
        return self._replace(node.children[i], key, value)
    
    
    def _insert_non_full(self, node: BTreeNode, key: str, value: Any) -> None:
        i = len(node.keys) - 1
        if node.leaf:
            # # insertar ordenadamente en una hoja
            node.keys.append("")  # placeholder temporal
            node.values.append(None)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            node.keys[i + 1] = key
            node.values[i + 1] = value
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            # if child full, split
            if len(node.children[i].keys) == 2 * self.t - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent: BTreeNode, index: int) -> None:
        t = self.t
        y = parent.children[index]
        z = BTreeNode(leaf=y.leaf)
        # z toma las últimas t-1 claves y valores de y
        z.keys = y.keys[t:]
        z.values = y.values[t:]
        # clave media q sube
        mid_key = y.keys[t - 1]
        mid_value = y.values[t - 1]
       
        y.keys = y.keys[: t - 1]
        y.values = y.values[: t - 1]

        # si no es hoja, divide los hijos también
        if not y.leaf:
            z.children = y.children[t:]
            y.children = y.children[:t]
        parent.keys.insert(index, mid_key)
        parent.values.insert(index, mid_value)
        parent.children.insert(index + 1, z)
    
    #Representa el árbol completo como diccionario para guardarlo en JSON.
    def to_dict(self) -> Dict[str, Any]:
        return {"t": self.t, "root": self.root.to_dict() if self.root else None, "file_path": self.file_path}

    @staticmethod
    # Reconstruye el BTreeStore completo a partir de un diccionario JSON cargado.
    def from_dict(d: Dict[str, Any]) -> "BTreeStore":
        t = d.get("t", 2)
        path = d.get("file_path", "btree_store.json")
        bt = BTreeStore(t=t, file_path=path)
        root_d = d.get("root")
        if root_d is not None:
            bt.root = BTreeNode.from_dict(root_d)
        return bt

    # Autoguardado del árbol en un archivo JSON.
    def save(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def load(self) -> None:
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        loaded = BTreeStore.from_dict(data)
        self.t = loaded.t
        self.root = loaded.root

    @classmethod
    def load_or_create(cls, file_path: str = "btree_store.json", t: int = 2) -> "BTreeStore":
        """
        Intenta cargar el archivo del Árbol B.
        Si no existe, crea uno nuevo vacío.
        """   
        try:
            bt = cls(t=t, file_path=file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            loaded = cls.from_dict(data)
            loaded.file_path = file_path
            return loaded
        except FileNotFoundError:
            return cls(t=t, file_path=file_path)


# Guarda un subgrafo bajo la clave especificada dentro del B-Tree persistente.

def guardar_subgrafo(clave: str, subgrafo: Dict[str, Any], store_path: str = "btree_store.json", t: int = 2) -> None:
    bt = BTreeStore.load_or_create(store_path, t=t)
    bt.insert(clave, subgrafo)


#Recupera un subgrafo almacenado en el Árbol B si la clave existe.
def recuperar_subgrafo(clave: str, store_path: str = "btree_store.json", t: int = 2) -> Optional[Dict[str, Any]]:
    bt = BTreeStore.load_or_create(store_path, t=t)
    return bt.search(clave)

