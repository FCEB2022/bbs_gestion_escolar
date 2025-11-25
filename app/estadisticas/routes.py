from flask import render_template, flash
from flask_login import login_required, current_user
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta
from app.extensions import db

# Importar modelos necesarios
from app.matriculas.models import Matricula, ESTADO_MAT_VALIDADA, ESTADO_MAT_PENDIENTE, ESTADO_MAT_RECHAZADA
from app.cursos.models import Curso
from app.pagos.models import Pago, ESTADO_PAGO_VALIDADO, ESTADO_PAGO_PENDIENTE, ESTADO_PAGO_RECHAZADO, ESTADO_PAGO_INICIAL
from app.usuarios.models import Usuario

from . import bp

# Funciones de permisos
def es_admin():
    return any(r.nombre == "Administrador" for r in current_user.roles)

def es_supervisor():
    return any(r.nombre == "Supervisor" for r in current_user.roles)

def puede_ver_facturacion():
    return es_admin() or es_supervisor()

@bp.route('/')
@login_required
def index():
    """Dashboard principal de estadísticas del sistema"""
    
    # Fecha actual y rango para métricas temporales
    hoy = datetime.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    hace_7_dias = hoy - timedelta(days=7)
    
    try:
        # ========== MÉTRICAS BÁSICAS ==========
        
        # Total de estudiantes matriculados
        total_estudiantes = Matricula.query.filter_by(estado=ESTADO_MAT_VALIDADA).count()
        
        # Estudiantes por campus
        estudiantes_bata = Matricula.query.filter_by(
            estado=ESTADO_MAT_VALIDADA, 
            campus="BATA"
        ).count()
        
        estudiantes_malabo = Matricula.query.filter_by(
            estado=ESTADO_MAT_VALIDADA, 
            campus="MALABO"
        ).count()
        
        # ========== ESTADÍSTICAS POR CURSO ==========
        
        estudiantes_por_curso = db.session.query(
            Curso.nombre,
            func.count(Matricula.id).label('total')
        ).join(Matricula, Matricula.curso_id == Curso.id)\
         .filter(Matricula.estado == ESTADO_MAT_VALIDADA)\
         .group_by(Curso.nombre)\
         .order_by(func.count(Matricula.id).desc())\
         .all()
        
        # ========== FACTURACIÓN (solo para admin/supervisor) ==========
        facturacion = None
        if puede_ver_facturacion():
            # Total esperado (suma de todos los costes de matrículas validadas)
            total_esperado_result = db.session.query(
                func.sum(Matricula.coste_total)
            ).filter(Matricula.estado == ESTADO_MAT_VALIDADA).first()
            total_esperado = total_esperado_result[0] if total_esperado_result[0] else 0
            
            # Total pagado (pagos iniciales + cuotas validadas)
            total_pagado_result = db.session.query(
                func.sum(Pago.monto)
            ).filter(
                (Pago.estado == ESTADO_PAGO_VALIDADO) | (Pago.es_pago_inicial == True)
            ).first()
            total_pagado = total_pagado_result[0] if total_pagado_result[0] else 0
            
            # Deuda total
            deuda_total = total_esperado - total_pagado
            
            # Facturación del último mes
            facturacion_mes_result = db.session.query(
                func.sum(Pago.monto)
            ).filter(
                and_(
                    (Pago.estado == ESTADO_PAGO_VALIDADO) | (Pago.es_pago_inicial == True),
                    Pago.fecha_pago >= hace_30_dias
                )
            ).first()
            facturacion_mes = facturacion_mes_result[0] if facturacion_mes_result[0] else 0
            
            facturacion = {
                'total_esperado': total_esperado,
                'total_pagado': total_pagado,
                'deuda_total': deuda_total,
                'facturacion_mes': facturacion_mes,
                'porcentaje_pagado': (total_pagado / total_esperado * 100) if total_esperado > 0 else 0
            }
        
        # ========== MÉTRICAS ADICIONALES ==========
        
        # Estado de matrículas
        matriculas_pendientes = Matricula.query.filter_by(estado=ESTADO_MAT_PENDIENTE).count()
        matriculas_rechazadas = Matricula.query.filter_by(estado=ESTADO_MAT_RECHAZADA).count()
        
        # Estado de pagos
        pagos_pendientes = Pago.query.filter_by(estado=ESTADO_PAGO_PENDIENTE).count()
        pagos_rechazados = Pago.query.filter_by(estado=ESTADO_PAGO_RECHAZADO).count()
        pagos_validados = Pago.query.filter_by(estado=ESTADO_PAGO_VALIDADO).count()
        
        # Cursos activos
        cursos_activos = Curso.query.filter(
            Curso.estado.in_(['VALIDADO', 'PROGRAMADO'])
        ).count()
        
        # Nuevas matrículas (últimos 7 días) - Versión compatible
        # Verificar si la tabla tiene la columna created_at
        try:
            nuevas_matriculas = Matricula.query.filter(
                Matricula.created_at >= hace_7_dias
            ).count()
        except Exception:
            # Si no existe created_at, contar todas las matrículas
            nuevas_matriculas = Matricula.query.count()
        
        # Pagos pendientes de validación
        pagos_pendientes_validacion = Pago.query.filter_by(
            estado='PENDIENTE_VALIDACION'
        ).count()
        
        # ========== MÉTRICAS DE USUARIOS ==========
        
        total_usuarios = Usuario.query.count()
        usuarios_activos = Usuario.query.filter_by(activo=True).count()
        
        # ========== MÉTRICAS TEMPORALES COMPATIBLES ==========
        # Eliminamos date_trunc que no es compatible con SQLite
        
    except Exception as e:
        flash(f"Error al cargar las estadísticas: {str(e)}", "danger")
        # En caso de error, devolver valores por defecto basados en consultas simples
        total_estudiantes = Matricula.query.count()
        estudiantes_bata = Matricula.query.filter_by(campus="BATA").count()
        estudiantes_malabo = Matricula.query.filter_by(campus="MALABO").count()
        estudiantes_por_curso = []
        matriculas_pendientes = Matricula.query.filter_by(estado=ESTADO_MAT_PENDIENTE).count()
        matriculas_rechazadas = Matricula.query.filter_by(estado=ESTADO_MAT_RECHAZADA).count()
        pagos_pendientes = Pago.query.filter_by(estado=ESTADO_PAGO_PENDIENTE).count()
        pagos_rechazados = Pago.query.filter_by(estado=ESTADO_PAGO_RECHAZADO).count()
        pagos_validados = Pago.query.filter_by(estado=ESTADO_PAGO_VALIDADO).count()
        cursos_activos = Curso.query.count()
        nuevas_matriculas = Matricula.query.count()
        pagos_pendientes_validacion = Pago.query.filter_by(estado='PENDIENTE_VALIDACION').count()
        total_usuarios = Usuario.query.count()
        usuarios_activos = Usuario.query.filter_by(activo=True).count()
        facturacion = None

    return render_template(
        'estadisticas/index.html',
        # Métricas básicas
        total_estudiantes=total_estudiantes,
        estudiantes_bata=estudiantes_bata,
        estudiantes_malabo=estudiantes_malabo,
        
        # Por curso
        estudiantes_por_curso=estudiantes_por_curso,
        
        # Facturación
        facturacion=facturacion,
        puede_ver_facturacion=puede_ver_facturacion(),
        
        # Métricas adicionales
        matriculas_pendientes=matriculas_pendientes,
        matriculas_rechazadas=matriculas_rechazadas,
        pagos_pendientes=pagos_pendientes,
        pagos_rechazados=pagos_rechazados,
        pagos_validados=pagos_validados,
        cursos_activos=cursos_activos,
        nuevas_matriculas=nuevas_matriculas,
        pagos_pendientes_validacion=pagos_pendientes_validacion,
        
        # Métricas de usuarios
        total_usuarios=total_usuarios,
        usuarios_activos=usuarios_activos,
        
        # Fechas
        hoy=hoy,
        hace_7_dias=hace_7_dias,
        hace_30_dias=hace_30_dias
    )