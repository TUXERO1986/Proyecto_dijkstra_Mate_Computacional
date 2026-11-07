import os, sys, json
sys.path.insert(0, r"C:\Users\pc\Desktop\Matematica compuitacional\programa\AWDADAWD")
import tkinter as tk
from PIL import ImageGrab
from types import SimpleNamespace
from unittest import mock
import ui
from ui import App

scene = sys.argv[1]
OUT = r"C:\Users\pc\Desktop\Matematica compuitacional\graficos"
EXAMPLE = r"C:\Users\pc\Desktop\Matematica compuitacional\programa\AWDADAWD\ejemplos\grafo_informe_8nodos.json"

root = tk.Tk()
app = App(root)
root.geometry("1180x720+20+20")
root.attributes("-topmost", True); root.lift(); root.focus_force()
vis = app.visualizer


def grab(name, crop=None):
    root.update()
    x, y, w, h = root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()
    box = (x, y, x + w, y + h) if crop is None else (x + crop[0], y + crop[1], x + crop[2], y + crop[3])
    ImageGrab.grab(box).save(os.path.join(OUT, name))
    root.destroy()


def ev(x, y, button=1):
    px, py = vis.ax.transData.transform((x, y))
    return SimpleNamespace(inaxes=vis.ax, xdata=x, ydata=y, x=px, y=py, button=button,
                           guiEvent=SimpleNamespace(state=0))


def load_example():
    with mock.patch.object(ui.filedialog, "askopenfilename", return_value=EXAMPLE):
        app.on_load()


def go():
    if scene == "random":
        app.n_var.set(8)
        app.source_var.set("A"); app.target_var.set("H")
        app.min_hops_var.set(4); app.max_out_var.set(3)
        app.force_tie_var.set(True)
        app.on_generate()
        root.after(900, lambda: grab("figura2_opciones_aleatorio.png", (0, 0, 1180, 430)))
        return

    if scene == "draw":
        app.mode_var.set("draw"); root.update()
        data = json.load(open(EXAMPLE, encoding="utf-8"))
        labels = "ABCDEFGH"
        pos = {k: v for k, v in data["posiciones"].items()}
        weights = {(e["desde"], e["hasta"]): e["peso"] for e in data["aristas"]}
        for L in labels:
            x, y = pos[L]
            vis._on_press(ev(x * 0.92, y * 0.92)); vis._on_release(ev(x * 0.92, y * 0.92))
        with mock.patch.object(app, "_ask_weight", side_effect=lambda a, b: weights[(a, b)]):
            idx = {L: i for i, L in enumerate(labels)}
            drawn = [("A", "B"), ("A", "C"), ("A", "D"), ("B", "E"), ("B", "C"), ("C", "F"), ("C", "E"),
                     ("D", "G"), ("D", "C"), ("E", "H")]
            for a, b in drawn:
                pa, pb = vis.pos[idx[a]], vis.pos[idx[b]]
                vis._on_press(ev(*pa)); vis._on_motion(ev(*pb)); vis._on_release(ev(*pb))
        # arista en curso: línea guía desde F hacia H (sin soltar)
        pf, ph = vis.pos[idx["F"]], vis.pos[idx["H"]]
        vis._on_press(ev(*pf))
        vis._on_motion(ev(pf[0] + (ph[0] - pf[0]) * 0.55, pf[1] + (ph[1] - pf[1]) * 0.55))
        app.target_var.set("H")
        root.after(700, lambda: grab("figura3_modo_dibujo.png"))
        return

    app.mode_var.set("draw"); root.update()
    load_example()
    if scene == "loaded":
        root.after(700, lambda: grab("figura4_grafo_inicial.png"))
        return
    app.on_run()
    if scene == "step":
        for i, s in enumerate(app.steps):
            if s.kind == "relax" and s.edge == (2, 5):
                app.step_index = i
                break
        app.render_current()
        root.after(700, lambda: grab("figura5_ejecucion_paso.png"))
    elif scene == "final":
        app.on_end()
        root.after(700, lambda: grab("figura7_resultados_finales.png"))


root.after(700, go)
root.mainloop()
