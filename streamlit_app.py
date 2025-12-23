import streamlit as st
import os
import json
import re
from graphviz import Digraph
from io import StringIO
import tempfile
import zipfile
import importlib.util
from collections import defaultdict

# Importar analizadores finales sin ejecutar sus mains
spec_rm = importlib.util.spec_from_file_location("roadmap07", os.path.join(os.path.dirname(__file__), "RoadMap.08.py"))
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
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        parrafo_inicio = st.text_input("Párrafo inicial (opcional)", value="")
    with col2:
        analizar_sql = st.checkbox("Incluir tablas DB2", value=True)
    with col3:
        orientacion = st.selectbox("Orientación", ["Horizontal", "Vertical"], index=0, help="Horizontal (LR) para árboles profundos, Vertical (TB) para árboles anchos")
    
    run_btn = st.button("Analizar jerarquía", type="primary") 

    def build_graph(diccionario, selects_por_parrafo, analizar_sql=False, orientacion='LR'):
        dot = Digraph(comment='Llamadas COBOL', format='png', engine='dot')
        rankdir = 'LR' if orientacion == 'Horizontal' else 'TB'
        dot.attr(dpi='300', rankdir=rankdir, nodesep='0.6', ranksep='1.2', bgcolor='white')
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

            st.subheader("Diagrama de jerarquía (zoom con rueda del ratón, arrastrar para mover)")
            dot = build_graph(dicc, selects, analizar_sql, orientacion)

            # Visor interactivo con zoom y pan
            dot_escaped = json.dumps(dot.source)
            viewer_html = f'''
            <div style="border:1px solid #444; border-radius:8px; background:#fff; margin-bottom:10px;">
                <div style="padding:8px; background:#f0f0f0; border-bottom:1px solid #ddd; border-radius:8px 8px 0 0;">
                    <button onclick="panZoomInstance.zoomIn()" style="padding:5px 15px; margin-right:5px; cursor:pointer;">➕ Zoom In</button>
                    <button onclick="panZoomInstance.zoomOut()" style="padding:5px 15px; margin-right:5px; cursor:pointer;">➖ Zoom Out</button>
                    <button onclick="panZoomInstance.fit(); panZoomInstance.center();" style="padding:5px 15px; margin-right:5px; cursor:pointer;">🔄 Reset</button>
                    <button onclick="panZoomInstance.zoom(0.5); panZoomInstance.center();" style="padding:5px 15px; cursor:pointer;">📐 Alejar</button>
                </div>
                <div id="graph-container" style="width:100%; height:100vh; overflow:hidden;"></div>
            </div>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/viz.js/2.1.2/viz.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/viz.js/2.1.2/full.render.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
            <script>
                var panZoomInstance = null;
                (function() {{
                    var dotSrc = {dot_escaped};
                    var viz = new Viz();
                    viz.renderSVGElement(dotSrc).then(function(svg) {{
                        var container = document.getElementById('graph-container');
                        container.innerHTML = '';
                        svg.setAttribute('width', '100%');
                        svg.setAttribute('height', '100%');
                        svg.style.background = 'white';
                        container.appendChild(svg);
                        panZoomInstance = svgPanZoom(svg, {{
                            zoomEnabled: true,
                            controlIconsEnabled: false,
                            fit: true,
                            center: true,
                            minZoom: 0.05,
                            maxZoom: 20,
                            zoomScaleSensitivity: 0.3
                        }});
                        // Ajustar zoom inicial para ver todo
                        setTimeout(function() {{
                            panZoomInstance.fit();
                            panZoomInstance.center();
                        }}, 100);
                    }}).catch(function(err) {{
                        console.error('Viz.js error:', err);
                        document.getElementById('graph-container').innerHTML = '<p style="color:red; padding:20px;">Error renderizando diagrama</p>';
                    }});
                }})();
            </script>
            '''
            st.components.v1.html(viewer_html, height=1000, scrolling=False)

            # Descargar DOT
            st.download_button(
                label="📄 Descargar DOT",
                data=dot.source,
                file_name="jerarquia_parrafos.dot",
                mime="text/vnd.graphviz",
                help="Abre en https://dreampuf.github.io/GraphvizOnline/ para exportar PNG/SVG"
            )

            if analizar_sql:
                st.info(f"Bloques EXEC SQL encontrados: {sql_blocks}")

        finally:
            os.unlink(tmp_path)

# --- Tab 2: Llamadas entre programas - Estilo XPLAIN ---
with mode[1]:
    st.markdown("Genera un diagrama estilo XPLAIN: programa objetivo, llamantes, llamados y tablas DB2.")
    
    uploaded_xplain = st.file_uploader("Sube el archivo COBOL del programa objetivo (.cob/.txt)", type=["cob", "cbl", "cobol", "txt"], key="xplain_file")
    uploaded_others = st.file_uploader("Sube otros programas COBOL (opcional, para detectar llamantes)", type=["cob", "cbl", "cobol", "txt", "zip"], accept_multiple_files=True, key="xplain_others")
    run_xplain = st.button("Generar diagrama XPLAIN", type="primary")

    def extraer_nombre_programa(filename):
        """Extrae nombre del programa (primeros 6 chars del nombre de archivo sin extensión)"""
        return os.path.splitext(os.path.basename(filename))[0].upper()[:6]

    def detectar_calls_en_archivo(contenido):
        """Detecta CALL y EXEC CICS LINK/START/INVOKE en contenido COBOL"""
        calls = []
        for linea in contenido.split('\n'):
            linea_u = linea.upper()
            # Ignorar comentarios
            if len(linea_u) > 6 and linea_u[6] == '*':
                continue
            # CALL 'PROGRAMA' o CALL WS-VARIABLE
            m = re.search(r"\sCALL\s+['\"]?([\w-]+)['\"]?", linea_u)
            if m:
                prog = m.group(1)
                # Si tiene guión, tomar la segunda parte (nombre real, no prefijo de variable)
                if '-' in prog:
                    parts = prog.split('-')
                    if len(parts) > 1:
                        prog = parts[-1]  # última parte después del guión
                if prog and len(prog) >= 4:
                    calls.append(prog[:8])  # máximo 8 chars
            # EXEC CICS LINK/START/INVOKE
            m2 = re.search(r"EXEC\s+CICS\s+(?:LINK|START|INVOKE)\s+PROGRAM\s*\(['\"]?([\w-]+)['\"]?\)", linea_u)
            if m2:
                calls.append("CICS-" + m2.group(1)[:6])
        return list(set(calls))

    def extraer_tablas_db2(contenido):
        """Extrae nombres de tablas/vistas DB2 desde sentencias EXEC SQL"""
        tablas = {}  # tabla -> tipo de acceso (SELECT, INSERT, UPDATE, DELETE)
        
        # Unir líneas para manejar SQL multilínea
        contenido_limpio = re.sub(r'\n\s{6}\*.*', '', contenido)  # quitar comentarios COBOL
        
        # Buscar SELECT ... FROM tabla
        for m in re.finditer(r'SELECT\s+.*?\s+FROM\s+([\w]+)', contenido_limpio, re.IGNORECASE | re.DOTALL):
            tabla = m.group(1).upper()
            if tabla not in ('DUAL', 'SYSIBM'):
                tablas[tabla] = tablas.get(tabla, []) + ['SELECT']
        
        # Buscar INSERT INTO tabla
        for m in re.finditer(r'INSERT\s+INTO\s+([\w]+)', contenido_limpio, re.IGNORECASE):
            tabla = m.group(1).upper()
            tablas[tabla] = tablas.get(tabla, []) + ['INSERT']
        
        # Buscar UPDATE tabla
        for m in re.finditer(r'UPDATE\s+([\w]+)\s+SET', contenido_limpio, re.IGNORECASE):
            tabla = m.group(1).upper()
            tablas[tabla] = tablas.get(tabla, []) + ['UPDATE']
        
        # Buscar DELETE FROM tabla
        for m in re.finditer(r'DELETE\s+FROM\s+([\w]+)', contenido_limpio, re.IGNORECASE):
            tabla = m.group(1).upper()
            tablas[tabla] = tablas.get(tabla, []) + ['DELETE']
        
        # Buscar OPEN CURSOR ... FOR SELECT ... FROM tabla (cursores)
        for m in re.finditer(r'DECLARE\s+([\w]+)\s+CURSOR.*?SELECT.*?FROM\s+([\w]+)', contenido_limpio, re.IGNORECASE | re.DOTALL):
            tabla = m.group(2).upper()
            tablas[tabla] = tablas.get(tabla, []) + ['CURSOR']
        
        # Consolidar tipos
        resultado = {}
        for tabla, tipos in tablas.items():
            tipos_unicos = list(set(tipos))
            if 'INSERT' in tipos_unicos or 'UPDATE' in tipos_unicos or 'DELETE' in tipos_unicos:
                resultado[tabla] = 'WRITE'
            else:
                resultado[tabla] = 'READ'
        
        return resultado

    def construir_grafo_xplain(prog_objetivo, llamados, tablas_db2, llamantes=None):
        """
        Construye un grafo estilo XPLAIN:
        - Programa objetivo en el centro (caja grande)
        - Llamantes a la izquierda (si los hay)
        - Programas llamados a la derecha
        - Tablas DB2 como cilindros (READ=azul, WRITE=naranja)
        """
        dot = Digraph(comment='Diagrama XPLAIN', format='png', engine='dot')
        dot.attr(dpi='300', rankdir='LR', nodesep='0.4', ranksep='1.2', splines='ortho', bgcolor='white')
        dot.attr('node', fontname='Helvetica', fontsize='11', fontcolor='black', width='1.5', height='1.0')
        
        # Subgrafo izquierdo: Llamantes
        if llamantes:
            with dot.subgraph(name='cluster_llamantes') as c:
                c.attr(label='Llamantes', style='rounded', color='#E8E8E8', bgcolor='#FAFAFA', fontsize='12')
                for llamante in llamantes:
                    c.node(f"in_{llamante}", llamante, shape='box', style='filled,bold', 
                           fillcolor='#FFE6E6', color='#CC0000', penwidth='2', width='1.8')
        
        # Subgrafo izquierdo: Tablas DB2 de lectura
        tablas_read = [t for t, tipo in tablas_db2.items() if tipo == 'READ']
        if tablas_read:
            with dot.subgraph(name='cluster_db2_read') as c:
                c.attr(label='Tablas DB2 (Lectura)', style='rounded', color='#E8E8E8', bgcolor='#F0F8FF', fontsize='12')
                for tabla in tablas_read:
                    label = f"{tabla}\n(SELECT)"
                    c.node(f"db2_{tabla}", label, shape='cylinder', style='filled', 
                           fillcolor='#9FC5E8', color='#3D85C6', penwidth='1.5', width='1.6')
        
        # Nodo central: Programa objetivo
        with dot.subgraph(name='cluster_objetivo') as c:
            c.attr(label='', style='invis')
            c.node(prog_objetivo, f"{prog_objetivo}\n\nPrograma\nObjetivo", shape='box', style='filled,bold',
                   fillcolor='#B4C7E7', color='#000000', penwidth='3', width='2.2', height='1.6', fontsize='14')
        
        # Subgrafo derecho: Programas llamados
        llamados_prog = [l for l in llamados if not l.startswith('CICS-')]
        llamados_cics = [l for l in llamados if l.startswith('CICS-')]
        
        if llamados_prog:
            with dot.subgraph(name='cluster_llamados') as c:
                c.attr(label='Programas Llamados', style='rounded', color='#E8E8E8', bgcolor='#F5F5F5', fontsize='12')
                for prog in llamados_prog:
                    c.node(f"out_{prog}", prog, shape='box', style='filled', 
                           fillcolor='#E3F2FD', color='#1976D2', penwidth='1.5', width='1.8')
        
        if llamados_cics:
            with dot.subgraph(name='cluster_cics') as c:
                c.attr(label='Transacciones CICS', style='rounded', color='#E8E8E8', bgcolor='#FFF8E1', fontsize='12')
                for prog in llamados_cics:
                    nombre = prog.replace('CICS-', '')
                    c.node(f"out_{prog}", nombre, shape='cylinder', style='filled', 
                           fillcolor='#FFD966', color='#F57C00', penwidth='1.5', width='1.6')
        
        # Subgrafo derecho: Tablas DB2 de escritura
        tablas_write = [t for t, tipo in tablas_db2.items() if tipo == 'WRITE']
        if tablas_write:
            with dot.subgraph(name='cluster_db2_write') as c:
                c.attr(label='Tablas DB2 (Escritura)', style='rounded', color='#E8E8E8', bgcolor='#FFF3E0', fontsize='12')
                for tabla in tablas_write:
                    label = f"{tabla}\n(INSERT/UPDATE)"
                    c.node(f"db2_{tabla}", label, shape='cylinder', style='filled', 
                           fillcolor='#F6B26B', color='#E65100', penwidth='1.5', width='1.6')
        
        # Edges: Llamantes -> Objetivo
        if llamantes:
            for llamante in llamantes:
                dot.edge(f"in_{llamante}", prog_objetivo, color='#CC0000', penwidth='1.5', arrowsize='0.8')
        
        # Edges: Tablas READ -> Objetivo
        for tabla in tablas_read:
            dot.edge(f"db2_{tabla}", prog_objetivo, color='#3D85C6', penwidth='1.2', arrowsize='0.7')
        
        # Edges: Objetivo -> Programas llamados
        for prog in llamados_prog:
            dot.edge(prog_objetivo, f"out_{prog}", color='#1976D2', penwidth='1.5', arrowsize='0.8')
        
        for prog in llamados_cics:
            dot.edge(prog_objetivo, f"out_{prog}", color='#F57C00', penwidth='1.5', arrowsize='0.8')
        
        # Edges: Objetivo -> Tablas WRITE
        for tabla in tablas_write:
            dot.edge(prog_objetivo, f"db2_{tabla}", color='#E65100', penwidth='1.2', arrowsize='0.7')
        
        return dot

    if run_xplain and uploaded_xplain:
        # Leer programa objetivo
        contenido_objetivo = uploaded_xplain.getvalue().decode('latin-1')
        prog_objetivo = extraer_nombre_programa(uploaded_xplain.name)
        
        # Detectar calls y tablas
        llamados = detectar_calls_en_archivo(contenido_objetivo)
        tablas_db2 = extraer_tablas_db2(contenido_objetivo)
        
        # Detectar llamantes desde otros archivos
        llamantes = []
        if uploaded_others:
            for f in uploaded_others:
                if f.name.lower().endswith('.zip'):
                    # Procesar ZIP
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        zip_path = os.path.join(tmp_dir, f.name)
                        with open(zip_path, 'wb') as zf:
                            zf.write(f.getvalue())
                        with zipfile.ZipFile(zip_path, 'r') as z:
                            z.extractall(tmp_dir)
                        for root, _, files in os.walk(tmp_dir):
                            for fname in files:
                                if fname.lower().endswith(('.cob', '.cbl', '.cobol', '.txt')):
                                    fpath = os.path.join(root, fname)
                                    with open(fpath, 'r', encoding='latin-1') as fh:
                                        contenido = fh.read()
                                        prog_name = extraer_nombre_programa(fname)
                                        if prog_name != prog_objetivo:
                                            calls = detectar_calls_en_archivo(contenido)
                                            if prog_objetivo in calls or any(prog_objetivo in c for c in calls):
                                                llamantes.append(prog_name)
                else:
                    contenido = f.getvalue().decode('latin-1')
                    prog_name = extraer_nombre_programa(f.name)
                    if prog_name != prog_objetivo:
                        calls = detectar_calls_en_archivo(contenido)
                        if prog_objetivo in calls or any(prog_objetivo in c for c in calls):
                            llamantes.append(prog_name)
        
        llamantes = list(set(llamantes))
        
        # Mostrar resumen
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Programas llamados", len(llamados))
        with col2:
            st.metric("Tablas DB2", len(tablas_db2))
        with col3:
            st.metric("Llamantes detectados", len(llamantes))
        
        # Generar grafo
        dot_xplain = construir_grafo_xplain(prog_objetivo, llamados, tablas_db2, llamantes if llamantes else None)
        
        st.subheader(f"Diagrama XPLAIN: {prog_objetivo}")
        
        # Visor interactivo
        dot_escaped = json.dumps(dot_xplain.source)
        viewer_html = f'''
        <div style="border:1px solid #444; border-radius:8px; background:#fff; margin-bottom:10px;">
            <div style="padding:8px; background:#f0f0f0; border-bottom:1px solid #ddd; border-radius:8px 8px 0 0;">
                <button onclick="panZoomXplain.zoomIn()" style="padding:5px 15px; margin-right:5px; cursor:pointer;">➕ Zoom In</button>
                <button onclick="panZoomXplain.zoomOut()" style="padding:5px 15px; margin-right:5px; cursor:pointer;">➖ Zoom Out</button>
                <button onclick="panZoomXplain.fit(); panZoomXplain.center();" style="padding:5px 15px; margin-right:5px; cursor:pointer;">🔄 Reset</button>
                <button onclick="panZoomXplain.zoom(0.5); panZoomXplain.center();" style="padding:5px 15px; cursor:pointer;">📐 Alejar</button>
            </div>
            <div id="graph-xplain-container" style="width:100%; height:100vh; overflow:hidden;"></div>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/viz.js/2.1.2/viz.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/viz.js/2.1.2/full.render.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
        <script>
            var panZoomXplain = null;
            (function() {{
                var dotSrc = {dot_escaped};
                var viz = new Viz();
                viz.renderSVGElement(dotSrc).then(function(svg) {{
                    var container = document.getElementById('graph-xplain-container');
                    container.innerHTML = '';
                    svg.setAttribute('width', '100%');
                    svg.setAttribute('height', '100%');
                    svg.style.background = 'white';
                    container.appendChild(svg);
                    panZoomXplain = svgPanZoom(svg, {{
                        zoomEnabled: true,
                        controlIconsEnabled: false,
                        fit: true,
                        center: true,
                        minZoom: 0.05,
                        maxZoom: 20,
                        zoomScaleSensitivity: 0.3,
                        initialViewBox: {{ x: 0, y: 0, width: 2000, height: 2000 }}
                    }});
                    // Ajustar zoom inicial para ver todo
                    setTimeout(function() {{
                        panZoomXplain.fit();
                        panZoomXplain.center();
                    }}, 100);
                }}).catch(function(err) {{
                    console.error('Viz.js error:', err);
                    document.getElementById('graph-xplain-container').innerHTML = '<p style="color:red; padding:20px;">Error renderizando diagrama</p>';
                }});
            }})();
        </script>
        '''
        st.components.v1.html(viewer_html, height=1000, scrolling=False)
        
        # Detalles expandibles
        with st.expander("📋 Detalles del análisis"):
            if llamados:
                st.write("**Programas llamados:**")
                for p in sorted(llamados):
                    st.write(f"  - {p}")
            if tablas_db2:
                st.write("**Tablas DB2:**")
                for t, tipo in sorted(tablas_db2.items()):
                    st.write(f"  - {t} ({tipo})")
            if llamantes:
                st.write("**Programas que llaman a este:**")
                for p in sorted(llamantes):
                    st.write(f"  - {p}")
        
        # Descargar DOT
        st.download_button(
            label="📄 Descargar DOT",
            data=dot_xplain.source,
            file_name=f"xplain_{prog_objetivo}.dot",
            mime="text/vnd.graphviz",
            help="Abre en https://dreampuf.github.io/GraphvizOnline/ para exportar PNG/SVG"
        )


