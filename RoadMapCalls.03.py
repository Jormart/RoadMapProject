# se añaden las modificaciones siguientes sobre la version 02
#  -> se corta el nombre del programa por un guion "-" en los casos en los que se trata de una variable para tener el nombre "limpio"
#  -> se genera la funcion guardar_diccionario2 llanada cuando se trata de un directorio para anexar los dict en uno solo
#  -> en generar_grafo() se genera el archivo pdf antes del dot.render y se corrije el nombre del archivo en el dot.render corrigiendo el error de memoria que daba al tratar un directorio
# 

import os
import re
import sys
import json  # Añadido para guardar el diccionario en JSON
from graphviz import Digraph
from collections import defaultdict

# ------------------------------------------------------------
# FUNCIONES PRINCIPALES
# ------------------------------------------------------------

def detectar_call(linea):
    """
    Detecta llamadas a otros módulos COBOL (CALL o EXEC CICS LINK/START/INVOKE).
    Retorna el nombre del módulo llamado, si lo encuentra.
    """
    linea = linea.upper()

    # CALL 'MODULO' o CALL WS-MODULO
    # ~ m = re.search(r"\bCALL\s+['\"]?([\w-]+)['\"]?", linea)
    m = re.search(r"\sCALL\s+['\"]?([\w-]+)['\"]?", linea)
    if m:
        # parte el nombre del programa por un - ( para decidir si es una variable o no)
        n = re.search(r"([\w+]+)?-([\w+]+)?", m.group(1))
         if n:
             return n.group(2)
        else:
             return m.group(1)

    # EXEC CICS LINK/START/INVOKE PROGRAM('MODULO') END-EXEC
    m = re.search(r"EXEC\s+CICS\s+(?:LINK|START|INVOKE)\s+PROGRAM\s*\(['\"]?([\w-]+)['\"]?\)", linea)
    if m:
        return "CICS-" + m.group(1)

    return None


def es_linea_ignorable(linea):
    """Devuelve True si la línea es un comentario o vacía."""
    """añadimos como lineas idnorables si:
        - contiene un move(por temas de literales)
        - se trata de un parrafo (posicion 7 informada)"""
    return not linea.strip() or (len(linea) > 6 and linea[6] == '*') or (re.search(r"\s+MOVE\s+", linea)) or linea[7] != ' '


def analizar_cobol(ruta_archivo):
    """
    Analiza un programa COBOL y extrae todas las llamadas externas (CALL y CICS).
    No tiene en cuenta los párrafos.
    """
    llamadas = defaultdict(list)
    origen = os.path.splitext(os.path.basename(ruta_archivo))[0].upper()

    try:
        with open(ruta_archivo, 'r', encoding='latin-1') as archivo:
            for linea in archivo:
                linea = linea.upper()
                if es_linea_ignorable(linea):
                    continue

                destino = detectar_call(linea)
                if destino:
                    llamadas[origen].append(destino.upper())

    except Exception as e:
        print(f"Error al analizar el archivo: {e}")

    return llamadas

def guardar_diccionario(llamadas, archivo_salida):
    """
    Guarda el diccionario de llamadas en un archivo .dict (formato JSON).
    """
    dict_llamadas = dict(llamadas)  # Convertir defaultdict a dict normal
    # ~ ruta_dict = f"{archivo_salida}.dict"
    ruta_dict = f"./tmp/{archivo_salida}.dict"
    try:
        with open(ruta_dict, 'w', encoding='utf-8') as f:
            json.dump(dict_llamadas, f, indent=4, ensure_ascii=False)
        print(f"Diccionario de llamadas guardado en: {ruta_dict}")
    except Exception as e:
        print(f"Error al guardar el diccionario: {e}")

def guardar_diccionario2(llamadas, archivo_salida):
    """
    Guarda el diccionario de llamadas en un archivo .dict (formato JSON)., APPEND
    """
    dict_llamadas = dict(llamadas)  # Convertir defaultdict a dict normal
    ruta_dict = f"./tmp/{archivo_salida}.dict"
    try:
        with open(ruta_dict, 'a', encoding='utf-8') as f:
            json.dump(dict_llamadas, f, indent=4, ensure_ascii=False)
        print(f"Diccionario de llamadas añadido a : {ruta_dict}")
    except Exception as e:
        print(f"Error al añadir al diccionario: {e}")

def generar_grafo(llamadas, archivo_salida):
    """
    Genera un grafo PDF con las llamadas externas detectadas.
    """
    dot = Digraph(comment='Llamadas COBOL', format='pdf', engine='dot')
    # ~ dot.attr(dpi='200', rankdir='TB', nodesep='1.0', ranksep='1.3', splines='ortho')
    # nodesep -> separacion horizontal
    # ranksep -> separacion vertical minima
    #
    dot.attr(dpi='200', rankdir='TB', nodesep='0.5', ranksep='0.3 equally', splines='ortho')

    # Crear nodos y relaciones
    for origen, destinos in llamadas.items():
        dot.node(origen, origen, style='filled', fillcolor='#B4C7E7', shape='box', fontname='Helvetica')
        
        # Quitar duplicados de destinos
        destinos_unicos = set(destinos)
        
        for destino in destinos_unicos:
            color = '#A4C2F4'
            shape = 'house'
            shape = 'component'
            
            if destino.startswith('CICS-'):
                color = '#FFD966'
                shape = 'cylinder'
                
            dot.node(destino, destino, style='filled', fillcolor=color, shape=shape, fontname='Helvetica')
            #dot.edge(origen, destino, color='#4A86E8', arrowsize='0.7')
            dot.edge(origen, destino, color='#3D85C6', arrowsize='0.7')

    dot.save(filename=f"{archivo_salida}.pdf")
    # ~ pdf_path = dot.render(filename=f"{archivo_salida}.pdf", cleanup=True)
    pdf_path = dot.render(filename=f"{archivo_salida}", cleanup=True)
    
    print(f"Grafo generado: {pdf_path}")

    # Abrir el PDF automáticamente según el SO
    # ~ if sys.platform.startswith('win'):
        # ~ os.startfile(pdf_path)
    # ~ elif sys.platform == 'darwin':
        # ~ os.system(f'open \"{pdf_path}\"')
    # ~ else:
        # ~ os.system(f'xdg-open \"{pdf_path}\"')

def encontrar_archivos_cobol(directorio):
    """
    Recorre recursivamente un directorio y retorna una lista de rutas a archivos COBOL (.cob o .cbl).
    """
    archivos_cobol = []
    for root, _, files in os.walk(directorio):
        for file in files:
            if file.lower().endswith(('.cob', '.cbl', '.cobol')):
                archivos_cobol.append(os.path.join(root, file))
    return archivos_cobol
    
# ------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python RoadMapCalls.py <fuente_cobol>")
        sys.exit(1)
        
    ruta_cobol = sys.argv[1]
    if os.path.isdir(ruta_cobol):
        print(f"Analizando llamadas externas en el directorio: {ruta_cobol}")
        archivos = encontrar_archivos_cobol(ruta_cobol)
        if not archivos:
            print("No se encontraron archivos COBOL (.cob,.cbl o .COBOL) en el directorio.")
            sys.exit(1)
        for archivo in archivos:
            archivo_salida = os.path.splitext(os.path.basename(archivo))[0]
            print(f"\nProcesando archivo: {archivo}")
            llamadas = analizar_cobol(archivo)
            total_llamadas = sum(len(v) for v in llamadas.values())
            print(f"{total_llamadas} llamadas únicas encontradas en {archivo}.")
            print(f"archivo_salida:{archivo_salida}<-")
            print(f"Llamadas:{llamadas}<-")
            guardar_diccionario(llamadas, archivo_salida)
            guardar_diccionario2(llamadas, ruta_cobol)
            generar_grafo(llamadas, archivo_salida)
    else:
        archivo_salida = os.path.splitext(os.path.basename(ruta_cobol))[0]
        print(f"Analizando llamadas externas en: {ruta_cobol}")
        llamadas = analizar_cobol(ruta_cobol)
        total_llamadas = sum(len(v) for v in llamadas.values())
        print(f"{total_llamadas} llamadas únicas encontradas.")
        guardar_diccionario(llamadas, archivo_salida)
        generar_grafo(llamadas, archivo_salida)
    '''
    ruta_cobol = sys.argv[1]
    archivo_salida = os.path.splitext(os.path.basename(ruta_cobol))[0]

    print(f"Analizando llamadas externas en: {ruta_cobol}")

    llamadas = analizar_cobol(ruta_cobol)
    total_llamadas = sum(len(v) for v in llamadas.values())

    print(f"{total_llamadas} llamadas encontradas.")

    # Nueva funcionalidad: guardar el diccionario
    guardar_diccionario(llamadas, archivo_salida)
    
    generar_grafo(llamadas, archivo_salida)
    '''
