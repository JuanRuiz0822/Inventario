#!/usr/bin/env python3
"""
Script de prueba específico para Google Sheets
ID: 1E68HmwdDy8TuP3FH9KCJbv6TnZ6-tj0i
"""

import os
import sys
from pathlib import Path

def test_connection():
    print("🔍 PROBANDO CONEXIÓN CON TU GOOGLE SHEET")
    print("=" * 50)
    
    # Configuración específica
    CREDENTIALS_FILE = "backend/credentials.json"
    SHEET_ID = "1E68HmwdDy8TuP3FH9KCJbv6TnZ6-tj0i"
    
    # Verificar archivos
    print(f"📁 Verificando: {CREDENTIALS_FILE}")
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ No encontrado: {CREDENTIALS_FILE}")
        return False
    
    print(f"✅ Archivo de credenciales encontrado")
    print(f"📊 ID de Google Sheet: {SHEET_ID}")
    print()
    
    try:
        # Importar dependencias
        print("📦 Importando dependencias...")
        import gspread
        from google.oauth2.service_account import Credentials
        print("✅ Dependencias importadas")
        
        # Configurar credenciales
        print("🔐 Configurando credenciales...")
        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        print("✅ Cliente autorizado")
        
        # Conectar a la hoja específica
        print("🔗 Conectando a tu Google Sheet...")
        sheet = client.open_by_key(SHEET_ID)
        print(f"✅ Conectado exitosamente a: '{sheet.title}'")
        
        # Listar todas las hojas
        worksheets = sheet.worksheets()
        print(f"\n📋 Hojas disponibles en tu documento ({len(worksheets)}):")
        for i, ws in enumerate(worksheets, 1):
            print(f"   {i}. '{ws.title}' (ID: {ws.id}, {ws.row_count}x{ws.col_count})")
        
        # Probar con la primera hoja
        if worksheets:
            worksheet = worksheets[0]
            print(f"\n🔍 Analizando hoja: '{worksheet.title}'")
            
            try:
                # Leer todos los valores
                all_values = worksheet.get_all_values()
                print(f"✅ Datos leídos: {len(all_values)} filas")
                
                if len(all_values) > 0:
                    print(f"📊 Primera fila: {all_values[0]}")
                    if len(all_values) > 1:
                        print(f"📊 Datos disponibles: {len(all_values)-1} registros")
                        print(f"📊 Ejemplo registro: {all_values[1][:5]}...")
                else:
                    print("⚠️  La hoja está vacía")
                    
            except Exception as read_error:
                print(f"⚠️  Error leyendo datos: {read_error}")
        
        print(f"\n🎉 ¡CONEXIÓN EXITOSA!")
        print(f"✅ Tu Google Sheet está accesible")
        print(f"✅ Las credenciales funcionan correctamente")
        print(f"✅ La sincronización debería funcionar")
        
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print(f"\n🔧 POSIBLES SOLUCIONES:")
        print(f"   1. Verificar que la hoja está compartida con:")
        print(f"      sync-inventario@inventariosync.iam.gserviceaccount.com")
        print(f"   2. Verificar que los permisos son de 'Editor'")
        print(f"   3. Verificar que el archivo credentials.json es correcto")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print(f"\n🚀 PRÓXIMO PASO:")
        print(f"   1. Reiniciar servidor: ./manage.sh dev")
        print(f"   2. Probar en: http://localhost:8000/admin.html")
    else:
        print(f"\n🔧 CORREGIR PROBLEMAS ANTES DE CONTINUAR")
