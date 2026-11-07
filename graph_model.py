import heapq
import json
import math
import random
import string
from collections import deque

LABELS = list(string.ascii_uppercase[:16])
MAX_NODES = len(LABELS)
MAX_LEVEL_WIDTH = 5

# extra: prob. de arista adicional entre capas consecutivas; skip: prob. de arista que salta una capa
DENSITY_PROFILES = {
    "baja": {"extra": 0.10, "skip": 0.04},
    "media": {"extra": 0.30, "skip": 0.12},
    "alta": {"extra": 0.55, "skip": 0.25},
}


class Graph:
    def __init__(self, n):
        self.n = n
        self.adj = {i: [] for i in range(n)}
        self.info = {}

    @property
    def labels(self):
        return LABELS[:self.n]

    def add_node(self):
        if self.n >= MAX_NODES:
            raise ValueError(f"Máximo {MAX_NODES} nodos.")
        self.adj[self.n] = []
        self.n += 1
        return self.n - 1

    def remove_node(self, node):
        # Los nodos restantes se renumeran para que las etiquetas sigan siendo A, B, C...
        def remap(i):
            return i if i < node else i - 1

        self.adj = {remap(u): [(remap(v), w) for v, w in nbrs if v != node]
                    for u, nbrs in self.adj.items() if u != node}
        self.n -= 1

    def add_edge(self, u, v, w):
        self.adj[u].append((v, w))

    def remove_edge(self, u, v):
        self.adj[u] = [(x, w) for x, w in self.adj[u] if x != v]

    def has_edge(self, u, v):
        return any(x == v for x, _ in self.adj[u])

    def set_weight(self, u, v, w):
        self.adj[u] = [(x, w if x == v else old) for x, old in self.adj[u]]

    def edges(self):
        return [(u, v, w) for u in range(self.n) for v, w in self.adj[u]]

    def creates_cycle(self, u, v):
        if u == v:
            return True
        stack = [v]
        visited = set()
        while stack:
            node = stack.pop()
            if node == u:
                return True
            if node in visited:
                continue
            visited.add(node)
            for nxt, _ in self.adj[node]:
                if nxt not in visited:
                    stack.append(nxt)
        return False

    def index_of_label(self, label):
        return self.labels.index(label)


def topological_order(graph):
    indeg = {i: 0 for i in range(graph.n)}
    for _, v, _ in graph.edges():
        indeg[v] += 1
    queue = deque(i for i in range(graph.n) if indeg[i] == 0)
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for v, _ in graph.adj[node]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return order


def topological_layers(graph):
    order = topological_order(graph)
    depth = {i: 0 for i in range(graph.n)}
    for node in order:
        for v, _ in graph.adj[node]:
            depth[v] = max(depth[v], depth[node] + 1)
    return depth


# ---------------------------------------------------------------- métricas
def hop_distance(graph, source, target):
    """Menor cantidad de aristas de source a target (BFS); math.inf si no hay camino."""
    seen = {source: 0}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        if u == target:
            return seen[u]
        for v, _ in graph.adj[u]:
            if v not in seen:
                seen[v] = seen[u] + 1
                queue.append(v)
    return math.inf


def _hop_path(graph, source, target):
    parent = {source: None}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        if u == target:
            break
        for v, _ in graph.adj[u]:
            if v not in parent:
                parent[v] = u
                queue.append(v)
    path, node = [], target
    while node is not None:
        path.append(node)
        node = parent[node]
    return path[::-1]


def count_paths(graph, source, target):
    """Cantidad de caminos distintos source -> target (programación dinámica sobre el DAG)."""
    ways = {i: 0 for i in range(graph.n)}
    ways[source] = 1
    for u in topological_order(graph):
        for v, _ in graph.adj[u]:
            ways[v] += ways[u]
    return ways[target]


def _costs_from_source(graph, order, source):
    dist = {i: math.inf for i in range(graph.n)}
    dist[source] = 0
    for u in order:
        if dist[u] < math.inf:
            for v, w in graph.adj[u]:
                dist[v] = min(dist[v], dist[u] + w)
    return dist


def _costs_to_target(graph, order, target):
    dist = {i: math.inf for i in range(graph.n)}
    dist[target] = 0
    for u in reversed(order):
        for v, w in graph.adj[u]:
            if dist[v] < math.inf:
                dist[u] = min(dist[u], w + dist[v])
    return dist


def _optimal_slacks(graph, source, target):
    """Devuelve (d*, nº de caminos óptimos, holguras por arista).

    La holgura de (u, v, w) es d(s,u) + w + d(v,t) - d*: cuánto más caro que el óptimo
    es el mejor camino que pasa por esa arista. Holgura 0 = la arista está en un camino óptimo.
    """
    order = topological_order(graph)
    ds = _costs_from_source(graph, order, source)
    dt = _costs_to_target(graph, order, target)
    best = ds[target]
    ways = {i: 0 for i in range(graph.n)}
    ways[source] = 1
    slacks = []
    for u in order:
        for v, w in graph.adj[u]:
            if ds[u] == math.inf or dt[v] == math.inf:
                continue
            slack = ds[u] + w + dt[v] - best
            slacks.append((slack, u, v, w))
            if slack == 0:
                ways[v] += ways[u]
    return best, ways[target], slacks


# ---------------------------------------------------------------- generador
def _assign_levels(n, source, target, min_hops, max_out, rng):
    """Reparte los nodos en capas: [source], capas intermedias..., [target]."""
    others = [v for v in range(n) if v not in (source, target)]
    rng.shuffle(others)
    mid_levels = min(len(others), max(min_hops - 1, (len(others) + 1) // 2))
    sizes = [1] * mid_levels
    remaining = len(others) - mid_levels
    while remaining > 0:
        options = []
        for i in range(mid_levels):
            prev = sizes[i - 1] if i > 0 else 1
            if sizes[i] < MAX_LEVEL_WIDTH and sizes[i] + 1 <= max_out * prev:
                options.append(i)
        if not options:
            raise ValueError("No se pudo repartir los nodos en capas con esos parámetros.")
        sizes[rng.choice(options)] += 1
        remaining -= 1

    levels = [[source]]
    pos = 0
    for s in sizes:
        levels.append(others[pos:pos + s])
        pos += s
    levels.append([target])
    return levels


def _force_tie(graph, source, target, w_min, rng):
    """Baja el peso de UNA arista para crear un segundo camino de costo exactamente d*.

    Los costos d(s,u) y d(v,t) no dependen de la arista (u, v) en un DAG, así que al fijar
    w' = w - holgura el mejor camino por esa arista cuesta justo d* y ningún otro camino cambia.
    """
    best, n_opt, slacks = _optimal_slacks(graph, source, target)
    if n_opt >= 2:
        return True
    candidates = [(s, u, v, w) for s, u, v, w in slacks if s > 0 and w - s >= w_min]
    if not candidates:
        return False
    smallest = min(c[0] for c in candidates)
    _, u, v, w = rng.choice([c for c in candidates if c[0] == smallest])
    graph.set_weight(u, v, w - smallest)
    return True


def generate_advanced_dag(n, source=0, target=None, min_hops=4, density="media",
                          max_out=3, forbid_direct=True, force_tie=False,
                          min_paths=1, w_min=1, w_max=99, seed=None):
    """DAG aleatorio con origen y destino fijados y restricciones configurables.

    - Ningún camino origen->destino tiene menos de `min_hops` aristas (regla del docente).
    - Cada nodo tiene a lo sumo `max_out` aristas salientes (red dispersa "real").
    - `force_tie` garantiza al menos dos caminos de costo mínimo idéntico.
    - `min_paths` exige al menos esa cantidad de caminos distintos origen->destino.
    """
    rng = random.Random(seed)
    if target is None:
        target = n - 1
    if not (2 <= n <= MAX_NODES):
        raise ValueError(f"n debe estar entre 2 y {MAX_NODES}.")
    if not (0 <= source < n and 0 <= target < n) or source == target:
        raise ValueError("Origen y destino deben ser nodos distintos del grafo.")
    if density not in DENSITY_PROFILES:
        raise ValueError("Densidad no válida (baja, media o alta).")
    if max_out < 2:
        raise ValueError("Máx. salidas por nodo debe ser al menos 2.")
    if not (1 <= w_min <= w_max <= 99):
        raise ValueError("Los pesos deben cumplir 1 ≤ mínimo ≤ máximo ≤ 99.")
    if forbid_direct:
        min_hops = max(min_hops, 2)
    if not (1 <= min_hops <= n - 1):
        raise ValueError(f"Con n={n} los saltos mínimos deben estar entre 1 y {n - 1}.")

    prof = DENSITY_PROFILES[density]
    levels = _assign_levels(n, source, target, min_hops, max_out, rng)
    level_of = {v: i for i, lv in enumerate(levels) for v in lv}
    graph = Graph(n)
    out_deg = {i: 0 for i in range(n)}

    def add(u, v):
        graph.add_edge(u, v, rng.randint(w_min, w_max))
        out_deg[u] += 1

    # 1) Conectividad: todo nodo recibe una arista de la capa anterior y emite una a la siguiente.
    for a, b in zip(levels, levels[1:]):
        for v in b:
            free = [u for u in a if out_deg[u] < max_out]
            add(rng.choice(free), v)
        for u in a:
            if out_deg[u] == 0:
                add(u, rng.choice(b))

    # 2) Aristas adicionales (competencia entre rutas) y atajos que saltan una capa.
    def extra_candidates():
        adjacent, skips = [], []
        for i, a in enumerate(levels):
            for u in a:
                for j, bucket in ((i + 1, adjacent), (i + 2, skips)):
                    if j < len(levels):
                        bucket += [(u, v) for v in levels[j] if not graph.has_edge(u, v)]
        return adjacent, skips

    adjacent, skips = extra_candidates()
    for pool, p in ((adjacent, prof["extra"]), (skips, prof["skip"])):
        for u, v in pool:
            if out_deg[u] < max_out and rng.random() < p:
                add(u, v)

    # 3) Regla de saltos: se eliminan atajos hasta que no exista camino con menos de min_hops aristas.
    def enforce_hops():
        while hop_distance(graph, source, target) < min_hops:
            path = _hop_path(graph, source, target)
            shortcuts = [(a, b) for a, b in zip(path, path[1:])
                         if level_of[b] - level_of[a] > 1]
            u, v = rng.choice(shortcuts)
            graph.remove_edge(u, v)
            out_deg[u] -= 1

    enforce_hops()

    # 4) Caminos alternativos mínimos.
    warnings = []
    if count_paths(graph, source, target) < min_paths:
        adjacent, skips = extra_candidates()
        pool = adjacent + skips
        rng.shuffle(pool)
        for u, v in pool:
            if count_paths(graph, source, target) >= min_paths:
                break
            if out_deg[u] >= max_out:
                continue
            add(u, v)
            if hop_distance(graph, source, target) < min_hops:
                graph.remove_edge(u, v)
                out_deg[u] -= 1
        if count_paths(graph, source, target) < min_paths:
            warnings.append(f"Solo se lograron {count_paths(graph, source, target)} "
                            f"caminos distintos (pedidos: {min_paths}).")

    # 5) Empate exacto en el óptimo; si los pesos no lo permiten se vuelven a sortear.
    if force_tie:
        tied = _force_tie(graph, source, target, w_min, rng)
        attempts = 0
        while not tied and attempts < 50:
            attempts += 1
            for u in range(n):
                graph.adj[u] = [(v, rng.randint(w_min, w_max)) for v, _ in graph.adj[u]]
            tied = _force_tie(graph, source, target, w_min, rng)
        if not tied:
            warnings.append("No fue posible forzar el empate con ese rango de pesos.")

    best, n_opt, _ = _optimal_slacks(graph, source, target)
    graph.info = {
        "source": source,
        "target": target,
        "hops": hop_distance(graph, source, target),
        "paths": count_paths(graph, source, target),
        "optimal_cost": best,
        "optimal_paths": n_opt,
        "warnings": warnings,
    }
    return graph


def generate_random_dag(n, seed=None):
    """Compatibilidad: DAG aleatorio de A (origen) a la última letra (destino)."""
    return generate_advanced_dag(n, 0, n - 1, min_hops=min(4, n - 1), seed=seed)


# ---------------------------------------------------------------- JSON
def graph_to_dict(graph, source=None, target=None, positions=None):
    data = {
        "formato": "dijkstra-dag",
        "version": 1,
        "n": graph.n,
        "aristas": [{"desde": graph.labels[u], "hasta": graph.labels[v], "peso": w}
                    for u, v, w in graph.edges()],
    }
    if source is not None and target is not None:
        data["origen"] = graph.labels[source]
        data["destino"] = graph.labels[target]
    if positions:
        data["posiciones"] = {graph.labels[i]: [round(x, 4), round(y, 4)]
                              for i, (x, y) in positions.items() if i < graph.n}
    return data


def graph_from_dict(data):
    """Reconstruye (grafo, origen, destino, posiciones) validando que sea un DAG."""
    try:
        n = int(data["n"])
        edges = data["aristas"]
    except (KeyError, TypeError, ValueError):
        raise ValueError("El archivo no tiene el formato esperado (faltan 'n' o 'aristas').")
    if not (2 <= n <= MAX_NODES):
        raise ValueError(f"n debe estar entre 2 y {MAX_NODES}.")

    graph = Graph(n)
    for e in edges:
        try:
            u = graph.index_of_label(e["desde"])
            v = graph.index_of_label(e["hasta"])
            w = int(e["peso"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"Arista no válida: {e}")
        if not (1 <= w <= 99):
            raise ValueError(f"Peso fuera de 1-99 en {e['desde']}→{e['hasta']}.")
        if u == v or graph.has_edge(u, v):
            raise ValueError(f"Arista repetida o bucle: {e['desde']}→{e['hasta']}.")
        graph.add_edge(u, v, w)
    if len(topological_order(graph)) != n:
        raise ValueError("El grafo contiene un ciclo: no es un DAG.")

    source = target = None
    if "origen" in data and "destino" in data:
        try:
            source = graph.index_of_label(data["origen"])
            target = graph.index_of_label(data["destino"])
        except ValueError:
            raise ValueError("Origen o destino no existen en el grafo.")

    positions = None
    if data.get("posiciones"):
        try:
            positions = {graph.index_of_label(k): (float(x), float(y))
                         for k, (x, y) in data["posiciones"].items()}
        except (ValueError, TypeError):
            positions = None
        if positions is not None and len(positions) != n:
            positions = None
    return graph, source, target, positions


def save_graph(path, graph, source=None, target=None, positions=None):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(graph_to_dict(graph, source, target, positions), f,
                  ensure_ascii=False, indent=2)


def load_graph(path):
    with open(path, "r", encoding="utf-8") as f:
        return graph_from_dict(json.load(f))
