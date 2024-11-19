import pdfplumber
import os
import re
import csv
import glob
import shutil

def extraer_texto_pdf_plumber(archivo_pdf):
    texto_completo = ""
    with pdfplumber.open(archivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto_completo += pagina.extract_text() or ''
    return texto_completo

def buscar_presupuesto_apalancamiento(texto):
    patron_apalancamiento = r"Meta 12 meses:\s*(\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?)"
    coincidencia = re.search(patron_apalancamiento, texto)
    if coincidencia:
        return coincidencia.group(1).replace("\n", "").strip()
    return None

def asignar_numero_segun_area(area_texto):
    if area_texto:
        if "Producción Alimentaria" in area_texto:
            return 1
        elif "Internacionalización" in area_texto:
            return 2
        elif "Medio Ambiente" in area_texto or "Sustentabilidad" in area_texto:
            return 3
        elif "Promoción Regional" in area_texto:
            return 4
        elif "Recursos Hídricos" in area_texto:
            return 5
        elif "Capital Humano" in area_texto:
            return 6
        elif "Energía" in area_texto:
            return 7
    return None

def insertar_espacios_texto(texto):
    texto = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", texto)
    texto = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", texto)
    texto = re.sub(r"([a-z])([A-Z])", r"\1 \2", texto)
    return texto

def extraer_periodo_robusto(texto):
    patrones_fechas = [
        r"Periodo\s*(\d{1,2}\s*de\s*\w+\s*\d{4})\s*(?:–|-|a|hasta|,)?\s*(\d{1,2}\s*de\s*\w+\s*\d{4})",
        r"(\d{1,2}\s*de\s*\w+\s*\d{4})\s*(?:–|-|a|hasta|,)?\s*(\d{1,2}\s*de\s*\w+\s*\d{4})"
    ]
    for patron in patrones_fechas:
        coincidencia = re.search(patron, texto)
        if coincidencia:
            return coincidencia.group(1).replace("\n", "").strip(), coincidencia.group(2).replace("\n", "").strip()
    return None, None

def buscar_texto_despues_de(texto, claves):
    for clave in claves:
        posicion_clave = texto.find(clave)
        if posicion_clave != -1:
            texto_despues = texto[posicion_clave + len(clave):]
            return texto_despues.split("\n", 1)[0].strip()
    return None

def procesar_pdfs_en_carpeta(carpeta, archivo_csv, carpeta_procesados):
    archivos_pdf = glob.glob(os.path.join(carpeta, "*.pdf"))
    
    if not archivos_pdf:
        return

    if not os.path.exists(carpeta_procesados):
        os.makedirs(carpeta_procesados)

    if os.path.exists(archivo_csv):
        with open(archivo_csv, mode='r', newline='', encoding='utf-8') as csvfile:
            lector = csv.DictReader(csvfile)
            rows = list(lector)
            ultimo_id = int(rows[-1]['ID_presupuesto']) if rows else 0
    else:
        ultimo_id = 0

    with open(archivo_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['ID_presupuesto', 'fecha_inicio', 'fecha_termino', 'presupuesto', 'Area_ID']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for archivo_pdf in archivos_pdf:
            texto_pdf = extraer_texto_pdf_plumber(archivo_pdf)
            texto_pdf = insertar_espacios_texto(texto_pdf)  # Insert spaces to fix format

            # Extraer fechas
            fecha_inicio, fecha_termino = extraer_periodo_robusto(texto_pdf)

            # Extraer presupuesto específico de Apalancamiento
            presupuesto = buscar_presupuesto_apalancamiento(texto_pdf)

            # Extraer área y asignar ID
            resultado_area = buscar_texto_despues_de(texto_pdf, ["Área", "Sector", "Campo"])
            numero_asignado = asignar_numero_segun_area(resultado_area)

            ultimo_id += 1
            fila = {
                'ID_presupuesto': ultimo_id,
                'fecha_inicio': fecha_inicio,
                'fecha_termino': fecha_termino,
                'presupuesto': presupuesto,
                'Area_ID': numero_asignado
            }
            writer.writerow(fila)

            # Mover archivo procesado a la carpeta correspondiente
            archivo_procesado = os.path.join(carpeta_procesados, os.path.basename(archivo_pdf))
            shutil.move(archivo_pdf, archivo_procesado)

# Especifica la ruta de la carpeta donde se encuentran los PDFs y el nombre del archivo CSV
carpeta_pdfs = 'C:/Users/acard/Desktop/script_pdf/'  # Cambia esta ruta por la de tu carpeta
archivo_csv = 'extracion.csv'  # Nombre del archivo CSV
carpeta_procesados = 'C:/Users/acard/Desktop/script_pdf/archivos_procesados'  # Carpeta para los archivos procesados

# Ejecutar el script para procesar los PDFs
procesar_pdfs_en_carpeta(carpeta_pdfs, archivo_csv, carpeta_procesados)
