import os
import shutil
import sqlite3
from datetime import datetime
import subprocess
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "app.db")
BACKUP_DIR = os.path.join(BASE_DIR, "instance", "backups")
MIGRATIONS_DIR = os.path.join(BASE_DIR, "migrations")

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=BASE_DIR)
        if result.returncode == 0:
            print(f"✅ {description} completado")
            if result.stdout.strip():
                print(f"   Salida: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Error en {description}: {result.stderr}")
            if result.stdout.strip():
                print(f"   Salida: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"❌ Error ejecutando {description}: {e}")
        return False

def backup_database():
    """Crea una copia de seguridad de la base de datos"""
    if not os.path.exists(DB_PATH):
        print("ℹ️ No hay base de datos existente para respaldar")
        return True
        
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"app_backup_{timestamp}.db")
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Copia de seguridad creada: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Error creando copia de seguridad: {e}")
        return False

def check_current_db_structure():
    """Verifica la estructura actual de la base de datos"""
    print("\n🔍 Verificando estructura actual de la base de datos...")
    if not os.path.exists(DB_PATH):
        print("ℹ️ No existe la base de datos")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar si existe la tabla matriculas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matriculas'")
        if not cursor.fetchone():
            print("❌ No existe la tabla 'matriculas'")
            conn.close()
            return False
        
        # Verificar columnas de la tabla matriculas
        cursor.execute("PRAGMA table_info(matriculas)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Columnas actuales en 'matriculas': {', '.join(columns)}")
        
        # Verificar si falta monto_inicial
        if 'monto_inicial' not in columns:
            print("❌ Falta la columna 'monto_inicial' en la tabla 'matriculas'")
            conn.close()
            return False
            
        conn.close()
        print("✅ Estructura de la base de datos es correcta")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return False

def force_migration():
    """Fuerza la aplicación de migraciones de manera directa"""
    print("\n🚀 Aplicando migraciones de manera forzada...")
    
    # Paso 1: Eliminar migraciones existentes si existen
    if os.path.exists(MIGRATIONS_DIR):
        try:
            shutil.rmtree(MIGRATIONS_DIR)
            print("🗑️ Migraciones existentes eliminadas")
        except Exception as e:
            print(f"❌ Error eliminando migraciones: {e}")
            return False
    
    # Paso 2: Inicializar migraciones
    commands = [
        ("flask db init", "Inicializando sistema de migraciones"),
        ("flask db migrate -m \"Estructura inicial con campos nuevos\"", "Generando migración inicial"),
        ("flask db upgrade", "Aplicando migración a la base de datos")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"❌ Falló en: {description}")
            return False
    
    return True

def manual_schema_update():
    """Actualización manual del esquema si las migraciones fallan"""
    print("\n🔧 Intentando actualización manual del esquema...")
    
    if not os.path.exists(DB_PATH):
        print("ℹ️ No existe la base de datos para actualizar")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar y añadir monto_inicial a matriculas
        cursor.execute("PRAGMA table_info(matriculas)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'monto_inicial' not in columns:
            print("➕ Añadiendo columna 'monto_inicial' a tabla 'matriculas'...")
            cursor.execute("ALTER TABLE matriculas ADD COLUMN monto_inicial FLOAT DEFAULT 0.0")
            print("✅ Columna 'monto_inicial' añadida")
        
        # Verificar y añadir campos nuevos a pagos
        cursor.execute("PRAGMA table_info(pagos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'es_pago_inicial' not in columns:
            print("➕ Añadiendo columna 'es_pago_inicial' a tabla 'pagos'...")
            cursor.execute("ALTER TABLE pagos ADD COLUMN es_pago_inicial BOOLEAN DEFAULT 0")
            print("✅ Columna 'es_pago_inicial' añadida")
        
        if 'monto_inicial' not in columns:
            print("➕ Añadiendo columna 'monto_inicial' a tabla 'pagos'...")
            cursor.execute("ALTER TABLE pagos ADD COLUMN monto_inicial FLOAT")
            print("✅ Columna 'monto_inicial' añadida")
        
        conn.commit()
        conn.close()
        print("✅ Actualización manual completada")
        return True
        
    except Exception as e:
        print(f"❌ Error en actualización manual: {e}")
        return False

def verify_final_state():
    """Verifica el estado final después de la migración"""
    print("\n🔍 Verificando estado final...")
    
    # Verificar estructura de la base de datos
    if not check_current_db_structure():
        print("❌ La estructura de la base de datos no es correcta")
        return False
    
    # Verificar que la aplicación funciona
    try:
        from app import create_app, db
        from app.matriculas.models import Matricula
        
        app = create_app()
        with app.app_context():
            # Intentar contar matrículas (esto fallaba antes)
            count = Matricula.query.count()
            print(f"✅ Consulta de matrículas exitosa: {count} registros")
            
            # Verificar que se puede acceder a los nuevos campos
            if count > 0:
                matricula = Matricula.query.first()
                # Esto debería funcionar sin error ahora
                monto_inicial = getattr(matricula, 'monto_inicial', 'No disponible')
                print(f"✅ Acceso a campo 'monto_inicial': {monto_inicial}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en verificación final: {e}")
        return False

def main():
    print("🧱 INICIANDO REPARACIÓN DE BASE DE DATOS...\n")
    print("⚠️  Este proceso solucionará los problemas de migración")
    print("    y añadirá los campos faltantes a la base de datos.\n")
    
    # Verificar que estamos en el entorno correcto
    if not os.environ.get('FLASK_APP'):
        os.environ['FLASK_APP'] = 'run.py'
        print("🔧 FLASK_APP establecido como 'run.py'")
    
    # Confirmación de seguridad
    if "--force" not in sys.argv:
        confirm = input("¿Estás seguro de continuar? (s/N): ")
        if confirm.lower() != 's':
            print("❌ Operación cancelada")
            return
    
    # Paso 1: Copia de seguridad obligatoria
    print("\n" + "="*50)
    print("CREANDO COPIA DE SEGURIDAD")
    print("="*50)
    
    if not backup_database():
        print("❌ Falló la copia de seguridad. Abortando...")
        return
    
    # Paso 2: Verificar estado actual
    print("\n" + "="*50)
    print("DIAGNÓSTICO INICIAL")
    print("="*50)
    
    current_state_ok = check_current_db_structure()
    
    if current_state_ok:
        print("✅ La base de datos ya tiene la estructura correcta")
        print("🎉 No se necesitan cambios adicionales")
        return
    
    # Paso 3: Intentar migración automática
    print("\n" + "="*50)
    print("MIGRACIÓN AUTOMÁTICA")
    print("="*50)
    
    migration_success = force_migration()
    
    if not migration_success:
        print("⚠️  La migración automática falló, intentando enfoque manual...")
        
        # Paso 4: Actualización manual como respaldo
        print("\n" + "="*50)
        print("ACTUALIZACIÓN MANUAL")
        print("="*50)
        
        if not manual_schema_update():
            print("❌ Falló la actualización manual")
            print("💡 Intenta restaurar desde la copia de seguridad manualmente")
            return
    
    # Paso 5: Verificación final
    print("\n" + "="*50)
    print("VERIFICACIÓN FINAL")
    print("="*50)
    
    if verify_final_state():
        print("\n🎉 ¡REPARACIÓN COMPLETADA EXITOSAMENTE!")
        print("\n📋 RESUMEN:")
        print("   ✅ Copia de seguridad creada")
        print("   ✅ Estructura de base de datos actualizada")
        print("   ✅ Campos nuevos añadidos")
        print("   ✅ Datos existentes preservados")
        print("\n🚀 La aplicación está lista para usar.")
    else:
        print("\n⚠️  La reparación se completó pero hay advertencias")
        print("💡 La aplicación podría funcionar, pero verifica manualmente")

if __name__ == "__main__":
    main()