import json
import math
import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

from dijkstra import all_min_paths, run_dijkstra
from graph_model import (LABELS, MAX_NODES, Graph, generate_advanced_dag, load_graph,
                         save_graph, topological_layers)
from visualizer import PATH_COLORS, GraphVisualizer


def _fmt(v):
    return "∞" if v == math.inf else str(v)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Visualizador de Dijkstra")
        root.geometry("1280x800")
        root.minsize(1100, 650)

        self.style = ttk.Style()
        self.initial_theme = self.style.theme_use()
        self.dark_mode = False

        self.graph = Graph(7)
        self.graph_ready = False
        self.source_idx = None
        self.target_idx = None
        self.steps = []
        self.step_index = 0
        self.auto_playing = False
        self.auto_job = None

        self._build_top_bar()
        self._build_options_bar()
        self._build_nav_bar()
        self._build_main_area()

        self._set_nav_state(False)
        self._on_n_changed()
        self._on_mode_change()
        self._apply_theme()

    def _build_top_bar(self):
        bar = ttk.Frame(self.root, padding=6)
        bar.pack(side="top", fill="x")
        self.top_bar = bar

        ttk.Label(bar, text="n:").pack(side="left")
        self.n_var = tk.IntVar(value=10)
        ttk.Spinbox(bar, from_=7, to=MAX_NODES, width=4, textvariable=self.n_var).pack(
            side="left", padx=(2, 12))
        self.n_var.trace_add("write", lambda *a: self._on_n_changed())

        self.mode_var = tk.StringVar(value="random")
        for text, value in (("Aleatorio", "random"), ("Formulario", "manual"), ("Dibujo", "draw")):
            ttk.Radiobutton(bar, text=text, value=value, variable=self.mode_var).pack(
                side="left", padx=(0, 4))
        self.mode_var.trace_add("write", lambda *a: self._on_mode_change())

        self.gen_btn = ttk.Button(bar, text="Generar grafo", command=self.on_generate)
        self.gen_btn.pack(side="left", padx=(8, 24))

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

        # Botón para alternar entre Modo Claro y Modo Oscuro
        self.theme_btn = ttk.Button(bar, text="🌙 Modo Oscuro", command=self.toggle_dark_mode)
        self.theme_btn.pack(side="right", padx=(12, 4))
        ttk.Button(bar, text="Cargar", width=8, command=self.on_load).pack(side="right", padx=2)
        ttk.Button(bar, text="Guardar", width=8, command=self.on_save).pack(side="right", padx=2)

    def _build_options_bar(self):
        """Opciones del generador aleatorio (solo visibles en modo Aleatorio)."""
        self.options_bar = ttk.LabelFrame(self.root, text="Opciones del grafo aleatorio", padding=(8, 2))

        self.forbid_direct_var = tk.BooleanVar(value=True)
        self.min_hops_var = tk.IntVar(value=4)
        self.max_out_var = tk.IntVar(value=3)
        self.density_var = tk.StringVar(value="Media")
        self.force_tie_var = tk.BooleanVar(value=False)
        self.min_paths_var = tk.IntVar(value=2)
        self.w_min_var = tk.IntVar(value=1)
        self.w_max_var = tk.IntVar(value=99)

        def spin(parent, var, lo, hi):
            return ttk.Spinbox(parent, from_=lo, to=hi, width=4, textvariable=var)

        r1 = ttk.Frame(self.options_bar)
        r1.pack(fill="x", pady=1)
        ttk.Checkbutton(r1, text="Prohibir arista directa Origen → Destino",
                        variable=self.forbid_direct_var).pack(side="left", padx=(0, 16))
        ttk.Label(r1, text="Saltos mínimos:").pack(side="left")
        spin(r1, self.min_hops_var, 1, MAX_NODES - 1).pack(side="left", padx=(2, 16))
        ttk.Label(r1, text="Máx. salidas por nodo:").pack(side="left")
        spin(r1, self.max_out_var, 2, 4).pack(side="left", padx=(2, 16))
        ttk.Label(r1, text="Densidad:").pack(side="left")
        ttk.Combobox(r1, textvariable=self.density_var, values=["Baja", "Media", "Alta"],
                     width=7, state="readonly").pack(side="left", padx=2)

        r2 = ttk.Frame(self.options_bar)
        r2.pack(fill="x", pady=1)
        ttk.Checkbutton(r2, text="Forzar empate entre caminos óptimos",
                        variable=self.force_tie_var).pack(side="left", padx=(0, 16))
        ttk.Label(r2, text="Caminos alternativos (mín.):").pack(side="left")
        spin(r2, self.min_paths_var, 1, 20).pack(side="left", padx=(2, 16))
        ttk.Label(r2, text="Peso mín.:").pack(side="left")
        spin(r2, self.w_min_var, 1, 99).pack(side="left", padx=(2, 8))
        ttk.Label(r2, text="máx.:").pack(side="left")
        spin(r2, self.w_max_var, 1, 99).pack(side="left", padx=2)

    def _build_main_area(self):
        area = ttk.Frame(self.root)
        area.pack(side="top", fill="both", expand=True)

        self.right = ttk.Frame(area, width=380, padding=6)
        self.right.pack(side="right", fill="y")
        self.right.pack_propagate(False)

        left = ttk.Frame(area)
        left.pack(side="left", fill="both", expand=True)

        zoom_bar = ttk.Frame(left, padding=(4, 2))
        zoom_bar.pack(side="top", fill="x")

        ttk.Button(zoom_bar, text="🔍+ Acercar", width=12,
                   command=lambda: self.visualizer.zoom_in()).pack(side="left", padx=2)
        ttk.Button(zoom_bar, text="🔍- Alejar", width=12,
                   command=lambda: self.visualizer.zoom_out()).pack(side="left", padx=2)
        ttk.Button(zoom_bar, text="↺ Restablecer", width=13,
                   command=lambda: self.visualizer.reset_zoom()).pack(side="left", padx=2)
        self.hint_label = ttk.Label(zoom_bar, font=("TkDefaultFont", 8))
        self.hint_label.pack(side="left", padx=8)
        self.draw_buttons = ttk.Frame(zoom_bar)
        ttk.Button(self.draw_buttons, text="Acomodar en capas",
                   command=self.on_auto_layout).pack(side="left", padx=2)
        ttk.Button(self.draw_buttons, text="Limpiar lienzo",
                   command=self._new_canvas).pack(side="left", padx=2)

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

        tree_font = tkfont.Font(family="TkDefaultFont", size=8)
        style = ttk.Style()
        style.configure("Dijkstra.Treeview", font=tree_font,
                         rowheight=tree_font.metrics("linespace") + 5)
        style.configure("Dijkstra.Treeview.Heading", font=(tree_font.actual("family"), 8, "bold"))

        dist_frame = ttk.LabelFrame(self.info_frame, text="Tabla de distancias", padding=4)
        dist_frame.pack(fill="both", expand=False, pady=(0, 6))
        cols = ("nodo", "dist", "vis", "pred")
        self.tree = ttk.Treeview(dist_frame, columns=cols, show="headings", height=10,
                                  style="Dijkstra.Treeview")
        for c, txt, w in zip(cols, ["Nodo", "Distancia", "Visitado", "Predecesor(es)"],
                              [46, 74, 66, 140]):
            self.tree.heading(c, text=txt)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("current", background="#ffe0b2")

        msg_frame = ttk.LabelFrame(self.info_frame, text="Mensaje del paso actual", padding=4)
        msg_frame.pack(fill="both", expand=False, pady=(0, 6))
        self.msg_text = tk.Text(msg_frame, height=4, wrap="word", state="disabled",
                                font=("TkDefaultFont", 9), padx=4, pady=4)
        self.msg_text.pack(fill="both", expand=True)

        result_frame = ttk.LabelFrame(self.info_frame, text="Resultados finales", padding=4)
        result_frame.pack(fill="both", expand=True)

        self.path_selector_var = tk.StringVar(value="Todos")
        self.path_selector = ttk.Combobox(result_frame, textvariable=self.path_selector_var,
                                           state="readonly", values=["Todos"])
        self.path_selector.pack(fill="x", side="bottom", pady=(4, 0))
        self.path_selector.bind("<<ComboboxSelected>>", lambda e: self.render_current())

        self.result_text = tk.Text(result_frame, height=8, wrap="word", state="disabled",
                                   font=("TkDefaultFont", 9), padx=4, pady=4)
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

    # ------------------------------------------------------------ modos
    def _on_n_changed(self):
        if self.mode_var.get() != "draw":
            self._refresh_combos(LABELS[:self._read_n()])
            self._update_run_state()

    def _read_n(self):
        try:
            return max(2, min(MAX_NODES, int(self.n_var.get())))
        except (tk.TclError, ValueError):
            return 7

    def _on_mode_change(self):
        mode = self.mode_var.get()
        self.gen_btn.config(text={"random": "Generar grafo", "manual": "Crear grafo",
                                  "draw": "Nuevo lienzo"}[mode])
        if mode == "random":
            self.options_bar.pack(side="top", fill="x", padx=6, after=self.top_bar)
        else:
            self.options_bar.pack_forget()
        if mode != "manual":
            self.show_manual_panel(False)

        drawing = mode == "draw"
        self.visualizer.set_edit_mode(drawing, {
            "empty_click": self._on_canvas_click,
            "edge_drawn": self._on_edge_drawn,
            "delete_node": self._on_delete_node,
            "delete_edge": self._on_delete_edge,
        } if drawing else None)
        if drawing:
            self.hint_label.config(text="Clic: nodo • Nodo→nodo: arista • "
                                        "Shift+arrastrar: mover • Clic der.: borrar")
            self.draw_buttons.pack(side="right")
            if not self.graph.edges():
                self._new_canvas()
            else:
                self._refresh_combos(self.graph.labels)
        else:
            self.hint_label.config(text="(Rueda del ratón para zoom • Arrastra para mover)")
            self.draw_buttons.pack_forget()
            self._refresh_combos(LABELS[:self._read_n()])
        self._update_run_state()

    def _refresh_combos(self, labels):
        """Actualiza Origen/Destino; conserva la selección si sigue siendo válida."""
        src, dst = self.source_var.get(), self.target_var.get()
        for combo in (self.source_combo, self.target_combo):
            combo["values"] = labels
        if not labels:
            self.source_var.set("")
            self.target_var.set("")
            return
        self.source_var.set(src if src in labels else labels[0])
        self.target_var.set(dst if dst in labels and dst != self.source_var.get()
                            else labels[-1])

    def _update_run_state(self):
        if self.mode_var.get() == "draw":
            ready = self.graph.n >= 2 and bool(self.graph.edges())
        else:
            ready = self.graph_ready
        self.run_btn.config(state="normal" if ready else "disabled")

    def _set_message(self, text):
        self.msg_text.config(state="normal")
        self.msg_text.delete("1.0", "end")
        self.msg_text.insert("1.0", text)
        self.msg_text.config(state="disabled")

    # ------------------------------------------------------------ generación
    def on_generate(self):
        mode = self.mode_var.get()
        if mode == "draw":
            self._new_canvas()
            return
        try:
            n = int(self.n_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Error", f"n debe ser un entero entre 7 y {MAX_NODES}.")
            return
        if not (7 <= n <= MAX_NODES):
            messagebox.showerror("Error", f"n debe estar entre 7 y {MAX_NODES}.")
            return

        self.graph_ready = False
        self._reset_execution()

        if mode == "random":
            self._generate_random(n)
        else:
            self.graph = Graph(n)
            self.edge_from_combo["values"] = self.graph.labels
            self.edge_to_combo["values"] = self.graph.labels
            self.edge_list.delete(0, "end")
            self.show_manual_panel(True)
            self.visualizer.set_graph(self.graph)
            self.visualizer.render()
            self._update_run_state()

    def _generate_random(self, n):
        src_label, dst_label = self.source_var.get(), self.target_var.get()
        if src_label not in LABELS[:n] or dst_label not in LABELS[:n] or src_label == dst_label:
            messagebox.showerror("Error", "Elija un Origen y un Destino distintos.")
            return
        try:
            graph = generate_advanced_dag(
                n, LABELS.index(src_label), LABELS.index(dst_label),
                min_hops=int(self.min_hops_var.get()),
                density=self.density_var.get().lower(),
                max_out=int(self.max_out_var.get()),
                forbid_direct=self.forbid_direct_var.get(),
                force_tie=self.force_tie_var.get(),
                min_paths=int(self.min_paths_var.get()),
                w_min=int(self.w_min_var.get()),
                w_max=int(self.w_max_var.get()))
        except (tk.TclError, ValueError) as exc:
            messagebox.showerror("Parámetros no válidos", str(exc))
            return

        self.graph = graph
        self._finish_graph_setup()
        info = graph.info
        lines = [f"Grafo generado {src_label}→{dst_label}: mínimo {info['hops']} aristas entre ambos, "
                 f"{info['paths']} caminos posibles.",
                 f"Costo óptimo esperado d* = {info['optimal_cost']} "
                 f"({info['optimal_paths']} camino(s) óptimo(s))."]
        lines += info["warnings"]
        self._set_message("\n".join(lines))

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
        self.visualizer.set_graph(self.graph, reset_view=False)
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
        self.visualizer.set_graph(self.graph, reset_view=False)
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

    def _finish_graph_setup(self, source=None, target=None, positions=None):
        if positions is not None:
            self.visualizer.set_graph(self.graph, positions=positions)
        else:
            self.visualizer.set_graph(self.graph, layers=topological_layers(self.graph))
        self.visualizer.render()
        labels = self.graph.labels
        if source is not None and target is not None:
            self.source_var.set(labels[source])
            self.target_var.set(labels[target])
        self._refresh_combos(labels)
        self.graph_ready = True
        self._update_run_state()

    # ------------------------------------------------------------ modo dibujo
    def _new_canvas(self):
        self._reset_execution()
        self.graph = Graph(0)
        self.graph_ready = False
        self.visualizer.set_graph(self.graph, positions={})
        self.visualizer.render()
        self._refresh_combos([])
        self._update_run_state()
        self._set_message("Lienzo vacío: haga clic para crear nodos "
                          f"(hasta {self._read_n()}; cambie n para ampliar el límite).")

    def _after_edit(self):
        """Tras agregar/quitar nodos o aristas: invalida la ejecución y redibuja."""
        self._reset_execution()
        self.graph_ready = self.graph.n >= 2
        self._refresh_combos(self.graph.labels)
        self._update_run_state()
        self.visualizer.render()

    def _on_canvas_click(self, x, y):
        if self.graph.n >= min(self._read_n(), MAX_NODES):
            messagebox.showinfo("Límite de nodos",
                                f"Ya hay {self.graph.n} nodos (límite n). Aumente n para agregar más.")
            return
        idx = self.graph.add_node()
        self.visualizer.place_node(idx, x, y)
        self._after_edit()

    def _on_edge_drawn(self, u, v):
        a, b = self.graph.labels[u], self.graph.labels[v]
        if self.graph.has_edge(u, v):
            messagebox.showerror("Error", f"La arista {a}→{b} ya existe.")
            return
        if self.graph.creates_cycle(u, v):
            messagebox.showwarning("Ciclo detectado",
                                   f"No se puede agregar {a}→{b}: crearía un ciclo.\n"
                                   "El grafo debe seguir siendo un DAG.")
            return
        w = self._ask_weight(a, b)
        if w is None:
            return
        self.graph.add_edge(u, v, w)
        self._after_edit()

    def _on_delete_node(self, node):
        self.graph.remove_node(node)
        self.visualizer.drop_node(node)
        self._after_edit()

    def _on_delete_edge(self, u, v):
        self.graph.remove_edge(u, v)
        self._after_edit()

    def on_auto_layout(self):
        if self.graph.n < 2:
            return
        self.visualizer.set_graph(self.graph, layers=topological_layers(self.graph))
        self.visualizer.render()

    def _dialog_colors(self):
        if self.dark_mode:
            return {"bg": "#252526", "fg": "#e0e0e0", "entry": "#2d2d2d", "btn": "#3e3e42",
                    "err": "#ff6b6b"}
        return {"bg": "#f0f0f0", "fg": "#000000", "entry": "#ffffff", "btn": "#e1e1e1",
                "err": "#c62828"}

    def _ask_weight(self, a, b):
        """Diálogo propio (respeta el tema) para pedir el peso 1-99 de la arista a→b."""
        c = self._dialog_colors()
        dlg = tk.Toplevel(self.root)
        dlg.title("Peso de la arista")
        dlg.configure(bg=c["bg"])
        dlg.transient(self.root)
        dlg.resizable(False, False)
        result = {"value": None}

        tk.Label(dlg, text=f"Peso de {a} → {b}  (1 a 99):", bg=c["bg"], fg=c["fg"]).pack(
            padx=16, pady=(14, 6))
        var = tk.StringVar()
        entry = tk.Entry(dlg, textvariable=var, width=8, justify="center", bg=c["entry"],
                         fg=c["fg"], insertbackground=c["fg"], relief="flat",
                         highlightthickness=1, highlightbackground="#888888")
        entry.pack(padx=16)
        err = tk.Label(dlg, text="", bg=c["bg"], fg=c["err"], font=("TkDefaultFont", 8))
        err.pack(pady=(4, 0))

        def accept(event=None):
            text = var.get().strip()
            if text.isdigit() and 1 <= int(text) <= 99:
                result["value"] = int(text)
                dlg.destroy()
            else:
                err.config(text="Ingrese un entero entre 1 y 99.")

        row = tk.Frame(dlg, bg=c["bg"])
        row.pack(pady=(6, 12))
        for text, cmd in (("Aceptar", accept), ("Cancelar", dlg.destroy)):
            tk.Button(row, text=text, width=9, command=cmd, bg=c["btn"], fg=c["fg"],
                      activebackground=c["btn"], activeforeground=c["fg"],
                      relief="flat").pack(side="left", padx=4)
        dlg.bind("<Return>", accept)
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        dlg.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dlg.winfo_height()) // 3
        dlg.geometry(f"+{x}+{y}")
        dlg.grab_set()
        entry.focus_set()
        self.root.wait_window(dlg)
        return result["value"]

    # ------------------------------------------------------------ guardar / cargar
    def _examples_dir(self):
        folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ejemplos")
        return folder if os.path.isdir(folder) else os.path.dirname(os.path.abspath(__file__))

    def on_save(self):
        if self.graph.n < 2 or not self.graph.edges():
            messagebox.showinfo("Guardar", "No hay un grafo con aristas para guardar.")
            return
        path = filedialog.asksaveasfilename(
            title="Guardar grafo", defaultextension=".json", initialdir=self._examples_dir(),
            filetypes=[("Grafo JSON", "*.json")])
        if not path:
            return
        labels = self.graph.labels
        src = labels.index(self.source_var.get()) if self.source_var.get() in labels else None
        dst = labels.index(self.target_var.get()) if self.target_var.get() in labels else None
        try:
            save_graph(path, self.graph, src, dst, self.visualizer.pos)
        except OSError as exc:
            messagebox.showerror("Guardar", f"No se pudo guardar el archivo:\n{exc}")

    def on_load(self):
        path = filedialog.askopenfilename(
            title="Cargar grafo", initialdir=self._examples_dir(),
            filetypes=[("Grafo JSON", "*.json"), ("Todos", "*.*")])
        if not path:
            return
        try:
            graph, src, dst, positions = load_graph(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Cargar", f"No se pudo cargar el grafo:\n{exc}")
            return
        self._reset_execution()
        self.show_manual_panel(False)
        self.graph = graph
        if self.mode_var.get() != "draw":
            self.n_var.set(graph.n)
        self._finish_graph_setup(src, dst, positions)
        self._set_message(f"Grafo cargado: {os.path.basename(path)} "
                          f"({graph.n} nodos, {len(graph.edges())} aristas).")

    def on_run(self):
        src_label = self.source_var.get()
        dst_label = self.target_var.get()
        if not src_label or not dst_label:
            messagebox.showerror("Error", "Seleccione origen y destino.")
            return
        if src_label == dst_label:
            messagebox.showerror("Error", "Origen y destino deben ser distintos.")
            return

        if src_label not in self.graph.labels or dst_label not in self.graph.labels:
            messagebox.showerror("Error", "Origen/destino no pertenecen al grafo actual. "
                                          "Genere o cargue el grafo de nuevo.")
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
        path_colors = self.visualizer.get_path_colors()
        for i in shown_indices:
            color = path_colors[i % len(path_colors)]
            for a, b in zip(paths[i], paths[i][1:]):
                colors.setdefault((a, b), []).append(color)
        return colors

    def _legend_for_paths(self, shown_indices):
        if len(shown_indices) <= 1:
            return None
        path_colors = self.visualizer.get_path_colors()
        return [(f"Camino {i + 1}", path_colors[i % len(path_colors)]) for i in shown_indices]

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self._apply_theme()

    def _apply_theme(self):
        style = self.style
        if self.dark_mode:
            self.theme_btn.config(text="☀️ Modo Claro")
            bg_main = "#1e1e1e"
            bg_panel = "#252526"
            bg_input = "#2d2d2d"
            fg_text = "#e0e0e0"
            border_col = "#3c3c3c"

            try:
                style.theme_use("clam")
            except Exception:
                pass

            self.root.configure(bg=bg_main)

            # Estilos generales de frames y etiquetas
            style.configure(".", background=bg_main, foreground=fg_text)
            style.configure("TFrame", background=bg_main)
            style.configure("TLabelframe", background=bg_main, bordercolor=border_col,
                            darkcolor=bg_main, lightcolor=bg_main)
            style.configure("TLabelframe.Label", background=bg_main, foreground=fg_text)
            style.configure("TLabel", background=bg_main, foreground=fg_text)

            # Radiobutton: evitar recuadro blanco al pasar el mouse (hover/active/focus)
            style.configure("TRadiobutton", background=bg_main, foreground=fg_text,
                            indicatorbackground="#2d2d2d", indicatorcolor="#ffffff", focuscolor="")
            style.map("TRadiobutton",
                      background=[("active", bg_main), ("selected", bg_main), ("disabled", bg_main)],
                      foreground=[("active", "#ffffff"), ("disabled", "#6e6e6e")],
                      indicatorbackground=[("pressed", "#0d47a1"), ("selected", "#1976d2"),
                                           ("active", "#3e3e42"), ("disabled", "#252526"),
                                           ("!disabled", "#2d2d2d")],
                      indicatorcolor=[("selected", "#ffffff"), ("pressed", "#ffffff"),
                                      ("!disabled", "#2d2d2d")])

            # Checkbutton (opciones avanzadas): mismo tratamiento que el Radiobutton
            style.configure("TCheckbutton", background=bg_main, foreground=fg_text,
                            indicatorbackground="#2d2d2d", indicatorforeground="#ffffff",
                            indicatorcolor="#2d2d2d", focuscolor="")
            style.map("TCheckbutton",
                      background=[("active", bg_main), ("selected", bg_main), ("disabled", bg_main)],
                      foreground=[("active", "#ffffff"), ("disabled", "#6e6e6e")],
                      indicatorbackground=[("selected", "#1976d2"), ("active", "#3e3e42"),
                                           ("!disabled", "#2d2d2d")],
                      indicatorcolor=[("selected", "#1976d2"), ("active", "#3e3e42"),
                                      ("!disabled", "#2d2d2d")],
                      indicatorforeground=[("selected", "#ffffff"), ("!disabled", "#ffffff")])

            # Botones: hover limpio sin bordes blancos de relieve 3D ni foco punteado
            style.configure("TButton", background=bg_input, foreground="#ffffff",
                            bordercolor=border_col, darkcolor=bg_input, lightcolor=bg_input, focuscolor="")
            style.map("TButton",
                      background=[("pressed", "#0d47a1"), ("active", "#3e3e42"),
                                  ("disabled", "#252526"), ("!disabled", bg_input)],
                      foreground=[("disabled", "#6e6e6e"), ("!disabled", "#ffffff")],
                      bordercolor=[("pressed", "#0d47a1"), ("active", "#555555"),
                                   ("!disabled", border_col)],
                      darkcolor=[("pressed", "#0d47a1"), ("active", "#3e3e42"),
                                 ("!disabled", bg_input)],
                      lightcolor=[("pressed", "#0d47a1"), ("active", "#3e3e42"),
                                  ("!disabled", bg_input)])

            # Spinbox: flechas y campo oscuros
            style.configure("TSpinbox", fieldbackground=bg_input, background=bg_input,
                            foreground=fg_text, arrowcolor=fg_text, bordercolor=border_col,
                            darkcolor=bg_input, lightcolor=bg_input, focuscolor="")
            style.map("TSpinbox",
                      fieldbackground=[("focus", bg_input), ("active", "#383838"),
                                       ("disabled", "#252526"), ("!disabled", bg_input)],
                      background=[("active", "#3e3e42"), ("pressed", "#0d47a1"),
                                  ("disabled", "#252526"), ("!disabled", bg_input)],
                      foreground=[("disabled", "#6e6e6e"), ("active", "#ffffff"),
                                  ("!disabled", fg_text)],
                      arrowcolor=[("active", "#ffffff"), ("disabled", "#555555"),
                                  ("!disabled", fg_text)],
                      bordercolor=[("focus", "#007acc"), ("active", "#555555")])

            # Combobox: fondo oscuro al pasar el cursor y lista desplegable oscura
            style.configure("TCombobox", fieldbackground=bg_input, background=bg_input,
                            foreground=fg_text, arrowcolor=fg_text, bordercolor=border_col,
                            darkcolor=bg_input, lightcolor=bg_input, focuscolor="",
                            selectbackground="#0d47a1", selectforeground="#ffffff")
            style.map("TCombobox",
                      fieldbackground=[("readonly", "focus", bg_input),
                                       ("readonly", "active", "#383838"),
                                       ("readonly", bg_input),
                                       ("disabled", "#252526")],
                      background=[("active", "#3e3e42"), ("pressed", "#0d47a1"),
                                  ("disabled", "#252526"), ("!disabled", bg_input)],
                      foreground=[("readonly", "focus", "#ffffff"),
                                  ("readonly", "active", "#ffffff"),
                                  ("disabled", "#6e6e6e"),
                                  ("!disabled", fg_text)],
                      arrowcolor=[("active", "#ffffff"), ("disabled", "#555555"),
                                  ("!disabled", fg_text)],
                      bordercolor=[("focus", "#007acc"), ("active", "#555555")])
            self.root.option_add("*TCombobox*Listbox.background", bg_input)
            self.root.option_add("*TCombobox*Listbox.foreground", fg_text)
            self.root.option_add("*TCombobox*Listbox.selectBackground", "#0d47a1")
            self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

            # Entry
            style.configure("TEntry", fieldbackground=bg_input, background=bg_input,
                            foreground=fg_text, bordercolor=border_col,
                            darkcolor=bg_input, lightcolor=bg_input, focuscolor="",
                            insertcolor="#ffffff")
            style.map("TEntry",
                      fieldbackground=[("focus", bg_input), ("active", "#383838"),
                                       ("disabled", "#252526"), ("!disabled", bg_input)],
                      foreground=[("disabled", "#6e6e6e"), ("!disabled", fg_text)],
                      bordercolor=[("focus", "#007acc"), ("active", "#555555")])

            # Treeview y encabezados
            tree_font = tkfont.Font(family="TkDefaultFont", size=8)
            style.configure("Dijkstra.Treeview", background=bg_panel, foreground=fg_text,
                            fieldbackground=bg_panel, font=tree_font, bordercolor=border_col,
                            lightcolor=bg_panel, darkcolor=bg_panel,
                            rowheight=tree_font.metrics("linespace") + 5)
            style.configure("Dijkstra.Treeview.Heading", background="#333333", foreground="#ffffff",
                            bordercolor=border_col, lightcolor="#333333", darkcolor="#333333",
                            relief="flat", font=(tree_font.actual("family"), 8, "bold"))
            style.map("Dijkstra.Treeview.Heading",
                      background=[("active", "#444444"), ("pressed", "#2d2d2d")],
                      foreground=[("active", "#ffffff")])
            self.tree.tag_configure("current", background="#5c3d11", foreground="#ffffff")

            # Áreas de texto y lista de aristas
            self.msg_text.config(bg=bg_panel, fg=fg_text, insertbackground="#ffffff",
                                 highlightthickness=1, highlightbackground=border_col)
            self.result_text.config(bg=bg_panel, fg=fg_text, insertbackground="#ffffff",
                                   highlightthickness=1, highlightbackground=border_col)
            self.edge_list.config(bg=bg_panel, fg=fg_text, selectbackground="#0d47a1",
                                  selectforeground="#ffffff", highlightthickness=1, highlightbackground=border_col)
        else:
            self.theme_btn.config(text="🌙 Modo Oscuro")
            try:
                style.theme_use(self.initial_theme)
            except Exception:
                pass

            bg_light = "#f0f0f0"
            self.root.configure(bg=bg_light)
            style.configure(".", background=bg_light, foreground="#000000")
            style.configure("TFrame", background=bg_light)
            style.configure("TLabelframe", background=bg_light)
            style.configure("TLabelframe.Label", background=bg_light, foreground="#000000")
            style.configure("TLabel", background=bg_light, foreground="#000000")
            style.configure("TRadiobutton", background=bg_light, foreground="#000000")
            style.map("TRadiobutton",
                      background=[("active", bg_light)],
                      foreground=[("active", "#000000")],
                      indicatorbackground=[],
                      indicatorcolor=[])

            style.configure("TCheckbutton", background=bg_light, foreground="#000000")
            style.map("TCheckbutton", background=[("active", bg_light)],
                      foreground=[("active", "#000000")])

            style.configure("TSpinbox", fieldbackground="#ffffff", background="#ffffff",
                            foreground="#000000", arrowcolor="#000000")
            style.map("TSpinbox",
                      fieldbackground=[("disabled", "#f0f0f0")],
                      background=[("active", "#e0e0e0")],
                      arrowcolor=[],
                      bordercolor=[])

            style.configure("TCombobox", fieldbackground="#ffffff", background="#ffffff",
                            foreground="#000000", arrowcolor="#000000")
            style.map("TCombobox",
                      fieldbackground=[("readonly", "#ffffff"), ("disabled", "#f0f0f0")],
                      background=[("active", "#e0e0e0")],
                      foreground=[],
                      arrowcolor=[],
                      bordercolor=[])

            style.configure("TEntry", fieldbackground="#ffffff", background="#ffffff", foreground="#000000")
            style.map("TEntry",
                      fieldbackground=[("disabled", "#f0f0f0")],
                      foreground=[("disabled", "#a0a0a0")],
                      bordercolor=[])

            style.configure("TButton", background="#e1e1e1", foreground="#000000")
            style.map("TButton",
                      background=[("active", "#ececec"), ("disabled", "#f4f4f4")],
                      foreground=[("disabled", "#a0a0a0")],
                      bordercolor=[],
                      darkcolor=[],
                      lightcolor=[])

            self.root.option_add("*TCombobox*Listbox.background", "#ffffff")
            self.root.option_add("*TCombobox*Listbox.foreground", "#000000")
            self.root.option_add("*TCombobox*Listbox.selectBackground", "#0078d7")
            self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

            tree_font = tkfont.Font(family="TkDefaultFont", size=8)
            style.configure("Dijkstra.Treeview", background="#ffffff", foreground="#000000",
                            fieldbackground="#ffffff", font=tree_font,
                            rowheight=tree_font.metrics("linespace") + 5)
            style.configure("Dijkstra.Treeview.Heading", background="#e1e1e1", foreground="#000000",
                            font=(tree_font.actual("family"), 8, "bold"))
            style.map("Dijkstra.Treeview.Heading",
                      background=[("active", "#d0d0d0")],
                      foreground=[("active", "#000000")])
            self.tree.tag_configure("current", background="#ffe0b2", foreground="#000000")

            self.msg_text.config(bg="#ffffff", fg="#000000", insertbackground="#000000",
                                 highlightthickness=1, highlightbackground="#cccccc")
            self.result_text.config(bg="#ffffff", fg="#000000", insertbackground="#000000",
                                   highlightthickness=1, highlightbackground="#cccccc")
            self.edge_list.config(bg="#ffffff", fg="#000000", selectbackground="#0078d7",
                                  selectforeground="#ffffff", highlightthickness=1, highlightbackground="#cccccc")

        self.visualizer.set_dark_mode(self.dark_mode)
        if self.steps:
            self.render_current()
        else:
            self.visualizer.render()
