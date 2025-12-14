
# RoadMapProject

Get quick visual insight into old legacy COBOL

## Descripción
Este proyecto permite analizar programas COBOL para extraer:
- Jerarquía de llamadas entre párrafos y sentencias SQL embebidas (DB2)
- Llamadas a módulos externos (CALLs/FEXXX) y dependencias tipo XPLAIN
Genera diagramas y archivos de salida para facilitar la comprensión de sistemas legacy.

## Interfaz gráfica (Streamlit)
Desde diciembre 2025, el análisis se realiza mediante una interfaz web local con Streamlit.

### Requisitos previos
- Python 3.8+
- Instalar dependencias:
	```powershell
	pip install streamlit graphviz
	```
- Instalar Graphviz (binario) y asegurarse de que `dot` está en el PATH ([descargar aquí](https://graphviz.org/download/)).

### Ejecución
```powershell
streamlit run main.py
```
Se abrirá una web local donde puedes subir un archivo COBOL y elegir el tipo de análisis.

### Salidas
- Archivos PDF y TXT generados en el directorio del proyecto.
- La salida textual del análisis se muestra en la web.

### Scripts principales
- `RoadMap.07.py`: análisis de párrafos y SQL (DB2)
- `RoadMapCalls.05.py`: análisis de llamadas externas (CALLs/FEXXX, XPLAIN)

