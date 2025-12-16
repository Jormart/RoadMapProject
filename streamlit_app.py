import streamlit as st
import os
import json
from graphviz import Digraph
from io import StringIO
import tempfile
import zipfile
import importlib.util
from collections import defaultdict

# Importar analizadores finales sin ejecutar sus mains
spec_rm = importlib.util.spec_from_file_location("roadmap07", os.path.join(os.path.dirname(__file__), "RoadMap.07.py"))
roadmap07 = importlib.util.module_from_spec(spec_rm)
spec_rm.loader.exec_module(roadmap07)

spec_calls = importlib.util.spec_from_file_location("roadmapcalls05", os.path.join(os.path.dirname(__file__), "RoadMapCalls.05.py"))
roadmapcalls05 = importlib.util.module_from_spec(spec_calls)
spec_calls.loader.exec_module(roadmapcalls05)

st.set_page_config(page_title="COBOL RoadMap Analyzer", layout="wide")
st.title("COBOL RoadMap Analyzer")
st.caption("Visualiza jerarquía de párrafos/SQL y llamadas entre programas.")

mode = st.tabs(["Jerarquía de párrafos", "Llamadas entre programas"])

# --- Tab 1: Jerarquía de párrafos (RoadMap.07) ---
with mode[0]:
    st.markdown("Analiza la jerarquía de llamadas entre párrafos y las tablas DB2 utilizadas.")
    uploaded = st.file_uploader("Sube un archivo COBOL (.cob/.txt)", type=["cob", "txt"])
    col1, col2 = st.columns([2,1])
    with col1:
        parrafo_inicio = st.text_input("Párrafo inicial (opcional)", value="")
    with col2:
        analizar_sql = st.checkbox("Incluir tablas DB2", value=True)
    
    run_btn = st.button("Analizar jerarquía", type="primary") 

    def build_graph(diccionario, selects_por_parrafo, analizar_sql=False):
        dot = Digraph(comment='Llamadas COBOL', format='png', engine='dot')
        dot.attr(dpi='300', rankdir='LR', nodesep='0.6', ranksep='1.2', bgcolor='white')
        dot.attr('node', shape='box', style='filled', fillcolor='#E3F2FD', fontname='Helvetica', fontsize='11', fontcolor='black', color='black')

        visitados = set()
        niveles = {}
        contador = [1]
        orden_llamadas = {}

        def asignar_niveles(nodo, nivel=0):
            if nodo in visitados:
                return
            visitados.add(nodo)
            niveles[nodo] = nivel
            for hijo in diccionario.get(nodo, []):
                orden_llamadas[(nodo, hijo)] = contador[0]
                contador[0] += 1
                asignar_niveles(hijo, nivel + 1)

        nodo_raiz = '__START__'
        if nodo_raiz not in diccionario and diccionario:
            nodo_raiz = next(iter(diccionario))
        asignar_niveles(nodo_raiz)

        niveles_invertido = {}
        for nodo, nivel in niveles.items():
            niveles_invertido.setdefault(nivel, []).append(nodo)

        for nivel in sorted(niveles_invertido):
            with dot.subgraph() as s:
                s.attr(rank='same')
                for nodo in niveles_invertido[nivel]:
                    color = '#E3F2FD'  # azul muy claro
                    if analizar_sql and nodo in selects_por_parrafo:
                        color = '#C8E6C9'  # verde muy claro
                    s.node(nodo, style='filled', fillcolor=color, fontcolor='black', color='black')

        for (origen, destino), numero in orden_llamadas.items():
            dot.edge(origen, destino, color='blue', style='solid', arrowsize='0.5', label=str(numero))

        if analizar_sql:
            for parrafo, selects in selects_por_parrafo.items():
                for idx, sel in enumerate(selects):
                    nodo_select = f"{parrafo}_SQL_{idx+1}"
                    # Estilizar según tipo SQL
                    tipo = sel.split()[0].upper()
                    if tipo == 'SELECT' or 'OPEN' in tipo or 'FETCH' in tipo:
                        fill = '#9FC5E8'  # azul claro
                        shape = 'cylinder'
                        edge_color = '#3D85C6'
                    elif tipo in ('INSERT', 'UPDATE', 'DELETE'):
                        fill = '#F6B26B'  # naranja claro
                        shape = 'component'
                        edge_color = '#E69138'
                    else:
                        fill = '#FFD966'  # amarillo para otros (COMMIT/ROLLBACK/CLOSE)
                        shape = 'note'
                        edge_color = 'orange'
                    dot.node(nodo_select, label=sel, shape=shape, style='filled', fillcolor=fill, fontcolor='black')
                    dot.edge(parrafo, nodo_select, style='dashed', color=edge_color)

        return dot

    def build_tree_text(diccionario, selects_por_parrafo):
        buf = StringIO()
        roadmap07.imprimir_arbol_llamadas(diccionario, selects_por_parrafo, archivo=buf)
        return buf.getvalue()

    if run_btn and uploaded is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".cob") as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name
        try:
            pi = parrafo_inicio.strip() or None
            dicc, sql_blocks, selects = roadmap07.analizar_cobol(tmp_path, pi, analizar_sql)
            # Si se analiza SQL, computar frecuencias por párrafo y etiquetar con (xN)
            if analizar_sql and isinstance(selects, dict):
                from collections import Counter
                selects_counted = {}
                for k, v in selects.items():
                    cnt = Counter(v)
                    selects_counted[k] = [f"{stmt} (x{n})" for stmt, n in sorted(cnt.items())]
                selects = selects_counted
            # Deduplicar sentencias SQL por párrafo para reducir repeticiones visuales
            if analizar_sql and isinstance(selects, dict):
                selects = {k: sorted(list(set(v))) for k, v in selects.items()}

            st.subheader("Jerarquía (texto)")
            tree_text = build_tree_text(dicc, selects)
            st.code(tree_text, language="text")

            st.subheader("Diagrama de jerarquía")
            dot = build_graph(dicc, selects, analizar_sql)

            # Vista en pantalla con scroll horizontal
            st.graphviz_chart(dot.source, use_container_width=False)

            # Generar PNG para descarga
            try:
                png_data = dot.pipe(format='png')
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.download_button(
                        label="📥 Descargar PNG",
                        data=png_data,
                        file_name="jerarquia_parrafos.png",
                        mime="image/png"
                    )
                with col_d2:
                    st.download_button(
                        label="📄 Descargar DOT",
                        data=dot.source,
                        file_name="jerarquia_parrafos.dot",
                        mime="text/vnd.graphviz"
                    )
            except Exception as e:
                st.warning(f"Descarga PNG no disponible en este entorno. Usa DOT y conviértelo localmente.")
                st.download_button(
                    label="📄 Descargar DOT",
                    data=dot.source,
                    file_name="jerarquia_parrafos.dot",
                    mime="text/vnd.graphviz"
                )

            if analizar_sql:
                st.info(f"Bloques EXEC SQL encontrados: {sql_blocks}")

        finally:
            os.unlink(tmp_path)

# --- Tab 2: Llamadas entre programas (RoadMapCalls.05) ---
with mode[1]:
    st.markdown("Analiza las llamadas a módulos externos (CALL y CICS LINK/START/INVOKE).")
    multi = st.file_uploader("Sube múltiples fuentes COBOL o un ZIP", type=["cob", "cbl", "cobol", "txt", "zip"], accept_multiple_files=True)
    prog_objetivo = st.text_input("Programa objetivo (opcional - 6 chars)", value="", placeholder="ej: ABC123")
    run_calls = st.button("Analizar llamadas", type="primary")

    def preparar_fuentes_archivos(files):
        temp_dir = tempfile.TemporaryDirectory()
        out_dir = temp_dir.name
        for f in files:
            if f.name.lower().endswith('.zip'):
                zip_path = os.path.join(out_dir, f.name)
                with open(zip_path, 'wb') as zf:
                    zf.write(f.getvalue())
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(out_dir)
            else:
                dest = os.path.join(out_dir, f.name)
                with open(dest, 'wb') as df:
                    df.write(f.getvalue())
        return out_dir, temp_dir

    def construir_grafo_directorio(llamadasdir, objetivo6):
        dot = Digraph(comment='Llamadas COBOL (directorio)', format='png', engine='dot')
        dot.attr(dpi='300', rankdir='LR', nodesep='0.8', ranksep='1.2', splines='ortho', bgcolor='white')
        dot.attr('node', shape='box', style='filled', fillcolor='#E3F2FD', fontname='Helvetica', fontsize='11', fontcolor='black', color='black')

        # nodo objetivo
        if objetivo6:
            dot.node(objetivo6, objetivo6, style='filled', fillcolor='#B4C7E7', shape='box', fontcolor='black', color='black')

        # llamantes (-> objetivo)
        for llamante, llamados in llamadasdir.items():
            for destino in set(llamados):
                if objetivo6 and (destino[:6] == objetivo6 or destino[:5] == objetivo6[:5]):
                    dot.node(llamante, llamante, style='filled', fillcolor='#A4C2F4', shape='component', fontcolor='black', color='black')
                    dot.edge(llamante, objetivo6, color='#3D85C6', arrowsize='0.7')

        # llamados (objetivo -> destino)
        if objetivo6 and objetivo6 in llamadasdir:
            for destino in set(llamadasdir[objetivo6]):
                color = '#A4C2F4'
                shape = 'component'
                if str(destino).startswith('CICS-'):
                    color = '#FFD966'
                    shape = 'cylinder'
                dot.node(destino, destino, style='filled', fillcolor=color, shape=shape, fontcolor='black', color='black')
                dot.edge(objetivo6, destino, color='#3D85C6', arrowsize='0.7')

        return dot

    if run_calls and multi:
        dir_path, tmp_dir_obj = preparar_fuentes_archivos(multi)
        try:
            archivos = roadmapcalls05.encontrar_archivos_cobol(dir_path)
            llamadasdir = defaultdict(list)

            for archivo in archivos:
                _ = roadmapcalls05.analizar_cobol(archivo)  # rellena llamadasdir interno, replicamos manualmente
                # Reaplicar lógica de analisis para acumular en nuestro llamadasdir
                origen = os.path.splitext(os.path.basename(archivo))[0].upper()[:6]
                with open(archivo, 'r', encoding='latin-1') as fh:
                    for linea in fh:
                        linea_u = linea.upper()
                        if roadmapcalls05.es_linea_ignorable(linea_u):
                            continue
                        destino = roadmapcalls05.detectar_call(linea_u)
                        if destino:
                            llamadasdir[origen].append(destino.upper())

            total = sum(len(v) for v in llamadasdir.values())
            st.metric("Llamadas detectadas", total)
            objetivo6 = (prog_objetivo or "").upper()[:6]
            dot_calls = construir_grafo_directorio(llamadasdir, objetivo6)
            st.subheader("Diagrama de llamadas")
            st.graphviz_chart(dot_calls.source, use_container_width=False)
            
            # Descargar PNG y DOT
            try:
                png_calls = dot_calls.pipe(format='png')
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.download_button(
                        label="📥 Descargar PNG",
                        data=png_calls,
                        file_name="grafo_llamadas.png",
                        mime="image/png"
                    )
                with col_c2:
                    st.download_button(
                        label="📄 Descargar DOT",
                        data=dot_calls.source,
                        file_name="grafo_llamadas.dot",
                        mime="text/vnd.graphviz"
                    )
            except Exception as e:
                st.warning("Descarga PNG no disponible. Usa DOT y conviértelo localmente.")
                st.download_button(
                    label="📄 Descargar DOT",
                    data=dot_calls.source,
                    file_name="grafo_llamadas.dot",
                    mime="text/vnd.graphviz"
                )

        finally:
            tmp_dir_obj.cleanup()


