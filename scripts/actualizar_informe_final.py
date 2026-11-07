"""Regenera el informe final (Word y PDF, 9 páginas) con las capturas reales.

Usa backups/_S15394_Grupo4_original.docx como plantilla (portada y membrete).
Requiere python-docx, pywin32, pypdf y Microsoft Word instalado.
"""
import os
import shutil
import win32com.client
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import pypdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if os.path.basename(os.path.dirname(os.path.abspath(__file__))).lower() == "matematica compuitacional" else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def add_page_number_to_section(section):
    """Add dynamic page number to section header."""
    header = section.header
    header.is_linked_to_previous = False
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run()
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11)
    
    # XML snippet for Word PAGE field
    fldSimple = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
    run._r.append(fldSimple)

def construir_informe_final():
    print("Construyendo el informe final (APA 7) con capturas reales del programa...")
    
    orig_path = os.path.join(BASE_DIR, "backups", "_S15394_Grupo4_original.docx")
    if not os.path.exists(orig_path):
        orig_path = os.path.join(BASE_DIR, "_S15394_Grupo4_original.docx")
    
    print(f"Cargando plantilla del usuario desde: {orig_path}")
    doc = Document(orig_path)

    # --------------------------------------------------------------------------
    # PÁGINA 1: PORTADA OFICIAL (Conservando membrete, integrantes y formato)
    # --------------------------------------------------------------------------
    doc.paragraphs[5].text = "TÍTULO: PROBLEMA DEL CAMINO MÍNIMO: IMPLEMENTACIÓN INTERACTIVA DEL ALGORITMO DE DIJKSTRA EN GRAFOS DIRIGIDOS ACÍCLICOS"
    doc.paragraphs[5].paragraph_format.space_before = Pt(8)
    doc.paragraphs[5].paragraph_format.space_after = Pt(14)
    doc.paragraphs[5].paragraph_format.line_spacing = 1.15
    for run in doc.paragraphs[5].runs:
        run.font.name = 'Calibri'
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)
    doc.paragraphs[6].text = ""

    doc.paragraphs[10].text = "PROFESOR"
    doc.paragraphs[11].text = "Antonio Marcos Medina Martínez"
    doc.paragraphs[12].text = "UPC, octubre de 2026"
    for idx in [10, 11, 12]:
        for r in doc.paragraphs[idx].runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(11)
            r.font.color.rgb = RGBColor(0, 0, 0)
        doc.paragraphs[idx].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Truncate broken TOC field codes and SDT elements after paragraph 14
    p14 = doc.paragraphs[14]._element
    body = doc._element.body
    idx_p14 = list(body).index(p14)
    for child in list(body)[idx_p14+1:]:
        if not child.tag.endswith('sectPr'):
            body.remove(child)

    doc.paragraphs[14].text = "Índice de contenido"
    doc.paragraphs[14].paragraph_format.space_before = Pt(12)
    doc.paragraphs[14].paragraph_format.space_after = Pt(10)
    doc.paragraphs[14].paragraph_format.line_spacing = 1.15
    for r in doc.paragraphs[14].runs:
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0, 0, 0)

    # Section 1 header: page numbering
    if len(doc.sections) > 1:
        add_page_number_to_section(doc.sections[1])

    # Helper functions
    def add_page_break():
        doc.add_page_break()

    def add_h1(text, space_before=5, space_after=2):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.line_spacing = 1.10
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_h2(text, space_before=4, space_after=2):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.line_spacing = 1.10
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_h3(text, space_before=3, space_after=1):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.line_spacing = 1.10
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_p(text, bold_prefix=None, italic_prefix=None, space_after=2.5):
        p = doc.add_paragraph()
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.08
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.first_line_indent = Inches(0.4)

        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = 'Times New Roman'
            r_pre.font.size = Pt(11)
            r_pre.font.bold = True
            r_pre.font.color.rgb = RGBColor(0, 0, 0)

        if italic_prefix:
            r_pre = p.add_run(italic_prefix)
            r_pre.font.name = 'Times New Roman'
            r_pre.font.size = Pt(11)
            r_pre.font.italic = True
            r_pre.font.color.rgb = RGBColor(0, 0, 0)

        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0, 0, 0)
        return p

    def add_fig_apa(fig_num, fig_title, img_path, note_text, width_inches=3.6, space_after=1.5):
        p_num = doc.add_paragraph()
        p_num.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_num.paragraph_format.space_before = Pt(1.5)
        p_num.paragraph_format.space_after = Pt(0.5)
        p_num.paragraph_format.keep_with_next = True
        r_num = p_num.add_run(f"Figura {fig_num}")
        r_num.font.name = 'Times New Roman'
        r_num.font.size = Pt(9.5)
        r_num.font.bold = True
        r_num.font.color.rgb = RGBColor(0, 0, 0)

        p_title = doc.add_paragraph()
        p_title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_title.paragraph_format.space_before = Pt(0)
        p_title.paragraph_format.space_after = Pt(1)
        p_title.paragraph_format.keep_with_next = True
        r_title = p_title.add_run(fig_title)
        r_title.font.name = 'Times New Roman'
        r_title.font.size = Pt(9.5)
        r_title.font.italic = True
        r_title.font.color.rgb = RGBColor(0, 0, 0)

        p_img = doc.add_paragraph()
        p_img.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(1)
        p_img.paragraph_format.space_after = Pt(1)
        p_img.paragraph_format.keep_with_next = True
        run_img = p_img.add_run()
        img_full_path = os.path.join(BASE_DIR, img_path) if not os.path.isabs(img_path) else img_path
        run_img.add_picture(img_full_path, width=Inches(width_inches))

        p_note = doc.add_paragraph()
        p_note.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_note.paragraph_format.line_spacing = 1.02
        p_note.paragraph_format.space_before = Pt(0.5)
        p_note.paragraph_format.space_after = Pt(space_after)
        
        r_note_lbl = p_note.add_run("Nota. ")
        r_note_lbl.font.name = 'Times New Roman'
        r_note_lbl.font.size = Pt(8.5)
        r_note_lbl.font.italic = True
        r_note_lbl.font.color.rgb = RGBColor(0, 0, 0)

        r_note_txt = p_note.add_run(note_text)
        r_note_txt.font.name = 'Times New Roman'
        r_note_txt.font.size = Pt(8.5)
        r_note_txt.font.color.rgb = RGBColor(0, 0, 0)

    def add_ref_apa_item(runs):
        p = doc.add_paragraph()
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.06
        p.paragraph_format.space_after = Pt(3.0)
        p.paragraph_format.left_indent = Inches(0.5)
        p.paragraph_format.first_line_indent = Inches(-0.5)
        for text, italic in runs:
            r = p.add_run(text)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(9.5)
            r.font.italic = italic
            r.font.color.rgb = RGBColor(0, 0, 0)

    # --------------------------------------------------------------------------
    # PÁGINA 2: ÍNDICE DE CONTENIDO
    # --------------------------------------------------------------------------
    toc_items = [
        ("Introducción", 3, False),
        ("Objetivo", 3, False),
        ("Metodología", 3, False),
        ("Algoritmo de Dijkstra y Grafos Dirigidos Acíclicos", 3, True),
        ("Generación de Grafos con Restricciones", 4, True),
        ("Desarrollo del código", 4, False),
        ("Librerías Utilizadas", 4, True),
        ("Descripción General del Programa", 5, True),
        ("Ingreso y Configuración del Grafo", 5, True),
        ("Modo de Dibujo Interactivo", 5, True),
        ("Búsqueda y Selección de Nodos", 5, True),
        ("Ejecución Interactiva del Algoritmo", 6, True),
        ("Diagrama de flujo del programa ejecutable", 6, True),
        ("Visualización de Resultados", 7, True),
        ("Programa", 7, False),
        ("Resultados", 7, False),
        ("Conclusiones", 8, False),
        ("Referencias Bibliográficas", 9, False)
    ]

    for title, page_num, is_sub in toc_items:
        p_item = doc.add_paragraph()
        p_item.paragraph_format.line_spacing = 1.05
        p_item.paragraph_format.space_after = Pt(2.5)
        indent_spaces = "    " if is_sub else ""
        left_text = indent_spaces + title + " "
        dots_len = max(4, 52 - len(left_text))
        dots = "." * dots_len
        full_line = f"{left_text}{dots} {page_num}"
        r_item = p_item.add_run(full_line)
        r_item.font.name = 'Times New Roman'
        r_item.font.size = Pt(10.5)
        if not is_sub:
            r_item.font.bold = True

    # --------------------------------------------------------------------------
    # PÁGINA 3: INTRODUCCIÓN, OBJETIVO, METODOLOGÍA (DIJKSTRA Y DAG)
    # --------------------------------------------------------------------------
    add_page_break()
    add_h1("Problema del camino mínimo: Algoritmo de Dijkstra")

    add_h2("Introducción")
    add_p("En el ámbito de la ingeniería y la computación, el estudio de redes y trayectorias mínimas es fundamental para resolver diversos problemas de la vida real, con amplias aplicaciones en cartografía digital, telecomunicaciones y optimización de recursos logísticos (Ahuja et al., 1993; Bondy & Murty, 2008). Desde la formulación inicial de la teoría de grafos por Leonard Euler en 1736 al resolver el célebre problema de los puentes de Königsberg, los modelos basados en redes permitieron formalizar problemas de conectividad e infraestructura. Encontrar el camino más corto permite optimizar tiempo, recursos y energía mediante procedimientos estructurados que facilitan el análisis computacional (Cormen et al., 2022). Por esta razón, el análisis de trayectorias mínimas es uno de los temas centrales de la matemática computacional.")

    add_p("El problema del camino mínimo consiste en encontrar, entre dos nodos de un grafo ponderado, una ruta cuya suma de pesos sea mínima (Ahuja et al., 1993). Al trabajar sobre un grafo dirigido acíclico, la red no contiene ciclos dirigidos, por lo que sus vértices pueden disponerse en un orden topológico en el que toda arista dirigida conecta un vértice anterior con uno posterior (Gross & Yellen, 2005; Kahn, 1962). En grafos con pesos no negativos, el algoritmo de Dijkstra construye las distancias mínimas de forma iterativa: selecciona el nodo no visitado con menor distancia tentativa y relaja sus aristas salientes (Cormen et al., 2022; Dijkstra, 1959). El presente informe expone el desarrollo del proyecto en cuatro componentes clave: marco metodológico, implementación en software y librerías, ejecución interactiva paso a paso con diagrama de flujo, y análisis de resultados con conclusiones.")

    add_h2("Objetivo")
    add_p("Desarrollar una aplicación en Python con una interfaz amigable e interactiva que permita al usuario participar en cada etapa de la ejecución del algoritmo de Dijkstra sobre grafos dirigidos acíclicos de n nodos, con n ∈ [7, 16], permitiendo generar el grafo de forma aleatoria con restricciones configurables, mediante un formulario de aristas o dibujándolo directamente sobre la pantalla, validando que no existan ciclos, mostrando el procedimiento paso a paso con su tabla de distancias y presentando al final la distancia mínima, la cantidad de caminos mínimos encontrados y la secuencia de nodos de cada uno resaltados en la pantalla gráfica.", bold_prefix="Objetivo General: ")

    add_h2("Metodología")
    add_h3("Algoritmo de Dijkstra y Grafos Dirigidos Acíclicos")
    add_p("Un grafo dirigido ponderado se representa mediante un conjunto de nodos V (donde la cantidad n está entre 7 y 16, identificados con letras desde la A hasta la P), un conjunto de aristas dirigidas E y un conjunto de pesos positivos w(u, v) mayores a cero asignados a cada conexión. Un grafo dirigido acíclico no contiene ciclos dirigidos; sus vértices pueden disponerse en un orden topológico en el que toda arista dirigida conecta un vértice anterior con uno posterior (Gross & Yellen, 2005; Kahn, 1962). Para la visualización, el programa agrupa los nodos en generaciones topológicas, de modo que los ancestros aparecen en generaciones anteriores y los descendientes en generaciones posteriores (NetworkX Developers, 2026a).")

    add_p("El algoritmo de Dijkstra funciona eligiendo en cada iteración el nodo que tenga la menor distancia acumulada provisional desde el origen, fijándolo como visitado o definitivo (Cormen et al., 2022). A continuación, revisa todos sus nodos vecinos salientes y aplica el proceso de relajación: si la distancia del nodo actual más el peso de la arista es menor que la distancia que tenía guardada el vecino, se actualiza con este nuevo valor más bajo y se guarda el nodo actual como su predecesor. Conforme a las pautas de la asignatura en la Lectura 5 de la UPC (Universidad Peruana de Ciencias Aplicadas, s. f.), cada nodo mantiene un seguimiento con su terna de etiquetado [dv, pv, k], donde dv representa la distancia acumulada, pv el vértice predecesor y k la iteración en que se consolidó la etiqueta permanente.")

    # --------------------------------------------------------------------------
    # PÁGINA 4: METODOLOGÍA (CONT.), GENERACIÓN, DESARROLLO DEL CÓDIGO, LIBRERÍAS, FIGURA 1
    # --------------------------------------------------------------------------
    add_page_break()
    add_p("En cada iteración se examinan las aristas salientes del nodo seleccionado. Si dist[u] + w(u, v) < dist[v], se actualizan la distancia tentativa de v y su predecesor; si ambos valores son iguales, el programa conserva todos los predecesores que conducen a una ruta mínima (Cormen et al., 2022; NetworkX Developers, 2026b). De esta manera, al terminar el algoritmo, una función de búsqueda hacia atrás (backtracking) recorre estos predecesores desde el destino hasta el origen para reconstruir todas las rutas mínimas posibles sin omitir ninguna solución, manteniendo una complejidad temporal de O((|V| + |E|) log |V|) gracias al uso de colas de prioridad (Sedgewick & Wayne, 2011; Skiena, 2020).")

    add_h3("Generación de Grafos con Restricciones")
    add_p("Para evitar grafos aleatorios triviales, el generador fija primero el origen y el destino y reparte los demás nodos en capas topológicas. Cada nodo recibe al menos una arista de la capa anterior y emite al menos una hacia la siguiente, y se limita a un máximo de tres aristas salientes por nodo, como ocurre en redes reales. Luego, una búsqueda en anchura (BFS) mide la menor cantidad de aristas entre origen y destino y se eliminan atajos hasta que no exista ningún camino de menos de k aristas (k = 4 por defecto). Opcionalmente se fuerza un empate: se calcula la holgura de cada arista, d(s, u) + w(u, v) + d(v, t) − d*, y se reduce el peso de una arista en esa holgura, de modo que aparezca un segundo camino de costo d* sin alterar el óptimo, pues en un DAG los costos d(s, u) y d(v, t) no dependen de dicha arista (Cormen et al., 2022).")

    add_h2("Desarrollo del código")
    add_h3("Librerías Utilizadas")
    add_p("Para la creación del programa se utilizaron las siguientes librerías de Python:")
    add_p("Tkinter y ttk se utilizaron para implementar la interfaz gráfica de escritorio, los diálogos y el guardado y carga de archivos (Python Software Foundation, 2026b).")
    add_p("Matplotlib se integró en la interfaz Tkinter para dibujar nodos, aristas, flechas y etiquetas de peso, y para detectar los gestos del mouse del modo de dibujo (Matplotlib Development Team, 2026).")
    add_p("Heapq proporcionó el min-heap empleado como cola de prioridad eficiente para extraer el elemento con menor valor tentativo (Python Software Foundation, 2026a).")
    add_p("NetworkX figura como dependencia del proyecto; el cálculo de generaciones topológicas con que se ubican los nodos por capas está implementado en graph_model.py bajo el mismo principio de la función topological_generations (NetworkX Developers, 2026a).")
    add_p("Json, Collections, Math, Random y String se usaron para guardar y cargar grafos, manejar colas de recorrido, representar el valor infinito, generar pesos aleatorios y nombrar los nodos con letras de la A a la P.")

    add_fig_apa(1, "Importaciones reales del código fuente del proyecto",
                "graficos/figura1_librerias.png",
                "Líneas de importación extraídas de los archivos del programa, con el módulo donde se encuentra cada una. Elaboración propia.",
                width_inches=3.9, space_after=1.5)

    # --------------------------------------------------------------------------
    # PÁGINA 5: DESCRIPCIÓN, INGRESO (FIGURA 2), DIBUJO (FIGURA 3), SELECCIÓN
    # --------------------------------------------------------------------------
    add_page_break()
    add_h3("Descripción General del Programa")
    add_p("La interfaz se organiza en una barra superior (n, modo de creación, origen, destino, ejecución, guardado y carga, y modo oscuro), un panel de opciones del grafo aleatorio, el lienzo del grafo a la izquierda y el panel de información a la derecha. El grafo puede obtenerse de tres formas: aleatoria con restricciones, mediante un formulario de aristas o dibujándolo con el mouse; además puede guardarse y cargarse en formato JSON.")

    add_h3("Ingreso y Configuración del Grafo")
    add_p("El usuario define «n» entre 7 y 16 nodos y elige el modo de creación. En el modo aleatorio selecciona el origen y el destino antes de generar y configura los saltos mínimos, el máximo de salidas por nodo, la densidad, la prohibición de la arista directa, el empate forzado, la cantidad mínima de caminos alternativos y el rango de pesos. En el modo de formulario se añaden aristas indicando origen, destino y peso; en ambos modos manuales, una búsqueda en profundidad (DFS) detecta si la nueva arista crearía un ciclo y, de ser así, la rechaza con una alerta (Cormen et al., 2022; Skiena, 2020).")

    add_fig_apa(2, "Modo aleatorio con restricciones configurables",
                "graficos/figura2_opciones_aleatorio.png",
                "Barra de opciones del generador y resumen del grafo creado (origen A, destino H, mínimo de 4 aristas, empate forzado). Elaboración propia.",
                width_inches=5.0, space_after=1)

    add_h3("Modo de Dibujo Interactivo")
    add_p("Un clic en una zona vacía crea el siguiente nodo (A, B, C…) y arrastrar de un nodo a otro traza una arista con una línea guía; al soltar, se verifica con DFS que no cierre un ciclo y se solicita el peso (1 a 99). Con Shift se reubican los nodos y con clic derecho se eliminan nodos o aristas.")

    add_fig_apa(3, "Dibujo interactivo del grafo con el mouse",
                "graficos/figura3_modo_dibujo.png",
                "Grafo de 8 nodos construido sobre el lienzo; la línea naranja discontinua es la arista F → H en trazado. Elaboración propia.",
                width_inches=3.3, space_after=1)

    add_h3("Búsqueda y Selección de Nodos")
    add_p("Una vez finalizado el grafo, o cargado desde un archivo JSON, las cajas de selección de la barra superior permiten escoger el nodo de origen A y de destino H para iniciar la ejecución del algoritmo.")

    # --------------------------------------------------------------------------
    # PÁGINA 6: EJECUCIÓN (FIGURA 4) Y DIAGRAMA DE FLUJO (FIGURA 5)
    # --------------------------------------------------------------------------
    add_page_break()
    add_h3("Ejecución Interactiva del Algoritmo")
    add_p("Al pulsar Ejecutar Dijkstra, se activan los controles de navegación. El usuario puede avanzar paso a paso observando el nodo actual en color naranja, los nodos en espera en azul claro y la tabla de distancias actualizándose.")

    add_fig_apa(4, "Ejecución interactiva paso a paso del algoritmo de Dijkstra",
                "graficos/figura5_ejecucion_paso.png",
                "Paso 13 de 23: se evalúa el nodo C (distancia acumulada 5) y se relaja su arista hacia F (peso 4), con lo que dist[F] = 9. Elaboración propia.",
                width_inches=4.2, space_after=1)

    add_h3("Diagrama de flujo del programa ejecutable")
    add_fig_apa(5, "Diagrama de flujo del sistema interactivo para el camino mínimo con Dijkstra",
                "graficos/figura6_diagrama_flujo.png",
                "El diagrama muestra la secuencia de operaciones del programa: elección del modo, validación de aciclicidad, guardado y carga, ejecución interactiva y presentación de todos los caminos mínimos. Elaboración propia.",
                width_inches=3.7, space_after=1)

    # --------------------------------------------------------------------------
    # PÁGINA 7: VISUALIZACIÓN DE RESULTADOS, FIGURA 6, PROGRAMA, RESULTADOS (INICIO)
    # --------------------------------------------------------------------------
    add_page_break()
    add_h3("Visualización de Resultados")
    add_p("Al llegar al paso final, el panel derecho muestra los resultados con la distancia mínima encontrada, la cantidad de caminos mínimos y la lista de nodos de cada recorrido. En el grafo, las rutas óptimas se resaltan con líneas gruesas de colores (rojo para el primer camino y azul para el segundo), acompañadas de su respectiva leyenda cuando existen varios caminos.")

    add_fig_apa(6, "Visualización de resultados finales y caminos mínimos resaltados",
                "graficos/figura7_resultados_finales.png",
                "Pantalla final del programa: distancia mínima de 13 entre A y H y los 2 caminos mínimos encontrados (A → B → E → H y A → C → F → H), resaltados con colores. Elaboración propia.",
                width_inches=5.0, space_after=2)

    add_h2("Programa")
    add_p("El proyecto se programó en Python mediante una estructura modular compuesta por cinco archivos: main.py para iniciar la aplicación, graph_model.py para la estructura del grafo, la validación de ciclos, el generador con restricciones y el guardado en JSON, dijkstra.py para la lógica del algoritmo y el registro de pasos, visualizer.py para el dibujo con Matplotlib y los gestos del mouse, y ui.py para el diseño visual de la interfaz y los modos claro y oscuro. La aplicación permite pausar la ejecución automática, avanzar o retroceder pasos y seleccionar si se desean ver todos los caminos juntos o uno por uno. El repositorio se encuentra disponible en: https://github.com/TUXERO1986/Proyecto_dijkstra_Mate_Computacional")

    add_h2("Resultados")
    add_p("Para comprobar el funcionamiento del programa, se realizaron pruebas experimentales sobre un banco de 10 instancias con tamaños de n = 7 a 16 nodos. En la prueba principal con 8 nodos (A hasta H), se configuró un grafo con 13 aristas y pesos entre 2 y 8. Al seleccionar A como origen y H como destino, el programa ejecutó 23 pasos de evaluación, encontrando que la distancia mínima es d* = 13. Además, identificó correctamente dos caminos mínimos distintos que empatan en costo: A → B → E → H (4 + 4 + 5 = 13) y A → C → F → H (5 + 4 + 4 = 13).")

    # --------------------------------------------------------------------------
    # PÁGINA 8: RESULTADOS (CONT.), CONCLUSIONES
    # --------------------------------------------------------------------------
    add_page_break()
    add_p("La ejecución paso a paso fue diseñada para apoyar la comprensión de la selección de nodos y la relajación de aristas. La literatura sobre visualización de algoritmos indica que estas herramientas pueden favorecer el aprendizaje cuando promueven una participación activa (Hundhausen et al., 2002). Durante las pruebas se comprobó que el entorno gráfico permite observar en qué momento se actualiza cada distancia y por qué se descartan otras opciones (como la ruta A → D → G → H, de costo 17); el algoritmo se resolvió en aproximadamente 0,07 ms por ejecución en Python 3.11, muy por debajo de 5 ms.")

    add_p("Para validar la exactitud, se resolvió a mano sobre papel un banco de 10 instancias (grafos de 7 a 16 nodos, generados de forma aleatoria y manual), anotando las ternas [dv, pv, k] y los predecesores paso a paso. Al compararlas con la salida del programa, los valores de distancia, los nodos visitados y los caminos mínimos finales coincidieron en un 100% de los casos. Además, las pruebas automáticas contrastaron Dijkstra con la enumeración exhaustiva de caminos en 150 grafos adicionales, con coincidencia total en distancia y cantidad de caminos óptimos.")

    add_p("Para validar el generador con restricciones se produjeron 1 000 grafos (n = 7 a 16, origen y destino aleatorios, mínimo de 4 aristas, máximo de 3 salidas por nodo y empate forzado). En el 100% de los casos el grafo fue acíclico, no existió ningún camino de menos de 4 aristas entre origen y destino, ningún nodo superó las 3 aristas salientes y se obtuvieron al menos dos caminos de costo mínimo idéntico; así, el generador evita los casos triviales señalados por el docente.")

    add_p("En la primera revisión se recomendó evitar grafos aleatorios triviales y facilitar el ingreso del grafo dibujado a mano. Lo primero se resolvió con las restricciones del modo aleatorio (origen y destino fijos, saltos mínimos, máximo de conexiones por nodo, densidad, arista directa prohibida, empate y caminos alternativos). Lo segundo, con el modo de dibujo interactivo (Figura 3) y el guardado y carga en JSON, que permite abrir en segundos el grafo del informe.", bold_prefix="Observaciones del docente atendidas. ")

    add_h2("Conclusiones")
    add_p("1. Cumplimiento del Objetivo: Se desarrolló una aplicación interactiva que permite crear (de forma aleatoria con restricciones, por formulario o dibujando) y analizar grafos dirigidos acíclicos de entre 7 y 16 nodos, aplicando el algoritmo de Dijkstra de forma visual y paso a paso, e incorporando las recomendaciones del docente.")

    add_p("2. Potencial Pedagógico: La interfaz con avance interactivo, tabla de distancias en tiempo real y mensajes descriptivos fue diseñada con potencial educativo; de acuerdo con Hundhausen et al. (2002), su valor formativo reside en propiciar una participación activa del usuario al explorar las decisiones del algoritmo.")

    add_p("3. Identificación de Múltiples Caminos: La inclusión de listas de predecesores y la búsqueda hacia atrás resolvieron los empates, identificando todos los caminos mínimos y resaltándolos con colores distintos; el generador puede, además, forzar estos empates para demostrarlo.")

    add_p("4. Integración Práctica: La combinación de Tkinter, Matplotlib y heapq demostró ser una solución eficiente para unir la teoría matemática con el desarrollo de software, creando un programa rápido, verificado con pruebas automáticas y fácil de usar para cualquier estudiante de ingeniería.")

    # --------------------------------------------------------------------------
    # PÁGINA 9: REFERENCIAS BIBLIOGRÁFICAS (APA 7)
    # --------------------------------------------------------------------------
    add_page_break()
    add_h2("Referencias Bibliográficas")
    
    apa_references = [
        [("Ahuja, R. K., Magnanti, T. L., & Orlin, J. B. (1993). ", False),
         ("Network flows: Theory, algorithms, and applications", True),
         (". Prentice Hall.", False)],
        
        [("Bondy, J. A., & Murty, U. S. R. (2008). ", False),
         ("Graph theory", True),
         (". Springer. https://doi.org/10.1007/978-1-84628-970-5", False)],
        
        [("Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). ", False),
         ("Introduction to algorithms", True),
         (" (4th ed.). The MIT Press.", False)],
        
        [("Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. ", False),
         ("Numerische Mathematik", True),
         (", ", False),
         ("1", True),
         (", 269–271. https://doi.org/10.1007/BF01386390", False)],
        
        [("Gross, J. L., & Yellen, J. (2005). ", False),
         ("Graph theory and its applications", True),
         (" (2nd ed.). Chapman & Hall/CRC. https://doi.org/10.1201/9781420057140", False)],
        
        [("Hundhausen, C. D., Douglas, S. A., & Stasko, J. T. (2002). A meta-study of algorithm visualization effectiveness. ", False),
         ("Journal of Visual Languages & Computing", True),
         (", ", False),
         ("13", True),
         ("(3), 259–290. https://doi.org/10.1006/jvlc.2002.0237", False)],
        
        [("Kahn, A. B. (1962). Topological sorting of large networks. ", False),
         ("Communications of the ACM", True),
         (", ", False),
         ("5", True),
         ("(11), 558–562. https://doi.org/10.1145/368996.369025", False)],
        
        [("Matplotlib Development Team. (2026). ", False),
         ("Embedding Matplotlib in graphical user interfaces", True),
         (" (Matplotlib 3.11.2 documentation). https://matplotlib.org/stable/gallery/user_interfaces/index.html", False)],
        
        [("NetworkX Developers. (2026a). ", False),
         ("Directed acyclic graphs", True),
         (" (NetworkX 3.7 documentation). https://networkx.org/documentation/stable/reference/algorithms/dag.html", False)],
        
        [("NetworkX Developers. (2026b). ", False),
         ("Shortest paths", True),
         (" (NetworkX 3.7 documentation). https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html", False)],
        
        [("Python Software Foundation. (2026a). ", False),
         ("heapq—Heap queue algorithm", True),
         (" (Python 3.14.8 documentation). https://docs.python.org/3/library/heapq.html", False)],
        
        [("Python Software Foundation. (2026b). ", False),
         ("tkinter—Python interface to Tcl/Tk", True),
         (" (Python 3.14.8 documentation). https://docs.python.org/3/library/tkinter.html", False)],
        
        [("Sedgewick, R., & Wayne, K. (2011). ", False),
         ("Algorithms", True),
         (" (4th ed.). Addison-Wesley Professional.", False)],
        
        [("Skiena, S. S. (2020). ", False),
         ("The algorithm design manual", True),
         (" (3rd ed.). Springer. https://doi.org/10.1007/978-3-030-54256-6", False)],
        
        [("Universidad Peruana de Ciencias Aplicadas. (s. f.). ", False),
         ("Lectura 5: Algoritmo de Dijkstra", True),
         (" [Material de curso]. Departamento de Ciencias. https://drive.google.com/file/d/1aLs_26jO-eGmSGPf6IsYw1_Q4HASBR6N/view", False)]
    ]

    for runs in apa_references:
        add_ref_apa_item(runs)

    # Save directly to _S15394_Grupo4.docx in project root
    out_docx = os.path.join(BASE_DIR, "_S15394_Grupo4.docx")
    doc.save(out_docx)
    print(f"Documento guardado con éxito: {out_docx}")

    # Mirror copy to Trabajo Mate Computacional.docx
    mirror_docx = os.path.join(BASE_DIR, "Trabajo Mate Computacional.docx")
    shutil.copyfile(out_docx, mirror_docx)
    print(f"Copia de respaldo actualizada: {mirror_docx}")

    # Convert to PDF via Word COM and verify page count
    print("Exportando a PDF con Word COM...")
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False

    out_pdf = os.path.join(BASE_DIR, "_S15394_Grupo4.pdf")
    doc_word = word.Documents.Open(os.path.abspath(out_docx))
    doc_word.ExportAsFixedFormat(os.path.abspath(out_pdf), 17) # 17 = wdExportFormatPDF
    doc_word.Close(False)
    print(f"PDF exportado con éxito: {out_pdf}")

    mirror_pdf = os.path.join(BASE_DIR, "Trabajo Mate Computacional.pdf")
    shutil.copyfile(out_pdf, mirror_pdf)

    word.Quit()

    reader = pypdf.PdfReader(out_pdf)
    num_pages = len(reader.pages)
    print(f"Número de páginas en {os.path.basename(out_pdf)}: {num_pages}")
    assert num_pages == 9, f"El documento debe tener exactamente 9 páginas, pero tiene {num_pages}."
    print("¡Verificación exitosa! El informe tiene estrictamente 9 páginas.")

if __name__ == '__main__':
    construir_informe_final()
