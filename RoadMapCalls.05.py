# se añaden las modificaciones siguientes sobre la version 03.
#  -> se corta el nombre del programa por un guion "-" en los casos en los que se trata de una variable para tener el nombre "limpio"
#  -> en generar_grafo() se genera el archivo pdf antes del dot.render y se corrije el nombre del archivo en el dot.render corrigiendo el error de memoria que daba al tratar un directorio
#  -> Solo se genera el PDF si hay algo que incluir, en caso de tener un pdf sin llamadas no se genera.
#  -> Se generan los PDF en la carpeta ./PDF/
#  -> se elimina guerdard_diccionario2 por no ser necesario
#  -> se adapta el analizar_cobol para generar un diccionario con todas las llamadas del directorio
#  -> se genera el generar_grafo_dir, para trabajara con el diccionario del directorio, generando el grafo con las llamdas y llamantes del programa a analizar
# 

import os
import re
import sys
import json  # Añadido para guardar el diccionario en JSON
import argparse   # Gestion de parametros
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
    origen = os.path.splitext(os.path.basename(ruta_archivo))[0].upper()[:6]
    
    print (f"Origen:{origen}<-\t Origen[:6]{origen[:6]}")
    
    try:
        with open(ruta_archivo, 'r', encoding='latin-1') as archivo:
            for linea in archivo:
                linea = linea.upper()
                if es_linea_ignorable(linea):
                    continue

                destino = detectar_call(linea)
                if destino:
                    llamadas[origen].append(destino.upper())
                    llamadasdir[origen[:6]].append(destino.upper())

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

def generar_grafo_dir(llamadasdir, archivo_salida):
    """
    Genera un grafo PDF con las llamadas externas detectadas.
    """
    
    # a partir del nombre del programa (SKZ+numeros+tipo+version.Lenguaje [FE000x00.COBOL] nos quedamos con el nombre del programa a analizar)
    prog_cobol = args.src[:6]
    
    dot = Digraph(comment='Llamadas COBOL', format='pdf', engine='dot')
    dot.attr(dpi='200', rankdir='TB', nodesep='0.5', ranksep='0.3 equally', splines='ortho')
    
    print (f"get[]:{llamadasdir[prog_cobol]}")
    
    # genera el nodo del programa analizado
    dot.node(prog_cobol, prog_cobol, style='filled', fillcolor='#B4C7E7', shape='box', fontname='Helvetica')
    
    #crear los nodos de los programas que llaman al programa analizado
    for llamante, llamados in llamadasdir.items():
        # Quitar duplicados de llamados
        llamados_unicos = set(llamados)
        print(f"llamante:{llamante}\nllamados:{llamados_unicos}")
        for llamado in llamados_unicos:
            if llamado[:6] == prog_cobol or llamado[:5] == prog_cobol[:5]:
                color = '#A4C2F4'
                shape = 'house'
                dot.node(llamante, llamante, style='filled', fillcolor=color, shape=shape, fontname='Helvetica')
                dot.edge(llamante, prog_cobol, color='#3D85C6', arrowsize='0.7')
                
    #crear los nodos de los programas llamdos por el programa analizado
    for destino in set(llamadasdir[prog_cobol]):
        color = '#A4C2F4'
        shape = 'house'
        shape = 'component'
        
        if destino.startswith('CICS-'):
            color = '#FFD966'
            shape = 'cylinder'
            
        dot.node(destino, destino, style='filled', fillcolor=color, shape=shape, fontname='Helvetica')
        dot.edge(prog_cobol, destino, color='#3D85C6', arrowsize='0.7')
            
        

    dot.save(filename=f"{archivo_salida}.pdf")
    # ~ pdf_path = dot.render(filename=f"{archivo_salida}.pdf", cleanup=True)
    pdf_path = dot.render(filename=f"{archivo_salida}", cleanup=True)
    
    print(f"Grafo generado: {pdf_path}")

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

    dot.save(filename=f"./PDF/{archivo_salida}.pdf")
    # ~ pdf_path = dot.render(filename=f"{archivo_salida}.pdf", cleanup=True)
    pdf_path = dot.render(filename=f"./PDF/{archivo_salida}", cleanup=True)
    
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
def main():
    return 0

if __name__ == "__main__":
    
    ap = argparse.ArgumentParser(description="Genera PDF con grafico de jerarquia de parrafos.\n https://github.com/RickDecar/RoadMapProject")
    # ~ ap.add_argument("--src",   required=True,  default="FE982A39.COBOL", help="Programa a analizar.")
    # ~ ap.add_argument("--dir",   required=True,  default="SRC", help="Directorio de Fuentes.")
    # ~ ap.add_argument("--all",   required=False, default="", action="store_true", help="genera grafo individual para cada los fuentes.")
    # ~ ap.add_argument("--debug", required=False, default="", action="store_true", help="Mostrar pasos salida.")
    ap.add_argument("--src", required=True, help="Programa a analizar.")
    ap.add_argument("--dir", required=True, help="Directorio de Fuentes.")
    ap.add_argument("--all", required=False, action="store_true", help="genera grafo individual para cada los fuentes.")
    ap.add_argument("--debug", required=False, action="store_true", help="Mostrar pasos salida.")
    
    args = ap.parse_args()
    
    print (f"parametros \n src:{args.src}\n dir:{args.dir}\n all:{args.all}\n debug:{args.debug}")
    
    ruta_cobol = args.dir + "/" + args.src
    
    if os.path.isfile(ruta_cobol):
        if args.debug:
            print(f"ok {args.dir}/{args.src}")
            
        llamadasdir = defaultdict(list)
        print(f"Analizando llamadas externas en el directorio: {args.dir}")
        archivos = encontrar_archivos_cobol(args.dir)
        if not archivos:
            print("No se encontraron archivos COBOL (.cob,.cbl o .COBOL) en el directorio.")
            sys.exit(1)
        for archivo in archivos:
            archivo_salida = os.path.splitext(os.path.basename(archivo))[0]
            print(f"\nProcesando archivo: {archivo}")
            llamadas = analizar_cobol(archivo)
            
            total_llamadas = sum(len(v) for v in llamadas.values())
            print(f"{total_llamadas} llamadas únicas encontradas en {archivo}.")
            if args.debug:
                print(f"archivo_salida:{archivo_salida}<-")
                print(f"Llamadas:{llamadas}<-")
                print(f"Llamadasdir:{llamadasdir}<-")
            
            if (args.all) and (total_llamadas > 0):
                guardar_diccionario(llamadas, archivo_salida)
                generar_grafo(llamadas, archivo_salida)
        if (total_llamadas > 0):
            guardar_diccionario(llamadasdir, args.dir)
            generar_grafo_dir(llamadasdir, args.src)
    else:
        print(f"Ko {args.dir}/{args.src}")
        
'''
    if len(sys.argv) < 2:
        print("Uso: python RoadMapCalls.py <fuente_cobol>")
        sys.exit(1)
        
    ruta_cobol = sys.argv[1]
    if os.path.isdir(ruta_cobol):
        llamadasdir = defaultdict(list)
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
            print(f"Llamadasdir:{llamadasdir}<-")
            # ~ guardar_diccionario(llamadas, archivo_salida)
            # ~ generar_grafo(llamadas, archivo_salida)
        guardar_diccionario(llamadasdir, ruta_cobol)
        # ~ generar_grafo(llamadasdir, archivo_salida)
    else:
        archivo_salida = os.path.splitext(os.path.basename(ruta_cobol))[0]
        print(f"Analizando llamadas externas en: {ruta_cobol}")
        llamadas = analizar_cobol(ruta_cobol)
        total_llamadas = sum(len(v) for v in llamadas.values())
        print(f"{total_llamadas} llamadas únicas encontradas.")
        guardar_diccionario(llamadas, archivo_salida)
        generar_grafo(llamadas, archivo_salida)
'''
