"""Pruebas de humo de la interfaz: Tk real, eventos del ratón simulados y diálogos sustituidos."""
import os
import sys
import tempfile
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ui
from ui import App


class TestUI(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.geometry("1280x800+10+10")
        self.app = App(self.root)
        self.root.update()
        patcher = mock.patch.multiple(ui.messagebox, showinfo=mock.DEFAULT, showerror=mock.DEFAULT,
                                      showwarning=mock.DEFAULT, askyesno=mock.DEFAULT)
        self.msgs = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.root.destroy()

    # ---- ayudas de eventos
    def event(self, x, y, button=1, shift=False):
        vis = self.app.visualizer
        px, py = vis.ax.transData.transform((x, y))
        return SimpleNamespace(inaxes=vis.ax, xdata=x, ydata=y, x=px, y=py, button=button,
                               guiEvent=SimpleNamespace(state=1 if shift else 0))

    def click(self, x, y, button=1):
        vis = self.app.visualizer
        vis._on_press(self.event(x, y, button))
        vis._on_release(self.event(x, y, button))

    def drag(self, p0, p1, shift=False):
        vis = self.app.visualizer
        vis._on_press(self.event(*p0, shift=shift))
        vis._on_motion(self.event((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, shift=shift))
        vis._on_motion(self.event(*p1, shift=shift))
        vis._on_release(self.event(*p1, shift=shift))

    # ---- pruebas
    def test_aleatorio_con_empate_y_dos_modos(self):
        app = self.app
        app.force_tie_var.set(True)
        app.min_hops_var.set(4)
        app.source_var.set("C")
        app.target_var.set("H")
        app.on_generate()
        self.assertTrue(app.graph_ready)
        self.assertEqual(app.graph.info["source"], 2)
        app.on_run()
        app.on_end()
        self.assertIn("Cantidad de caminos mínimos", app.result_text.get("1.0", "end"))
        self.assertGreaterEqual(app.graph.info["optimal_paths"], 2)
        app.toggle_dark_mode()
        app.toggle_dark_mode()

    def test_dibujo_completo(self):
        app, vis = self.app, self.app.visualizer
        app.mode_var.set("draw")
        self.root.update()
        pts = [(-0.8, 0.0), (-0.2, 0.5), (0.4, -0.3), (0.9, 0.2)]
        for p in pts:
            self.click(*p)
        self.assertEqual(app.graph.n, 4)

        with mock.patch.object(app, "_ask_weight", side_effect=[3, 2, 9, 1]):
            self.drag(pts[0], pts[1])      # A→B
            self.drag(pts[1], pts[2])      # B→C
            self.drag(pts[0], pts[2])      # A→C
            self.drag(pts[2], pts[3])      # C→D
        self.assertEqual(sorted(app.graph.edges()), [(0, 1, 3), (0, 2, 9), (1, 2, 2), (2, 3, 1)])

        self.drag(pts[3], pts[0])          # D→A crearía ciclo
        self.assertTrue(self.msgs["showwarning"].called)
        self.assertEqual(len(app.graph.edges()), 4)

        app.source_var.set("A")
        app.target_var.set("D")
        app.on_run()
        app.on_end()
        self.assertEqual(app.steps[-1].dist[3], 6)

        # mover nodo con Shift no cambia el modelo pero sí la posición
        before = list(app.graph.edges())
        self.drag(pts[3], (0.7, 0.6), shift=True)
        self.assertEqual(before, app.graph.edges())
        self.assertAlmostEqual(vis.pos[3][1], 0.6, places=3)

        # borrar arista (clic derecho a mitad de A→C) y luego el nodo B
        (x1, y1), (x2, y2) = vis.pos[0], vis.pos[2]
        self.click((x1 + x2) / 2, (y1 + y2) / 2 - 0.0, button=3)
        self.assertFalse(app.graph.has_edge(0, 2))
        self.click(*vis.pos[1], button=3)
        self.assertEqual(app.graph.n, 3)
        self.assertEqual(app.graph.labels, ["A", "B", "C"])

        app.toggle_dark_mode()
        app.on_auto_layout()
        app.toggle_dark_mode()

    def test_limite_de_nodos(self):
        app = self.app
        app.mode_var.set("draw")
        app.n_var.set(7)
        for i in range(8):
            self.click(-0.9 + 0.25 * i, 0.0)
        self.assertEqual(app.graph.n, 7)
        self.assertTrue(self.msgs["showinfo"].called)

    def test_guardar_y_cargar(self):
        app = self.app
        app.on_generate()
        edges = sorted(app.graph.edges())
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "g.json")
            with mock.patch.object(ui.filedialog, "asksaveasfilename", return_value=path):
                app.on_save()
            app.n_var.set(8)
            app.on_generate()
            with mock.patch.object(ui.filedialog, "askopenfilename", return_value=path):
                app.on_load()
        self.assertEqual(sorted(app.graph.edges()), edges)
        self.assertEqual(str(app.run_btn.cget("state")), "normal")

    def test_modo_manual_sigue_funcionando(self):
        app = self.app
        app.mode_var.set("manual")
        app.on_generate()
        app.edge_from_var.set("A"); app.edge_to_var.set("B"); app.edge_w_var.set("4")
        app.on_add_edge()
        self.assertEqual(app.graph.edges(), [(0, 1, 4)])


if __name__ == "__main__":
    unittest.main()
