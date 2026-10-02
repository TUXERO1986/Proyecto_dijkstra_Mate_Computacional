import math
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

from dijkstra import all_min_paths, run_dijkstra
from graph_model import Graph, generate_random_dag, topological_layers
from visualizer import PATH_COLORS, GraphVisualizer


def _fmt(v):
    return "∞" if v == math.inf else str(v)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Visualizador de Dijkstra")
        root.geometry("1280x800")
        root.minsize(1000, 650)

        self.graph = Graph(7)
        self.source_idx = None
        self.target_idx = None
        self.steps = []
        self.step_index = 0
        self.auto_playing = False
        self.auto_job = None

        self._build_top_bar()
        self._build_nav_bar()
        self._build_main_area()

        self._set_nav_state(False)

    def _build_top_bar(self):
        bar = ttk.Frame(self.root, padding=6)
        bar.pack(side="top", fill="x")

        ttk.Label(bar, text="n:").pack(side="left")
        self.n_var = tk.IntVar(value=10)
        ttk.Spinbox(bar, from_=7, to=16, width=4, textvariable=self.n_var).pack(
            side="left", padx=(2, 12))

        self.mode_var = tk.StringVar(value="random")
        ttk.Radiobutton(bar, text="Manual", value="manual", variable=self.mode_var).pack(side="left")
        ttk.Radiobutton(bar, text="Aleatorio", value="random", variable=self.mode_var).pack(
            side="left", padx=(0, 12))

        ttk.Button(bar, text="Generar grafo", command=self.on_generate).pack(side="left", padx=(0, 24))

        ttk.Label(bar, text="Origen:").pack(side="left")
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(bar, textvariable=self.source_var, width=4, state="readonly")
        self.source_combo.pack(side="left", padx=(2, 12))
        self.source_combo.bind("<<ComboboxSelected>>", lambda e: self._reset_execution())

        ttk.Label(bar, text="Destino:").pack(side="left")
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(bar, textvariable=self.target_var, width=4, state="readonly")
        self.target_combo.pack(side="left", padx=(2, 12))
        self.target_combo.bind("<<ComboboxSelected>>", lambda e: self._reset_execution())

        self.run_btn = ttk.Button(bar, text="Ejecutar Dijkstra", command=self.on_run, state="disabled")
        self.run_btn.pack(side="left")

    def _build_main_area(self):
        area = ttk.Frame(self.root)
        area.pack(side="top", fill="both", expand=True)

        self.right = ttk.Frame(area, width=380, padding=6)
        self.right.pack(side="right", fill="y")
        self.right.pack_propagate(False)

        left = ttk.Frame(area)
        left.pack(side="left", fill="both", expand=True)
        self.visualizer = GraphVisualizer(left, self.graph)
        self.visualizer.widget().pack(fill="both", expand=True)
        self.visualizer.render()

        self._build_manual_panel()
        self._build_result_panel()
        self.show_manual_panel(False)

    def _build_manual_panel(self):
        self.manual_frame = ttk.LabelFrame(self.right, text="Agregar aristas", padding=6)

        row = ttk.Frame(self.manual_frame)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Origen:").pack(side="left")
        self.edge_from_var = tk.StringVar()
        self.edge_from_combo = ttk.Combobox(row, textvariable=self.edge_from_var, width=4, state="readonly")
        self.edge_from_combo.pack(side="left", padx=4)

        ttk.Label(row, text="Destino:").pack(side="left")
        self.edge_to_var = tk.StringVar()
        self.edge_to_combo = ttk.Combobox(row, textvariable=self.edge_to_var, width=4, state="readonly")
        self.edge_to_combo.pack(side="left", padx=4)

        ttk.Label(row, text="Peso:").pack(side="left")
        self.edge_w_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.edge_w_var, width=5).pack(side="left", padx=4)

        ttk.Button(self.manual_frame, text="Agregar arista", command=self.on_add_edge).pack(fill="x", pady=4)

        self.edge_list = tk.Listbox(self.manual_frame, height=14)
        self.edge_list.pack(fill="both", expand=True, pady=4)

        ttk.Button(self.manual_frame, text="Eliminar arista seleccionada",
                   command=self.on_remove_edge).pack(fill="x", pady=2)
        ttk.Button(self.manual_frame, text="Finalizar grafo",
                   command=self.on_finish_manual).pack(fill="x", pady=(8, 2))

    def _build_result_panel(self):
        self.info_frame = ttk.Frame(self.right)

        tree_font = tkfont.Font(family="TkDefaultFont", size=6)
        style = ttk.Style()
        style.configure("Dijkstra.Treeview", font=tree_font,
                         rowheight=tree_font.metrics("linespace") + 4)
        style.configure("Dijkstra.Treeview.Heading", font=(tree_font.actual("family"), 6, "bold"))

        dist_frame = ttk.LabelFrame(self.info_frame, text="Tabla de distancias", padding=4)
        dist_frame.pack(fill="both", expand=False, pady=(0, 6))
        cols = ("nodo", "dist", "vis", "pred")
        self.tree = ttk.Treeview(dist_frame, columns=cols, show="headings", height=10,
                                  style="Dijkstra.Treeview")
        for c, txt, w in zip(cols, ["Nodo", "Distancia", "Visitado", "Predecesor(es)"],
                              [52, 84, 74, 130]):
            self.tree.heading(c, text=txt)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("current", background="#ffe0b2")

        msg_frame = ttk.LabelFrame(self.info_frame, text="Mensaje del paso actual", padding=4)
        msg_frame.pack(fill="both", expand=False, pady=(0, 6))
        self.msg_text = tk.Text(msg_frame, height=4, wrap="word", state="disabled")
        self.msg_text.pack(fill="both", expand=True)

        result_frame = ttk.LabelFrame(self.info_frame, text="Resultados finales", padding=4)
        result_frame.pack(fill="both", expand=True)

        self.path_selector_var = tk.StringVar(value="Todos")
        self.path_selector = ttk.Combobox(result_frame, textvariable=self.path_selector_var,
                                           state="readonly", values=["Todos"])
        self.path_selector.pack(fill="x", side="bottom", pady=(4, 0))
        self.path_selector.bind("<<ComboboxSelected>>", lambda e: self.render_current())

        self.result_text = tk.Text(result_frame, height=8, wrap="word", state="disabled")
        self.result_text.pack(fill="both", expand=True, side="top")

    def _build_nav_bar(self):
        bar = ttk.Frame(self.root, padding=6)
        bar.pack(side="bottom", fill="x")

        self.btn_reset = ttk.Button(bar, text="⏮ Reiniciar", command=self.on_reset)
        self.btn_reset.pack(side="left", padx=2)
        self.btn_prev = ttk.Button(bar, text="◀ Anterior", command=self.on_prev)
        self.btn_prev.pack(side="left", padx=2)
        self.btn_auto = ttk.Button(bar, text="▶ Auto", command=self.on_toggle_auto)
        self.btn_auto.pack(side="left", padx=2)
        self.btn_next = ttk.Button(bar, text="Siguiente ▶", command=self.on_next)
        self.btn_next.pack(side="left", padx=2)
        self.btn_end = ttk.Button(bar, text="Ir al final ⏭", command=self.on_end)
        self.btn_end.pack(side="left", padx=2)

        self.step_label = ttk.Label(bar, text="Paso 0 / 0")
        self.step_label.pack(side="right", padx=8)

    def show_manual_panel(self, show):
        if show:
            self.info_frame.pack_forget()
            self.manual_frame.pack(fill="both", expand=True)
        else:
            self.manual_frame.pack_forget()
            self.info_frame.pack(fill="both", expand=True)

    def on_generate(self):
        try:
            n = int(self.n_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Error", "n debe ser un entero entre 7 y 16.")
            return
        if not (7 <= n <= 16):
            messagebox.showerror("Error", "n debe estar entre 7 y 16.")
            return

        self._reset_execution()
        self.run_btn.config(state="disabled")
        self.source_var.set("")
        self.target_var.set("")

        if self.mode_var.get() == "random":
            self.graph = generate_random_dag(n)
            self.show_manual_panel(False)
            self._finish_graph_setup()
        else:
            self.graph = Graph(n)
            self.edge_from_combo["values"] = self.graph.labels
            self.edge_to_combo["values"] = self.graph.labels
            self.edge_list.delete(0, "end")
            self.show_manual_panel(True)
            self.visualizer.set_graph(self.graph)
            self.visualizer.render()

    def on_add_edge(self):
        u_label = self.edge_from_var.get()
        v_label = self.edge_to_var.get()
        w_text = self.edge_w_var.get().strip()

        if not u_label or not v_label:
            messagebox.showerror("Error", "Seleccione origen y destino.")
            return
        if u_label == v_label:
            messagebox.showerror("Error", "No se permite un self-loop (origen = destino).")
            return
        if not w_text.isdigit() or not (1 <= int(w_text) <= 99):
            messagebox.showerror("Error", "El peso debe ser un entero entre 1 y 99.")
            return

        u = self.graph.index_of_label(u_label)
        v = self.graph.index_of_label(v_label)
        w = int(w_text)

        if self.graph.has_edge(u, v):
            messagebox.showerror("Error", f"La arista {u_label}→{v_label} ya existe.")
            return
        if self.graph.creates_cycle(u, v):
            messagebox.showerror("Error", f"No se puede agregar {u_label}→{v_label}: crearía un ciclo")
            return

        self.graph.add_edge(u, v, w)
        self.edge_list.insert("end", f"{u_label} → {v_label}   (peso {w})")
        self.edge_w_var.set("")
        self.visualizer.set_graph(self.graph)
        self.visualizer.render()

    def on_remove_edge(self):
        sel = self.edge_list.curselection()
        if not sel:
            return
        idx = sel[0]
        text = self.edge_list.get(idx)
        left, right = text.split(" → ")
        u = self.graph.index_of_label(left.strip())
        v = self.graph.index_of_label(right.split("(")[0].strip())
        self.graph.remove_edge(u, v)
        self.edge_list.delete(idx)
        self.visualizer.set_graph(self.graph)
        self.visualizer.render()

    def on_finish_manual(self):
        if len(self.graph.edges()) < self.graph.n - 1:
            messagebox.showwarning(
                "Grafo incompleto",
                f"Se necesitan al menos {self.graph.n - 1} aristas para continuar.")
            return

        isolated = [n for n in range(self.graph.n)
                    if not self.graph.adj[n]
                    and not any(self.graph.has_edge(o, n) for o in range(self.graph.n))]
        if isolated:
            labels = ", ".join(self.graph.labels[n] for n in isolated)
            if not messagebox.askyesno(
                    "Nodos aislados",
                    f"Los siguientes nodos no tienen ninguna conexión: {labels}. "
                    f"¿Continuar de todas formas?"):
                return

        self.show_manual_panel(False)
        self._finish_graph_setup()

    def _finish_graph_setup(self):
        layers = topological_layers(self.graph)
        self.visualizer.set_graph(self.graph, layers=layers)
        self.visualizer.render()
        labels = self.graph.labels
        self.source_combo["values"] = labels
        self.target_combo["values"] = labels
        self.source_var.set(labels[0])
        self.target_var.set(labels[-1])
        self.run_btn.config(state="normal")

    def on_run(self):
        src_label = self.source_var.get()
        dst_label = self.target_var.get()
        if not src_label or not dst_label:
            messagebox.showerror("Error", "Seleccione origen y destino.")
            return
        if src_label == dst_label:
            messagebox.showerror("Error", "Origen y destino deben ser distintos.")
            return

        self.source_idx = self.graph.index_of_label(src_label)
        self.target_idx = self.graph.index_of_label(dst_label)

        self._stop_auto()
        self.steps = run_dijkstra(self.graph, self.source_idx, self.target_idx, self.graph.labels)
        self.step_index = 0
        self._set_nav_state(True)
        self.render_current()

    def on_prev(self):
        if self.step_index > 0:
            self.step_index -= 1
            self.render_current()

    def on_next(self):
        if self.step_index < len(self.steps) - 1:
            self.step_index += 1
            self.render_current()

    def on_reset(self):
        self._stop_auto()
        self.step_index = 0
        self.render_current()

    def on_end(self):
        self._stop_auto()
        self.step_index = len(self.steps) - 1
        self.render_current()

    def on_toggle_auto(self):
        if self.auto_playing:
            self._stop_auto()
        else:
            self.auto_playing = True
            self.btn_auto.config(text="⏸ Pausa")
            self._auto_tick()

    def _auto_tick(self):
        if not self.auto_playing:
            return
        if self.step_index >= len(self.steps) - 1:
            self._stop_auto()
            return
        self.step_index += 1
        self.render_current()
        self.auto_job = self.root.after(1200, self._auto_tick)

    def _stop_auto(self):
        self.auto_playing = False
        self.btn_auto.config(text="▶ Auto")
        if self.auto_job is not None:
            self.root.after_cancel(self.auto_job)
            self.auto_job = None

    def _reset_execution(self):
        self._stop_auto()
        self.steps = []
        self.step_index = 0
        self.step_label.config(text="Paso 0 / 0")
        self._set_nav_state(False)
        self._clear_results()
        self.msg_text.config(state="normal")
        self.msg_text.delete("1.0", "end")
        self.msg_text.config(state="disabled")
        for item in self.tree.get_children():
            self.tree.delete(item)
        if self.graph is not None:
            self.visualizer.render()

    def _set_nav_state(self, enabled):
        state = "normal" if enabled else "disabled"
        for b in (self.btn_reset, self.btn_prev, self.btn_auto, self.btn_next, self.btn_end):
            b.config(state=state)

    def render_current(self):
        if not self.steps:
            return
        step = self.steps[self.step_index]
        total = len(self.steps)
        self.step_label.config(text=f"Paso {self.step_index + 1} / {total}")

        self.btn_prev.config(state="normal" if self.step_index > 0 else "disabled")
        self.btn_next.config(state="normal" if self.step_index < total - 1 else "disabled")
        self.btn_reset.config(state="normal" if self.step_index > 0 else "disabled")
        self.btn_end.config(state="normal" if self.step_index < total - 1 else "disabled")

        self._update_table(step)
        self._update_message(step)

        is_last = self.step_index == total - 1
        if is_last:
            dv = step.dist.get(self.target_idx, math.inf)
            if math.isinf(dv):
                paths, truncated = [], False
            else:
                paths, truncated = all_min_paths(step.preds, self.source_idx, self.target_idx, step.dist)
            self._update_results(step, paths, truncated)
            shown = self._shown_indices(paths)
            path_edge_colors = self._build_path_colors(paths, shown)
            legend = self._legend_for_paths(shown)
            self.visualizer.render(dist=step.dist, visited=step.visited, current=None,
                                    frontier=step.frontier, eval_edge=None, tree_edges=None,
                                    path_edge_colors=path_edge_colors, legend_entries=legend)
        else:
            self._clear_results()
            tree_edges = self._tree_edges(step.preds)
            self.visualizer.render(dist=step.dist, visited=step.visited, current=step.current,
                                    frontier=step.frontier, eval_edge=step.edge,
                                    tree_edges=tree_edges)

    def _tree_edges(self, preds):
        edges = set()
        for node, plist in preds.items():
            for p in plist:
                edges.add((p, node))
        return edges

    def _update_table(self, step):
        for item in self.tree.get_children():
            self.tree.delete(item)
        g = self.graph
        for node in range(g.n):
            dstr = _fmt(step.dist.get(node, math.inf))
            vis = "Sí" if node in step.visited else "No"
            preds = ", ".join(g.labels[p] for p in step.preds.get(node, []))
            tag = "current" if node == step.current else ""
            self.tree.insert("", "end", values=(g.labels[node], dstr, vis, preds), tags=(tag,))

    def _update_message(self, step):
        self.msg_text.config(state="normal")
        self.msg_text.delete("1.0", "end")
        self.msg_text.insert("1.0", step.message)
        self.msg_text.config(state="disabled")

    def _update_results(self, step, paths, truncated):
        g = self.graph
        dv = step.dist.get(self.target_idx, math.inf)
        lines = []
        if math.isinf(dv):
            lines.append(f"No existe camino de {g.labels[self.source_idx]} a {g.labels[self.target_idx]}.")
        else:
            suffix = "+" if truncated else ""
            lines.append(f"Distancia mínima: {dv}")
            lines.append(f"Cantidad de caminos mínimos: {len(paths)}{suffix}")
            for path in paths:
                path_str = " → ".join(g.labels[node] for node in path)
                lines.append(f"{path_str}   (distancia: {dv})")
            if truncated:
                lines.append("Se muestran los primeros 50 caminos mínimos.")

        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "\n".join(lines))
        self.result_text.config(state="disabled")

        options = ["Todos"] + [f"Camino {i + 1}" for i in range(len(paths))]
        self.path_selector["values"] = options
        if self.path_selector_var.get() not in options:
            self.path_selector_var.set("Todos")

    def _clear_results(self):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.config(state="disabled")
        self.path_selector["values"] = ["Todos"]
        self.path_selector_var.set("Todos")

    def _shown_indices(self, paths):
        sel = self.path_selector_var.get()
        if sel == "Todos" or not paths:
            return list(range(len(paths)))
        try:
            idx = int(sel.split(" ")[1]) - 1
            if 0 <= idx < len(paths):
                return [idx]
        except (IndexError, ValueError):
            pass
        return list(range(len(paths)))

    def _build_path_colors(self, paths, shown_indices):
        colors = {}
        for i in shown_indices:
            color = PATH_COLORS[i % len(PATH_COLORS)]
            for a, b in zip(paths[i], paths[i][1:]):
                colors.setdefault((a, b), []).append(color)
        return colors

    def _legend_for_paths(self, shown_indices):
        if len(shown_indices) <= 1:
            return None
        return [(f"Camino {i + 1}", PATH_COLORS[i % len(PATH_COLORS)]) for i in shown_indices]
