"""
Script para corregir los formatos de fecha en la base de datos
"""
import os
import sqlite3
from datetime import datetime
from app import create_app

def fix_date_formats():
    """Convierte todos los formatos de fecha incorrectos en la base de datos"""
    app = create_app()
    
    with app.app_context():
        DB_PATH = os.path.join(app.instance_path, "app.db")
        
        if not os.path.exists(DB_PATH):
            print("❌ No se encontró la base de datos")
            return False
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            print("🔍 Verificando y corrigiendo formatos de fecha...")
            
            # Verificar la estructura actual de las tablas
            cursor.execute("PRAGMA table_info(pagos)")
            pagos_columns = [col[1] for col in cursor.fetchall()]
            print(f"📋 Columnas en 'pagos': {pagos_columns}")
            
            # Corregir fechas en la tabla pagos
            if 'fecha_vencimiento' in pagos_columns:
                print("🔄 Corrigiendo formato de fecha_vencimiento...")
                
                # Obtener todos los registros con fecha_vencimiento
                cursor.execute("SELECT id, fecha_vencimiento FROM pagos WHERE fecha_vencimiento IS NOT NULL")
                rows = cursor.fetchall()
                
                updated_count = 0
                for row_id, fecha_str in rows:
                    if fecha_str and ' ' in fecha_str:  # Si contiene espacio (formato datetime)
                        try:
                            # Convertir de datetime a date
                            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S.%f')
                            fecha_date = fecha_dt.strftime('%Y-%m-%d')
                            
                            # Actualizar el registro
                            cursor.execute(
                                "UPDATE pagos SET fecha_vencimiento = ? WHERE id = ?",
                                (fecha_date, row_id)
                            )
                            updated_count += 1
                        except ValueError as e:
                            print(f"⚠️ Error procesando fecha {fecha_str}: {e}")
                
                print(f"✅ Corregidas {updated_count} fechas en fecha_vencimiento")
            
            if 'fecha_pago' in pagos_columns:
                print("🔄 Corrigiendo formato de fecha_pago...")
                
                # Obtener todos los registros con fecha_pago
                cursor.execute("SELECT id, fecha_pago FROM pagos WHERE fecha_pago IS NOT NULL")
                rows = cursor.fetchall()
                
                updated_count = 0
                for row_id, fecha_str in rows:
                    if fecha_str and ' ' in fecha_str:  # Si contiene espacio (formato datetime)
                        try:
                            # Convertir de datetime a date
                            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S.%f')
                            fecha_date = fecha_dt.strftime('%Y-%m-%d')
                            
                            # Actualizar el registro
                            cursor.execute(
                                "UPDATE pagos SET fecha_pago = ? WHERE id = ?",
                                (fecha_date, row_id)
                            )
                            updated_count += 1
                        except ValueError as e:
                            print(f"⚠️ Error procesando fecha {fecha_str}: {e}")
                
                print(f"✅ Corregidas {updated_count} fechas en fecha_pago")
            
            # Verificar también la tabla matriculas si tiene campos de fecha
            cursor.execute("PRAGMA table_info(matriculas)")
            matriculas_columns = [col[1] for col in cursor.fetchall()]
            
            if 'created_at' in matriculas_columns:
                print("🔄 Verificando formato de created_at en matriculas...")
                cursor.execute("SELECT id, created_at FROM matriculas WHERE created_at IS NOT NULL LIMIT 5")
                sample_rows = cursor.fetchall()
                for row_id, fecha_str in sample_rows:
                    print(f"   Muestra created_at: {fecha_str}")
            
            conn.commit()
            conn.close()
            
            print("✅ Corrección de formatos de fecha completada")
            return True
            
        except Exception as e:
            print(f"❌ Error corrigiendo formatos de fecha: {e}")
            return False

def verify_date_fix():
    """Verifica que las fechas se hayan corregido correctamente"""
    app = create_app()
    
    with app.app_context():
        DB_PATH = os.path.join(app.instance_path, "app.db")
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            print("\n🔍 Verificando corrección de fechas...")
            
            # Verificar fechas en pagos
            cursor.execute("""
                SELECT id, fecha_vencimiento, fecha_pago 
                FROM pagos 
                WHERE fecha_vencimiento IS NOT NULL OR fecha_pago IS NOT NULL
                LIMIT 5
            """)
            rows = cursor.fetchall()
            
            print("📋 Muestra de fechas corregidas:")
            for row in rows:
                print(f"   ID: {row[0]}, Vencimiento: {row[1]}, Pago: {row[2]}")
            
            # Contar fechas con formato incorrecto
            cursor.execute("SELECT COUNT(*) FROM pagos WHERE fecha_vencimiento LIKE '% %'")
            bad_format_count = cursor.fetchone()[0]
            
            if bad_format_count == 0:
                print("✅ Todas las fechas tienen el formato correcto")
            else:
                print(f"⚠️ Aún hay {bad_format_count} fechas con formato incorrecto")
            
            conn.close()
            return bad_format_count == 0
            
        except Exception as e:
            print(f"❌ Error verificando corrección: {e}")
            return False

if __name__ == "__main__":
    print("🔄 INICIANDO CORRECCIÓN DE FORMATOS DE FECHA...")
    
    if fix_date_formats():
        print("\n✅ Corrección completada")
        
        if verify_date_fix():
            print("\n🎉 ¡Todas las fechas han sido corregidas correctamente!")
            print("🚀 La aplicación debería funcionar sin errores ahora.")
        else:
            print("\n⚠️  La corrección se completó pero hay advertencias")
            print("💡 Es posible que necesites ejecutar el script nuevamente")
    else:
        print("\n❌ Error en la corrección de fechas")