import heapq
import math
from dataclasses import dataclass


@dataclass
class Step:
    kind: str
    current: int | None
    edge: tuple[int, int] | None
    dist: dict[int, float]
    visited: set[int]
    frontier: list[int]
    preds: dict[int, list[int]]
    message: str


def _fmt(v):
    return "∞" if v == math.inf else str(v)


def run_dijkstra(graph, source, target, labels):
    dist = {i: math.inf for i in range(graph.n)}
    dist[source] = 0
    preds = {i: [] for i in range(graph.n)}
    visited = set()
    pq = [(0, source)]
    steps = []

    def snapshot():
        return (dict(dist), set(visited), [node for _, node in pq],
                {k: list(v) for k, v in preds.items()})

    d, v, f, p = snapshot()
    steps.append(Step("init", None, None, d, v, f, p,
                       f"Inicialización: dist[{labels[source]}]=0, resto ∞. "
                       f"Cola: [{labels[source]}]"))

    while pq:
        d0, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)

        d, v, f, p = snapshot()
        steps.append(Step("select", u, None, d, v, f, p,
                           f"Se selecciona {labels[u]} (dist={d0}), el menor no visitado. "
                           f"Se marca como visitado."))

        for v_node, w in graph.adj[u]:
            nd = d0 + w
            old = dist[v_node]
            if nd < old:
                dist[v_node] = nd
                preds[v_node] = [u]
                heapq.heappush(pq, (nd, v_node))
                d, vs, f, p = snapshot()
                steps.append(Step("relax", u, (u, v_node), d, vs, f, p,
                                   f"Arista {labels[u]}→{labels[v_node]} (peso {w}): "
                                   f"{d0}+{w}={nd} < {_fmt(old)}. Se actualiza "
                                   f"dist[{labels[v_node]}]={nd}, predecesor "
                                   f"{labels[v_node]}←{labels[u]}"))
            elif nd == old:
                if u not in preds[v_node]:
                    preds[v_node].append(u)
                    d, vs, f, p = snapshot()
                    steps.append(Step("tie", u, (u, v_node), d, vs, f, p,
                                       f"Arista {labels[u]}→{labels[v_node]} (peso {w}): "
                                       f"{d0}+{w}={nd} = dist[{labels[v_node]}]. Empate: "
                                       f"se agrega {labels[u]} como predecesor adicional de "
                                       f"{labels[v_node]}"))
            else:
                d, vs, f, p = snapshot()
                steps.append(Step("skip", u, (u, v_node), d, vs, f, p,
                                   f"Arista {labels[u]}→{labels[v_node]} (peso {w}): "
                                   f"{d0}+{w}={nd} > {_fmt(old)}. No se actualiza."))

    d, v, f, p = snapshot()
    if math.isinf(dist[target]):
        msg = f"Algoritmo finalizado. No existe camino de {labels[source]} a {labels[target]}."
    else:
        msg = (f"Algoritmo finalizado. Distancia mínima "
               f"{labels[source]}→{labels[target]} = {dist[target]}")
    steps.append(Step("done", None, None, d, v, f, p, msg))
    return steps


def all_min_paths(preds, source, target, dist, limit=50):
    if dist.get(target, math.inf) == math.inf:
        return [], False

    paths = []
    truncated = False

    def backtrack(node, acc):
        nonlocal truncated
        if len(paths) >= limit:
            truncated = True
            return
        if node == source:
            paths.append([source] + acc[::-1])
            return
        for p in preds.get(node, []):
            if len(paths) >= limit:
                truncated = True
                return
            backtrack(p, acc + [node])

    backtrack(target, [])
    return paths, truncated
