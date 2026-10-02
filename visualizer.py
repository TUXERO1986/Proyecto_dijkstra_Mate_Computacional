import math

import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

PATH_COLORS = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#a65628"]

COLOR_CURRENT = "#ff9800"
COLOR_VISITED = "#bdbdbd"
COLOR_FRONTIER = "#90caf9"
COLOR_UNREACHED = "#ffffff"
COLOR_EDGE_DEFAULT = "#9e9e9e"
COLOR_EDGE_EVAL = "#ff9800"
COLOR_EDGE_TREE = "#a5d6a7"


def _fmt(v):
    return "∞" if v == math.inf else str(v)


class GraphVisualizer:
    def __init__(self, master, graph):
        self.fig = Figure(figsize=(6.5, 6), facecolor="#fafafa")
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.graph = graph
        self.pos = {}
        self.node_radius = 0.06
        self.set_graph(graph)

    def widget(self):
        return self.canvas.get_tk_widget()

    def set_graph(self, graph, layers=None):
        self.graph = graph
        nxg = nx.DiGraph()
        nxg.add_nodes_from(range(graph.n))
        for u, v, w in graph.edges():
            nxg.add_edge(u, v, weight=w)

        pos = None
        num_layers = 1
        if layers:
            try:
                for node, layer in layers.items():
                    nxg.nodes[node]["subset"] = layer
                pos = nx.multipartite_layout(nxg, subset_key="subset")
                num_layers = max(layers.values()) + 1
            except Exception:
                pos = None
        if pos is None:
            pos = nx.spring_layout(nxg, seed=42, k=1.4 / max(1, graph.n ** 0.5))
        self.pos = pos

        gap = 2.0 / max(num_layers - 1, 1)
        self.node_radius = max(0.025, min(0.06, gap * 0.28))

    def render(self, dist=None, visited=None, current=None, frontier=None,
               eval_edge=None, tree_edges=None, path_edge_colors=None,
               legend_entries=None):
        ax = self.ax
        ax.clear()
        ax.axis("off")
        graph = self.graph
        visited = visited or set()
        frontier = frontier or []
        tree_edges = tree_edges or set()
        path_edge_colors = path_edge_colors or {}

        radius = self.node_radius
        for u, v, w in graph.edges():
            x1, y1 = self.pos[u]
            x2, y2 = self.pos[v]
            color, width, zorder = COLOR_EDGE_DEFAULT, 1.4, 1
            if (u, v) in path_edge_colors:
                color = path_edge_colors[(u, v)][0]
                width, zorder = 3.0, 3
            elif (u, v) in tree_edges:
                color, width, zorder = COLOR_EDGE_TREE, 2.2, 2
            if eval_edge is not None and (u, v) == eval_edge:
                color, width, zorder = COLOR_EDGE_EVAL, 3.0, 4

            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy)
            off = min(radius, length / 2 - 0.001) if length > 1e-6 else 0
            ux, uy = (dx / length, dy / length) if length > 1e-6 else (0, 0)
            sx, sy = x1 + ux * off, y1 + uy * off
            ex, ey = x2 - ux * off, y2 - uy * off

            ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=width,
                                         shrinkA=0, shrinkB=0, mutation_scale=10),
                        zorder=zorder)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx, my, str(w), fontsize=8, color="#333333", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85),
                    zorder=5)

        for node in range(graph.n):
            x, y = self.pos[node]
            if node == current:
                face, edge, lw = COLOR_CURRENT, "#e65100", 2.5
            elif node in visited:
                face, edge, lw = COLOR_VISITED, "#616161", 1.5
            elif node in frontier:
                face, edge, lw = COLOR_FRONTIER, "#1565c0", 1.5
            else:
                face, edge, lw = COLOR_UNREACHED, "#9e9e9e", 1.2

            circle = mpatches.Circle((x, y), radius, facecolor=face, edgecolor=edge,
                                      linewidth=lw, zorder=6)
            ax.add_patch(circle)

            label = graph.labels[node]
            text = f"{label}\n{_fmt(dist.get(node, math.inf))}" if dist is not None else label
            fontsize = 8 if radius >= 0.045 else max(5, 8 * radius / 0.06)
            ax.text(x, y, text, fontsize=fontsize, ha="center", va="center", zorder=7,
                     fontweight="bold")

        if legend_entries:
            handles = [mpatches.Patch(color=color, label=name) for name, color in legend_entries]
            ax.legend(handles=handles, loc="upper left", fontsize=7, framealpha=0.9)

        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        self.canvas.draw_idle()
