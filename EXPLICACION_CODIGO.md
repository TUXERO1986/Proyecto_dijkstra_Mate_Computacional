# Explicación del código — Visualizador de Dijkstra en DAGs (Grupo 4)

Documento para **entender y defender** el programa en la sustentación. Todo lo que aparece aquí está en el código de esta carpeta.

---

## 1. ¿Qué hace el programa?

Dado un **grafo dirigido acíclico (DAG) con pesos positivos**, un **origen** y un **destino**, calcula el **camino de costo mínimo** con el algoritmo de **Dijkstra** y lo muestra **paso a paso**: qué nodo se elige, qué arista se evalúa, cómo cambia la tabla `[d(v), p(v), k]` y, al final, **todos los caminos mínimos empatados**.

El grafo se puede obtener de tres maneras:

| Modo | Qué hace |
|---|---|
| **Aleatorio** | Genera un DAG respetando reglas configurables (lo que pidió el profe). |
| **Formulario** | Se agregan aristas con listas desplegables (Origen, Destino, Peso). |
| **Dibujo** | Se dibuja con el mouse sobre el lienzo (crear nodos, arrastrar aristas). |

Además: **Guardar / Cargar** el grafo en JSON, **zoom y desplazamiento**, y **Modo Claro / Oscuro**.

Ejecutar: `pip install -r requirements.txt` y luego `python main.py`.

---

## 2. Mapa de archivos (5 módulos)

```
main.py          → crea la ventana y arranca la app (13 líneas)
ui.py            → interfaz Tkinter: botones, modos, diálogos, tema claro/oscuro
graph_model.py   → clase Graph, orden topológico, generador aleatorio, JSON
dijkstra.py      → Dijkstra que registra cada paso + backtracking de caminos
visualizer.py    → dibujo con Matplotlib, zoom/pan y gestos del modo dibujo
tests/           → pruebas automáticas (no son parte de la app)
ejemplos/        → grafo_informe_8nodos.json (el caso del informe, carga en 1 s)
```

Flujo de datos:

```
ui.py ──(parámetros)──► graph_model.generate_advanced_dag() ──► Graph
  │                                  ▲
  │ (mouse) visualizer.py ──callbacks┘  (agregar nodo/arista/borrar)
  ▼
dijkstra.run_dijkstra(Graph, origen, destino) ──► lista de Step
  │
  ▼
ui.render_current() muestra el Step actual: tabla + mensaje + visualizer.render()
al llegar al último paso: dijkstra.all_min_paths() ──► caminos mínimos
```

Idea clave de diseño: **Dijkstra se ejecuta completo una sola vez y guarda una "foto" (`Step`) de cada paso.** Los botones ◀ ▶ solo se mueven por esa lista, por eso ir hacia atrás es gratis.

---

## 3. `graph_model.py` — el grafo y el generador

### 3.1 Clase `Graph`
- Lista de adyacencia: `adj[u] = [(v, peso), ...]`. Nodos numerados `0..n-1`; las etiquetas `A, B, C…` salen de la posición (`labels` es una propiedad).
- `creates_cycle(u, v)`: **antes de agregar u→v** hace una búsqueda en profundidad desde `v`; si llega a `u`, la arista cerraría un ciclo. Así el grafo nunca deja de ser DAG. Costo O(V+E).
- `add_node()` / `remove_node()`: para el modo dibujo. Al borrar un nodo se **renumera** el resto para que las letras sigan siendo A, B, C… sin huecos.

### 3.2 Orden topológico y capas
- `topological_order`: algoritmo de Kahn (grados de entrada). Si no procesa los `n` nodos, hay ciclo.
- `topological_layers`: profundidad de cada nodo = camino más largo hasta él. Se usa para **ubicar los nodos en columnas** (izquierda → derecha).

### 3.3 `generate_advanced_dag(...)` — la parte del profe
El profe dijo: *"en la vida real un nodo no se conecta con muchos, sino con 1, 2 o 3 cercanos; entre origen y destino no deben existir caminos de longitud 1, 2 o 3 sino de 4; predefinan origen y destino y el resto sea aleatorio"*. Se implementó así:

1. **Origen y destino se eligen antes** y se respetan.
2. **Capas**: el origen va solo en la capa 0, el destino solo en la última; los demás nodos se reparten al azar en capas intermedias (la cantidad de capas es ≥ `min_hops`−1).
3. **Conectividad garantizada**: cada nodo recibe al menos una arista de la capa anterior y emite al menos una hacia la siguiente → *todo nodo está en algún camino origen→destino*.
4. **Grado de salida máximo** (`max_out`, por defecto 3): ningún nodo supera ese número de aristas salientes (grafo disperso, "real").
5. **Densidad** (Baja/Media/Alta): probabilidad de aristas extra entre capas consecutivas y de "atajos" que saltan una capa.
6. **Regla de saltos mínimos**: tras construir, se mide con **BFS** la menor cantidad de aristas origen→destino. Mientras sea menor que `min_hops`, se **elimina un atajo** del camino más corto. Como los caminos que solo usan aristas entre capas consecutivas ya tienen ≥ `min_hops` aristas, siempre termina. Resultado: **no existe ningún camino de 1, 2 o 3 aristas** (con `min_hops=4`).
7. **Prohibir arista directa**: equivale a exigir `min_hops ≥ 2`.
8. **Caminos alternativos (mín.)**: si hay menos caminos distintos que los pedidos, se agregan aristas (respetando `max_out` y la regla de saltos). Los caminos se cuentan por **programación dinámica** sobre el orden topológico.
9. **Forzar empate** (`_force_tie`), el aporte propio:
   - Se calcula `d(s,u)` (costo mínimo desde el origen) y `d(v,t)` (hasta el destino) para todos los nodos.
   - La **holgura** de una arista (u,v,w) es `d(s,u) + w + d(v,t) − d*`: cuánto más cara que el óptimo es la mejor ruta que pasa por ella.
   - Se elige una arista con holgura positiva mínima y se le **baja el peso en exactamente su holgura**. Entonces la mejor ruta por esa arista cuesta justo `d*`.
   - **Por qué es correcto:** en un DAG, `d(s,u)` y `d(v,t)` no dependen de la arista (u,v), así que cambiar su peso no altera ninguna otra ruta. El óptimo global sigue siendo `d*` y ahora hay ≥ 2 caminos con ese costo (la arista tenía holgura > 0, por lo que el camino nuevo es distinto de los óptimos anteriores).
10. El grafo trae `graph.info` (saltos mínimos, nº de caminos, costo óptimo esperado, nº de caminos óptimos) que la UI muestra al generar.

### 3.4 JSON
`save_graph` / `load_graph` guardan `n`, aristas (`desde`, `hasta`, `peso`), `origen`, `destino` y `posiciones` (para que el dibujo quede igual). Al cargar se **valida**: formato, pesos 1–99, sin aristas repetidas y **sin ciclos** (si hay ciclo, se rechaza el archivo).

---

## 4. `dijkstra.py` — el algoritmo

### 4.1 `run_dijkstra(graph, origen, destino, etiquetas)`
Dijkstra clásico con **cola de prioridad** (`heapq`, un min-heap):

```
dist[origen]=0, resto=∞;  cola = [(0, origen)]
mientras haya cola:
    (d0, u) = sacar el menor;  si u ya visitado → ignorar
    marcar u visitado                                  → paso "select"
    para cada arista u→v con peso w:
        nd = d0 + w
        si nd <  dist[v]: dist[v]=nd; preds[v]=[u]; push → paso "relax"
        si nd == dist[v]: agregar u a preds[v]            → paso "tie"   ← empate
        si nd >  dist[v]: no hace nada                    → paso "skip"
```
- **Predecesores múltiples:** en lugar de guardar un solo `p(v)`, guarda una **lista**. Cuando aparece un empate (`nd == dist[v]`) se *añade* el predecesor en vez de ignorarlo. Esto permite recuperar **todos** los caminos mínimos.
- Se usa *lazy deletion*: no se actualiza una entrada del heap, se agrega otra y se descartan las viejas al sacarlas (`if u in visited: continue`).
- Cada `Step` guarda copias de `dist`, `visited`, la cola (`frontier`) y `preds`, más un mensaje en español explicando el paso.

### 4.2 `all_min_paths(preds, origen, destino, dist)`
**Backtracking** desde el destino: por cada predecesor del nodo actual se recurre hacia atrás hasta llegar al origen; cada llegada es un camino mínimo. Límite de 50 caminos (por seguridad) con aviso de truncado.

### 4.3 Complejidad
- Dijkstra con min-heap: **O((|V|+|E|) log |V|)**. Cada arista provoca a lo sumo un `push` (O(log V)) y cada nodo se procesa una vez.
- Nota honesta: guardar una copia de la tabla por paso cuesta O(V) por paso; eso es parte de la *visualización*, no del algoritmo.
- Es correcto porque **todos los pesos son positivos** (1–99). Con pesos negativos Dijkstra puede fallar.

---

## 5. `visualizer.py` — dibujo y mouse

- Usa **Matplotlib** incrustado en Tkinter (`FigureCanvasTkAgg`). Dibuja aristas como flechas con su peso, nodos como círculos y la distancia `d(v)` dentro del nodo.
- **Colores por estado:** naranja = nodo actual, azul = en la cola (frontera), gris = visitado, blanco = no alcanzado; arista verde = árbol de predecesores, naranja = arista evaluada; cada camino mínimo final usa un color distinto.
- **Zoom/Pan:** rueda del mouse, botones y arrastre. `_fit_limits` ajusta la ventana a la proporción del lienzo (antes se recortaba el eje vertical cuando el lienzo era bajo).
- **Temas:** `THEME_PALETTES` tiene la paleta clara y la oscura; `render` toma los colores de ahí.

### Gestos del modo Dibujo (el visualizador solo detecta; la UI modifica el grafo mediante *callbacks*)
| Gesto | Resultado |
|---|---|
| Clic en zona vacía (sin arrastrar) | Crea el siguiente nodo (A, B, C…) hasta el límite `n`. |
| Arrastrar de un nodo a otro | Dibuja una línea guía; al soltar sobre el destino → valida ciclo → pide peso → crea la arista. |
| Shift + arrastrar un nodo | Lo reubica. |
| Clic derecho sobre nodo o arista | Lo elimina. |
| Arrastrar en vacío / rueda | Desplaza / hace zoom. |

Detección: nodo = punto a distancia ≤ 1,15·radio del centro; arista = distancia punto-segmento ≤ 0,45·radio. Se distingue "clic" de "arrastre" con un umbral de 4 píxeles.

---

## 6. `ui.py` — la interfaz

- `App` arma tres barras: superior (n, modo, origen/destino, ejecutar, guardar/cargar, tema), **opciones del grafo aleatorio** (solo visible en modo Aleatorio) y navegación (⏮ ◀ ▶ Auto ▶ ⏭).
- `render_current()` toma el `Step` actual y actualiza: tabla de distancias, mensaje, grafo y, en el último paso, los caminos mínimos (con selector "Todos / Camino k").
- **Editar invalida la ejecución:** cualquier cambio de nodos/aristas llama a `_reset_execution()` para que nunca se muestren pasos de un grafo distinto. (Mover un nodo no la invalida: solo cambia la posición).
- **Peso de arista:** diálogo propio (`_ask_weight`) en vez de `simpledialog`, para que respete el modo oscuro. Valida 1–99.
- **Modo oscuro:** `_apply_theme` reconfigura estilos `ttk` (tema `clam`) y los widgets `tk` (Text, Listbox) y le avisa al visualizador. Se corrigieron los bordes blancos de la tabla y se estilizó el nuevo `Checkbutton`.

---

## 7. Pruebas (`tests/`)
Ejecutar desde esta carpeta: `python -m unittest tests.test_modelo tests.test_ui_smoke`
- Generador: miles de combinaciones de parámetros verifican DAG, saltos mínimos, grado máximo, rango de pesos y que **todo nodo esté en un camino origen→destino**.
- Empate forzado: se compara contra **fuerza bruta** (enumerar todos los caminos).
- Dijkstra vs fuerza bruta en 150 grafos (distancia y cantidad de caminos óptimos).
- Interfaz: eventos de mouse simulados (crear nodos, aristas, ciclo rechazado, mover, borrar), guardar/cargar y cambio de tema.

---

