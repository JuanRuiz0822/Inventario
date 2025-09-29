#!/usr/bin/env python3
"""
ANÁLISIS COMPLETO FINAL DEL SISTEMA
Verificación exhaustiva de estado funcional y configuración
"""

import os
import sys
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

class AnalisisCompletoFinal:
    def __init__(self):
        self.ruta_proyecto = Path.cwd()
        self.estado_sistema = {
            "estructura": {},
            "configuracion": {},
            "dependencias": {},
            "sintaxis": {},
            "conexion_sheets": {},
            "funcionalidad": {}
        }
        self.errores_criticos = []
        self.advertencias = []
        self.puntaje_total = 0
        
    def imprimir_cabecera(self):
        print("🔍 ANÁLISIS COMPLETO FINAL DEL SISTEMA")
        print("=" * 70)
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Directorio: {self.ruta_proyecto}")
        print(f"🎯 Objetivo: Verificar funcionalidad completa")
        print(f"🔗 Google Sheet: 1tCILvM3VkaACJMNnTZu4ZYM3x81HcoTlg6uoj-K6RRQ")
        print()

    def verificar_estructura_proyecto(self):
        """Verificar estructura completa del proyecto"""
        print("📁 VERIFICANDO ESTRUCTURA DEL PROYECTO")
        print("-" * 45)
        
        estructura_critica = {
            "backend/": ("directorio", "Directorio principal del backend"),
            "backend/app.py": ("archivo", "Aplicación FastAPI principal"),
            "backend/credentials.json": ("archivo", "Credenciales Google Sheets"),
            ".env": ("archivo", "Variables de entorno"),
            ".venv/": ("directorio", "Entorno virtual Python"),
            "frontend/": ("directorio", "Directorio frontend"),
            "frontend/admin.html": ("archivo", "Panel administrativo"),
            "manage.sh": ("archivo", "Script de gestión"),
        }
        
        estructura_opcional = {
            "requirements.txt": ("archivo", "Dependencias Python"),
            "README.md": ("archivo", "Documentación"),
            "frontend/style.css": ("archivo", "Estilos CSS"),
        }
        
        puntaje_estructura = 0
        max_puntaje_estructura = len(estructura_critica) * 10
        
        print("📋 ARCHIVOS CRÍTICOS:")
        for ruta, (tipo, descripcion) in estructura_critica.items():
            ruta_completa = self.ruta_proyecto / ruta
            existe = ruta_completa.exists()
            
            if existe:
                if (tipo == "directorio" and ruta_completa.is_dir()) or (tipo == "archivo" and ruta_completa.is_file()):
                    print(f"✅ {ruta:<25} - {descripcion}")
                    puntaje_estructura += 10
                    self.estado_sistema["estructura"][ruta] = "OK"
                else:
                    print(f"⚠️  {ruta:<25} - Tipo incorrecto")
                    self.estado_sistema["estructura"][ruta] = "TIPO_INCORRECTO"
                    self.advertencias.append(f"Tipo incorrecto: {ruta}")
            else:
                print(f"❌ {ruta:<25} - FALTANTE")
                self.estado_sistema["estructura"][ruta] = "FALTANTE"
                self.errores_criticos.append(f"Archivo crítico faltante: {ruta}")
        
        print(f"\n📋 ARCHIVOS OPCIONALES:")
        for ruta, (tipo, descripcion) in estructura_opcional.items():
            ruta_completa = self.ruta_proyecto / ruta
            existe = ruta_completa.exists()
            
            if existe:
                print(f"✅ {ruta:<25} - {descripcion}")
                puntaje_estructura += 2
            else:
                print(f"⚠️  {ruta:<25} - Opcional")
        
        print(f"\n📊 Puntaje Estructura: {puntaje_estructura}/{max_puntaje_estructura + len(estructura_opcional) * 2}")
        self.estado_sistema["estructura"]["puntaje"] = puntaje_estructura
        print()

    def verificar_configuracion_archivos(self):
        """Verificar configuración de archivos clave"""
        print("🔧 VERIFICANDO CONFIGURACIÓN DE ARCHIVOS")
        print("-" * 45)
        
        puntaje_config = 0
        
        # Verificar .env
        print("📄 Archivo .env:")
        ruta_env = self.ruta_proyecto / ".env"
        if ruta_env.exists():
            try:
                with open(ruta_env, 'r', encoding='utf-8') as f:
                    contenido_env = f.read()
                
                configuraciones_env = {
                    "GOOGLE_SHEET_ID=1tCILvM3VkaACJMNnTZu4ZYM3x81HcoTlg6uoj-K6RRQ": "Sheet ID correcto",
                    "GOOGLE_CREDENTIALS_PATH=backend/credentials.json": "Ruta credenciales",
                    "DEBUG=true": "Modo debug"
                }
                
                for config, descripcion in configuraciones_env.items():
                    if config in contenido_env:
                        print(f"   ✅ {descripcion}")
                        puntaje_config += 10
                    else:
                        print(f"   ❌ {descripcion} - FALTANTE")
                        self.errores_criticos.append(f".env: {descripcion} faltante")
                        
            except Exception as e:
                print(f"   ❌ Error leyendo .env: {e}")
                self.errores_criticos.append(f"Error leyendo .env: {e}")
        else:
            print("   ❌ Archivo .env no existe")
            self.errores_criticos.append("Archivo .env faltante")
        
        # Verificar credentials.json
        print("\n🔑 Archivo credentials.json:")
        ruta_creds = self.ruta_proyecto / "backend" / "credentials.json"
        if ruta_creds.exists():
            try:
                with open(ruta_creds, 'r', encoding='utf-8') as f:
                    credentials = json.load(f)
                
                campos_criticos = ["type", "project_id", "private_key", "client_email"]
                campos_presentes = [campo for campo in campos_criticos if campo in credentials and credentials[campo]]
                
                if len(campos_presentes) == len(campos_criticos):
                    print("   ✅ Todas las credenciales presentes")
                    print(f"   📧 Email servicio: {credentials.get('client_email')}")
                    print(f"   🏗️  Proyecto: {credentials.get('project_id')}")
                    puntaje_config += 20
                else:
                    faltantes = [c for c in campos_criticos if c not in campos_presentes]
                    print(f"   ❌ Campos faltantes: {faltantes}")
                    self.errores_criticos.append(f"Credentials incompleto: {faltantes}")
                    
            except json.JSONDecodeError:
                print("   ❌ JSON inválido")
                self.errores_criticos.append("credentials.json formato inválido")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.errores_criticos.append(f"Error credentials.json: {e}")
        else:
            print("   ❌ Archivo credentials.json no existe")
            self.errores_criticos.append("credentials.json faltante")
        
        print(f"\n📊 Puntaje Configuración: {puntaje_config}/50")
        self.estado_sistema["configuracion"]["puntaje"] = puntaje_config
        print()

    def verificar_dependencias_python(self):
        """Verificar dependencias de Python"""
        print("📦 VERIFICANDO DEPENDENCIAS PYTHON")
        print("-" * 35)
        
        dependencias_criticas = {
            "fastapi": "Framework web",
            "uvicorn": "Servidor ASGI", 
            "gspread": "Google Sheets API",
            "google.auth": "Autenticación Google",
            "dotenv": "Variables entorno",
            "sqlalchemy": "ORM base datos",
            "pydantic": "Validación datos"
        }
        
        puntaje_deps = 0
        deps_instaladas = 0
        
        for dep, descripcion in dependencias_criticas.items():
            try:
                if dep == "google.auth":
                    from google.oauth2.service_account import Credentials
                elif dep == "dotenv":
                    from dotenv import load_dotenv
                else:
                    __import__(dep.replace('-', '_'))
                
                print(f"✅ {dep:<15} - {descripcion}")
                puntaje_deps += 10
                deps_instaladas += 1
                
            except ImportError:
                print(f"❌ {dep:<15} - NO INSTALADO")
                self.errores_criticos.append(f"Dependencia faltante: {dep}")
        
        print(f"\n📊 Dependencias instaladas: {deps_instaladas}/{len(dependencias_criticas)}")
        print(f"📊 Puntaje Dependencias: {puntaje_deps}/{len(dependencias_criticas) * 10}")
        self.estado_sistema["dependencias"]["puntaje"] = puntaje_deps
        print()

    def verificar_sintaxis_backend(self):
        """Verificar sintaxis de backend/app.py"""
        print("🐍 VERIFICANDO SINTAXIS BACKEND")
        print("-" * 32)
        
        ruta_app = self.ruta_proyecto / "backend" / "app.py"
        puntaje_sintaxis = 0
        
        if not ruta_app.exists():
            print("❌ backend/app.py no existe")
            self.errores_criticos.append("backend/app.py faltante")
            self.estado_sistema["sintaxis"]["puntaje"] = 0
            return
        
        try:
            # Verificar sintaxis
            with open(ruta_app, 'r', encoding='utf-8') as f:
                contenido_app = f.read()
            
            print(f"📄 Tamaño archivo: {len(contenido_app):,} caracteres")
            
            # Compilar para verificar sintaxis
            try:
                compile(contenido_app, str(ruta_app), 'exec')
                print("✅ Sintaxis correcta")
                puntaje_sintaxis += 20
            except SyntaxError as e:
                print(f"❌ Error sintaxis línea {e.lineno}: {e.text}")
                print(f"   Error: {e.msg}")
                self.errores_criticos.append(f"Error sintaxis línea {e.lineno}: {e.msg}")
                return
            
            # Verificar imports necesarios
            imports_necesarios = [
                ("from fastapi import FastAPI", "FastAPI framework"),
                ("import gspread", "Google Sheets"),
                ("from google.oauth2.service_account import Credentials", "Google Auth"),
                ("from dotenv import load_dotenv", "Variables entorno")
            ]
            
            print("\n📦 Verificando imports críticos:")
            for import_texto, descripcion in imports_necesarios:
                if import_texto in contenido_app:
                    print(f"   ✅ {descripcion}")
                    puntaje_sintaxis += 5
                else:
                    print(f"   ❌ {descripcion} - FALTANTE")
                    self.errores_criticos.append(f"Import faltante: {descripcion}")
            
            # Verificar funciones críticas
            funciones_criticas = [
                ("def get_google_sheet_data():", "Función Google Sheets"),
                ("@app.get(", "Endpoints API"),
                ("app = FastAPI(", "Instancia FastAPI")
            ]
            
            print("\n🔗 Verificando funciones críticas:")
            for funcion, descripcion in funciones_criticas:
                if funcion in contenido_app:
                    print(f"   ✅ {descripcion}")
                    puntaje_sintaxis += 5
                else:
                    print(f"   ❌ {descripcion} - FALTANTE")
                    self.errores_criticos.append(f"Función faltante: {descripcion}")
            
            # Verificar Sheet ID
            sheet_id_correcto = "1tCILvM3VkaACJMNnTZu4ZYM3x81HcoTlg6uoj-K6RRQ"
            if sheet_id_correcto in contenido_app:
                print("   ✅ Sheet ID correcto")
                puntaje_sintaxis += 10
            else:
                print("   ❌ Sheet ID incorrecto/faltante")
                self.advertencias.append("Sheet ID necesita verificación")
            
        except Exception as e:
            print(f"❌ Error verificando app.py: {e}")
            self.errores_criticos.append(f"Error verificando app.py: {e}")
        
        print(f"\n📊 Puntaje Sintaxis: {puntaje_sintaxis}/60")
        self.estado_sistema["sintaxis"]["puntaje"] = puntaje_sintaxis
        print()

    def probar_conexion_google_sheets(self):
        """Probar conexión real con Google Sheets"""
        print("🔗 PROBANDO CONEXIÓN GOOGLE SHEETS")
        print("-" * 37)
        
        puntaje_conexion = 0
        
        try:
            # Verificar archivos necesarios
            if not (self.ruta_proyecto / ".env").exists():
                print("❌ Archivo .env faltante para conexión")
                self.estado_sistema["conexion_sheets"]["puntaje"] = 0
                return
            
            if not (self.ruta_proyecto / "backend" / "credentials.json").exists():
                print("❌ Credenciales faltantes para conexión")
                self.estado_sistema["conexion_sheets"]["puntaje"] = 0
                return
            
            # Intentar imports
            try:
                import gspread
                from google.oauth2.service_account import Credentials
                from dotenv import load_dotenv
                print("✅ Librerías de conexión disponibles")
                puntaje_conexion += 10
            except ImportError as e:
                print(f"❌ Librerías faltantes: {e}")
                self.errores_criticos.append(f"Librerías Google Sheets faltantes: {e}")
                self.estado_sistema["conexion_sheets"]["puntaje"] = 0
                return
            
            # Cargar configuración
            load_dotenv()
            sheet_id = os.getenv('GOOGLE_SHEET_ID', '1tCILvM3VkaACJMNnTZu4ZYM3x81HcoTlg6uoj-K6RRQ')
            credentials_path = self.ruta_proyecto / "backend" / "credentials.json"
            
            print(f"🔍 Probando conexión con Sheet: {sheet_id[:20]}...")
            
            # Configurar credenciales
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly"
            ]
            
            creds = Credentials.from_service_account_file(str(credentials_path), scopes=scopes)
            client = gspread.authorize(creds)
            print("✅ Credenciales autorizadas")
            puntaje_conexion += 15
            
            # Probar apertura del sheet
            sheet = client.open_by_key(sheet_id)
            print(f"✅ Google Sheet abierto: {sheet.title}")
            puntaje_conexion += 15
            
            # Obtener información de hojas
            worksheets = sheet.worksheets()
            print(f"📊 Hojas disponibles: {len(worksheets)}")
            for i, ws in enumerate(worksheets[:3]):
                print(f"   {i+1}. {ws.title} (ID: {ws.id})")
            puntaje_conexion += 10
            
            # Probar acceso a datos
            worksheet = sheet.sheet1
            all_values = worksheet.get_all_values()
            total_filas = len(all_values)
            print(f"📈 Total de filas en primera hoja: {total_filas}")
            puntaje_conexion += 10
            
            if total_filas > 1:
                headers = all_values[0]
                print(f"📋 Columnas detectadas: {len(headers)}")
                
                # Verificar columnas críticas para inventario
                columnas_inventario = ['Placa', 'Descripción Actual', 'Marca', 'Valor Ingreso']
                columnas_encontradas = [col for col in columnas_inventario if col in headers]
                
                print(f"✅ Columnas inventario encontradas: {len(columnas_encontradas)}/{len(columnas_inventario)}")
                for col in columnas_encontradas:
                    print(f"   ✅ {col}")
                
                puntaje_conexion += len(columnas_encontradas) * 2
                
                # Contar registros válidos
                if 'Placa' in headers:
                    placa_idx = headers.index('Placa')
                    registros_validos = sum(1 for row in all_values[1:] if len(row) > placa_idx and row[placa_idx].strip())
                    print(f"📊 Registros con placa válida: {registros_validos:,}")
                    
                    if registros_validos > 1000:
                        puntaje_conexion += 20
                        print("✅ Base de datos robusta (>1000 registros)")
                    elif registros_validos > 100:
                        puntaje_conexion += 10
                        print("✅ Base de datos moderada (>100 registros)")
                    
                    self.estado_sistema["conexion_sheets"]["registros_validos"] = registros_validos
            
            self.estado_sistema["conexion_sheets"]["conexion_exitosa"] = True
            
        except gspread.exceptions.SpreadsheetNotFound:
            print("❌ Google Sheet no encontrado - verificar permisos")
            self.errores_criticos.append("Google Sheet sin acceso - verificar compartido")
            
        except gspread.exceptions.APIError as e:
            print(f"❌ Error API Google Sheets: {e}")
            self.errores_criticos.append(f"Error API Google: {e}")
            
        except Exception as e:
            print(f"❌ Error conexión: {e}")
            self.errores_criticos.append(f"Error conexión Google Sheets: {e}")
        
        print(f"\n📊 Puntaje Conexión: {puntaje_conexion}/100")
        self.estado_sistema["conexion_sheets"]["puntaje"] = puntaje_conexion
        print()

    def verificar_funcionalidad_servidor(self):
        """Verificar que el servidor puede arrancar"""
        print("🚀 VERIFICANDO FUNCIONALIDAD DEL SERVIDOR")
        print("-" * 42)
        
        puntaje_funcionalidad = 0
        
        # Verificar que se puede importar el módulo
        try:
            import sys
            sys.path.insert(0, str(self.ruta_proyecto / "backend"))
            
            import importlib.util
            spec = importlib.util.spec_from_file_location("app", self.ruta_proyecto / "backend" / "app.py")
            app_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app_module)
            
            print("✅ Módulo app.py se importa correctamente")
            puntaje_funcionalidad += 20
            
            # Verificar que tiene instancia FastAPI
            if hasattr(app_module, 'app'):
                print("✅ Instancia FastAPI encontrada")
                puntaje_funcionalidad += 10
                
                # Verificar algunos endpoints críticos
                app_instance = app_module.app
                routes = [route.path for route in app_instance.routes if hasattr(route, 'path')]
                
                endpoints_criticos = ['/api/articulos', '/admin.html', '/']
                endpoints_encontrados = [ep for ep in endpoints_criticos if any(ep in route for route in routes)]
                
                print(f"✅ Endpoints encontrados: {len(endpoints_encontrados)}/{len(endpoints_criticos)}")
                for ep in endpoints_encontrados:
                    print(f"   ✅ {ep}")
                
                puntaje_funcionalidad += len(endpoints_encontrados) * 10
                
            else:
                print("❌ Instancia FastAPI no encontrada")
                self.errores_criticos.append("Instancia FastAPI faltante")
            
        except Exception as e:
            print(f"❌ Error importando módulo: {e}")
            self.errores_criticos.append(f"Error importando app.py: {e}")
        
        # Verificar script de gestión
        if (self.ruta_proyecto / "manage.sh").exists():
            print("✅ Script de gestión disponible")
            puntaje_funcionalidad += 10
        else:
            print("⚠️  Script de gestión faltante")
            self.advertencias.append("manage.sh faltante")
        
        print(f"\n📊 Puntaje Funcionalidad: {puntaje_funcionalidad}/70")
        self.estado_sistema["funcionalidad"]["puntaje"] = puntaje_funcionalidad
        print()

    def calcular_puntaje_total(self):
        """Calcular puntaje total del sistema"""
        puntajes = [
            self.estado_sistema.get("estructura", {}).get("puntaje", 0),
            self.estado_sistema.get("configuracion", {}).get("puntaje", 0),
            self.estado_sistema.get("dependencias", {}).get("puntaje", 0),
            self.estado_sistema.get("sintaxis", {}).get("puntaje", 0),
            self.estado_sistema.get("conexion_sheets", {}).get("puntaje", 0),
            self.estado_sistema.get("funcionalidad", {}).get("puntaje", 0)
        ]
        
        self.puntaje_total = sum(puntajes)
        puntaje_maximo = 82 + 50 + 70 + 60 + 100 + 70  # Total teórico máximo
        
        return self.puntaje_total, puntaje_maximo

    def generar_reporte_final(self):
        """Generar reporte final completo"""
        puntaje_total, puntaje_maximo = self.calcular_puntaje_total()
        porcentaje = (puntaje_total / puntaje_maximo) * 100
        
        print("\n" + "=" * 70)
        print("🎯 REPORTE FINAL DEL SISTEMA")
        print("=" * 70)
        
        print(f"📊 PUNTAJE TOTAL: {puntaje_total}/{puntaje_maximo} ({porcentaje:.1f}%)")
        
        # Barra de progreso visual
        barra_longitud = 50
        progreso = int((porcentaje / 100) * barra_longitud)
        barra = "█" * progreso + "░" * (barra_longitud - progreso)
        print(f"📈 Progreso: [{barra}] {porcentaje:.1f}%")
        
        # Clasificación del estado
        if porcentaje >= 95:
            estado = "🎉 COMPLETAMENTE FUNCIONAL"
            color = "verde"
        elif porcentaje >= 85:
            estado = "✅ MAYORMENTE FUNCIONAL"
            color = "amarillo"
        elif porcentaje >= 70:
            estado = "⚠️  PARCIALMENTE FUNCIONAL"
            color = "naranja"
        else:
            estado = "❌ NO FUNCIONAL"
            color = "rojo"
        
        print(f"\n🏆 ESTADO DEL SISTEMA: {estado}")
        
        # Detalles por categoría
        categorias = [
            ("Estructura Proyecto", "estructura"),
            ("Configuración Archivos", "configuracion"), 
            ("Dependencias Python", "dependencias"),
            ("Sintaxis Backend", "sintaxis"),
            ("Conexión Google Sheets", "conexion_sheets"),
            ("Funcionalidad Servidor", "funcionalidad")
        ]
        
        print(f"\n📋 DETALLES POR CATEGORÍA:")
        print("-" * 40)
        for nombre, clave in categorias:
            puntaje = self.estado_sistema.get(clave, {}).get("puntaje", 0)
            print(f"   {nombre:<25}: {puntaje:3d} puntos")
        
        # Errores críticos
        if self.errores_criticos:
            print(f"\n❌ ERRORES CRÍTICOS ({len(self.errores_criticos)}):")
            print("-" * 30)
            for i, error in enumerate(self.errores_criticos[:10], 1):  # Máximo 10
                print(f"   {i}. {error}")
            if len(self.errores_criticos) > 10:
                print(f"   ... y {len(self.errores_criticos) - 10} errores más")
        
        # Advertencias
        if self.advertencias:
            print(f"\n⚠️  ADVERTENCIAS ({len(self.advertencias)}):")
            print("-" * 25)
            for i, advertencia in enumerate(self.advertencias[:5], 1):  # Máximo 5
                print(f"   {i}. {advertencia}")
            if len(self.advertencias) > 5:
                print(f"   ... y {len(self.advertencias) - 5} advertencias más")
        
        # Recomendaciones finales
        print(f"\n🎯 RECOMENDACIONES FINALES:")
        print("-" * 30)
        
        if porcentaje >= 95:
            print("🎊 ¡EXCELENTE! Tu sistema está completamente configurado y funcional.")
            registros = self.estado_sistema.get("conexion_sheets", {}).get("registros_validos", 0)
            if registros > 0:
                print(f"✅ Conectado exitosamente con {registros:,} registros en Google Sheets")
            print("🚀 Ejecutar: ./manage.sh dev")
            print("🌐 Acceder: http://localhost:8000/admin.html")
            
        elif porcentaje >= 85:
            print("✅ Tu sistema está mayormente funcional con algunos ajustes menores.")
            if self.errores_criticos:
                print("🔧 Corregir errores críticos listados arriba")
            print("🚀 Debería funcionar tras las correcciones")
            
        elif porcentaje >= 70:
            print("⚠️ Tu sistema está parcialmente funcional pero necesita varios ajustes.")
            print("🔧 Priorizar corrección de errores críticos")
            print("📋 Revisar configuración de Google Sheets")
            
        else:
            print("❌ Tu sistema requiere configuración sustancial.")
            print("🔧 Seguir guía de configuración paso a paso")
            print("📋 Verificar instalación de dependencias")
            print("🔗 Configurar Google Sheets API desde cero")
        
        # Información de registros si hay conexión
        registros = self.estado_sistema.get("conexion_sheets", {}).get("registros_validos", 0)
        if registros > 0:
            print(f"\n📊 DATOS DISPONIBLES: {registros:,} registros válidos")
            
        return porcentaje >= 95

    def guardar_reporte_detallado(self):
        """Guardar reporte detallado en archivo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"reporte_final_sistema_{timestamp}.txt"
        
        puntaje_total, puntaje_maximo = self.calcular_puntaje_total()
        porcentaje = (puntaje_total / puntaje_maximo) * 100
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(f"# REPORTE FINAL DEL SISTEMA\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Directorio: {self.ruta_proyecto}\n\n")
            
            f.write(f"## PUNTAJE TOTAL\n")
            f.write(f"{puntaje_total}/{puntaje_maximo} ({porcentaje:.1f}%)\n\n")
            
            f.write(f"## ESTADO POR CATEGORÍAS\n")
            for categoria, datos in self.estado_sistema.items():
                if isinstance(datos, dict) and "puntaje" in datos:
                    f.write(f"- {categoria}: {datos['puntaje']} puntos\n")
            
            f.write(f"\n## ERRORES CRÍTICOS ({len(self.errores_criticos)})\n")
            for error in self.errores_criticos:
                f.write(f"- {error}\n")
            
            f.write(f"\n## ADVERTENCIAS ({len(self.advertencias)})\n")
            for advertencia in self.advertencias:
                f.write(f"- {advertencia}\n")
            
            # Información de conexión
            if self.estado_sistema.get("conexion_sheets", {}).get("conexion_exitosa"):
                registros = self.estado_sistema.get("conexion_sheets", {}).get("registros_validos", 0)
                f.write(f"\n## CONEXIÓN GOOGLE SHEETS\n")
                f.write(f"Estado: EXITOSA\n")
                f.write(f"Registros disponibles: {registros:,}\n")
        
        print(f"\n💾 Reporte detallado guardado: {nombre_archivo}")

    def ejecutar_analisis_completo(self):
        """Ejecutar análisis completo del sistema"""
        self.imprimir_cabecera()
        self.verificar_estructura_proyecto()
        self.verificar_configuracion_archivos()
        self.verificar_dependencias_python()
        self.verificar_sintaxis_backend()
        self.probar_conexion_google_sheets()
        self.verificar_funcionalidad_servidor()
        
        sistema_funcional = self.generar_reporte_final()
        self.guardar_reporte_detallado()
        
        return sistema_funcional

if __name__ == "__main__":
    analizador = AnalisisCompletoFinal()
    sistema_ok = analizador.ejecutar_analisis_completo()
    
    # Código de salida para scripts
    sys.exit(0 if sistema_ok else 1)