

# Interfaz gráfica con Streamlit
import streamlit as st
import subprocess
import os

st.set_page_config(page_title="RoadMapProject - Analizador COBOL", layout="centered")
st.title("RoadMapProject - Analizador COBOL")
st.write("""
Selecciona el tipo de análisis a realizar sobre un programa COBOL y sube el archivo a analizar.
""")

uploaded_file = st.file_uploader("Selecciona un archivo COBOL", type=["cob", "cbl", "txt", "*"], accept_multiple_files=False)

col1, col2 = st.columns(2)

if uploaded_file:
    # Guardar archivo temporalmente
    temp_path = os.path.join("temp_input.cob")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    with col1:
        if st.button("Análisis de párrafos y SQL (DB2)"):
            with st.spinner("Ejecutando análisis de párrafos y SQL..."):
                try:
                    result = subprocess.run(["python", "RoadMap.07.py", temp_path, "SQL"], capture_output=True, text=True, check=True)
                    st.success("Análisis de párrafos y SQL completado. Revisa los archivos generados.")
                    st.text_area("Salida del análisis:", result.stdout)
                except subprocess.CalledProcessError as e:
                    st.error(f"Error al ejecutar el análisis: {e.stderr}")

    with col2:
        if st.button("Análisis de llamadas externas (CALLs/FEXXX, XPLAIN)"):
            with st.spinner("Ejecutando análisis de llamadas externas..."):
                try:
                    result = subprocess.run(["python", "RoadMapCalls.05.py", temp_path], capture_output=True, text=True, check=True)
                    st.success("Análisis de llamadas externas completado. Revisa los archivos generados.")
                    st.text_area("Salida del análisis:", result.stdout)
                except subprocess.CalledProcessError as e:
                    st.error(f"Error al ejecutar el análisis: {e.stderr}")

    # Limpieza del archivo temporal (opcional)
    # os.remove(temp_path)
else:
    st.info("Por favor, selecciona un archivo COBOL para analizar.")
