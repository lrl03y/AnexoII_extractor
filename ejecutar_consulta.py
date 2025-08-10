#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===============================================================================
📊 EJECUTOR DE CONSULTAS SQL PARA BASE DE DATOS ACCESS ANEXO II
===============================================================================

🎯 Descripción:
Script que ejecuta consultas SQL directamente en la BD Access del proyecto
AnexoII_extractor y muestra los resultados formateados.

⚠️  IMPORTANTE - INSTRUCCIONES DE USO:
   🔸 Copia las consultas SQL en una sola línea (sin saltos)
   🔸 No copies consultas con formato multilínea
   🔸 Asegúrate de terminar con punto y coma (;)
   🔸 Evita funciones no compatibles con Access (COUNT(DISTINCT), etc.)

🔧 Requisitos:
- Base de datos Access en: resultados/firmas.accdb
- win32com.client instalado
- Microsoft Access (opcional para mejor rendimiento)

💡 Uso:
1. Recibe SQL generado por IA (en una sola línea)
2. Ejecuta la consulta en BD Access
3. Muestra resultados formateados

📅 Autor: Asistente IA del proyecto AnexoII_extractor
===============================================================================
"""

import os
import sys
from datetime import datetime

try:
    import win32com.client
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("❌ Error: win32com no disponible")
    print("💡 Instala con: pip install pywin32")
    sys.exit(1)

class AccessQueryExecutor:
    """Ejecutor de consultas SQL en Access"""
    
    def __init__(self, db_path="resultados/firmas.accdb"):
        self.db_path = os.path.abspath(db_path)
        self.access_app = None
        self.db = None
        self.connected = False
        self.connect()
    
    def connect(self):
        """Conecta a la base de datos Access"""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ Base de datos no encontrada: {self.db_path}")
                return False
                
            self.access_app = win32com.client.Dispatch("Access.Application")
            self.access_app.OpenCurrentDatabase(self.db_path)
            self.db = self.access_app.CurrentDb()
            self.connected = True
            print(f"✅ Conectado a: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Error conectando a Access: {e}")
            return False
    
    def disconnect(self):
        """Desconecta de la base de datos"""
        try:
            if self.access_app:
                self.access_app.CloseCurrentDatabase()
                self.access_app.Quit()
        except:
            pass
        self.connected = False
    
    def ejecutar_consulta(self, sql):
        """Ejecuta una consulta SQL y devuelve resultados"""
        if not self.connected:
            print("❌ No hay conexión a la base de datos")
            return None
            
        try:
            print(f"\n🔍 Ejecutando consulta...")
            print(f"📝 SQL: {sql}")
            
            # Ejecutar consulta
            recordset = self.db.OpenRecordset(sql)
            
            # Obtener nombres de campos
            campos = []
            for i in range(recordset.Fields.Count):
                campos.append(recordset.Fields(i).Name)
            
            # Obtener datos
            resultados = []
            if not recordset.BOF:  # Si no está al principio (hay datos)
                recordset.MoveFirst()
                
                while not recordset.EOF:
                    fila = []
                    for i in range(recordset.Fields.Count):
                        valor = recordset.Fields(i).Value
                        # Formatear valores None/null
                        if valor is None:
                            fila.append("NULL")
                        elif isinstance(valor, datetime):
                            fila.append(valor.strftime("%Y-%m-%d %H:%M:%S"))
                        else:
                            fila.append(str(valor))
                    resultados.append(fila)
                    recordset.MoveNext()
            
            recordset.Close()
            
            return {
                'campos': campos,
                'resultados': resultados,
                'total_filas': len(resultados)
            }
            
        except Exception as e:
            print(f"❌ Error ejecutando consulta: {e}")
            # Mostrar consulta problemática
            print(f"📝 Consulta que falló: {sql}")
            return None
    
    def mostrar_resultados(self, resultado):
        """Muestra resultados formateados"""
        if not resultado:
            print("❌ No hay resultados para mostrar")
            return
            
        campos = resultado['campos']
        resultados = resultado['resultados']
        total_filas = resultado['total_filas']
        
        if total_filas == 0:
            print(f"\n📊 RESULTADOS: 0 filas encontradas")
            return
            
        print(f"\n📊 RESULTADOS ({total_filas} filas encontradas)")
        print("=" * 80)
        
        # Calcular ancho de columnas
        anchos = []
        for i, campo in enumerate(campos):
            max_ancho = len(str(campo))
            for fila in resultados:
                if i < len(fila):
                    max_ancho = max(max_ancho, len(str(fila[i])))
            anchos.append(min(max_ancho, 30))  # Máximo 30 caracteres por columna
        
        # Mostrar cabecera
        cabecera = " | ".join(f"{campo:<{anchos[i]}}" for i, campo in enumerate(campos))
        print(cabecera)
        print("-" * len(cabecera))
        
        # Mostrar resultados
        for fila in resultados:
            linea = " | ".join(f"{str(fila[i])[:anchos[i]]:<{anchos[i]}}" if i < len(fila) else f"{'':<{anchos[i]}}" for i in range(len(campos)))
            print(linea)
        
        print("=" * 80)

def mostrar_menu():
    """Muestra menú de opciones"""
    print("\n" + "📊 EJECUTOR DE CONSULTAS SQL".center(60, "="))
    print("1. 📝 Ejecutar consulta SQL")
    print("2. 📋 Ver estructura de tablas")
    print("3. 🎯 Consultas de ejemplo (COMPATIBLES)")
    print("4. ❌ Salir")
    print("=" * 60)

def mostrar_estructura_tablas():
    """Muestra estructura básica de las tablas"""
    estructura = {
        "Firmas": [
            "ID (AutoNum)", "Archivo (Texto255)", "Ayuntamiento (Texto100)", 
            "Prioridad (Texto10)", "Firmante (Memo)", "Emisor (Memo)",
            "Valido_Hasta (Fecha/Hora)", "Firma_Valida (Sí/No)", "Fecha_Proceso (Fecha/Hora)"
        ],
        "Cuerpo_Tecnico": [
            "ID (AutoNum)", "Archivo (Texto255)", "Ayuntamiento (Texto100)",
            "NOMBRE (Texto100)", "APELLIDOS (Texto100)", "EMAIL (Texto100)",
            "Nom_Proyecto (Texto255)", "Imp_Total (Moneda)", "Firma_Valida (Sí/No)"
        ],
        "Gastos_Globales": [
            "ID (AutoNum)", "Archivo (Texto255)", "Ayuntamiento (Texto100)",
            "Fila (Número)", "Tipo (Texto50)", "Descripcion (Memo)",
            "Importe (Moneda)", "Solicitado (Moneda)", "Fecha_Proceso (Fecha/Hora)"
        ]
    }
    
    print("\n📋 ESTRUCTURA DE TABLAS:")
    for tabla, campos in estructura.items():
        print(f"\n📊 {tabla}:")
        for campo in campos:
            print(f"   • {campo}")

def mostrar_consultas_ejemplo():
    """Muestra consultas de ejemplo COMPATIBLES con Access"""
    ejemplos = [
        ("✅ Contar todos los formularios:", "SELECT COUNT(*) AS Total FROM Firmas;"),
        ("✅ Formularios con firma válida:", "SELECT Archivo, Ayuntamiento FROM Firmas WHERE Firma_Valida = True;"),
        ("✅ Gastos por ayuntamiento (COUNT compatible):", "SELECT Ayuntamiento, COUNT(*) AS Total_Gastos FROM Gastos_Globales GROUP BY Ayuntamiento;"),
        ("✅ Top 5 gastos más caros:", "SELECT TOP 5 Archivo, Importe FROM Gastos_Globales ORDER BY Importe DESC;"),
        ("✅ Total importe por ayuntamiento:", "SELECT Ayuntamiento, SUM(Importe) AS Total_Importe FROM Gastos_Globales GROUP BY Ayuntamiento;"),
        ("✅ Contar ayuntamientos distintos (subconsulta):", "SELECT COUNT(*) AS Num_Ayuntamientos FROM (SELECT DISTINCT Ayuntamiento FROM Gastos_Globales WHERE Importe > 1000);"),
        ("✅ Gastos mayores de 1000 ordenados:", "SELECT Ayuntamiento, Importe FROM Gastos_Globales WHERE Importe > 1000 ORDER BY Importe DESC;"),
        ("✅ Promedio de importes:", "SELECT AVG(Importe) AS Promedio_Importe FROM Gastos_Globales;")
    ]
    
    print("\n🎯 CONSULTAS DE EJEMPLO (COMPATIBLES CON ACCESS):")
    print("⚠️  RECUERDA: Copia en una sola línea sin saltos")
    for descripcion, sql in ejemplos:
        print(f"\n{descripcion}")
        print(f"   {sql}")

def main():
    """Función principal"""
    print("🚀 Ejecutor de Consultas SQL para BD Access AnexoII")
    print("⚠️  RECUERDA: Copia las consultas en una sola línea")
    
    # Inicializar ejecutor
    executor = AccessQueryExecutor()
    
    if not executor.connected:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        while True:
            mostrar_menu()
            opcion = input("\n🔢 Opción (1-4): ").strip()
            
            if opcion == "1":
                print("\n📝 Introduce tu consulta SQL")
                print("💡 Usa ';' al final")
                print("⚠️  COPIA EN UNA SOLA LÍNEA (sin saltos)")
                print("⚠️  NO uses COUNT(DISTINCT ...) - usa subconsultas")
                
                sql = input("\n🔍 SQL: ").strip()
                if sql:
                    if not sql.endswith(';'):
                        sql += ';'
                    
                    resultado = executor.ejecutar_consulta(sql)
                    if resultado:
                        executor.mostrar_resultados(resultado)
                    else:
                        print("❌ Error ejecutando la consulta")
                        print("💡 Prueba con una consulta de ejemplo (opción 3)")
                        
            elif opcion == "2":
                mostrar_estructura_tablas()
                
            elif opcion == "3":
                mostrar_consultas_ejemplo()
                
            elif opcion == "4":
                print("👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción no válida")
                
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego! (Interrumpido)")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        executor.disconnect()

if __name__ == "__main__":
    main()