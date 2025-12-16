import streamlit as st
import os
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
    uploaded = st.file_uploader("Sube un archivo COBOL (.cob/.txt)", type=["cob", "txt"])
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        analizar_sql = st.checkbox("Analizar SQL (EXEC SQL)", value=False)
    with col2:
        parrafo_inicio = st.text_input("Párrafo inicial (opcional)", value="")
    with col3:
        run_btn = st.button("Analizar")

    colA, colB, colC = st.columns([1,1,1])
    with colA:
        rankdir_opt = st.selectbox("Orientación", options=["Vertical (TB)", "Horizontal (LR)"], index=0)
    with colB:
        nodesep = st.slider("Separación horizontal", min_value=0.2, max_value=2.0, value=0.6, step=0.1)
    with colC:
        ranksep = st.slider("Separación vertical", min_value=0.2, max_value=2.0, value=0.6, step=0.1)

    colF1, colF2 = st.columns([1,1])
    with colF1:
        max_depth = st.slider("Profundidad máxima (recursión)", min_value=1, max_value=20, value=10, step=1)
    with colF2:
        sql_types = st.multiselect("Tipos SQL a mostrar", options=["SELECT", "INSERT", "UPDATE", "DELETE", "OPEN CURSOR", "CLOSE CURSOR", "FETCH CURSOR", "COMMIT", "ROLLBACK"], default=["SELECT", "INSERT", "UPDATE", "DELETE", "OPEN CURSOR", "CLOSE CURSOR", "FETCH CURSOR"]) 

    def build_graph(diccionario, selects_por_parrafo, analizar_sql=False, rankdir='TB', nodesep_val=0.6, ranksep_val=0.6):
        dot = Digraph(comment='Llamadas COBOL', format='svg', engine='dot')
        dot.attr(dpi='150', rankdir=rankdir, nodesep=str(nodesep_val), ranksep=str(ranksep_val))
        dot.attr('node', shape='box', style='filled', fontname='Helvetica', fontsize='10')

        visitados = set()
        niveles = {}
        contador = [1]
        orden_llamadas = {}

        def asignar_niveles(nodo, nivel=0):
            if nodo in visitados:
                return
            visitados.add(nodo)
            niveles[nodo] = nivel
            if nivel >= max_depth:
                return
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
                    color = 'lightblue'
                    if analizar_sql and nodo in selects_por_parrafo:
                        color = 'lightgreen'
                    s.node(nodo, style='filled', fillcolor=color)

        for (origen, destino), numero in orden_llamadas.items():
            dot.edge(origen, destino, color='blue', style='solid', arrowsize='0.5', label=str(numero))

        if analizar_sql:
            for parrafo, selects in selects_por_parrafo.items():
                for idx, sel in enumerate(selects):
                    # Filtrar por tipo seleccionado
                    tipo_label = sel.split()[0]
                    if sql_types and tipo_label not in sql_types:
                        continue
                    nodo_select = f"{parrafo}_SQL_{idx+1}"
                    dot.node(nodo_select, label=sel, shape='note', style='filled', fillcolor='yellow')
                    dot.edge(parrafo, nodo_select, style='dashed', color='orange')

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

            st.subheader("Jerarquía de llamadas")
            tree_text = build_tree_text(dicc, selects)
            st.code(tree_text, language="text")

            st.subheader("Diagrama de llamadas")
            rd = 'TB' if rankdir_opt.startswith('Vertical') else 'LR'
            dot = build_graph(dicc, selects, analizar_sql, rankdir=rd, nodesep_val=nodesep, ranksep_val=ranksep)
            st.graphviz_chart(dot.source)

            # Render client-side with viz.js for zoom and PNG export
            import streamlit.components.v1 as components
            dot_src = dot.source.replace("`", "\\`")
            components.html(
                    f"""
                    <div id='viz_parrafos_container' style='border:1px solid #333; border-radius:8px; overflow:auto; max-height:600px;'>
                        <div id='viz_parrafos'></div>
                    </div>
                    <button id='dlpng_parrafos' style='margin-top:8px;'>Descargar PNG</button>
                    <script src='https://unpkg.com/viz.js@2.1.2/dist/viz.js'></script>
                    <script src='https://unpkg.com/viz.js@2.1.2/dist/lite.render.js'></script>
                    <script>
                        const dotSrc = `{dot_src}`;
                        const viz = new Viz();
                        viz.renderSVGElement(dotSrc).then(svg => {{
                            const cont = document.getElementById('viz_parrafos');
                            cont.innerHTML='';
                            cont.appendChild(svg);
                        }});
                        document.getElementById('dlpng_parrafos').onclick = async () => {{
                            const svgEl = document.querySelector('#viz_parrafos svg');
                            if(!svgEl) return;
                            const xml = new XMLSerializer().serializeToString(svgEl);
                            const svg64 = btoa(unescape(encodeURIComponent(xml)));
                            const image64 = 'data:image/svg+xml;base64,' + svg64;
                            const img = new Image();
                            img.onload = function(){{
                                const canvas = document.createElement('canvas');
                                canvas.width = img.width; canvas.height = img.height;
                                const ctx = canvas.getContext('2d');
                                ctx.drawImage(img, 0, 0);
                                const link = document.createElement('a');
                                link.download = 'jerarquia_parrafos.png';
                                link.href = canvas.toDataURL('image/png');
                                link.click();
                            }};
                            img.src = image64;
                        }};
                    </script>
                    """,
                    height=700,
                    scrolling=True
            )

            # En Streamlit Cloud, graphviz backend binarios pueden no estar disponibles.
            # Evitamos dot.pipe/render y ofrecemos descarga del DOT fuente.
            st.download_button(
                label="Descargar DOT",
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
    st.markdown("Analiza llamadas externas (CALL y CICS) a nivel de directorio.")
    prog_objetivo = st.text_input("Programa objetivo (primeros 6 chars)", value="")
    multi = st.file_uploader("Sube múltiples fuentes COBOL o un ZIP", type=["cob", "cbl", "cobol", "txt", "zip"], accept_multiple_files=True)
    run_calls = st.button("Analizar llamadas")

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
        dot = Digraph(comment='Llamadas COBOL (directorio)', format='svg', engine='dot')
        dot.attr(dpi='150', rankdir='TB', nodesep='0.5', ranksep='0.5', splines='ortho')
        dot.attr('node', shape='box', style='filled', fontname='Helvetica', fontsize='10')

        # nodo objetivo
        if objetivo6:
            dot.node(objetivo6, objetivo6, style='filled', fillcolor='#B4C7E7', shape='box')

        # llamantes (-> objetivo)
        for llamante, llamados in llamadasdir.items():
            for destino in set(llamados):
                if objetivo6 and (destino[:6] == objetivo6 or destino[:5] == objetivo6[:5]):
                    dot.node(llamante, llamante, style='filled', fillcolor='#A4C2F4', shape='component')
                    dot.edge(llamante, objetivo6, color='#3D85C6', arrowsize='0.7')

        # llamados (objetivo -> destino)
        if objetivo6 and objetivo6 in llamadasdir:
            for destino in set(llamadasdir[objetivo6]):
                color = '#A4C2F4'
                shape = 'component'
                if str(destino).startswith('CICS-'):
                    color = '#FFD966'
                    shape = 'cylinder'
                dot.node(destino, destino, style='filled', fillcolor=color, shape=shape)
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

            st.subheader("Resumen de llamadas detectadas")
            total = sum(len(v) for v in llamadasdir.values())
            st.write(f"Total de llamadas detectadas: {total}")
            objetivo6 = (prog_objetivo or "").upper()[:6]
            dot_calls = construir_grafo_directorio(llamadasdir, objetivo6)
            st.subheader("Grafo de llamadas (directorio)")
            st.graphviz_chart(dot_calls.source)

            import streamlit.components.v1 as components
            dot_calls_src = dot_calls.source.replace("`", "\\`")
            components.html(
                    f"""
                    <div id='viz_calls_container' style='border:1px solid #333; border-radius:8px; overflow:auto; max-height:600px;'>
                        <div id='viz_calls'></div>
                    </div>
                    <button id='dlpng_calls' style='margin-top:8px;'>Descargar PNG</button>
                    <script src='https://unpkg.com/viz.js@2.1.2/dist/viz.js'></script>
                    <script src='https://unpkg.com/viz.js@2.1.2/dist/lite.render.js'></script>
                    <script>
                        const dotCalls = `{dot_calls_src}`;
                        const vizc = new Viz();
                        vizc.renderSVGElement(dotCalls).then(svg => {{
                            const cont = document.getElementById('viz_calls');
                            cont.innerHTML='';
                            cont.appendChild(svg);
                        }});
                        document.getElementById('dlpng_calls').onclick = async () => {{
                            const svgEl = document.querySelector('#viz_calls svg');
                            if(!svgEl) return;
                            const xml = new XMLSerializer().serializeToString(svgEl);
                            const svg64 = btoa(unescape(encodeURIComponent(xml)));
                            const image64 = 'data:image/svg+xml;base64,' + svg64;
                            const img = new Image();
                            img.onload = function(){{
                                const canvas = document.createElement('canvas');
                                canvas.width = img.width; canvas.height = img.height;
                                const ctx = canvas.getContext('2d');
                                ctx.drawImage(img, 0, 0);
                                const link = document.createElement('a');
                                link.download = 'grafo_llamadas.png';
                                link.href = canvas.toDataURL('image/png');
                                link.click();
                            }};
                            img.src = image64;
                        }};
                    </script>
                    """,
                    height=700,
                    scrolling=True
            )

        finally:
            tmp_dir_obj.cleanup()

st.markdown("---")
st.markdown("Notas:")
st.markdown("- En nube se muestran gráficos inline (SVG); no se generan PDFs ni se abren archivos.")
st.markdown("- El análisis de párrafos usa heurísticas que pueden requerir ajuste según el estilo COBOL.")
