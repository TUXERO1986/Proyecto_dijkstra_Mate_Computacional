import heapq
import math
import random
import string

LABELS = list(string.ascii_uppercase[:16])


class Graph:
    def __init__(self, n):
        self.n = n
        self.adj = {i: [] for i in range(n)}
        self.labels = LABELS[:n]

    def add_edge(self, u, v, w):
        self.adj[u].append((v, w))

    def remove_edge(self, u, v):
        self.adj[u] = [(x, w) for x, w in self.adj[u] if x != v]

    def has_edge(self, u, v):
        return any(x == v for x, _ in self.adj[u])

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
    queue = [i for i in range(graph.n) if indeg[i] == 0]
    order = []
    while queue:
        node = queue.pop(0)
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


def _distances_from(graph, source):
    dist = {i: math.inf for i in range(graph.n)}
    dist[source] = 0
    visited = set()
    pq = [(0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        for v, w in graph.adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def _seed_tie(graph, order, rng):
    root = order[0]
    dist = _distances_from(graph, root)
    candidates = list(order[1:])
    rng.shuffle(candidates)
    for node in candidates:
        incoming = [(u, w) for u in range(graph.n) for v, w in graph.adj[u] if v == node]
        reachable = [(u, w) for u, w in incoming if not math.isinf(dist[u])]
        if len(reachable) < 2:
            continue
        for i in range(len(reachable)):
            for j in range(len(reachable)):
                if i == j:
                    continue
                u1, w1 = reachable[i]
                u2, w2 = reachable[j]
                new_w = dist[u1] + w1 - dist[u2]
                if 1 <= new_w <= 99 and new_w != w2:
                    graph.remove_edge(u2, node)
                    graph.add_edge(u2, node, new_w)
                    return


def generate_random_dag(n, seed=None):
    rng = random.Random(seed)
    order = list(range(n))
    rng.shuffle(order)

    graph = Graph(n)
    candidates = [(order[i], order[j]) for i in range(n) for j in range(i + 1, n)]
    rng.shuffle(candidates)

    p = 0.35
    for u, v in candidates:
        if rng.random() < p:
            graph.add_edge(u, v, rng.randint(1, 99))

    target_min = int(round(1.5 * n))
    target_max = int(round(2.5 * n))

    if len(graph.edges()) < target_min:
        missing = [(u, v) for u, v in candidates if not graph.has_edge(u, v)]
        rng.shuffle(missing)
        for u, v in missing:
            if len(graph.edges()) >= target_min:
                break
            graph.add_edge(u, v, rng.randint(1, 99))
    elif len(graph.edges()) > target_max:
        existing = graph.edges()
        rng.shuffle(existing)
        for u, v, _ in existing:
            if len(graph.edges()) <= target_max:
                break
            graph.remove_edge(u, v)

    for i, node in enumerate(order):
        if i < n - 1 and not graph.adj[node]:
            graph.add_edge(node, order[i + 1], rng.randint(1, 99))

    for i, node in enumerate(order):
        if i == 0:
            continue
        has_incoming = any(graph.has_edge(order[j], node) for j in range(i))
        if not has_incoming:
            source = order[i - 1]
            if not graph.has_edge(source, node):
                graph.add_edge(source, node, rng.randint(1, 99))

    if rng.random() < 0.5:
        _seed_tie(graph, order, rng)

    return graph
