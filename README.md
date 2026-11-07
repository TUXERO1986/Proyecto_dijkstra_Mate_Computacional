# Visualizador de Dijkstra en DAGs — Grupo 4

Matemática Computacional (1AMA0726) — UPC. Camino mínimo con Dijkstra paso a paso sobre grafos dirigidos acíclicos.

## Ejecutar
```
pip install -r requirements.txt
python main.py
```
Requiere Python 3.10+ (Tkinter viene incluido en la instalación oficial de Python para Windows).

## Uso rápido
- **Aleatorio:** elija Origen/Destino y las opciones (saltos mínimos, máx. salidas, densidad, empate, caminos alternativos, rango de pesos) → *Generar grafo*.
- **Formulario:** *Crear grafo* → agregue aristas con las listas → *Finalizar grafo*.
- **Dibujo:** clic = nodo · arrastrar nodo→nodo = arista · Shift+arrastrar = mover · clic derecho = borrar.
- **Guardar / Cargar:** JSON; ejemplo listo en `ejemplos/grafo_informe_8nodos.json`.
- *Ejecutar Dijkstra* y navegue con ⏮ ◀ ▶ Auto ▶ ⏭. *Modo Oscuro* alterna el tema.

## Pruebas
```
python -m unittest tests.test_modelo tests.test_ui_smoke
```

La explicación completa del código está en [EXPLICACION_CODIGO.md](EXPLICACION_CODIGO.md).
