import itertools
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dijkstra import all_min_paths, run_dijkstra
from graph_model import (Graph, count_paths, generate_advanced_dag, hop_distance,
                         load_graph, save_graph, topological_order, _optimal_slacks)


def brute_force_min(graph, s, t):
    """Costo mínimo y nº de caminos óptimos enumerando todos los caminos (DFS)."""
    costs = []

    def dfs(u, acc):
        if u == t:
            costs.append(acc)
            return
        for v, w in graph.adj[u]:
            dfs(v, acc + w)

    dfs(s, 0)
    best = min(costs)
    return best, costs.count(best)


class TestGenerador(unittest.TestCase):
    def check(self, g, n, s, t, min_hops, max_out, w_min, w_max):
        self.assertEqual(len(topological_order(g)), n, "debe ser DAG")
        self.assertGreaterEqual(hop_distance(g, s, t), min_hops)
        self.assertFalse(g.has_edge(s, t) and min_hops >= 2)
        for u in range(n):
            self.assertLessEqual(len(g.adj[u]), max_out)
        for _, _, w in g.edges():
            self.assertTrue(w_min <= w <= w_max)
        for v in range(n):  # todo nodo está en algún camino s -> t
            self.assertTrue(v == s or hop_distance(g, s, v) < math.inf)
            self.assertTrue(v == t or hop_distance(g, v, t) < math.inf)

    def test_malla_de_parametros(self):
        for n, min_hops, max_out, dens in itertools.product(
                (7, 8, 10, 13, 16), (1, 2, 3, 4, 5, 6), (2, 3, 4), ("baja", "media", "alta")):
            if min_hops > n - 1:
                continue
            for seed in range(8):
                s, t = (seed * 3) % n, (seed * 5 + 1) % n
                if s == t:
                    t = (t + 1) % n
                g = generate_advanced_dag(n, s, t, min_hops, dens, max_out, True,
                                          False, 2, 1, 99, seed)
                self.check(g, n, s, t, max(min_hops, 2), max_out, 1, 99)

    def test_empate_forzado_y_conteo(self):
        for n in (7, 8, 12, 16):
            for seed in range(40):
                g = generate_advanced_dag(n, 0, n - 1, 4 if n > 4 else 2, "media", 3,
                                          True, True, 2, 1, 30, seed)
                best, ties = brute_force_min(g, 0, n - 1)
                self.assertGreaterEqual(ties, 2, f"n={n} seed={seed}")
                self.assertEqual(best, g.info["optimal_cost"])
                self.assertEqual(ties, g.info["optimal_paths"])
                self.assertGreaterEqual(g.info["paths"], 2)
                self.assertEqual(count_paths(g, 0, n - 1), g.info["paths"])

    def test_parametros_invalidos(self):
        with self.assertRaises(ValueError):
            generate_advanced_dag(7, 0, 6, min_hops=7)
        with self.assertRaises(ValueError):
            generate_advanced_dag(7, 3, 3)
        with self.assertRaises(ValueError):
            generate_advanced_dag(7, 0, 6, max_out=1)


class TestDijkstra(unittest.TestCase):
    def test_contra_fuerza_bruta(self):
        for seed in range(150):
            n = 7 + seed % 6
            g = generate_advanced_dag(n, 0, n - 1, 3, "alta", 4, True, seed % 2 == 0, 1,
                                      1, 20, seed)
            steps = run_dijkstra(g, 0, n - 1, g.labels)
            last = steps[-1]
            best, ties = brute_force_min(g, 0, n - 1)
            self.assertEqual(last.dist[n - 1], best)
            paths, _ = all_min_paths(last.preds, 0, n - 1, last.dist)
            self.assertEqual(len(paths), ties)

    def test_caso_insignia_informe(self):
        g = Graph(8)
        for u, v, w in [(0, 1, 4), (0, 2, 5), (0, 3, 3), (1, 4, 4), (1, 2, 2), (2, 5, 4),
                        (2, 4, 3), (3, 6, 6), (3, 2, 3), (4, 7, 5), (5, 7, 4), (6, 5, 2),
                        (6, 7, 8)]:
            g.add_edge(u, v, w)
        last = run_dijkstra(g, 0, 7, g.labels)[-1]
        self.assertEqual(last.dist[7], 13)
        paths, _ = all_min_paths(last.preds, 0, 7, last.dist)
        # Con las aristas de scripts/generar_graficos.py hay 3 caminos óptimos, no 2:
        # A→C→E→H (5+3+5) también suma 13. Revisar que el grafo del informe coincida.
        self.assertIn([0, 1, 4, 7], paths)
        self.assertIn([0, 2, 5, 7], paths)
        self.assertEqual(len(paths), 3)


class TestJson(unittest.TestCase):
    def test_ida_y_vuelta(self):
        g = generate_advanced_dag(10, 2, 7, 4, "media", 3, True, True, 2, 1, 50, 5)
        pos = {i: (i * 0.1, -i * 0.05) for i in range(10)}
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "g.json")
            save_graph(path, g, 2, 7, pos)
            g2, s, t, p2 = load_graph(path)
        self.assertEqual((s, t), (2, 7))
        self.assertEqual(sorted(g.edges()), sorted(g2.edges()))
        self.assertAlmostEqual(p2[3][0], 0.3, places=3)

    def test_rechaza_ciclo_y_formato(self):
        from graph_model import graph_from_dict
        ciclo = {"n": 3, "aristas": [{"desde": "A", "hasta": "B", "peso": 1},
                                     {"desde": "B", "hasta": "C", "peso": 1},
                                     {"desde": "C", "hasta": "A", "peso": 1}]}
        with self.assertRaises(ValueError):
            graph_from_dict(ciclo)
        with self.assertRaises(ValueError):
            graph_from_dict({"hola": 1})


class TestNodos(unittest.TestCase):
    def test_remove_node_renumera(self):
        g = Graph(4)
        g.add_edge(0, 1, 1); g.add_edge(1, 2, 2); g.add_edge(2, 3, 3); g.add_edge(0, 3, 9)
        g.remove_node(1)
        self.assertEqual(g.n, 3)
        self.assertEqual(sorted(g.edges()), [(0, 2, 9), (1, 2, 3)])
        self.assertEqual(g.labels, ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()
