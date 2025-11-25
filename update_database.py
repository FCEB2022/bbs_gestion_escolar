"""
Script seguro para resetear la base de datos MANTENIENDO los datos existentes
"""
import os
import sqlite3
import shutil
from datetime import datetime
from app import create_app, db
from app.usuarios.models import Usuario, Role
from app.cursos.models import Curso, Modulo
from app.matriculas.models import Matricula, MatriculaDocumento
from app.pagos.models import Pago

def export_data():
    """Exporta todos los datos existentes de la base de datos"""
    app = create_app()
    
    with app.app_context():
        DB_PATH = os.path.join(app.instance_path, "app.db")
        
        if not os.path.exists(DB_PATH):
            print("❌ No se encontró la base de datos para exportar")
            return None
        
        try:
            # Conectar a la base de datos existente
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Obtener todas las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            data_export = {}
            
            for table in tables:
                if table == 'sqlite_sequence':
                    continue
                    
                print(f"📊 Exportando datos de: {table}")
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                # Convertir a lista de diccionarios
                table_data = []
                for row in rows:
                    table_data.append(dict(row))
                
                data_export[table] = table_data
            
            conn.close()
            print("✅ Datos exportados correctamente")
            return data_export
            
        except Exception as e:
            print(f"❌ Error exportando datos: {e}")
            return None

def import_data(data_export):
    """Importa los datos exportados a la nueva base de datos"""
    app = create_app()
    
    with app.app_context():
        try:
            # Conectar a la nueva base de datos
            conn = sqlite3.connect(os.path.join(app.instance_path, "app.db"))
            cursor = conn.cursor()
            
            for table, rows in data_export.items():
                if not rows:
                    continue
                
                print(f"📥 Importando datos a: {table}")
                
                # Obtener columnas de la tabla
                cursor.execute(f"PRAGMA table_info({table})")
                columns_info = cursor.fetchall()
                columns = [col[1] for col in columns_info]
                
                # Insertar datos
                for row in rows:
                    # Filtrar solo las columnas que existen en la nueva estructura
                    filtered_row = {k: v for k, v in row.items() if k in columns}
                    
                    if filtered_row:
                        placeholders = ', '.join(['?' for _ in filtered_row])
                        columns_str = ', '.join(filtered_row.keys())
                        values = list(filtered_row.values())
                        
                        cursor.execute(
                            f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})",
                            values
                        )
            
            conn.commit()
            conn.close()
            print("✅ Datos importados correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error importando datos: {e}")
            return False

def reset_database_safe():
    """Resetea la base de datos manteniendo los datos existentes"""
    app = create_app()
    
    with app.app_context():
        DB_PATH = os.path.join(app.instance_path, "app.db")
        
        if not os.path.exists(DB_PATH):
            print("ℹ️ No hay base de datos existente, creando una nueva...")
            db.create_all()
            return True
        
        # Paso 1: Crear copia de seguridad
        print("📦 Creando copia de seguridad...")
        backup_dir = os.path.join(app.instance_path, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"app_backup_{timestamp}.db")
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Copia de seguridad creada: {backup_path}")
        
        # Paso 2: Exportar datos existentes
        print("🔄 Exportando datos existentes...")
        data_export = export_data()
        
        if not data_export:
            print("❌ No se pudieron exportar los datos existentes")
            return False
        
        # Paso 3: Eliminar base de datos antigua
        print("🗑️ Eliminando base de datos antigua...")
        db.session.close()
        os.remove(DB_PATH)
        
        # Paso 4: Crear nueva estructura
        print("🔄 Creando nueva estructura de base de datos...")
        db.create_all()
        
        # Paso 5: Importar datos
        print("🔄 Importando datos a la nueva estructura...")
        success = import_data(data_export)
        
        if success:
            print("✅ Base de datos actualizada correctamente manteniendo los datos")
            return True
        else:
            # Restaurar desde backup si falla la importación
            print("⚠️ Error importando datos, restaurando desde copia de seguridad...")
            shutil.copy2(backup_path, DB_PATH)
            print("✅ Base de datos restaurada desde copia de seguridad")
            return False

def verify_database_integrity():
    """Verifica la integridad de la base de datos después del reset"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar que las tablas críticas existen y tienen datos
            tables_to_check = ['usuarios', 'roles', 'cursos', 'matriculas', 'pagos']
            
            for table in tables_to_check:
                count = db.session.execute(f"SELECT COUNT(*) FROM {table}").scalar()
                print(f"📊 {table}: {count} registros")
            
            # Verificar estructura de pagos
            print("\n🔍 Verificando estructura de pagos...")
            pago_columns = db.session.execute("PRAGMA table_info(pagos)").fetchall()
            pago_column_names = [col[1] for col in pago_columns]
            print(f"📋 Columnas en 'pagos': {pago_column_names}")
            
            required_columns = ['fecha_pago', 'comprobante_path', 'motivo_rechazo']
            missing_columns = [col for col in required_columns if col not in pago_column_names]
            
            if missing_columns:
                print(f"❌ Faltan columnas: {missing_columns}")
                return False
            else:
                print("✅ Todas las columnas necesarias están presentes")
                return True
                
        except Exception as e:
            print(f"❌ Error verificando integridad: {e}")
            return False

if __name__ == "__main__":
    print("🚀 INICIANDO ACTUALIZACIÓN SEGURA DE LA BASE DE DATOS...")
    print("⚠️  Este proceso mantendrá todos los datos existentes")
    print("    y actualizará la estructura de la base de datos.\n")
    
    # Confirmación de seguridad
    confirm = input("¿Estás seguro de continuar? (s/N): ")
    
    if confirm.lower() == 's':
        print("\n" + "="*50)
        print("PROCESO INICIADO")
        print("="*50)
        
        if reset_database_safe():
            print("\n" + "="*50)
            print("VERIFICACIÓN DE INTEGRIDAD")
            print("="*50)
            
            if verify_database_integrity():
                print("\n🎉 ¡ACTUALIZACIÓN COMPLETADA EXITOSAMENTE!")
                print("\n📋 RESUMEN:")
                print("   ✅ Copia de seguridad creada")
                print("   ✅ Datos existentes preservados")
                print("   ✅ Nueva estructura aplicada")
                print("   ✅ Integridad verificada")
                print("\n🚀 La aplicación está lista para usar con la nueva estructura.")
            else:
                print("\n⚠️  La actualización se completó pero hay advertencias en la verificación")
                print("💡 Verifica manualmente la base de datos")
        else:
            print("\n❌ Error en la actualización de la base de datos")
            print("💡 Se restauró la copia de seguridad automáticamente")
    else:
        print("❌ Operación cancelada")