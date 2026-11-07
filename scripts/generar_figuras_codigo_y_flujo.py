"""Figura 1 (importaciones reales del código) y Figura 6 (diagrama de flujo actualizado).

Las capturas del programa en ejecución (figuras 2, 3, 4, 5 y 7) las toma
scripts/capturar_pantallas.py con la aplicación real.
"""
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "graficos")
SRC = os.path.join(BASE, "programa", "AWDADAWD")


# ------------------------------------------------------------------ Figura 1
def figura1():
    """Muestra las importaciones tal como están en los archivos del proyecto."""
    wanted = [
        ("ui.py", "import tkinter as tk", "Interfaz gráfica de escritorio"),
        ("ui.py", "from tkinter import filedialog, messagebox, ttk", "Widgets, diálogos y guardar/cargar"),
        ("visualizer.py", "from matplotlib.figure import Figure", "Lienzo para dibujar el grafo"),
        ("visualizer.py", "from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg",
         "Integración con Tkinter"),
        ("visualizer.py", "import matplotlib.patches as mpatches", "Nodos circulares y leyenda"),
        ("visualizer.py", "from matplotlib.lines import Line2D", "Línea guía al dibujar aristas"),
        ("dijkstra.py", "import heapq", "Cola de prioridad (min-heap) de Dijkstra"),
        ("graph_model.py", "import json", "Guardar y cargar grafos"),
        ("graph_model.py", "import math", "Valor infinito (∞)"),
        ("graph_model.py", "import random", "Grafos aleatorios con restricciones"),
        ("graph_model.py", "import string", "Etiquetas de nodos A..P"),
        ("graph_model.py", "from collections import deque", "Colas para BFS y orden topológico"),
        ("dijkstra.py", "from dataclasses import dataclass", "Registro estructurado de cada paso"),
    ]
    # verificación: cada línea debe existir realmente en su archivo
    for fname, line, _ in wanted:
        text = open(os.path.join(SRC, fname), encoding="utf-8").read()
        assert re.search(r"^" + re.escape(line) + r"$", text, re.M), f"{line} no está en {fname}"

    fig = plt.figure(figsize=(10, 5.4), dpi=200, facecolor="#1f1f2e")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(FancyBboxPatch((0.02, 0.9), 0.96, 0.08, boxstyle="round,pad=0,rounding_size=0.01",
                                fc="#2a2a3d", ec="#3d3d55"))
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        ax.add_patch(plt.Circle((0.05 + i * 0.025, 0.94), 0.011, color=c))
    ax.text(0.5, 0.94, "Proyecto Dijkstra - Importaciones reales (Python)", color="#c9d1ff",
            ha="center", va="center", fontsize=11, fontweight="bold")
    y = 0.84
    for fname, line, comment in wanted:
        ax.text(0.04, y, line, color="#f5d5f0", family="DejaVu Sans Mono", fontsize=7.6, va="center")
        ax.text(0.60, y, "# " + comment, color="#8fa0c8", family="DejaVu Sans Mono", fontsize=7.6, va="center")
        ax.text(0.97, y, fname, color="#6e7bbf", family="DejaVu Sans Mono", fontsize=6.5,
                va="center", ha="right")
        y -= 0.062
    fig.savefig(os.path.join(OUT, "figura1_librerias.png"), facecolor=fig.get_facecolor())
    plt.close(fig)


# ------------------------------------------------------------------ Figura 6
def figura6():
    fig = plt.figure(figsize=(5.6, 7.9), dpi=260, facecolor="#f8fafc")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    DARK = "#334155"

    def term(x, y, w, h, text, fc, ec):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.02",
                                    fc=fc, ec=ec, lw=1.6))
        ax.text(x, y, text, ha="center", va="center", fontsize=8.2, fontweight="bold",
                color="white" if fc in ("#16a34a", "#ef4444") else DARK)

    def proc(x, y, w, h, text, fc="#f1f5f9", ec="#64748b", bold=False):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.008",
                                    fc=fc, ec=ec, lw=1.5))
        ax.text(x, y, text, ha="center", va="center", fontsize=7.4, color="#1e293b",
                fontweight="bold" if bold else "normal", linespacing=1.3)

    def io(x, y, w, h, text, fc="#e0f2fe", ec="#0284c7"):
        s = h * 0.9
        ax.add_patch(Polygon([(x - w / 2 + s, y + h / 2), (x + w / 2, y + h / 2), (x + w / 2 - s, y - h / 2),
                              (x - w / 2, y - h / 2)], closed=True, fc=fc, ec=ec, lw=1.5))
        ax.text(x, y, text, ha="center", va="center", fontsize=7.4, fontweight="bold", color="#1e293b",
                linespacing=1.3)

    def dec(x, y, w, h, text, fc="#fef08a", ec="#ca8a04"):
        ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)], closed=True,
                             fc=fc, ec=ec, lw=1.6))
        ax.text(x, y, text, ha="center", va="center", fontsize=7.4, fontweight="bold", color="#1e293b")

    def line(pts, arrow=True, color=DARK, ls="-"):
        xs, ys = zip(*pts)
        ax.plot(xs[:-1] if arrow else xs, ys[:-1] if arrow else ys, color=color, lw=1.4, ls=ls,
                solid_capstyle="butt")
        if arrow:
            ax.annotate("", xy=pts[-1], xytext=pts[-2],
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.4, ls=ls, shrinkA=0, shrinkB=0))
            ax.plot([pts[-2][0], pts[-1][0]], [pts[-2][1], pts[-1][1]], color=color, lw=1.4, ls=ls)

    def label(x, y, t, color="#0f172a"):
        ax.text(x, y, t, fontsize=7.2, fontweight="bold", color=color, ha="center", va="center")

    L, R, C = 0.24, 0.76, 0.5
    term(C, 0.972, 0.34, 0.032, "INICIO (main.py)", "#16a34a", "#15803d")
    line([(C, 0.956), (C, 0.935)])
    io(C, 0.912, 0.78, 0.036, "Ingresar n ∈ [7, 16], elegir modo\ny origen / destino")
    line([(C, 0.894), (C, 0.868)])
    dec(C, 0.835, 0.36, 0.066, "¿Modo?")
    # ramas
    line([(C - 0.18, 0.835), (L, 0.835), (L, 0.76)])
    label(0.20, 0.851, "Aleatorio")
    line([(C + 0.18, 0.835), (R, 0.835), (R, 0.76)])
    label(0.80, 0.851, "Formulario / Dibujo")
    proc(L, 0.725, 0.42, 0.07,
         "generate_advanced_dag()\norigen/destino fijos, capas,\nsaltos mín., grado máx., empate")
    proc(R, 0.725, 0.42, 0.07,
         "Formulario: elegir u, v, w\nDibujo: clic = nodo;\narrastrar nodo → nodo = arista")
    line([(R, 0.69), (R, 0.655)])
    dec(R, 0.615, 0.36, 0.07, "¿Crea ciclo\nal agregar?", fc="#fee2e2", ec="#dc2626")
    label(R + 0.025, 0.565, "No")
    line([(R, 0.58), (R, 0.535)])
    proc(R, 0.51, 0.34, 0.05, "Agregar arista al DAG\n(peso 1 a 99)")
    # lazo de error
    line([(R + 0.18, 0.615), (0.975, 0.615), (0.975, 0.725), (R + 0.21, 0.725)], color="#dc2626", ls="--")
    label(0.905, 0.668, "Sí: rechazar", "#dc2626")
    # confluencia
    line([(L, 0.69), (L, 0.445)], arrow=False)
    line([(R, 0.485), (R, 0.445)], arrow=False)
    line([(L, 0.445), (R, 0.445)], arrow=False)
    line([(C, 0.445), (C, 0.418)])
    io(C, 0.397, 0.78, 0.036, "Guardar / Cargar grafo (JSON), opcional", fc="#ede9fe", ec="#7c3aed")
    line([(C, 0.379), (C, 0.358)])
    io(C, 0.337, 0.78, 0.036, "Seleccionar Origen (s) y Destino (t)")
    line([(C, 0.319), (C, 0.292)])
    proc(C, 0.268, 0.80, 0.058,
         "run_dijkstra(): lista de pasos\n(init, select, relax, tie, skip, done)\ncon copias de dist, visited y preds")
    line([(C, 0.245), (C, 0.215)])
    dec(C, 0.18, 0.36, 0.066, "¿Hay más\npasos?")
    label(C + 0.205, 0.195, "Sí")
    proc(0.835, 0.115, 0.30, 0.07,
         "Anterior / Siguiente / Auto:\ntabla [d, p, k], mensaje\ny colores")
    line([(C + 0.18, 0.18), (0.835, 0.18), (0.835, 0.15)])
    line([(0.685, 0.115), (C, 0.115), (C, 0.147)])  # vuelve a preguntar
    label(C - 0.205, 0.195, "Fin")
    line([(C - 0.18, 0.18), (0.18, 0.18), (0.18, 0.11)])
    proc(0.30, 0.085, 0.44, 0.046, "all_min_paths():\nbacktracking de caminos mínimos",
         fc="#ede9fe", ec="#7c3aed")
    line([(0.30, 0.062), (0.30, 0.04)])
    io(0.30, 0.022, 0.50, 0.034, "Mostrar y resaltar caminos", fc="#dcfce7", ec="#16a34a")
    term(0.80, 0.022, 0.2, 0.03, "FIN", "#ef4444", "#dc2626")
    line([(0.56, 0.022), (0.70, 0.022)])
    fig.savefig(os.path.join(OUT, "figura6_diagrama_flujo.png"), facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    figura1()
    figura6()
    print("figuras 1 y 6 generadas")
