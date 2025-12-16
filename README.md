
# RoadMapProject

**Análisis visual de código COBOL legacy** — Herramienta para visualizar la estructura interna de programas COBOL y sus relaciones con otros módulos y recursos DB2.

---

## 🚀 Demo en Vivo

Despliega tu propia instancia en [Streamlit Cloud](https://streamlit.io/cloud) conectando este repositorio.

---

## 📋 Funcionalidades

### Tab 1: Jerarquía de Párrafos
Analiza la estructura interna de un programa COBOL individual:

- **Árbol de llamadas PERFORM**: Visualiza cómo los párrafos se invocan entre sí
- **Detección de SQL embebido**: Identifica tablas DB2 referenciadas en cada párrafo
- **Diagrama interactivo**: Zoom, pan y navegación con el mouse
- **Vista de texto**: Árbol jerárquico en formato texto para copiar/pegar

### Tab 2: Llamadas entre Programas (Estilo XPLAIN)
Genera un diagrama de contexto del programa con estilo XPLAIN:

- **Programa principal** al centro (caja azul)
- **Tablas DB2**: Separadas en lectura (SELECT) y escritura (INSERT/UPDATE/DELETE)
- **Módulos llamados**: Programas invocados via CALL, CICS LINK/START/INVOKE
- **Programas llamadores**: Si subes múltiples archivos, detecta quién llama al programa principal
- **Transacciones CICS**: Detecta EXEC CICS START TRANSID

---

## 🖥️ Uso

### Ejecución Local
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
streamlit run streamlit_app.py
```

La aplicación se abrirá en `http://localhost:8501`

### Despliegue en Streamlit Cloud
1. Sube el repositorio a GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu cuenta de GitHub
4. Selecciona el repositorio y configura:
   - **Main file path**: `streamlit_app.py`
   - **Python version**: 3.9 o superior
5. Click en "Deploy"

---

## 📁 Archivos Soportados

| Extensión | Descripción |
|-----------|-------------|
| `.cob`    | Fuente COBOL |
| `.cbl`    | Fuente COBOL |
| `.txt`    | Fuente COBOL en texto plano |
| `.zip`    | Archivo comprimido con múltiples fuentes |

> **Nota**: Los archivos se procesan con codificación `latin-1` para compatibilidad con sistemas legacy.

---

## 🔧 Componentes del Proyecto

| Archivo | Descripción |
|---------|-------------|
| `streamlit_app.py` | Interfaz web principal con visualizadores interactivos |
| `RoadMap.07.py` | Motor de análisis de jerarquía de párrafos y SQL |
| `RoadMapCalls.05.py` | Motor de detección de llamadas entre programas |
| `requirements.txt` | Dependencias Python (Streamlit + Graphviz wrapper) |

---

## ⚡ Características Técnicas

- **Sin binarios externos**: No requiere instalación de Graphviz en el sistema
- **Renderizado client-side**: Usa [Viz.js](https://github.com/mdaines/viz.js) para generar SVG en el navegador
- **Zoom interactivo**: Implementado con [svg-pan-zoom](https://github.com/ariutta/svg-pan-zoom)
- **Auto-ajuste**: Los diagramas se ajustan automáticamente al tamaño del contenedor
- **Descarga DOT**: Exporta el código fuente del grafo para uso externo

---

## 📊 Leyenda de Colores (Tab 2 - XPLAIN)

| Elemento | Color | Descripción |
|----------|-------|-------------|
| Programa principal | 🔵 Azul (#4A90D9) | El programa que se está analizando |
| Tablas DB2 Lectura | 🟡 Amarillo (#FFD700) | Tablas accedidas con SELECT |
| Tablas DB2 Escritura | 🟠 Naranja (#FF8C00) | Tablas con INSERT/UPDATE/DELETE |
| Módulos llamados | 🟢 Verde (#90EE90) | Programas invocados (CALL/CICS) |
| Programas llamadores | ⚪ Gris (#D3D3D3) | Programas que llaman al principal |
| Transacciones CICS | 🟣 Violeta (#DDA0DD) | EXEC CICS START TRANSID |

---

## 📝 Requisitos

```
streamlit==1.39.0
graphviz==0.20.3
```

Python 3.9 o superior recomendado.

---

## 📄 Licencia

Proyecto interno para análisis de código COBOL legacy.
