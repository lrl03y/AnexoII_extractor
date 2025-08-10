import os
import csv
import re
import fitz  # PyMuPDF
from datetime import datetime
import time
import shutil

# Nuevas importaciones para firmas digitales
try:
    from pyhanko.pdf_utils.reader import PdfFileReader
    from pyhanko.sign.validation import validate_pdf_signature
    PYHANKO_AVAILABLE = True
except ImportError:
    PYHANKO_AVAILABLE = False
    print("⚠️  pyHanko no disponible. Instala con: pip install pyHanko")

# Importaciones para Access
try:
    import win32com.client
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("⚠️  win32com no disponible. Instala con: pip install pywin32")

entrada = "formularios"
salida = "resultados"
db_path = os.path.join(salida, "firmas.accdb")

csv_tecnico = os.path.join(salida, "cuerpo_anexoII.csv")
csv_global_gastos = os.path.join(salida, "gastos_globales.csv")

# Limpiar resultados anteriores
if os.path.exists(salida):
    print("🗑️  Eliminando resultados anteriores...")
    shutil.rmtree(salida)

if not os.path.exists(salida):
    os.makedirs(salida)

# Campos del cuerpo técnico
campos_tecnicos = [
    "Archivo", "Ayuntamiento", "Prioridad", "NOMBRE", "APELLIDOS", "TELÉFONO",
    "EMAIL", "Nom_Proyecto", "ChkBox1", "URL", "ChkBox2", "ChkBox3",
    "Red_Social1", "Red_Social2", "ChkBox4", "Imp_Total", "Imp_Total_Solici",
    "Firmante", "Emisor", "Valido_Hasta", "Firma_Valida"
]

# Campos de cada fila de gastos
campos_gastos = [
    "Archivo", "Ayuntamiento", "Prioridad", "Fila", "Tipo", "Descripción",
    "Vertical", "Sensores", "Importe", "Solicitado"
]

# Variables para estadísticas finales
total_formularios = 0
total_gastos = 0
formularios_firmados = 0
formularios_sin_firma = 0

def extraer_ayuntamiento_prioridad(nombre_archivo):
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
    start_time = time.time()
    print(f"    Extrayendo campos del formulario...")
    doc = fitz.open(ruta_pdf)
    campos = {}
    for page_num, page in enumerate(doc):
        widgets_count = 0
        for widget in page.widgets():
            if widget.field_name:
                campos[widget.field_name] = widget.field_value
                widgets_count += 1
        print(f"      Página {page_num + 1}: {widgets_count} campos")
    
    doc.close()
    elapsed = time.time() - start_time
    print(f"    ✅ Campos extraídos en {elapsed:.2f} segundos ({len(campos)} campos totales)")
    return campos

def extraer_firma_digital(ruta_pdf):
    if not PYHANKO_AVAILABLE:
        return {
            "firmante": "pyHanko no disponible",
            "emisor": "pyHanko no disponible",
            "valido_hasta": "",
            "valido": False
        }
        
    start_time = time.time()
    try:
        print("    Leyendo PDF...")
        with open(ruta_pdf, 'rb') as f:
            reader = PdfFileReader(f)
            print("    Buscando firmas...")
            embedded_sigs = reader.embedded_signatures

            if not embedded_sigs or len(embedded_sigs) == 0:
                print("    No se encontraron firmas")
                elapsed = time.time() - start_time
                print(f"    ✅ Proceso de firma completado en {elapsed:.2f} segundos")
                return {
                    "firmante": "No firmado",
                    "emisor": "No firmado",
                    "valido_hasta": "",
                    "valido": False
                }

            print(f"    Encontradas {len(embedded_sigs)} firma(s)")
            sig = embedded_sigs[0]
            
            print("    Validando firma...")
            try:
                status = validate_pdf_signature(sig, reader)
                print(f"    Validación completada: {status.valid}")
            except Exception as e:
                print(f"    Error en validación: {e}")
                status = type('Status', (), {'valid': False})()

            cert = sig.signer_cert
            if cert:
                print("    Extrayendo certificado...")
                firmante = str(cert.subject.human_friendly) if hasattr(cert.subject, 'human_friendly') else "Desconocido"
                emisor = str(cert.issuer.human_friendly) if hasattr(cert.issuer, 'human_friendly') else "Desconocido"
                valido_hasta = cert.not_valid_after.strftime("%Y-%m-%d %H:%M:%S") if cert.not_valid_after else ""
                
                print(f"    Firmante: {firmante[:50]}...")
                elapsed = time.time() - start_time
                print(f"    ✅ Firma extraída en {elapsed:.2f} segundos")
                return {
                    "firmante": firmante,
                    "emisor": emisor,
                    "valido_hasta": valido_hasta,
                    "valido": status.valid
                }
            else:
                print("    Certificado no disponible")
                elapsed = time.time() - start_time
                print(f"    ✅ Proceso de firma completado en {elapsed:.2f} segundos")
                return {
                    "firmante": "Certificado no disponible",
                    "emisor": "Certificado no disponible",
                    "valido_hasta": "",
                    "valido": False
                }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"    Error general extrayendo firma en {elapsed:.2f} segundos: {e}")
        return {
            "firmante": "Error",
            "emisor": "Error",
            "valido_hasta": "",
            "valido": False
        }

def crear_db_access_completa():
    if not WIN32_AVAILABLE:
        print("❌ win32com no disponible para crear BD Access")
        return False
        
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        if os.path.exists(db_path):
            os.remove(db_path)
        
        db_path_abs = os.path.abspath(db_path)
        print(f"Creando BD en: {db_path_abs}")
        
        access_app = win32com.client.Dispatch("Access.Application")
        access_app.NewCurrentDatabase(db_path_abs)
        db = access_app.CurrentDb()
        
        tablas_sql = {
            'Firmas': '''
            CREATE TABLE Firmas (
                ID AUTOINCREMENT PRIMARY KEY,
                Archivo TEXT(255),
                Ayuntamiento TEXT(100),
                Prioridad TEXT(10),
                Firmante MEMO,
                Emisor MEMO,
                Valido_Hasta DATETIME,
                Firma_Valida YESNO,
                Fecha_Proceso DATETIME
            )
            ''',
            'Cuerpo_Tecnico': '''
            CREATE TABLE Cuerpo_Tecnico (
                ID AUTOINCREMENT PRIMARY KEY,
                Archivo TEXT(255),
                Ayuntamiento TEXT(100),
                Prioridad TEXT(10),
                NOMBRE TEXT(100),
                APELLIDOS TEXT(100),
                TELEFONO TEXT(20),
                EMAIL TEXT(100),
                Nom_Proyecto TEXT(255),
                ChkBox1 TEXT(10),
                URL TEXT(255),
                ChkBox2 TEXT(10),
                ChkBox3 TEXT(10),
                Red_Social1 TEXT(100),
                Red_Social2 TEXT(100),
                ChkBox4 TEXT(10),
                Imp_Total CURRENCY,
                Imp_Total_Solici CURRENCY,
                Firmante MEMO,
                Emisor MEMO,
                Valido_Hasta DATETIME,
                Firma_Valida YESNO,
                Fecha_Proceso DATETIME
            )
            ''',
            'Gastos_Globales': '''
            CREATE TABLE Gastos_Globales (
                ID AUTOINCREMENT PRIMARY KEY,
                Archivo TEXT(255),
                Ayuntamiento TEXT(100),
                Prioridad TEXT(10),
                Fila INTEGER,
                Tipo TEXT(50),
                Descripcion MEMO,
                Vertical TEXT(50),
                Sensores TEXT(50),
                Importe CURRENCY,
                Solicitado CURRENCY,
                Fecha_Proceso DATETIME
            )
            ''',
            'Gastos_Individuales': '''
            CREATE TABLE Gastos_Individuales (
                ID AUTOINCREMENT PRIMARY KEY,
                Archivo TEXT(255),
                Ayuntamiento TEXT(100),
                Prioridad TEXT(10),
                Fila INTEGER,
                Tipo TEXT(50),
                Descripcion MEMO,
                Vertical TEXT(50),
                Sensores TEXT(50),
                Importe CURRENCY,
                Solicitado CURRENCY,
                Fecha_Proceso DATETIME
            )
            '''
        }
        
        for nombre_tabla, sql in tablas_sql.items():
            try:
                db.Execute(sql)
                print(f"✅ Tabla {nombre_tabla} creada")
            except Exception as e:
                print(f"❌ Error creando tabla {nombre_tabla}: {e}")
        
        access_app.CloseCurrentDatabase()
        access_app.Quit()
        
        print("✅ Base de datos Access creada con todas las tablas")
        return True
    except Exception as e:
        print(f"❌ Error creando BD completa con COM: {e}")
        return False

class AccessDBManager:
    """Gestor de conexión única a Access para mejorar rendimiento"""
    def __init__(self, db_path):
        self.db_path = os.path.abspath(db_path)
        self.access_app = None
        self.db = None
        self.connected = False
    
    def connect(self):
        try:
            if not WIN32_AVAILABLE:
                return False
                
            self.access_app = win32com.client.Dispatch("Access.Application")
            self.access_app.OpenCurrentDatabase(self.db_path)
            self.db = self.access_app.CurrentDb()
            self.connected = True
            return True
        except Exception as e:
            print(f"❌ Error conectando a Access: {e}")
            return False
    
    def disconnect(self):
        try:
            if self.access_app:
                self.access_app.CloseCurrentDatabase()
                self.access_app.Quit()
        except:
            pass
        self.connected = False
    
    def insertar_registro(self, tabla, campos, valores):
        if not self.connected:
            return False
            
        try:
            valores_escaped = []
            for valor in valores:
                if valor is None or valor == "":
                    valores_escaped.append("NULL")
                elif isinstance(valor, bool):
                    valores_escaped.append("True" if valor else "False")
                elif isinstance(valor, (int, float)):
                    valores_escaped.append(str(valor))
                else:
                    texto = str(valor).replace('"', '""')
                    valores_escaped.append(f'"{texto}"')
            
            for i, campo in enumerate(campos):
                if "Fecha" in campo and valores_escaped[i] != "NULL":
                    if "Proceso" in campo:
                        valores_escaped[i] = f"#{datetime.now().strftime('%m/%d/%Y %H:%M:%S')}#"
            
            campos_str = ", ".join(campos)
            valores_str = ", ".join(valores_escaped)
            
            sql_insert = f'''
            INSERT INTO {tabla} ({campos_str})
            VALUES ({valores_str})
            '''
            
            self.db.Execute(sql_insert)
            return True
        except Exception as e:
            print(f"  Error insertando en {tabla}: {e}")
            return False

# Inicializar gestor de BD
db_manager = AccessDBManager(db_path)

def insertar_firma_db(datos_firma):
    campos = ["Archivo", "Ayuntamiento", "Prioridad", "Firmante", "Emisor", "Valido_Hasta", "Firma_Valida", "Fecha_Proceso"]
    valores = [
        datos_firma['archivo'],
        datos_firma['ayuntamiento'],
        datos_firma['prioridad'],
        datos_firma['firmante'],
        datos_firma['emisor'],
        datos_firma['valido_hasta'] if datos_firma['valido_hasta'] else None,
        datos_firma['valido'],
        datetime.now()
    ]
    return db_manager.insertar_registro("Firmas", campos, valores)

def insertar_datos_tecnicos(datos_tecnicos):
    campos = [
        "Archivo", "Ayuntamiento", "Prioridad", "NOMBRE", "APELLIDOS", "TELEFONO",
        "EMAIL", "Nom_Proyecto", "ChkBox1", "URL", "ChkBox2", "ChkBox3",
        "Red_Social1", "Red_Social2", "ChkBox4", "Imp_Total", "Imp_Total_Solici",
        "Firmante", "Emisor", "Valido_Hasta", "Firma_Valida", "Fecha_Proceso"
    ]
    valores = list(datos_tecnicos) + [datetime.now()]
    return db_manager.insertar_registro("Cuerpo_Tecnico", campos, valores)

def insertar_gasto_global(datos_gasto):
    campos = [
        "Archivo", "Ayuntamiento", "Prioridad", "Fila", "Tipo", "Descripcion",
        "Vertical", "Sensores", "Importe", "Solicitado", "Fecha_Proceso"
    ]
    valores = list(datos_gasto) + [datetime.now()]
    return db_manager.insertar_registro("Gastos_Globales", campos, valores)

def insertar_gasto_individual(datos_gasto):
    campos = [
        "Archivo", "Ayuntamiento", "Prioridad", "Fila", "Tipo", "Descripcion",
        "Vertical", "Sensores", "Importe", "Solicitado", "Fecha_Proceso"
    ]
    valores = list(datos_gasto) + [datetime.now()]
    return db_manager.insertar_registro("Gastos_Individuales", campos, valores)

# Inicializar CSVs
with open(csv_tecnico, "w", newline="", encoding="utf-8") as f:
    csv.writer(f, delimiter=";").writerow(campos_tecnicos)

with open(csv_global_gastos, "w", newline="", encoding="utf-8") as f:
    csv.writer(f, delimiter=";").writerow(campos_gastos)

# Crear base de datos Access
if not crear_db_access_completa():
    print("ADVERTENCIA: No se pudo crear base de datos Access")

# Conectar gestor de BD
if not db_manager.connect():
    print("❌ No se pudo conectar a la base de datos")
    exit(1)

# Procesar PDFs
for archivo in os.listdir(entrada):
    if not archivo.lower().endswith(".pdf"):
        continue

    total_formularios += 1
    print(f"\nProcesando: {archivo}")
    start_time = time.time()
    ruta = os.path.join(entrada, archivo)

    try:
        # Extraer firma digital
        print(f"  Extrayendo firma digital...")
        firma_info = extraer_firma_digital(ruta)
        
        if firma_info['firmante'] != "No firmado":
            formularios_firmados += 1
        else:
            formularios_sin_firma += 1

        # Extraer campos del formulario
        campos = extraer_campos_fitx(ruta)
        ayuntamiento, prioridad = extraer_ayuntamiento_prioridad(archivo)

        # Guardar firma en base de datos
        datos_db = {
            'archivo': archivo,
            'ayuntamiento': ayuntamiento,
            'prioridad': prioridad,
            'firmante': firma_info['firmante'],
            'emisor': firma_info['emisor'],
            'valido_hasta': firma_info['valido_hasta'],
            'valido': firma_info['valido']
        }
        insertar_firma_db(datos_db)

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
            campos.get("Imp_Total_Solici", ""),
            firma_info['firmante'],
            firma_info['emisor'],
            firma_info['valido_hasta'],
            firma_info['valido']
        ]

        # Guardar en CSV técnico
        with open(csv_tecnico, "a", newline="", encoding="utf-8") as f:
            csv.writer(f, delimiter=";").writerow(fila_tecnica)

        # Guardar en BD técnica
        insertar_datos_tecnicos(fila_tecnica)

        # CSV individual y procesamiento de gastos
        nombre_csv_individual = os.path.join(salida, archivo.replace(".pdf", ".csv"))

        with open(nombre_csv_individual, "w", newline="", encoding="utf-8") as f_indiv:
            writer_indiv = csv.writer(f_indiv, delimiter=";")
            writer_indiv.writerow(campos_gastos)

            filas_procesadas = 0
            gastos_start_time = time.time()
            print(f"  Procesando filas de gastos...")
            
            for i in range(1, 100):
                tipo = campos.get(f"T1_{i}1", "")
                descripcion = campos.get(f"T1_{i}2", "")
                vertical = campos.get(f"T1_{i}3", "")
                sensores = campos.get(f"T1_{i}4", "")
                importe = campos.get(f"T1_{i}5", "")
                solicitado = campos.get(f"T1_{i}6", "")

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

                # Guardar en CSV individual
                writer_indiv.writerow(fila_gasto)
                
                # Guardar en CSV global
                with open(csv_global_gastos, "a", newline="", encoding="utf-8") as f_global:
                    csv.writer(f_global, delimiter=";").writerow(fila_gasto)

                # Guardar en BD (ambas tablas)
                insertar_gasto_global(fila_gasto)
                insertar_gasto_individual(fila_gasto)

                filas_procesadas += 1
                total_gastos += 1

            gastos_elapsed = time.time() - gastos_start_time
            print(f"  ✅ {filas_procesadas} filas de gastos procesadas en {gastos_elapsed:.2f} segundos")

            # Mostrar resumen del archivo
            archivo_elapsed = time.time() - start_time
            print(f"  📊 Resumen {archivo}: {filas_procesadas} gastos, {archivo_elapsed:.1f}s")
            print(f"  👤 Firmante: {firma_info['firmante'][:30]}...")
            print(f"  ✅ Firma válida: {firma_info['valido']}")

    except Exception as e:
        print(f"❌ Error procesando {archivo}: {e}")
        continue

# Desconectar BD
db_manager.disconnect()

# RESUMEN FINAL
print("\n" + "="*60)
print("✅ PROCESAMIENTO COMPLETADO")
print("="*60)
print(f"📊 Estadísticas finales:")
print(f"   • Formularios procesados: {total_formularios}")
print(f"   • Filas de gastos totales: {total_gastos}")
print(f"   • Formularios con firma: {formularios_firmados}")
print(f"   • Formularios sin firma: {formularios_sin_firma}")
print(f"📂 Archivos generados:")
print(f"   • {csv_tecnico}")
print(f"   • {csv_global_gastos}")
if os.path.exists(db_path):
    print(f"   • Base de datos: {db_path}")
print(f"📁 CSVs individuales en '{salida}'")
print("="*60)