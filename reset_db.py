"""
RESET_DB.PY — Reinicia la base de datos del Sistema BBS (versión mejorada)
------------------------------------------------------------------------------
1️⃣ Verifica y aplica migraciones pendientes
2️⃣ Si hay problemas, crea una copia de seguridad y reinicia completamente
3️⃣ Crea todas las tablas según los modelos activos
4️⃣ Inserta datos de prueba para todos los módulos
"""

import os
import shutil
import subprocess
from datetime import datetime, timedelta
from app import create_app, db
from app.usuarios.models import Usuario, Role
from app.cursos.models import Curso, Modulo, CURSO_TIPO_FP, ESTADO_VALIDADO
from app.matriculas.models import Matricula, MatriculaDocumento, MatriculaAsignatura
from app.pagos.models import Pago, ESTADO_PAGO_PENDIENTE

app = create_app()
DB_PATH = os.path.join(app.instance_path, "app.db")
MIGRATIONS_DIR = "migrations"


def backup_database():
    """Crea una copia de seguridad de la base de datos actual"""
    if os.path.exists(DB_PATH):
        backup_dir = os.path.join(app.instance_path, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"app_backup_{timestamp}.db")
        
        shutil.copy2(DB_PATH, backup_path)
        print(f"📦 Copia de seguridad creada: {backup_path}")
        return backup_path
    return None


def try_migrations():
    """Intenta aplicar migraciones existentes"""
    if not os.path.exists(MIGRATIONS_DIR):
        print("❌ No existe la carpeta de migraciones")
        return False

    print("🔄 Intentando aplicar migraciones existentes...")
    try:
        # Usar subprocess para ejecutar comandos Flask
        result = subprocess.run(['flask', 'db', 'upgrade'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("✅ Migraciones aplicadas correctamente")
            return True
        else:
            print(f"❌ Error aplicando migraciones: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error ejecutando migraciones: {e}")
        return False


def init_migrations():
    """Inicializa el sistema de migraciones si no existe"""
    print("🔄 Inicializando sistema de migraciones...")
    
    try:
        # Ejecutar flask db init
        result = subprocess.run(['flask', 'db', 'init'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            print(f"❌ Error inicializando migraciones: {result.stderr}")
            return False
        
        # Ejecutar flask db migrate
        result = subprocess.run(['flask', 'db', 'migrate', '-m', 'Initial migration'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            print(f"❌ Error creando migración inicial: {result.stderr}")
            return False
        
        # Ejecutar flask db upgrade
        result = subprocess.run(['flask', 'db', 'upgrade'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            print(f"❌ Error aplicando migración: {result.stderr}")
            return False
        
        print("✅ Sistema de migraciones inicializado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error inicializando migraciones: {e}")
        return False


def force_create_tables():
    """Fuerza la creación de todas las tablas directamente"""
    print("🔨 Forzando creación de tablas...")
    try:
        with app.app_context():
            # Crear todas las tablas
            db.create_all()
            
            # Verificar que las tablas críticas existen
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['usuarios', 'roles', 'cursos', 'matriculas', 'pagos']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ Tablas faltantes: {missing_tables}")
                return False
            else:
                print("✅ Todas las tablas creadas correctamente")
                return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False


def reset_database(force_reset=False):
    """Reinicia la base de datos de manera inteligente"""
    print("⚙️ Iniciando proceso de reinicio de base de datos...")
    
    # Crear copia de seguridad
    backup_path = backup_database()
    
    if not force_reset:
        # Si no hay migraciones, inicializarlas primero
        if not os.path.exists(MIGRATIONS_DIR):
            print("📝 No hay migraciones existentes, inicializando...")
            if init_migrations():
                print("✅ Base de datos configurada con migraciones")
                return True
            else:
                print("❌ Falló la inicialización de migraciones, continuando con reset completo")
        else:
            # Intentar migraciones existentes
            if try_migrations():
                print("✅ Base de datos actualizada con migraciones")
                return True
    
    # Si las migraciones fallan o se fuerza el reset
    print("🔄 Iniciando reset completo...")
    
    # 1️⃣ Eliminar archivo existente
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"🗑️ Base de datos eliminada: {DB_PATH}")
    
    # 2️⃣ Crear estructura nueva
    success = force_create_tables()
    
    if success:
        seed_data()
        print("✅ Reinicio de base de datos completado.")
        
        # Inicializar migraciones para el futuro
        if not os.path.exists(MIGRATIONS_DIR):
            init_migrations()
        else:
            # Si ya existen migraciones, crear una nueva migración que refleje el estado actual
            try:
                subprocess.run(['flask', 'db', 'migrate', '-m', 'Current state after reset'], 
                             capture_output=True, text=True, shell=True)
                subprocess.run(['flask', 'db', 'upgrade'], 
                             capture_output=True, text=True, shell=True)
                print("✅ Migraciones actualizadas")
            except Exception as e:
                print(f"⚠️ No se pudieron actualizar las migraciones: {e}")
    else:
        print("❌ Error en el reinicio de la base de datos")
        if backup_path:
            print(f"💾 Puedes restaurar la copia de seguridad desde: {backup_path}")
    
    return success


def seed_data():
    """Inserta roles, usuario admin, cursos, matrículas y pagos de prueba"""
    print("🧩 Insertando datos iniciales...")

    # ==== ROLES ====
    roles_base = ["Administrador", "Administrativo", "Supervisor", "Profesor"]
    for nombre in roles_base:
        if not Role.query.filter_by(nombre=nombre).first():
            db.session.add(Role(nombre=nombre, descripcion=f"Rol del sistema: {nombre}"))
    db.session.commit()
    print("✅ Roles creados.")

    # ==== USUARIO ADMIN ====
    admin = Usuario(
        username="admin",
        full_name="Administrador del Sistema",
        email="admin@bbs.edu",
        activo=True,
        ultimo_login=datetime.now(),
        sesion_activa=False
    )
    
    if hasattr(admin, "set_password"):
        admin.set_password("admin123")
    else:
        admin.password_hash = "admin123"

    rol_admin = Role.query.filter_by(nombre="Administrador").first()
    if rol_admin and hasattr(admin, "roles"):
        admin.roles.append(rol_admin)

    db.session.add(admin)
    db.session.commit()
    print("✅ Usuario administrador creado: admin / admin123")

    # ==== CURSOS DE PRUEBA ====
    cursos = [
        Curso(
            nombre="Técnico Superior en Banca y Finanzas",
            tipo=CURSO_TIPO_FP,
            horas_totales=1800,
            horas_semanales=20,
            estado=ESTADO_VALIDADO,
            es_plantilla=True,
            created_by=admin if hasattr(Curso, "created_by") else None,
        ),
        Curso(
            nombre="Técnico Superior en Contabilidad y Auditoría",
            tipo=CURSO_TIPO_FP,
            horas_totales=1800,
            horas_semanales=20,
            estado=ESTADO_VALIDADO,
            es_plantilla=True,
            created_by=admin if hasattr(Curso, "created_by") else None,
        ),
        Curso(
            nombre="Técnico Superior en Gestión de Recursos Humanos",
            tipo=CURSO_TIPO_FP,
            horas_totales=1800,
            horas_semanales=20,
            estado=ESTADO_VALIDADO,
            es_plantilla=True,
            created_by=admin if hasattr(Curso, "created_by") else None,
        ),
    ]
    db.session.add_all(cursos)
    db.session.commit()
    print("📘 Cursos base creados.")

    # ==== MÓDULOS ASOCIADOS ====
    modulos = [
        # Banca y Finanzas
        Modulo(curso_id=cursos[0].id, nombre="Matemática Financiera", horas_modulo=90, anio_fp=1, semestre_fp=1),
        Modulo(curso_id=cursos[0].id, nombre="Productos y Servicios Bancarios", horas_modulo=100, anio_fp=1, semestre_fp=2),
        Modulo(curso_id=cursos[0].id, nombre="Gestión de Créditos y Riesgos", horas_modulo=100, anio_fp=2, semestre_fp=1),

        # Contabilidad
        Modulo(curso_id=cursos[1].id, nombre="Contabilidad General", horas_modulo=90, anio_fp=1, semestre_fp=1),
        Modulo(curso_id=cursos[1].id, nombre="Fiscalidad Nacional", horas_modulo=100, anio_fp=2, semestre_fp=1),
        Modulo(curso_id=cursos[1].id, nombre="Auditoría Financiera", horas_modulo=100, anio_fp=2, semestre_fp=2),

        # RRHH
        Modulo(curso_id=cursos[2].id, nombre="Psicología Laboral", horas_modulo=80, anio_fp=1, semestre_fp=1),
        Modulo(curso_id=cursos[2].id, nombre="Legislación Laboral de Guinea Ecuatorial", horas_modulo=90, anio_fp=1, semestre_fp=2),
        Modulo(curso_id=cursos[2].id, nombre="Gestión del Talento Humano", horas_modulo=100, anio_fp=2, semestre_fp=1),
    ]
    db.session.add_all(modulos)
    db.session.commit()
    print("✅ Módulos agregados correctamente.")

    # ==== MATRÍCULAS DE EJEMPLO ====
    matriculas = [
        Matricula(
            curso_id=cursos[0].id,
            estudiante_nombre="Juan Esono Mba",
            doc_identidad="GE123456",
            telefono="222-111-222",
            email="juan.esono@estudiantes.bbs.edu",
            direccion="Barrio Sampaka, Malabo",
            campus="MALABO",
            tipo_fp_anho="PRIMER_ANO",
            coste_total=75000,
            numero_plazos=6,  # ✅ NUEVO CAMPO
            created_by_id=admin.id,
        ),
        Matricula(
            curso_id=cursos[1].id,
            estudiante_nombre="Rosa Obiang Ndong",
            doc_identidad="GE789012",
            telefono="222-333-444",
            email="rosa.obiang@estudiantes.bbs.edu",
            direccion="Calle Bata Centro",
            campus="BATA",
            tipo_fp_anho="SEGUNDO_ANO",
            coste_total=70000,
            numero_plazos=4,  # ✅ NUEVO CAMPO
            created_by_id=admin.id,
        ),
    ]
    db.session.add_all(matriculas)
    db.session.commit()
    print("🎓 Matrículas de prueba registradas correctamente.")

    # ==== PAGOS DE EJEMPLO ====
    print("💰 Creando calendarios de pagos...")
    for matricula in matriculas:
        cuota = round(matricula.coste_total / matricula.numero_plazos, 2)
        for i in range(1, matricula.numero_plazos + 1):
            pago = Pago(
                matricula_id=matricula.id,
                numero_cuota=i,
                monto=cuota,
                estado=ESTADO_PAGO_PENDIENTE,
                fecha_vencimiento=datetime.now() + timedelta(days=30 * i)
            )
            db.session.add(pago)
    
    db.session.commit()
    print("✅ Calendarios de pagos creados correctamente.")
    print("🌱 Todos los datos de prueba insertados correctamente.")


if __name__ == "__main__":
    import sys
    
    # Verificar argumentos
    force_reset = "--force" in sys.argv
    
    if force_reset:
        print("🚨 MODO FUERZA ACTIVADO - Se reiniciará completamente la base de datos")
        user_input = input("¿Estás seguro? (s/N): ")
        if user_input.lower() != 's':
            print("❌ Operación cancelada")
            sys.exit(0)
    
    with app.app_context():
        success = reset_database(force_reset=force_reset)
        
        if success:
            print("\n🎉 ¡Base de datos lista!")
            print("📊 Puedes acceder al sistema con:")
            print("   Usuario: admin")
            print("   Contraseña: admin123")
            
            # Verificación final
            try:
                from app.matriculas.models import Matricula
                from app.pagos.models import Pago
                
                total_matriculas = Matricula.query.count()
                total_pagos = Pago.query.count()
                
                print(f"📈 Verificación: {total_matriculas} matrículas, {total_pagos} pagos creados")
            except Exception as e:
                print(f"⚠️ Verificación: {e}")
        else:
            print("\n💥 Hubo problemas con la base de datos")
            sys.exit(1)