


# Interfaz gráfica con Streamlit
import streamlit as st
import subprocess
import os

st.set_page_config(page_title="RoadMapProject - Analizador COBOL", layout="centered")
st.title("RoadMapProject - Analizador COBOL")
st.write("""
Selecciona el tipo de análisis a realizar sobre un programa COBOL y sube el archivo a analizar.
""")

# Selección de tipo de análisis
analisis = st.radio(
    "Selecciona el tipo de análisis:",
    ("Análisis de párrafos y SQL (DB2)", "Análisis de llamadas externas (CALLs/FEXXX, XPLAIN)")
)

uploaded_file = st.file_uploader("Selecciona un archivo COBOL", type=["cob", "cbl", "txt", "*"], accept_multiple_files=False)

if uploaded_file:
    # Guardar archivo temporalmente
    temp_path = os.path.join("temp_input.cob")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    if analisis == "Análisis de párrafos y SQL (DB2)":
        if st.button("Ejecutar análisis de párrafos y SQL (DB2)"):
            with st.spinner("Ejecutando análisis de párrafos y SQL..."):
                try:
                    result = subprocess.run(["python", "RoadMap.07.py", temp_path, "SQL"], capture_output=True, text=True, check=True)
                    st.success("Análisis de párrafos y SQL completado. Revisa los archivos generados.")
                    st.text_area("Salida del análisis:", result.stdout)
                except subprocess.CalledProcessError as e:
                    st.error(f"Error al ejecutar el análisis: {e.stderr}")
    else:
        if st.button("Ejecutar análisis de llamadas externas (CALLs/FEXXX, XPLAIN)"):
            with st.spinner("Ejecutando análisis de llamadas externas..."):
                try:
                    result = subprocess.run(["python", "RoadMapCalls.05.py", temp_path], capture_output=True, text=True, check=True)
                    st.success("Análisis de llamadas externas completado. Revisa los archivos generados.")
                    st.text_area("Salida del análisis:", result.stdout)
                except subprocess.CalledProcessError as e:
                    st.error(f"Error al ejecutar el análisis: {e.stderr}")
else:
    st.info("Por favor, selecciona un archivo COBOL para analizar.")
