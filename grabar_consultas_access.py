#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
💾 GRABADOR DE CONSULTAS EN ACCESS
===============================================================================

🎯 Descripción:
Script que graba consultas SQL permanentemente en la BD Access.
NO genera informes Word (evita problemas de compatibilidad).

💡 Uso:
1. Introduce consulta SQL
2. Se graba permanentemente en Access
3. Puedes ejecutarla desde Access manualmente
4. Puedes exportar resultados a CSV posteriormente

📅 Autor: Asistente IA del proyecto AnexoII_extractor
===============================================================================
"""

import os
import sys
import csv
from datetime import datetime

try:
    import win32com.client
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("❌ Error: win32com no disponible")
    print("💡 Instala con: pip install pywin32")
    sys.exit(1)

class AccessQuerySaver:
    """Grabador de consultas en Access"""
    
    def __init__(self, db_path="resultados/firmas.accdb"):
        self.db_path = os.path.abspath(db_path)
        self.access_app = None
        self.db = None
        self.connected = False
        
    def connect_access(self):
        """Conecta a la base de datos Access"""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ Base de datos no encontrada: {self.db_path}")
                return False
                
            print("🔍 Conectando a Access...")
            self.access_app = win32com.client.Dispatch("Access.Application")
            self.access_app.OpenCurrentDatabase(self.db_path)
            self.db = self.access_app.CurrentDb()
            self.connected = True
            print(f"✅ Conectado a: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Error conectando a Access: {e}")
            return False
    
    def disconnect_access(self):
        """Desconecta de Access"""
        try:
            if self.access_app:
                self.access_app.CloseCurrentDatabase()
                self.access_app.Quit()
                print("✅ Conexión a Access cerrada")
        except:
            pass
        self.connected = False
    
    def grabar_consulta(self, nombre_consulta, sql):
        """Graba consulta permanentemente en Access"""
        if not self.connected:
            print("❌ No hay conexión a Access")
            return False
            
        try:
            # Limpiar nombre de consulta
            nombre_limpio = "".join(c for c in nombre_consulta if c.isalnum() or c in "_")
            if not nombre_limpio or nombre_limpio[0].isdigit():
                nombre_limpio = f"Consulta_{int(datetime.now().timestamp())}"
            
            # Limpiar SQL
            sql_limpio = sql.strip()
            if not sql_limpio.endswith(';'):
                sql_limpio += ';'
            
            # Eliminar consulta si ya existe
            try:
                self.db.QueryDefs.Delete(nombre_limpio)
                print(f"🔄 Reemplazando consulta existente: {nombre_limpio}")
            except:
                pass
            
            # Crear nueva consulta
            query_def = self.db.CreateQueryDef(nombre_limpio, sql_limpio)
            query_def.Close()
            print(f"✅ Consulta grabada en Access: {nombre_limpio}")
            return True
        except Exception as e:
            print(f"❌ Error grabando consulta: {e}")
            return False
    
    def ejecutar_y_exportar_csv(self, sql, nombre_archivo_csv=None):
        """Ejecuta consulta y exporta resultados a CSV"""
        if not self.connected:
            print("❌ No hay conexión a Access")
            return False
            
        try:
            print("🔍 Ejecutando consulta...")
            
            recordset = self.db.OpenRecordset(sql)
            
            # Obtener campos
            campos = []
            for i in range(recordset.Fields.Count):
                campos.append(recordset.Fields(i).Name)
            
            # Obtener datos
            resultados = []
            if not recordset.BOF:
                recordset.MoveFirst()
                while not recordset.EOF:
                    fila = []
                    for i in range(recordset.Fields.Count):
                        valor = recordset.Fields(i).Value
                        if valor is None:
                            fila.append("")
                        else:
                            fila.append(str(valor))
                    resultados.append(fila)
                    recordset.MoveNext()
            
            recordset.Close()
            
            print(f"✅ Consulta ejecutada: {len(resultados)} filas encontradas")
            
            # Exportar a CSV
            if not nombre_archivo_csv:
                nombre_archivo_csv = f"export_{int(datetime.now().timestamp())}.csv"
            
            ruta_csv = os.path.join("resultados", nombre_archivo_csv)
            if not ruta_csv.endswith('.csv'):
                ruta_csv += '.csv'
            
            with open(ruta_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(campos)  # Cabecera
                writer.writerows(resultados)  # Datos
            
            print(f"✅ Resultados exportados a: {ruta_csv}")
            print(f"📊 Total de filas: {len(resultados)}")
            return True
            
        except Exception as e:
            print(f"❌ Error ejecutando consulta o exportando CSV: {e}")
            return False
    
    def mostrar_consultas_grabadas(self):
        """Muestra consultas grabadas"""
        if not self.connected:
            print("❌ No hay conexión a Access")
            return []
            
        try:
            print("\n📋 CONSULTAS GRABADAS:")
            print("=" * 50)
            querydefs = self.db.QueryDefs
            consultas = []
            
            for i in range(querydefs.Count):
                query = querydefs(i)
                if not query.Name.startswith("~") and not query.Name.startswith("MSys"):
                    consultas.append(query)
                    sql_preview = query.SQL[:60] + "..." if len(query.SQL) > 60 else query.SQL
                    print(f"📊 {query.Name}")
                    print(f"   {sql_preview}")
                    print()
            
            if not consultas:
                print("No hay consultas grabadas.")
            
            return consultas
            
        except Exception as e:
            print(f"❌ Error mostrando consultas: {e}")
            return []

def main():
    """Función principal"""
    print("💾 GRABADOR DE CONSULTAS EN ACCESS")
    print("=" * 40)
    
    # Crear carpeta resultados
    if not os.path.exists("resultados"):
        os.makedirs("resultados")
    
    # Inicializar grabador
    grabador = AccessQuerySaver()
    
    # Conectar a Access
    if not grabador.connect_access():
        print("❌ No se pudo conectar a Access")
        return
    
    try:
        while True:
            print("\n" + "📋 MENÚ PRINCIPAL".center(40, "="))
            print("1. 💾 Grabar nueva consulta")
            print("2. 📋 Ver consultas grabadas")
            print("3. 📤 Ejecutar consulta y exportar a CSV")
            print("4. ❌ Salir")
            print("=" * 40)
            
            opcion = input("\nOpción (1-4): ").strip()
            
            if opcion == "1":
                print("\n📝 Introduce consulta SQL:")
                sql = input("SQL: ").strip()
                
                if sql:
                    sql = sql.split('--')[0].strip()  # Eliminar comentarios
                    if not sql.endswith(';'):
                        sql += ';'
                    
                    nombre = input("Nombre para la consulta: ").strip()
                    if not nombre:
                        nombre = f"Consulta_{int(datetime.now().timestamp())}"
                    
                    if grabador.grabar_consulta(nombre, sql):
                        print("✅ Consulta grabada correctamente")
                        print("💡 Ahora puedes ejecutarla desde Access")
                    else:
                        print("❌ Error grabando consulta")
                        
            elif opcion == "2":
                grabador.mostrar_consultas_grabadas()
                
            elif opcion == "3":
                print("\n📝 Introduce consulta SQL para ejecutar:")
                sql = input("SQL: ").strip()
                
                if sql:
                    sql = sql.split('--')[0].strip()
                    if not sql.endswith(';'):
                        sql += ';'
                    
                    nombre_csv = input("Nombre archivo CSV (sin .csv): ").strip()
                    if not nombre_csv:
                        nombre_csv = f"export_{int(datetime.now().timestamp())}"
                    
                    if grabador.ejecutar_y_exportar_csv(sql, nombre_csv):
                        print("✅ Consulta ejecutada y resultados exportados")
                    else:
                        print("❌ Error ejecutando consulta")
                        
            elif opcion == "4":
                print("👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción no válida")
                
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        grabador.disconnect_access()

if __name__ == "__main__":
    main()