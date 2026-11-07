import math

import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

THEME_PALETTES = {
    "light": {
        "bg": "#fafafa",
        "current": "#ff9800",
        "current_edge": "#e65100",
        "visited": "#d4d4d4",
        "visited_edge": "#616161",
        "frontier": "#90caf9",
        "frontier_edge": "#1565c0",
        "unreached": "#ffffff",
        "unreached_edge": "#757575",
        "node_text": "#111111",
        "dist_text": "#222222",
        "dist_current_text": "#111111",
        "edge_default": "#9e9e9e",
        "edge_eval": "#ff9800",
        "edge_tree": "#2e7d32",
        "badge_bg": "#ffffff",
        "badge_edge": "#cccccc",
        "badge_text": "#222222",
        "legend_bg": "#ffffff",
        "legend_edge": "#cccccc",
        "legend_text": "#222222",
        "path_colors": ["#d32f2f", "#1976d2", "#2e7d32", "#7b1fa2", "#ef6c00", "#6d4c41"],
    },
    "dark": {
        "bg": "#1e1e1e",
        "current": "#ff9800",
        "current_edge": "#ffe082",
        "visited": "#383d47",
        "visited_edge": "#6c7689",
        "frontier": "#1976d2",
        "frontier_edge": "#64b5f6",
        "unreached": "#2b3240",
        "unreached_edge": "#5c6b84",
        "node_text": "#ffffff",
        "dist_text": "#abb2bf",
        "dist_current_text": "#ffffff",
        "edge_default": "#5e697d",
        "edge_eval": "#ffb74d",
        "edge_tree": "#81c784",
        "badge_bg": "#282c34",
        "badge_edge": "#4b5263",
        "badge_text": "#e5c07b",
        "legend_bg": "#252526",
        "legend_edge": "#444444",
        "legend_text": "#f0f0f0",
        "path_colors": ["#ff5252", "#40c4ff", "#69f0ae", "#ea80fc", "#ffd740", "#ffab91"],
    },
}

PATH_COLORS = THEME_PALETTES["light"]["path_colors"]

COLOR_CURRENT = THEME_PALETTES["light"]["current"]
COLOR_VISITED = THEME_PALETTES["light"]["visited"]
COLOR_FRONTIER = THEME_PALETTES["light"]["frontier"]
COLOR_UNREACHED = THEME_PALETTES["light"]["unreached"]
COLOR_EDGE_DEFAULT = THEME_PALETTES["light"]["edge_default"]
COLOR_EDGE_EVAL = THEME_PALETTES["light"]["edge_eval"]
COLOR_EDGE_TREE = THEME_PALETTES["light"]["edge_tree"]


def _fmt(v):
    return "∞" if v == math.inf else str(v)


class GraphVisualizer:
    def __init__(self, master, graph):
        self.dark_mode = False
        initial_bg = THEME_PALETTES["light"]["bg"]
        self.fig = Figure(figsize=(6.5, 6), facecolor=initial_bg)
        # Use full 100% bounds to prevent artificial margins and inner border clipping
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        try:
            self.canvas.get_tk_widget().configure(bg=initial_bg, highlightthickness=0, bd=0)
        except Exception:
            pass
        self.graph = graph
        self.pos = {}
        self.node_radius = 0.06

        # Zoom and pan state
        self.xlim = (-1.1, 1.1)
        self.ylim = (-1.1, 1.1)
        self.base_xlim = (-1.1, 1.1)
        self.base_ylim = (-1.1, 1.1)
        self._drag_data = {"x0": None, "y0": None, "xlim0": None, "ylim0": None, "dragging": False}

        # Modo de dibujo interactivo: gesto en curso, línea guía y callbacks hacia la UI
        self.edit_mode = False
        self.handlers = {}
        self._gesture = None
        self._guide = None
        self._last_render = {}

        self.set_graph(graph)

        # Mouse event bindings for zoom and pan
        self.canvas.mpl_connect("resize_event", lambda e: self.apply_zoom())
        self.canvas.mpl_connect("scroll_event", self._on_scroll)
        self.canvas.mpl_connect("button_press_event", self._on_press)
        self.canvas.mpl_connect("button_release_event", self._on_release)
        self.canvas.mpl_connect("motion_notify_event", self._on_motion)

    def set_dark_mode(self, is_dark):
        self.dark_mode = bool(is_dark)
        theme = "dark" if self.dark_mode else "light"
        bg = THEME_PALETTES[theme]["bg"]
        self.fig.set_facecolor(bg)
        self.ax.set_facecolor(bg)
        try:
            self.canvas.get_tk_widget().configure(bg=bg, highlightthickness=0, bd=0)
        except Exception:
            pass

    def get_path_colors(self):
        theme = "dark" if self.dark_mode else "light"
        return THEME_PALETTES[theme]["path_colors"]

    def widget(self):
        return self.canvas.get_tk_widget()

    def set_graph(self, graph, layers=None, reset_view=True, positions=None):
        self.graph = graph
        pos = None
        num_layers = 1

        if positions is not None:
            pos = {k: tuple(v) for k, v in positions.items()}
            layers = None

        if layers:
            try:
                from collections import defaultdict
                layer_nodes = defaultdict(list)
                for node in range(graph.n):
                    layer_nodes[layers.get(node, 0)].append(node)
                num_layers = max(layers.values()) + 1

                pos = {}
                for l in range(num_layers):
                    nodes = layer_nodes.get(l, [])
                    x = -1.0 + 2.0 * l / max(num_layers - 1, 1)
                    m = len(nodes)
                    if m == 1:
                        if l == 0 or l == num_layers - 1:
                            y = 0.0
                        else:
                            y = 0.32 if (l % 2 == 1) else -0.22
                        pos[nodes[0]] = (x, y)
                    elif m > 1:
                        for idx, node in enumerate(nodes):
                            y = -0.72 + 1.44 * idx / (m - 1)
                            pos[node] = (x, y)
            except Exception:
                pos = None

        if pos is None:
            # Layout circular simétrico y ordenado para modo manual o grafos sin capas:
            # Distribuye los nodos en un círculo de radio 1.0, empezando arriba (12:00) en sentido horario.
            pos = {}
            for i in range(graph.n):
                angle = math.pi / 2.0 - (2.0 * math.pi * i) / graph.n
                pos[i] = (math.cos(angle), math.sin(angle))
            num_layers = 1

        self.pos = pos

        if positions is not None:
            self.node_radius = 0.06
        elif layers:
            layer_gap = 2.0 / max(num_layers - 1, 1)
            self.node_radius = max(0.048, min(0.075, layer_gap * 0.30))
        else:
            chord = 2.0 * math.sin(math.pi / max(graph.n, 1))
            self.node_radius = max(0.050, min(0.075, chord * 0.22))

        # Calculate bounding box to fit the graph closely without excess empty margins
        if not self.pos:
            self.base_xlim = (-1.1, 1.1)
            self.base_ylim = (-1.1, 1.1)
            if reset_view:
                self.xlim, self.ylim = self.base_xlim, self.base_ylim
        else:
            xs = [x for x, y in self.pos.values()]
            ys = [y for x, y in self.pos.values()]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            pad_x = self.node_radius * 2.0 + 0.08
            pad_y = self.node_radius * 2.0 + 0.10
            top_margin = 0.18 if (layers and num_layers > 1) else 0.0
            self.base_xlim = (min_x - pad_x, max_x + pad_x)
            self.base_ylim = (min_y - pad_y, max_y + pad_y + top_margin)
            if reset_view:
                self.xlim = self.base_xlim
                self.ylim = self.base_ylim

    def _fit_limits(self):
        """Amplía la ventana de datos para que coincida con la proporción del lienzo.

        Con aspecto 'equal' Matplotlib recortaba el eje Y cuando el lienzo era bajo
        (por ejemplo con el panel de opciones visible); así solo se amplía, nunca se recorta.
        """
        w, h = self.ax.bbox.width, self.ax.bbox.height
        (x0, x1), (y0, y1) = self.xlim, self.ylim
        if w > 0 and h > 0 and y1 > y0 and x1 > x0:
            if (x1 - x0) / (y1 - y0) < w / h:
                half = (y1 - y0) * w / h / 2.0
                cx = (x0 + x1) / 2.0
                x0, x1 = cx - half, cx + half
            else:
                half = (x1 - x0) * h / w / 2.0
                cy = (y0 + y1) / 2.0
                y0, y1 = cy - half, cy + half
        self.xlim, self.ylim = (x0, x1), (y0, y1)

    def apply_zoom(self):
        self._fit_limits()
        self.ax.set_xlim(self.xlim)
        self.ax.set_ylim(self.ylim)
        self.canvas.draw_idle()

    def zoom_in(self, factor=0.8):
        cx = (self.xlim[0] + self.xlim[1]) / 2.0
        cy = (self.ylim[0] + self.ylim[1]) / 2.0
        dx = (self.xlim[1] - self.xlim[0]) * factor / 2.0
        dy = (self.ylim[1] - self.ylim[0]) * factor / 2.0
        self.xlim = (cx - dx, cx + dx)
        self.ylim = (cy - dy, cy + dy)
        self.apply_zoom()

    def zoom_out(self, factor=1.25):
        cx = (self.xlim[0] + self.xlim[1]) / 2.0
        cy = (self.ylim[0] + self.ylim[1]) / 2.0
        dx = (self.xlim[1] - self.xlim[0]) * factor / 2.0
        dy = (self.ylim[1] - self.ylim[0]) * factor / 2.0
        self.xlim = (cx - dx, cx + dx)
        self.ylim = (cy - dy, cy + dy)
        self.apply_zoom()

    def reset_zoom(self):
        self.xlim = self.base_xlim
        self.ylim = self.base_ylim
        self.apply_zoom()

    def _on_scroll(self, event):
        if event.inaxes != self.ax:
            return
        scale = 0.82 if event.button == "up" else 1.22
        xdata, ydata = event.xdata, event.ydata
        if xdata is None or ydata is None:
            return
        x_left = xdata - (xdata - self.xlim[0]) * scale
        x_right = xdata + (self.xlim[1] - xdata) * scale
        y_bottom = ydata - (ydata - self.ylim[0]) * scale
        y_top = ydata + (self.ylim[1] - ydata) * scale
        self.xlim = (x_left, x_right)
        self.ylim = (y_bottom, y_top)
        self.apply_zoom()

    # ------------------------------------------------------------ edición
    def set_edit_mode(self, enabled, handlers=None):
        self.edit_mode = bool(enabled)
        self.handlers = handlers or {}
        self._gesture = None

    def place_node(self, node, x, y):
        self.pos[node] = (x, y)

    def drop_node(self, node):
        self.pos = {(k if k < node else k - 1): v for k, v in self.pos.items() if k != node}

    def _call(self, name, *args):
        handler = self.handlers.get(name)
        if handler:
            handler(*args)

    def _node_at(self, x, y):
        if x is None or y is None:
            return None
        best, best_d = None, self.node_radius * 1.15
        for node, (nx, ny) in self.pos.items():
            d = math.hypot(x - nx, y - ny)
            if d <= best_d:
                best, best_d = node, d
        return best

    def _edge_at(self, x, y):
        if x is None or y is None:
            return None
        tol = self.node_radius * 0.45
        for u, v, _ in self.graph.edges():
            (x1, y1), (x2, y2) = self.pos[u], self.pos[v]
            dx, dy = x2 - x1, y2 - y1
            length2 = dx * dx + dy * dy
            t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / length2))
            if math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)) <= tol:
                return (u, v)
        return None

    def _clear_guide(self):
        if self._guide is not None:
            try:
                self._guide.remove()
            except (ValueError, NotImplementedError):
                pass
            self._guide = None

    # ------------------------------------------------------------ eventos
    def _on_press(self, event):
        if event.inaxes != self.ax:
            return
        if self.edit_mode:
            if event.button == 3:
                node = self._node_at(event.xdata, event.ydata)
                if node is not None:
                    self._call("delete_node", node)
                else:
                    edge = self._edge_at(event.xdata, event.ydata)
                    if edge is not None:
                        self._call("delete_edge", *edge)
                return
            if event.button == 1:
                node = self._node_at(event.xdata, event.ydata)
                if node is not None:
                    shift = bool(getattr(event.guiEvent, "state", 0) & 0x1)
                    self._gesture = {"kind": "move" if shift else "edge", "node": node,
                                     "x0": event.x, "y0": event.y, "moved": False}
                    if not shift:
                        x, y = self.pos[node]
                        self._guide = Line2D([x, x], [y, y], color="#ff9800", lw=2.2,
                                             ls="--", zorder=10)
                        self.ax.add_line(self._guide)
                    return
                self._gesture = {"kind": "click", "x0": event.x, "y0": event.y, "moved": False,
                                 "xdata": event.xdata, "ydata": event.ydata}
        if event.button in (1, 2, 3):
            self._drag_data["x0"] = event.x
            self._drag_data["y0"] = event.y
            self._drag_data["xlim0"] = self.xlim
            self._drag_data["ylim0"] = self.ylim
            self._drag_data["dragging"] = True

    def _on_release(self, event):
        self._drag_data["dragging"] = False
        g, self._gesture = self._gesture, None
        if g is None:
            return
        inside = event.inaxes == self.ax
        if g["kind"] == "edge":
            self._clear_guide()
            target = self._node_at(event.xdata, event.ydata) if inside else None
            if g["moved"] and target is not None and target != g["node"]:
                self._call("edge_drawn", g["node"], target)
            self.render(**self._last_render)
        elif g["kind"] == "move":
            self.render(**self._last_render)
        elif g["kind"] == "click" and not g["moved"] and inside:
            self._call("empty_click", g["xdata"], g["ydata"])

    def _on_motion(self, event):
        g = self._gesture
        if g is not None and event.x is not None:
            if math.hypot(event.x - g["x0"], event.y - g["y0"]) > 4:
                g["moved"] = True
            if g["kind"] in ("edge", "move"):
                if event.inaxes != self.ax or event.xdata is None:
                    return
                if g["kind"] == "edge":
                    x, y = self.pos[g["node"]]
                    self._guide.set_data([x, event.xdata], [y, event.ydata])
                    self.canvas.draw_idle()
                elif g["moved"]:
                    self.pos[g["node"]] = (event.xdata, event.ydata)
                    self.render(**self._last_render)
                return
        if not self._drag_data["dragging"] or event.x is None or event.y is None:
            return
        dx_pixels = event.x - self._drag_data["x0"]
        dy_pixels = event.y - self._drag_data["y0"]
        bbox = self.ax.bbox
        if bbox.width <= 0 or bbox.height <= 0:
            return
        data_width = self._drag_data["xlim0"][1] - self._drag_data["xlim0"][0]
        data_height = self._drag_data["ylim0"][1] - self._drag_data["ylim0"][0]
        dx = (dx_pixels / bbox.width) * data_width
        dy = (dy_pixels / bbox.height) * data_height
        self.xlim = (self._drag_data["xlim0"][0] - dx, self._drag_data["xlim0"][1] - dx)
        self.ylim = (self._drag_data["ylim0"][0] - dy, self._drag_data["ylim0"][1] - dy)
        self.apply_zoom()

    def render(self, dist=None, visited=None, current=None, frontier=None,
               eval_edge=None, tree_edges=None, path_edge_colors=None,
               legend_entries=None):
        self._last_render = dict(dist=dist, visited=visited, current=current,
                                 frontier=frontier, eval_edge=eval_edge, tree_edges=tree_edges,
                                 path_edge_colors=path_edge_colors, legend_entries=legend_entries)
        self._guide = None
        theme = "dark" if self.dark_mode else "light"
        p = THEME_PALETTES[theme]

        ax = self.ax
        ax.clear()
        ax.axis("off")
        ax.set_facecolor(p["bg"])
        self.fig.set_facecolor(p["bg"])
        ax.set_position([0, 0, 1, 1])
        ax.set_aspect("equal", adjustable="datalim")

        graph = self.graph
        visited = visited or set()
        frontier = frontier or []
        tree_edges = tree_edges or set()
        path_edge_colors = path_edge_colors or {}

        radius = self.node_radius
        for u, v, w in graph.edges():
            x1, y1 = self.pos[u]
            x2, y2 = self.pos[v]
            color, width, zorder = p["edge_default"], 1.4, 1
            if (u, v) in path_edge_colors:
                color = path_edge_colors[(u, v)][0]
                width, zorder = 3.0, 3
            elif (u, v) in tree_edges:
                color, width, zorder = p["edge_tree"], 2.2, 2
            if eval_edge is not None and (u, v) == eval_edge:
                color, width, zorder = p["edge_eval"], 3.0, 4

            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy)
            off = min(radius, length / 2 - 0.001) if length > 1e-6 else 0
            ux, uy = (dx / length, dy / length) if length > 1e-6 else (0, 0)
            sx, sy = x1 + ux * off, y1 + uy * off
            ex, ey = x2 - ux * off, y2 - uy * off

            ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=width,
                                         shrinkA=0, shrinkB=0, mutation_scale=10),
                        zorder=zorder, clip_on=False)
            t = 0.35 + 0.15 * ((u + v * 3) % 3) / 2.0
            mx, my = x1 + t * dx, y1 + t * dy
            ax.text(mx, my, str(w), fontsize=8.0, color=p["badge_text"], ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.12", fc=p["badge_bg"], ec=p["badge_edge"], lw=0.5, alpha=0.95),
                    zorder=5, clip_on=False)

        fs_label = max(8.0, min(10.5, radius * 135))
        fs_dist = max(6.5, min(8.0, radius * 105))
        dy = radius * 0.23

        for node in range(graph.n):
            x, y = self.pos[node]
            if node == current:
                face, edge, lw = p["current"], p["current_edge"], 2.5
            elif node in visited:
                face, edge, lw = p["visited"], p["visited_edge"], 1.8
            elif node in frontier:
                face, edge, lw = p["frontier"], p["frontier_edge"], 1.8
            else:
                face, edge, lw = p["unreached"], p["unreached_edge"], 1.4

            circle = mpatches.Circle((x, y), radius, facecolor=face, edgecolor=edge,
                                      linewidth=lw, zorder=6, clip_on=False)
            ax.add_patch(circle)

            label = graph.labels[node]
            if dist is not None:
                d_val = dist.get(node, math.inf)
                d_str = "∞" if math.isinf(d_val) else str(int(d_val))
                eff_fs_dist = fs_dist * 0.85 if len(d_str) >= 3 else fs_dist
                ax.text(x, y + dy, label, fontsize=fs_label, fontweight="bold",
                        ha="center", va="center", zorder=7, color=p["node_text"], clip_on=False)
                dist_color = p["dist_current_text"] if node == current else p["dist_text"]
                ax.text(x, y - dy * 1.35, d_str, fontsize=eff_fs_dist, fontweight="bold",
                        ha="center", va="center", zorder=7, color=dist_color, clip_on=False)
            else:
                ax.text(x, y, label, fontsize=fs_label + 1.0, fontweight="bold",
                        ha="center", va="center", zorder=7, color=p["node_text"], clip_on=False)

        if legend_entries:
            handles = [mpatches.Patch(color=color, label=name) for name, color in legend_entries]
            ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.06),
                      ncol=min(len(handles), 4), fontsize=8, framealpha=0.92,
                      facecolor=p["legend_bg"], edgecolor=p["legend_edge"],
                      labelcolor=p["legend_text"])

        self._fit_limits()
        ax.set_xlim(self.xlim)
        ax.set_ylim(self.ylim)
        self.canvas.draw_idle()
