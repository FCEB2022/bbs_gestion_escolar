# app/matriculas/routes.py
import os
import io
import zipfile
from datetime import datetime, timedelta
from flask import (
    render_template, request, redirect, url_for, flash, abort,
    current_app, send_file
)
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.usuarios.models import Usuario
from app.cursos.models import Curso, Modulo, CURSO_TIPO_FP, CURSO_TIPO_INTENSIVO, ESTADO_VALIDADO, ESTADO_PROGRAMADO
from . import bp
from .models import (
    Matricula, MatriculaDocumento, MatriculaAsignatura,
    ESTADO_MAT_PENDIENTE, ESTADO_MAT_VALIDADA, ESTADO_MAT_RECHAZADA,
    TIPO_FP_PRIMERO, TIPO_FP_SEGUNDO
)
from .forms import (
    FiltrosTablaForm, MatriculaFPForm, MatriculaIntensivoForm,
    RechazoForm, ValidarForm, CalificacionForm
)

# 🔹 Importación adicional para creación de pagos automáticos
from app.pagos.models import (
    Pago,
    ESTADO_PAGO_PENDIENTE,
    ESTADO_PAGO_VALIDADO,
    ESTADO_PAGO_INICIAL,
    ESTADO_PAGO_PENDIENTE_VALIDACION
)

# ----------------- Helpers de roles y permisos -----------------
def es_admin() -> bool:
    return any(r.nombre == "Administrador" for r in current_user.roles)

def es_administrativo() -> bool:
    return any(r.nombre == "Administrativo" for r in current_user.roles)

def es_supervisor() -> bool:
    return any(r.nombre == "Supervisor" for r in current_user.roles)

def puede_editar_matricula(m: Matricula) -> bool:
    """Editable solo si está pendiente o rechazada, y el usuario es admin/administrativo"""
    return m.estado in (ESTADO_MAT_PENDIENTE, ESTADO_MAT_RECHAZADA) and (es_admin() or es_administrativo())

# ----------------- Funciones auxiliares -----------------
def _save_if_present(file_storage, tipo: str, matricula_id: int):
    """Guarda un archivo si está presente"""
    if not file_storage or file_storage.filename == "":
        return None
    upload_dir = os.path.join(current_app.config.get("UPLOAD_FOLDER", "uploads"), "matriculas")
    os.makedirs(upload_dir, exist_ok=True)
    fname = f"{matricula_id}_{tipo}_{int(datetime.utcnow().timestamp())}_{file_storage.filename}"
    path = os.path.join(upload_dir, fname)
    file_storage.save(path)
    doc = MatriculaDocumento(matricula_id=matricula_id, tipo=tipo, filename=file_storage.filename, path=path)
    db.session.add(doc)
    # retornamos la instancia (está en la sesión, puede no tener id hasta commit)
    return doc

def _hook_crear_expediente_pagos(m: Matricula):
    """Hook futuro para crear expediente/pagos automáticamente"""
    pass

def _calcular_fechas_vencimiento(fecha_base, numero_cuota):
    """Calcular fecha de vencimiento (siempre día 10 de cada mes)"""
    from datetime import date
    
    # El primer vencimiento es el día 10 del mes siguiente
    if fecha_base.day <= 10:
        # Si es antes del día 10, el primer vencimiento es el 10 del mes actual
        primer_vencimiento = date(fecha_base.year, fecha_base.month, 10)
    else:
        # Si es después del día 10, el primer vencimiento es el 10 del mes siguiente
        if fecha_base.month == 12:
            primer_vencimiento = date(fecha_base.year + 1, 1, 10)
        else:
            primer_vencimiento = date(fecha_base.year, fecha_base.month + 1, 10)
    
    # Para cuotas subsiguientes, sumar meses
    meses_adicionales = numero_cuota - 1
    year = primer_vencimiento.year
    month = primer_vencimiento.month + meses_adicionales
    
    # Ajustar año si pasa de diciembre
    while month > 12:
        month -= 12
        year += 1
    
    return date(year, month, 10)



def calcular_monto_pagado(matricula_id):
    """Calcula el monto total pagado (pago inicial + cuotas validadas)"""
    from app.pagos.models import Pago, ESTADO_PAGO_VALIDADO, ESTADO_PAGO_INICIAL
    
    pagos = Pago.query.filter_by(matricula_id=matricula_id).all()
    monto_pagado = 0
    
    for pago in pagos:
        if pago.estado == ESTADO_PAGO_VALIDADO or getattr(pago, "es_pago_inicial", False):
            monto_pagado += pago.monto
    
    return monto_pagado

def calcular_deuda_actual(matricula):
    """Calcula la deuda actual (costo total - monto pagado)"""
    monto_pagado = calcular_monto_pagado(matricula.id)
    return matricula.coste_total - monto_pagado

def redistribuir_cuotas_pendientes(matricula):
    """Redistribuye el monto de las cuotas pendientes basado en la deuda actual"""
    from app.pagos.models import Pago, ESTADO_PAGO_PENDIENTE
    
    # Obtener cuotas pendientes
    cuotas_pendientes = Pago.query.filter_by(
        matricula_id=matricula.id, 
        estado=ESTADO_PAGO_PENDIENTE
    ).order_by(Pago.numero_cuota).all()
    
    if not cuotas_pendientes:
        return
    
    # Calcular deuda actual
    deuda_actual = calcular_deuda_actual(matricula)
    
    # Recalcular monto por cuota
    nuevo_monto_cuota = round(deuda_actual / len(cuotas_pendientes), 2)
    
    # Ajustar la última cuota por posibles diferencias de redondeo
    for i, cuota in enumerate(cuotas_pendientes):
        if i == len(cuotas_pendientes) - 1:
            # La última cuota lleva el ajuste por redondeo
            total_asignado = nuevo_monto_cuota * (len(cuotas_pendientes) - 1)
            cuota.monto = round(deuda_actual - total_asignado, 2)
        else:
            cuota.monto = nuevo_monto_cuota
    
    db.session.commit()


# ----------------- INDEX GENERAL -----------------
@bp.route("/")
@login_required
def index():
    total = Matricula.query.count()
    total_val = Matricula.query.filter_by(estado=ESTADO_MAT_VALIDADA).count()
    total_pend = Matricula.query.filter_by(estado=ESTADO_MAT_PENDIENTE).count()
    total_rech = Matricula.query.filter_by(estado=ESTADO_MAT_RECHAZADA).count()

    cursos_visibles = (
        Curso.query.filter(Curso.estado.in_([ESTADO_VALIDADO, ESTADO_PROGRAMADO]))
        .order_by(Curso.nombre.asc())
        .all()
    )

    mats_por_curso = {}
    for m in Matricula.query.order_by(Matricula.created_at.desc()).all():
        mats_por_curso.setdefault(m.curso_id, []).append(m)

    return render_template(
        "matriculas/index.html",
        cursos=cursos_visibles,
        mats_por_curso=mats_por_curso,
        total=total,
        total_val=total_val,
        total_pend=total_pend,
        total_rech=total_rech,
    )


# ----------------- LISTA CON FILTROS -----------------
@bp.route("/lista")
@login_required
def lista():
    """Listado general de matrículas con filtros"""
    search = request.args.get("search", "").strip()
    estado = request.args.get("estado", "").strip()
    campus = request.args.get("campus", "").strip()

    query = Matricula.query
    if search:
        query = query.filter(
            db.or_(
                Matricula.estudiante_nombre.ilike(f"%{search}%"),
                Matricula.doc_identidad.ilike(f"%{search}%")
            )
        )
    if estado:
        query = query.filter(Matricula.estado == estado)
    if campus:
        query = query.filter(Matricula.campus == campus)

    matriculas = query.order_by(Matricula.created_at.desc()).all()
    return render_template(
        "matriculas/lista.html",
        matriculas=matriculas,
        search=search,
        estado=estado,
        campus=campus,
    )


# ----------------- NUEVA MATRÍCULA -----------------
@bp.route("/nueva/<int:curso_id>", methods=["GET", "POST"])
@login_required
def nueva(curso_id):
    curso = db.session.get(Curso, curso_id) or abort(404)
    form = MatriculaFPForm() if curso.tipo == CURSO_TIPO_FP else MatriculaIntensivoForm()

    if request.method == "POST" and form.validate_on_submit():
        tipo_fp_val = getattr(form, "tipo_fp_anho", None)
        tipo_fp_val = tipo_fp_val.data if tipo_fp_val else None

        m = Matricula(
            curso_id=curso.id,
            estudiante_nombre=form.estudiante_nombre.data.strip(),
            doc_identidad=form.doc_identidad.data.strip() if form.doc_identidad.data else None,
            telefono=form.telefono.data.strip() if form.telefono.data else None,
            email=form.email.data.strip() if form.email.data else None,
            direccion=form.direccion.data.strip() if form.direccion.data else None,
            campus=form.campus.data,
            tipo_fp_anho=tipo_fp_val,
            estado=ESTADO_MAT_VALIDADA,  # ✅ Cambiado a VALIDADA
            coste_total=form.coste_total.data,
            numero_plazos=form.numero_plazos.data,  # ✅ Agregado
            monto_inicial=form.monto_inicial.data,  # ✅ Guardar monto inicial
            created_by_id=current_user.id
        )
        db.session.add(m)
        db.session.flush()

        # Guardar documentos requeridos (ahora retornan la instancia doc si se sube)
        doc_expediente = _save_if_present(form.expediente_academico.data, "expediente_academico", m.id)
        doc_factura = _save_if_present(form.factura_primer_pago.data, "factura_primer_pago", m.id)

        # Asignación automática de módulos para FP
        if curso.tipo == CURSO_TIPO_FP:
            mod_anio1 = Modulo.query.filter_by(curso_id=curso.id, anio_fp=1).all()
            mod_anio2 = Modulo.query.filter_by(curso_id=curso.id, anio_fp=2).all()

            if tipo_fp_val == "PRIMER_ANO":
                for mo in mod_anio1:
                    db.session.add(MatriculaAsignatura(matricula_id=m.id, modulo_id=mo.id))
            elif tipo_fp_val == "SEGUNDO_ANO":
                for mo in mod_anio2:
                    db.session.add(MatriculaAsignatura(matricula_id=m.id, modulo_id=mo.id))

        # 🔹 CREAR CALENDARIO DE PAGOS MEJORADO
        # 1. Pago inicial (marcado como pendiente de validación)
        pago_inicial = Pago(
            matricula_id=m.id,
            numero_cuota=0,  # Cuota especial para pago inicial
            monto=form.monto_inicial.data,
            estado=ESTADO_PAGO_PENDIENTE_VALIDACION,  # marcar para validación
            es_pago_inicial=True,
            monto_inicial=form.monto_inicial.data,
            fecha_vencimiento=None,
            fecha_pago=getattr(m, "created_at", None)
        )
        # intentar marcar origen si existe
        try:
            if hasattr(pago_inicial, "origen"):
                pago_inicial.origen = "MATRICULA"
        except Exception:
            pass

        db.session.add(pago_inicial)

        # Vincular doc_factura con el pago inicial si subieron factura
        try:
            if doc_factura is None:
                # intentar buscarlo en sesión/DB por si _save_if_present no devolvió
                doc_factura = MatriculaDocumento.query.filter_by(matricula_id=m.id, tipo="factura_primer_pago").order_by(MatriculaDocumento.id.desc()).first()
            if doc_factura is not None:
                # probar distintas propiedades posibles en Pago
                if hasattr(pago_inicial, "documento_id"):
                    pago_inicial.documento_id = getattr(doc_factura, "id", None)
                elif hasattr(pago_inicial, "comprobante_id"):
                    pago_inicial.comprobante_id = getattr(doc_factura, "id", None)
                elif hasattr(pago_inicial, "documento_path"):
                    pago_inicial.documento_path = getattr(doc_factura, "path", None)
                elif hasattr(pago_inicial, "filename"):
                    # no ideal, pero al menos dejamos referencia
                    pago_inicial.filename = getattr(doc_factura, "filename", None)
        except Exception:
            # no rompemos el flujo si no es posible vincular
            pass

        # 2. Calcular monto restante y crear cuotas normales
        monto_restante = (m.coste_total or 0) - (form.monto_inicial.data or 0)
        if m.numero_plazos and m.numero_plazos > 1:
            cuota_normal = monto_restante / (m.numero_plazos - 1)
            
            for i in range(1, m.numero_plazos):
                pago = Pago(
                    matricula_id=m.id,
                    numero_cuota=i,
                    monto=round(cuota_normal, 2),
                    estado=ESTADO_PAGO_PENDIENTE,
                    fecha_vencimiento=_calcular_fechas_vencimiento(getattr(m, "created_at", datetime.utcnow().date()), i)
                )
                db.session.add(pago)

        db.session.commit()
        flash("✅ Matrícula creada correctamente con calendario de pagos.", "success")
        return redirect(url_for("matriculas.detalle", matricula_id=m.id))

    mod_anio1 = mod_anio2 = []
    if curso.tipo == CURSO_TIPO_FP:
        mod_anio1 = Modulo.query.filter_by(curso_id=curso.id, anio_fp=1).order_by(Modulo.nombre).all()
        mod_anio2 = Modulo.query.filter_by(curso_id=curso.id, anio_fp=2).order_by(Modulo.nombre).all()

    return render_template("matriculas/nueva.html", curso=curso, form=form,
                           mod_anio1=mod_anio1, mod_anio2=mod_anio2)


# ----------------- DETALLE -----------------
@bp.route("/<int:matricula_id>")
@login_required
def detalle(matricula_id):
    # Recuperar la matrícula
    # Intentamos usar query normal y luego forzar .all() en relaciones dinámicas
    m = db.session.get(Matricula, matricula_id) or abort(404)

    # Convertir relaciones dinámicas (AppenderQuery) a listas para uso en plantillas
    # Esto evita errores de Jinja al usar |length o len() sobre AppenderQuery.
    try:
        if hasattr(m, "documentos") and hasattr(m.documentos, "all"):
            m.documentos = m.documentos.all()
    except Exception:
        # no rompemos la vista por un fallo en la conversión
        pass

    try:
        if hasattr(m, "pagos") and hasattr(m.pagos, "all"):
            m.pagos = m.pagos.all()
    except Exception:
        pass

    try:
        if hasattr(m, "asignaturas") and hasattr(m.asignaturas, "all"):
            m.asignaturas = m.asignaturas.all()
    except Exception:
        pass

    return render_template("matriculas/detalle.html", m=m)


# ----------------- EDITAR -----------------
@bp.route("/<int:matricula_id>/editar", methods=["GET", "POST"])
@login_required
def editar(matricula_id):
    m = db.session.get(Matricula, matricula_id) or abort(404)
    if not puede_editar_matricula(m):
        abort(403)

    curso = m.curso
    form = MatriculaFPForm() if curso.tipo == CURSO_TIPO_FP else MatriculaIntensivoForm()

    if request.method == "GET":
        form.estudiante_nombre.data = m.estudiante_nombre
        form.doc_identidad.data = m.doc_identidad
        form.telefono.data = m.telefono
        form.email.data = m.email
        form.direccion.data = m.direccion
        form.campus.data = m.campus
        form.coste_total.data = m.coste_total
        form.numero_plazos.data = m.numero_plazos
        form.monto_inicial.data = m.monto_inicial  # ✅ Agregar monto inicial en edición
        if curso.tipo == CURSO_TIPO_FP:
            form.tipo_fp_anho.data = m.tipo_fp_anho

        return render_template("matriculas/nueva.html", curso=curso, form=form, edit_mode=True, m=m)

    if form.validate_on_submit():
        m.estudiante_nombre = form.estudiante_nombre.data.strip()
        m.doc_identidad = form.doc_identidad.data.strip() if form.doc_identidad.data else None
        m.telefono = form.telefono.data.strip() if form.telefono.data else None
        m.email = form.email.data.strip() if form.email.data else None
        m.direccion = form.direccion.data.strip() if form.direccion.data else None
        m.campus = form.campus.data
        m.coste_total = form.coste_total.data
        m.numero_plazos = form.numero_plazos.data
        m.monto_inicial = form.monto_inicial.data  # ✅ Actualizar monto inicial

        if m.estado == ESTADO_MAT_RECHAZADA:
            m.estado = ESTADO_MAT_PENDIENTE
            m.motivo_rechazo = None

        doc_expediente = _save_if_present(form.expediente_academico.data, "expediente_academico", m.id)
        doc_factura = _save_if_present(form.factura_primer_pago.data, "factura_primer_pago", m.id)

        # 🔹 ACTUALIZAR CALENDARIO DE PAGOS AL EDITAR
        # Eliminar pagos existentes y recrearlos
        Pago.query.filter_by(matricula_id=m.id).delete()
        
        # Crear nuevo pago inicial (marcado para validación)
        pago_inicial = Pago(
            matricula_id=m.id,
            numero_cuota=0,
            monto=form.monto_inicial.data,
            estado=ESTADO_PAGO_PENDIENTE_VALIDACION,
            es_pago_inicial=True,
            monto_inicial=form.monto_inicial.data,
            fecha_vencimiento=None,
            fecha_pago=getattr(m, "created_at", None)
        )
        try:
            if hasattr(pago_inicial, "origen"):
                pago_inicial.origen = "MATRICULA"
        except Exception:
            pass

        db.session.add(pago_inicial)

        # Vincular doc_factura con el pago inicial si subieron factura
        try:
            if doc_factura is None:
                doc_factura = MatriculaDocumento.query.filter_by(matricula_id=m.id, tipo="factura_primer_pago").order_by(MatriculaDocumento.id.desc()).first()
            if doc_factura is not None:
                if hasattr(pago_inicial, "documento_id"):
                    pago_inicial.documento_id = getattr(doc_factura, "id", None)
                elif hasattr(pago_inicial, "comprobante_id"):
                    pago_inicial.comprobante_id = getattr(doc_factura, "id", None)
                elif hasattr(pago_inicial, "documento_path"):
                    pago_inicial.documento_path = getattr(doc_factura, "path", None)
                elif hasattr(pago_inicial, "filename"):
                    pago_inicial.filename = getattr(doc_factura, "filename", None)
        except Exception:
            pass

        # Recrear cuotas normales
        monto_restante = (m.coste_total or 0) - (form.monto_inicial.data or 0)
        if m.numero_plazos and m.numero_plazos > 1:
            cuota_normal = monto_restante / (m.numero_plazos - 1)
            
            for i in range(1, m.numero_plazos):
                pago = Pago(
                    matricula_id=m.id,
                    numero_cuota=i,
                    monto=round(cuota_normal, 2),
                    estado=ESTADO_PAGO_PENDIENTE,
                    fecha_vencimiento=_calcular_fechas_vencimiento(getattr(m, "created_at", datetime.utcnow().date()), i)
                )
                db.session.add(pago)

        db.session.commit()
        flash("✅ Matrícula actualizada correctamente con nuevo calendario de pagos.", "success")
        return redirect(url_for("matriculas.detalle", matricula_id=m.id))

    return redirect(url_for("matriculas.detalle", matricula_id=m.id))


# ----------------- ELIMINAR (solo admin) -----------------
@bp.route("/<int:matricula_id>/eliminar", methods=["POST"])
@login_required
def eliminar(matricula_id):
    if not es_admin():
        abort(403)
    m = db.session.get(Matricula, matricula_id) or abort(404)
    db.session.delete(m)
    db.session.commit()
    flash("🗑️ Matrícula eliminada.", "success")
    return redirect(url_for("matriculas.index"))


# ----------------- DESCARGAR DOCUMENTOS -----------------
@bp.route("/<int:matricula_id>/descargar", defaults={"documento_id": None}, endpoint="descargar_documentos")
@bp.route("/<int:matricula_id>/descargar/<int:documento_id>", endpoint="descargar_documentos")
@login_required
def descargar_documentos(matricula_id, documento_id=None):
    """Descarga todos los documentos de una matrícula en ZIP, o un documento individual si documento_id viene."""
    m = db.session.get(Matricula, matricula_id)
    if not m:
        flash("Matrícula no encontrada.", "danger")
        return redirect(url_for("matriculas.lista"))

    # Si se solicita un documento individual
    if documento_id is not None:
        doc = db.session.get(MatriculaDocumento, documento_id)
        if not doc or doc.matricula_id != m.id or not os.path.exists(doc.path):
            flash("Documento no encontrado.", "danger")
            return redirect(url_for("matriculas.detalle", matricula_id=m.id))
        return send_file(doc.path, as_attachment=True, download_name=doc.filename)

    # Si no, crear ZIP con todos los documentos
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        # si m.documentos es AppenderQuery, iterar con .all() por seguridad
        docs_iter = m.documentos.all() if hasattr(m, "documentos") and hasattr(m.documentos, "all") else getattr(m, "documentos", []) or []
        for doc in docs_iter:
            if os.path.exists(doc.path):
                zipf.write(doc.path, arcname=doc.filename)
    buffer.seek(0)
    filename = f"matricula_{m.id}_{(m.estudiante_nombre or 'alumno').replace(' ', '_')}.zip"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/zip")

# ----------------- DESCARGAR DOCUMENTO INDIVIDUAL -----------------
@bp.route("/documento/<int:documento_id>")
@login_required
def descargar_documento(documento_id):
    """Descarga un documento individual de matrícula"""
    doc = db.session.get(MatriculaDocumento, documento_id)
    if not doc or not os.path.exists(doc.path):
        flash("Documento no encontrado.", "danger")
        return redirect(url_for("matriculas.lista"))
    
    return send_file(doc.path, as_attachment=True, download_name=doc.filename)
# ----------------- VALIDACIONES -----------------
@bp.route("/validaciones")
@login_required
def validaciones_index():
    """Redirige al módulo central de validaciones"""
    return redirect(url_for('validaciones.index'))


@bp.route("/validaciones/<int:matricula_id>", methods=["GET", "POST"])
@login_required
def validar_o_rechazar(matricula_id):
    if not (es_admin() or es_supervisor()):
        abort(403)
    m = db.session.get(Matricula, matricula_id) or abort(404)
    f_ok = ValidarForm(prefix="ok")
    f_bad = RechazoForm(prefix="bad")

    if f_ok.validate_on_submit() and "ok-confirmar" in request.form:
        m.estado = ESTADO_MAT_VALIDADA
        m.motivo_rechazo = None
        db.session.commit()
        _hook_crear_expediente_pagos(m)
        flash("✅ Matrícula validada correctamente.", "success")
        return redirect(url_for("matriculas.validaciones_index"))

    if f_bad.validate_on_submit() and "bad-rechazar" in request.form:
        m.estado = ESTADO_MAT_RECHAZADA
        m.motivo_rechazo = f_bad.motivo.data.strip()
        db.session.commit()
        flash("❌ Matrícula rechazada.", "warning")
        return redirect(url_for("matriculas.validaciones_index"))

    return render_template("matriculas/validaciones/validar.html", m=m, f_ok=f_ok, f_bad=f_bad)


# ----------------- GESTIÓN DE CALIFICACIONES -----------------
from .models import Calificacion, TIPO_CALIF_ORDINARIO, TIPO_CALIF_PARCIAL, TIPO_CALIF_FINAL, TIPO_CALIF_RECUPERACION

@bp.route("/calificaciones/gestion/<int:matricula_asignatura_id>")
@login_required
def gestion_notas(matricula_asignatura_id):
    """Vista para gestionar las notas de una asignatura específica"""
    ma = db.session.get(MatriculaAsignatura, matricula_asignatura_id) or abort(404)
    
    # Permisos: solo admin, supervisor o docente asignado (si existiera lógica de docente)
    # Por ahora restringimos a roles administrativos
    if not (es_admin() or es_supervisor() or es_administrativo()):
        abort(403)

    # Instanciar formulario
    form = CalificacionForm()

    # Organizar calificaciones por tipo
    califs = ma.calificaciones
    ordinarios = [c for c in califs if c.tipo == TIPO_CALIF_ORDINARIO]
    parciales = [c for c in califs if c.tipo == TIPO_CALIF_PARCIAL]
    final = next((c for c in califs if c.tipo == TIPO_CALIF_FINAL), None)
    recuperacion = next((c for c in califs if c.tipo == TIPO_CALIF_RECUPERACION), None)

    return render_template(
        "matriculas/gestion_notas.html",
        ma=ma,
        form=form,
        ordinarios=ordinarios,
        parciales=parciales,
        final=final,
        recuperacion=recuperacion,
        tipos={
            "ORDINARIO": TIPO_CALIF_ORDINARIO,
            "PARCIAL": TIPO_CALIF_PARCIAL,
            "FINAL": TIPO_CALIF_FINAL,
            "RECUPERACION": TIPO_CALIF_RECUPERACION
        }
    )

@bp.route("/calificaciones/agregar", methods=["POST"])
@login_required
def agregar_calificacion():
    if not (es_admin() or es_supervisor() or es_administrativo()):
        abort(403)

    form = CalificacionForm()
    ma_id = request.form.get("matricula_asignatura_id")
    
    if not ma_id:
        flash("Error: No se identificó la asignatura.", "danger")
        return redirect(request.referrer)

    ma = db.session.get(MatriculaAsignatura, ma_id) or abort(404)

    if form.validate_on_submit():
        tipo = form.tipo.data
        valor = form.valor.data
        observacion = form.observacion.data

        # Validaciones de unicidad para Final y Recuperación
        if tipo in (TIPO_CALIF_FINAL, TIPO_CALIF_RECUPERACION):
            existe = Calificacion.query.filter_by(matricula_asignatura_id=ma.id, tipo=tipo).first()
            if existe:
                flash(f"Ya existe una nota de {tipo}. Elimínela antes de agregar una nueva.", "warning")
                return redirect(url_for('matriculas.gestion_notas', matricula_asignatura_id=ma.id))

        calif = Calificacion(
            matricula_asignatura_id=ma.id,
            tipo=tipo,
            valor=valor,
            observacion=observacion,
            fecha=datetime.utcnow()
        )
        db.session.add(calif)
        db.session.flush() 
        
        ma.calcular_nota_final()
        
        db.session.commit()
        flash("Nota agregada correctamente.", "success")
    else:
        # Si falla la validación, mostrar errores
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error en {getattr(form, field).label.text}: {error}", "danger")

    return redirect(url_for('matriculas.gestion_notas', matricula_asignatura_id=ma.id))

@bp.route("/calificaciones/eliminar/<int:calificacion_id>", methods=["POST"])
@login_required
def eliminar_calificacion(calificacion_id):
    if not (es_admin() or es_supervisor() or es_administrativo()):
        abort(403)

    calif = db.session.get(Calificacion, calificacion_id) or abort(404)
    ma = calif.asignatura
    
    db.session.delete(calif)
    db.session.flush() # Para que el cálculo no vea la borrada
    
    # Recalcular
    # Nota: al borrar, la colección ma.calificaciones en memoria podría seguir teniéndolo hasta el refresh.
    db.session.refresh(ma)
    ma.calcular_nota_final()
    
    db.session.commit()
    flash("Nota eliminada.", "success")
    return redirect(url_for('matriculas.gestion_notas', matricula_asignatura_id=ma.id))