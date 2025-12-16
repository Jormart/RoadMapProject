
# RoadMapProject

Análisis visual de código COBOL legacy

## Interfaz Streamlit

Interfaz web simplificada para analizar programas COBOL con dos funcionalidades principales:

### 1. Jerarquía de Párrafos
- Analiza la estructura de llamadas entre párrafos (PERFORM)
- Identifica tablas DB2 utilizadas en cada párrafo (EXEC SQL)
- Muestra un diagrama visual de la jerarquía completa

### 2. Llamadas entre Programas
- Detecta llamadas a módulos externos (CALL)
- Identifica invocaciones CICS (LINK, START, INVOKE)
- Muestra el flujo de llamadas a nivel de directorio

## Uso

### Ejecución local
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Despliegue en Streamlit Cloud
1. Sube el repositorio a GitHub
2. En Streamlit Cloud, selecciona el repo y configura `streamlit_app.py` como entrada
3. Asegúrate de que la versión de Python soporte los paquetes en requirements.txt

## Componentes

- **RoadMap.07.py**: Analizador de jerarquía de párrafos y SQL
- **RoadMapCalls.05.py**: Analizador de llamadas entre programas
- **streamlit_app.py**: Interfaz web unificada

## Características

- Sin instalación de Graphviz requerida (usa Python wrapper)
- Descarga de diagramas en formato SVG (vectorial, zoom sin pérdida)
- Interfaz simple y directa sin opciones complejas
- Compatible con archivos .cob, .cbl, .txt y .zip
