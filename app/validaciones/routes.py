# app/validaciones/routes.py

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    abort
)
from flask_login import login_required, current_user
from datetime import date
from app.extensions import db
from . import bp
from app.pagos.routes import redistribuir_cuotas_pendientes

# --- MODELOS Y CONSTANTES ---
from app.cursos.models import (
    Curso,
    Programacion,
    ESTADO_BORRADOR,
    ESTADO_VALIDADO,
    PROG_PENDIENTE,
)
from app.matriculas.models import Matricula
from app.pagos.models import Pago, ESTADO_PAGO_PENDIENTE, ESTADO_PAGO_VALIDADO, ESTADO_PAGO_RECHAZADO, ESTADO_PAGO_PENDIENTE_VALIDACION

# Importar estados adicionales
from app.cursos.models import ESTADO_PENDIENTE_VALIDACION, ESTADO_RECHAZADO


# -------------------------------------------------------------
# 🔐 Funciones de permiso
# -------------------------------------------------------------
def tiene_permiso_validacion():
    """Verifica si el usuario tiene permisos para validar pagos/cursos (Administrador o Administrativo)."""
    return any(role.nombre in ['Administrador', 'Administrativo'] for role in current_user.roles)

def es_admin():
    return any(r.nombre == "Administrador" for r in current_user.roles)

def es_supervisor():
    return any(r.nombre == "Supervisor" for r in current_user.roles)


# -------------------------------------------------------------
# 🧭 PANEL CENTRAL DE VALIDACIONES
# -------------------------------------------------------------
@bp.route("/", endpoint="index")
@login_required
def index():
    """
    Panel central de validaciones del sistema.
    Muestra cursos pendientes y pagos pendientes de validación.
    """
    if not (es_admin() or es_supervisor()):
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for("core.dashboard"))

    # --- CURSOS ---
    cursos_pend_creacion = (
        Curso.query.filter(Curso.estado == ESTADO_BORRADOR)
        .order_by(Curso.created_at.desc())
        .all()
    )

    cursos_pend_prog = (
        Curso.query.filter(Curso.estado == ESTADO_VALIDADO)
        .join(Programacion, isouter=True)
        .filter(
            (Programacion.id.isnot(None))
            & (Programacion.estado_programacion == PROG_PENDIENTE)
        )
        .order_by(Curso.created_at.desc())
        .all()
    )

    # Incluimos BORRADOR y PENDIENTE_VALIDACION como "pendientes" para revisión por Supervisor/Admin
    cursos_pendientes = Curso.query.filter(
        Curso.estado.in_([ESTADO_PENDIENTE_VALIDACION, ESTADO_BORRADOR])
    ).order_by(Curso.created_at.desc()).all()

    cursos_rechazados = Curso.query.filter_by(estado=ESTADO_RECHAZADO).all()

    # --- PAGOS PENDIENTES DE VALIDACIÓN ---
    if tiene_permiso_validacion():
        pagos_pendientes = Pago.query.filter_by(estado=ESTADO_PAGO_PENDIENTE_VALIDACION).all()

        # Filtrar pagos vencidos que no están procesados
        pagos_vencidos = []
        all_pagos = Pago.query.all()
        for pago in all_pagos:
            if pago.esta_vencido() and pago.estado not in [ESTADO_PAGO_VALIDADO, ESTADO_PAGO_RECHAZADO, ESTADO_PAGO_PENDIENTE_VALIDACION]:
                pagos_vencidos.append(pago)
    else:
        pagos_pendientes = []
        pagos_vencidos = []

    # --- RENDERIZAR ---
    return render_template(
        "validaciones/index.html",
        cursos_pend_creacion=cursos_pend_creacion,
        cursos_pend_prog=cursos_pend_prog,
        total_cursos_pend_creacion=len(cursos_pend_creacion),
        total_cursos_pend_prog=len(cursos_pend_prog),
        total_cursos_rechazados=len(cursos_rechazados),
        pagos_pendientes=pagos_pendientes,
        pagos_vencidos=pagos_vencidos,
        hoy=date.today(),
        cursos_pendientes=cursos_pendientes,
        cursos_rechazados=cursos_rechazados
    )


# -------------------------------------------------------------
# ✅ VALIDAR PAGO
# -------------------------------------------------------------
@bp.route("/validar_pago/<int:pago_id>", methods=["POST"], endpoint="validar_pago")
@login_required
def validar_pago(pago_id):
    if not tiene_permiso_validacion():
        flash("No tiene permisos para validar pagos.", "danger")
        return redirect(url_for("core.dashboard"))
    
    pago = Pago.query.get_or_404(pago_id)
    
    if pago.estado != ESTADO_PAGO_PENDIENTE_VALIDACION:
        flash("Este pago no está pendiente de validación.", "warning")
        return redirect(url_for("validaciones.index"))
    
    pago.estado = ESTADO_PAGO_VALIDADO
    db.session.commit()
    
    # 🔄 REDISTRIBUIR CUOTAS PENDIENTES DESPUÉS DE VALIDAR
    redistribuir_cuotas_pendientes(pago.matricula)
    
    flash("Pago validado correctamente y cuotas redistribuidas.", "success")
    return redirect(url_for("validaciones.index"))


# -------------------------------------------------------------
# ❌ RECHAZAR PAGO
# -------------------------------------------------------------
@bp.route("/rechazar_pago/<int:pago_id>", methods=["POST"], endpoint="rechazar_pago")
@login_required
def rechazar_pago(pago_id):
    if not tiene_permiso_validacion():
        flash("No tiene permisos para rechazar pagos.", "danger")
        return redirect(url_for("core.dashboard"))
    
    pago = Pago.query.get_or_404(pago_id)
    motivo = request.form.get('motivo', '').strip()
    
    if not motivo:
        flash("Debe proporcionar un motivo para el rechazo.", "danger")
        return redirect(url_for("validaciones.index"))
    
    if pago.estado != ESTADO_PAGO_PENDIENTE_VALIDACION:
        flash("Este pago no está pendiente de validación.", "warning")
        return redirect(url_for("validaciones.index"))
    
    pago.estado = ESTADO_PAGO_RECHAZADO
    pago.motivo_rechazo = motivo
    db.session.commit()
    
    flash("Pago rechazado correctamente.", "warning")
    return redirect(url_for("validaciones.index"))


# -------------------------------------------------------------
# ✅ VALIDAR CURSO (nuevo endpoint)
# -------------------------------------------------------------
@bp.route("/validar_curso/<int:curso_id>", methods=["POST"], endpoint="validar_curso")
@login_required
def validar_curso(curso_id):
    """Valida un curso (cambia su estado a VALIDADO)."""
    if not (es_admin() or es_supervisor()):
        flash("No tienes permisos para validar cursos.", "danger")
        return redirect(url_for("core.dashboard"))

    curso = Curso.query.get_or_404(curso_id)

    # Solo permitir validar si está en BORRADOR o PENDIENTE_VALIDACION
    if curso.estado not in (ESTADO_BORRADOR, ESTADO_PENDIENTE_VALIDACION):
        flash("El curso no está en un estado que permita validación.", "warning")
        return redirect(url_for("validaciones.index"))

    curso.estado = ESTADO_VALIDADO
    # Si existiera un objeto Programacion pendiente, no lo tocamos aquí
    db.session.commit()

    flash("Curso validado correctamente.", "success")
    return redirect(url_for("validaciones.index"))


# -------------------------------------------------------------
# ❌ RECHAZAR CURSO (nuevo endpoint)
# -------------------------------------------------------------
@bp.route("/rechazar_curso/<int:curso_id>", methods=["POST"], endpoint="rechazar_curso")
@login_required
def rechazar_curso(curso_id):
    """Rechaza un curso y guarda una observación si se proporciona."""
    if not (es_admin() or es_supervisor()):
        flash("No tienes permisos para rechazar cursos.", "danger")
        return redirect(url_for("core.dashboard"))

    curso = Curso.query.get_or_404(curso_id)
    observacion = request.form.get("observacion", "") or request.form.get("motivo", "")
    observacion = observacion.strip()

    # Cambiar estado
    curso.estado = ESTADO_RECHAZADO

    # Intentamos guardar la observación en un campo existente si existe.
    # Si el modelo no tiene ese atributo, lo añadimos a la instancia (no persistirá).
    try:
        # Preferimos campos llamados 'observacion_rechazo' o 'motivo_rechazo' si existen en el modelo.
        if hasattr(curso, "observacion_rechazo"):
            setattr(curso, "observacion_rechazo", observacion)
        elif hasattr(curso, "motivo_rechazo"):
            setattr(curso, "motivo_rechazo", observacion)
        else:
            # Guardamos dinámicamente en la instancia (no persistente)
            curso.observacion_rechazo = observacion
    except Exception:
        curso.observacion_rechazo = observacion

    db.session.commit()
    flash("Curso rechazado correctamente.", "warning")
    return redirect(url_for("validaciones.index"))


# -------------------------------------------------------------
# 📋 DETALLE DE PAGOS (Mantenida para compatibilidad)
# -------------------------------------------------------------
@bp.route("/pagos/<int:matricula_id>", methods=["GET", "POST"], endpoint="validaciones_pagos_detalle")
@login_required
def validaciones_pagos_detalle(matricula_id):
    """Vista de detalle para validar o rechazar pagos de un estudiante"""
    if not (es_admin() or es_supervisor()):
        abort(403)

    matricula = Matricula.query.get_or_404(matricula_id)
    pagos = Pago.query.filter_by(matricula_id=matricula.id).order_by(Pago.numero_cuota).all()

    if request.method == "POST":
        accion = request.form.get("accion")
        pago_id = request.form.get("pago_id")
        pago = Pago.query.get(pago_id)
        if not pago:
            flash("No se encontró el pago especificado.", "danger")
            return redirect(url_for("validaciones.validaciones_pagos_detalle", matricula_id=matricula.id))

        try:
            if accion == "validar":
                pago.estado = ESTADO_PAGO_VALIDADO
                db.session.commit()

                # 🔄 Redistribuir deuda automáticamente
                pagos_restantes = Pago.query.filter(
                    Pago.matricula_id == matricula.id,
                    Pago.estado != ESTADO_PAGO_VALIDADO
                ).all()
                total_restante = sum(p.monto for p in pagos_restantes)
                n_restantes = len(pagos_restantes)
                nueva_cuota = round(total_restante / n_restantes, 2) if n_restantes else 0
                for p in pagos_restantes:
                    p.monto = nueva_cuota
                db.session.commit()

                flash("✅ Pago validado correctamente.", "success")
                return redirect(url_for("validaciones.validaciones_pagos_detalle", matricula_id=matricula.id))

            elif accion == "rechazar":
                pago.estado = ESTADO_PAGO_RECHAZADO
                db.session.commit()
                flash("❌ Pago rechazado correctamente.", "danger")
                return redirect(url_for("validaciones.validaciones_pagos_detalle", matricula_id=matricula.id))

            else:
                flash("⚠️ No se reconoció la acción enviada.", "warning")

        except Exception:
            db.session.rollback()
            flash("❌ Error al procesar la acción. Inténtalo de nuevo.", "danger")

    return render_template("validaciones/pagos/detalle.html", matricula=matricula, pagos=pagos)