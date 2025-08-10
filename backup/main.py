import os
import csv
import re
import fitz  # PyMuPDF

entrada = "formularios"
salida = "resultados"

csv_tecnico = os.path.join(salida, "cuerpo_anexoII.csv")
csv_global_gastos = os.path.join(salida, "gastos_globales.csv")

if not os.path.exists(salida):
    os.makedirs(salida)

# Campos del cuerpo técnico
campos_tecnicos = [
    "Archivo", "Ayuntamiento", "Prioridad", "NOMBRE", "APELLIDOS", "TELÉFONO",
    "EMAIL", "Nom_Proyecto", "ChkBox1", "URL", "ChkBox2", "ChkBox3",
    "Red_Social1", "Red_Social2", "ChkBox4", "Imp_Total", "Imp_Total_Solici"
]

# Campos de cada fila de gastos
campos_gastos = [
    "Archivo", "Ayuntamiento", "Prioridad", "Fila", "Tipo", "Descripción",
    "Vertical", "Sensores", "Importe", "Solicitado"
]

def extraer_ayuntamiento_prioridad(nombre_archivo):
    """
    Extrae ayuntamiento y prioridad del nombre del archivo.
    Formato esperado: AnexoII[Ayuntamiento][Prioridad].pdf
    Ejemplo: AnexoIIAbanilla1.pdf -> Ayuntamiento='Abanilla', Prioridad='1'
    """
    nombre_base = os.path.splitext(nombre_archivo)[0]
    if nombre_base.startswith("AnexoII"):
        sin_prefijo = nombre_base[7:]
        prioridad = re.search(r'(\d+)$', sin_prefijo)
        if prioridad:
            prioridad_valor = prioridad.group(1)
            ayuntamiento = sin_prefijo[: -len(prioridad_valor)]
            return ayuntamiento, prioridad_valor
    return "Sin_Ayuntamiento", "0"

def extraer_campos_fitx(ruta_pdf):
    """
    Extrae todos los campos del formulario (AcroForm), incluidos dropdowns y checkboxes.
    """
    doc = fitz.open(ruta_pdf)
    campos = {}
    for page in doc:
        for widget in page.widgets():
            if widget.field_name:
                campos[widget.field_name] = widget.field_value
    return campos

# Inicializar CSVs técnicos y global de gastos
with open(csv_tecnico, "w", newline="", encoding="utf-8") as f:
    csv.writer(f, delimiter=";").writerow(campos_tecnicos)

with open(csv_global_gastos, "w", newline="", encoding="utf-8") as f:
    csv.writer(f, delimiter=";").writerow(campos_gastos)

# Procesar PDFs
for archivo in os.listdir(entrada):
    if not archivo.lower().endswith(".pdf"):
        continue

    print(f"Procesando: {archivo}")
    ruta = os.path.join(entrada, archivo)

    try:
        campos = extraer_campos_fitx(ruta)
        ayuntamiento, prioridad = extraer_ayuntamiento_prioridad(archivo)

        # Fila técnica
        fila_tecnica = [
            archivo,
            ayuntamiento,
            prioridad,
            campos.get("NOMBRE", ""),
            campos.get("APELLIDOS", ""),
            campos.get("TELÉFONO", ""),
            campos.get("EMAIL", ""),
            campos.get("Nom_Proyecto", ""),
            campos.get("ChkBox1", ""),
            campos.get("URL", ""),
            campos.get("ChkBox2", ""),
            campos.get("ChkBox3", ""),
            campos.get("Red_Social1", ""),
            campos.get("Red_Social2", ""),
            campos.get("ChkBox4", ""),
            campos.get("Imp_Total", ""),
            campos.get("Imp_Total_Solici", "")
        ]

        with open(csv_tecnico, "a", newline="", encoding="utf-8") as f:
            csv.writer(f, delimiter=";").writerow(fila_tecnica)

        # CSV individual
        nombre_csv_individual = os.path.join(salida, archivo.replace(".pdf", ".csv"))

        with open(nombre_csv_individual, "w", newline="", encoding="utf-8") as f_indiv:
            writer_indiv = csv.writer(f_indiv, delimiter=";")
            writer_indiv.writerow(campos_gastos)

            filas_procesadas = 0
            for i in range(1, 100):  # hasta 99 filas posibles
                tipo        = campos.get(f"T1_{i}1", "")
                descripcion = campos.get(f"T1_{i}2", "")
                vertical    = campos.get(f"T1_{i}3", "")
                sensores    = campos.get(f"T1_{i}4", "")
                importe     = campos.get(f"T1_{i}5", "")
                solicitado  = campos.get(f"T1_{i}6", "")

                if not any([tipo, descripcion, vertical, sensores, importe, solicitado]):
                    break

                fila_gasto = [
                    archivo,
                    ayuntamiento,
                    prioridad,
                    i,
                    tipo,
                    descripcion,
                    vertical,
                    sensores,
                    importe,
                    solicitado
                ]

                writer_indiv.writerow(fila_gasto)
                with open(csv_global_gastos, "a", newline="", encoding="utf-8") as f_global:
                    csv.writer(f_global, delimiter=";").writerow(fila_gasto)

                filas_procesadas += 1

            print(f"  Filas de gastos procesadas: {filas_procesadas}")

    except Exception as e:
        print(f"Error procesando {archivo}: {e}")
        continue

print("\nProcesamiento completado.")
print(f"- {csv_tecnico}")
print(f"- {csv_global_gastos}")
print(f"- CSVs individuales en '{salida}'")
