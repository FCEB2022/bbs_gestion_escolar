# app/pagos/routes.py
import os
from datetime import datetime, date, timedelta
from flask import (
    render_template, redirect, url_for, flash, request, 
    abort, send_file, current_app
)
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from app.extensions import db
from app.matriculas.models import Matricula
from app.pagos.models import Pago, ESTADO_PAGO_PENDIENTE, ESTADO_PAGO_VALIDADO, ESTADO_PAGO_RECHAZADO, ESTADO_PAGO_PENDIENTE_VALIDACION, ESTADO_PAGO_INICIAL
from app.pagos.forms import RegistrarPagoForm

from . import bp

# Configuración de subida de archivos
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}
MAX_FILE_MB = 10

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['pdf', 'png', 'jpg', 'jpeg']

def ensure_upload_dir():
    upload_dir = os.path.join(current_app.instance_path, "uploads", "pagos")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

# ----------------- NUEVAS FUNCIONES PARA CÁLCULOS FINANCIEROS -----------------
def calcular_monto_pagado(matricula_id):
    """Calcula el monto total pagado (pago inicial + cuotas validadas)"""
    pagos = Pago.query.filter_by(matricula_id=matricula_id).all()
    monto_pagado = 0
    
    for pago in pagos:
        if pago.estado == ESTADO_PAGO_VALIDADO or pago.es_pago_inicial:
            monto_pagado += pago.monto
    
    return monto_pagado

def calcular_deuda_actual(matricula):
    """Calcula la deuda actual (costo total - monto pagado)"""
    monto_pagado = calcular_monto_pagado(matricula.id)
    return matricula.coste_total - monto_pagado

def obtener_cuotas_pendientes(matricula_id):
    """Obtiene las cuotas pendientes de validación"""
    return Pago.query.filter_by(
        matricula_id=matricula_id, 
        estado=ESTADO_PAGO_PENDIENTE
    ).order_by(Pago.numero_cuota).all()

def redistribuir_cuotas_pendientes(matricula):
    """Redistribuye el monto de las cuotas pendientes basado en la deuda actual"""
    # Obtener cuotas pendientes
    cuotas_pendientes = obtener_cuotas_pendientes(matricula.id)
    
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

def _calcular_balance(matricula):
    """Calcular balance total pagado y adeudado - VERSIÓN MEJORADA"""
    monto_pagado = calcular_monto_pagado(matricula.id)
    deuda_actual = calcular_deuda_actual(matricula)
    
    # Obtener información de cuotas
    cuotas_totales = Pago.query.filter_by(matricula_id=matricula.id).count()
    cuotas_pagadas = Pago.query.filter(
        Pago.matricula_id == matricula.id,
        db.or_(Pago.estado == ESTADO_PAGO_VALIDADO, Pago.es_pago_inicial == True)
    ).count()
    cuotas_pendientes = cuotas_totales - cuotas_pagadas
    
    return {
        'total_pagado': monto_pagado,
        'total_adeudado': deuda_actual,
        'coste_total': matricula.coste_total,
        'progreso': (monto_pagado / matricula.coste_total * 100) if matricula.coste_total > 0 else 0,
        'cuotas_pagadas': cuotas_pagadas,
        'cuotas_pendientes': cuotas_pendientes,
        'cuotas_totales': cuotas_totales
    }

def _verificar_crear_pago_inicial(matricula):
    """Verificar y crear pago inicial si no existe"""
    try:
        pago_inicial = Pago.query.filter_by(
            matricula_id=matricula.id, 
            es_pago_inicial=True
        ).first()
        
        if not pago_inicial and matricula.monto_inicial > 0:
            pago_inicial = Pago(
                matricula_id=matricula.id,
                numero_cuota=0,
                monto=matricula.monto_inicial,
                estado=ESTADO_PAGO_INICIAL,
                es_pago_inicial=True,
                monto_inicial=matricula.monto_inicial,
                fecha_vencimiento=None
            )
            db.session.add(pago_inicial)
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"⚠️ Error creando pago inicial: {e}")
        return False

def _calcular_fechas_vencimiento(fecha_base, numero_cuota):
    """Calcular fecha de vencimiento (siempre día 10 de cada mes)"""
    if fecha_base.day <= 10:
        primer_vencimiento = date(fecha_base.year, fecha_base.month, 10)
    else:
        if fecha_base.month == 12:
            primer_vencimiento = date(fecha_base.year + 1, 1, 10)
        else:
            primer_vencimiento = date(fecha_base.year, fecha_base.month + 1, 10)
    
    meses_adicionales = numero_cuota - 1
    year = primer_vencimiento.year
    month = primer_vencimiento.month + meses_adicionales
    
    while month > 12:
        month -= 12
        year += 1
    
    return date(year, month, 10)

# -------------------------------------------------------------
# 🧭 INDEX: Agrupa por campus
# -------------------------------------------------------------
@bp.route("/", endpoint="index")
@login_required
def index():
    malabo = Matricula.query.filter_by(campus="MALABO").all()
    bata = Matricula.query.filter_by(campus="BATA").all()

    return render_template(
        "pagos/index.html",
        malabo=malabo,
        bata=bata
    )

# -------------------------------------------------------------
# 📋 FICHA DE PAGOS DEL ESTUDIANTE (VERSIÓN MEJORADA)
# -------------------------------------------------------------
@bp.route("/ficha/<int:matricula_id>", endpoint="ficha")
@login_required
def ficha(matricula_id):
    matricula = Matricula.query.get_or_404(matricula_id)
    
    # Verificar y crear pago inicial si no existe
    _verificar_crear_pago_inicial(matricula)
    
    # Obtener todos los pagos de la matrícula
    pagos = Pago.query.filter_by(matricula_id=matricula_id).order_by(Pago.numero_cuota).all()
    
    # Obtener pago inicial
    pago_inicial = Pago.query.filter_by(matricula_id=matricula_id, es_pago_inicial=True).first()
    
    # Calcular información financiera actualizada
    monto_pagado = calcular_monto_pagado(matricula_id)
    deuda_actual = calcular_deuda_actual(matricula)
    cuotas_pendientes = obtener_cuotas_pendientes(matricula_id)
    
    balance = _calcular_balance(matricula)
    
    return render_template(
        "pagos/ficha_pago.html", 
        m=matricula, 
        pagos=pagos,
        pago_inicial=pago_inicial,
        balance=balance,
        monto_pagado=monto_pagado,
        deuda_actual=deuda_actual,
        cuotas_pendientes=cuotas_pendientes,
        ahora=datetime.utcnow()
    )

# -------------------------------------------------------------
# 💵 REGISTRAR NUEVO PAGO (por pago_id específico)
# -------------------------------------------------------------
@bp.route("/registrar/<int:pago_id>", methods=["POST"], endpoint="registrar_pago")
@login_required
def registrar_pago(pago_id):
    pago = Pago.query.get_or_404(pago_id)
    
    # Verificar que el pago no esté ya validado o sea pago inicial
    if pago.estado in [ESTADO_PAGO_VALIDADO, ESTADO_PAGO_INICIAL]:
        flash("Este pago ya ha sido procesado.", "warning")
        return redirect(url_for("pagos.ficha", matricula_id=pago.matricula_id))
    
    # Procesar archivo
    file = request.files.get('comprobante')
    if not file or file.filename == '':
        flash("Debe adjuntar un comprobante de pago.", "danger")
        return redirect(url_for("pagos.ficha", matricula_id=pago.matricula_id))
    
    if not allowed_file(file.filename):
        flash("Formato de archivo no permitido. Use PDF, JPG o PNG.", "danger")
        return redirect(url_for("pagos.ficha", matricula_id=pago.matricula_id))
    
    # Verificar tamaño del archivo
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    if size_mb > MAX_FILE_MB:
        flash(f"El archivo supera {MAX_FILE_MB} MB.", "danger")
        return redirect(url_for("pagos.ficha", matricula_id=pago.matricula_id))
    
    # Guardar archivo
    upload_dir = ensure_upload_dir()
    filename = secure_filename(f"pago_{pago.id}_{datetime.utcnow().timestamp()}_{file.filename}")
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    # Actualizar pago
    pago.comprobante_path = filepath
    pago.fecha_pago = date.today()
    pago.estado = ESTADO_PAGO_PENDIENTE_VALIDACION
    
    db.session.commit()
    
    flash("Pago registrado correctamente. Esperando validación.", "success")
    return redirect(url_for("pagos.ficha", matricula_id=pago.matricula_id))

# -------------------------------------------------------------
# 📄 DETALLES DEL PAGO
# -------------------------------------------------------------
@bp.route("/detalles/<int:pago_id>", endpoint="detalles_pago")
@login_required
def detalles_pago(pago_id):
    pago = Pago.query.get_or_404(pago_id)
    
    # Calcular información financiera para el contexto
    monto_pagado = calcular_monto_pagado(pago.matricula_id)
    deuda_actual = calcular_deuda_actual(pago.matricula)
    
    return render_template("pagos/detalles_pago.html", 
                         pago=pago,
                         monto_pagado=monto_pagado,
                         deuda_actual=deuda_actual)

# -------------------------------------------------------------
# ✏️ EDITAR PAGO (para pagos rechazados o fuera de plazo)
# -------------------------------------------------------------
@bp.route("/editar/<int:pago_id>", methods=["GET", "POST"], endpoint="editar_pago")
@login_required
def editar_pago(pago_id):
    pago = Pago.query.get_or_404(pago_id)
    
    # Solo permitir edición de pagos rechazados o fuera de plazo
    if pago.estado not in [ESTADO_PAGO_RECHAZADO] and not pago.esta_vencido():
        flash("No puede editar este pago.", "warning")
        return redirect(url_for("pagos.ficha", matricula_id=pago.matricula_id))
    
    if request.method == "POST":
        file = request.files.get('comprobante')
        if not file or file.filename == '':
            flash("Debe adjuntar un comprobante de pago.", "danger")
            return redirect(url_for("pagos.editar_pago", pago_id=pago.id))
        
        if not allowed_file(file.filename):
            flash("Formato de archivo no permitido. Use PDF, JPG o PNG.", "danger")
            return redirect(url_for("pagos.editar_pago", pago_id=pago.id))
        
        # Verificar tamaño del archivo
        file.seek(0, os.SEEK_END)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        if size_mb > MAX_FILE_MB:
            flash(f"El archivo supera {MAX_FILE_MB} MB.", "danger")
            return redirect(url_for("pagos.editar_pago", pago_id=pago.id))
        
        # Eliminar archivo anterior si existe
        if pago.comprobante_path and os.path.exists(pago.comprobante_path):
            try:
                os.remove(pago.comprobante_path)
            except OSError:
                pass
        
        # Guardar nuevo archivo
        upload_dir = ensure_upload_dir()
        filename = secure_filename(f"pago_{pago.id}_{datetime.utcnow().timestamp()}_{file.filename}")
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Actualizar pago
        pago.comprobante_path = filepath
        pago.fecha_pago = date.today()
        pago.estado = ESTADO_PAGO_PENDIENTE_VALIDACION
        pago.motivo_rechazo = None
        
        db.session.commit()
        
        flash("Pago actualizado correctamente. Esperando validación.", "success")
        return redirect(url_for("pagos.ficha", matricula_id=pago.matricula_id))
    
    return render_template("pagos/editar_pago.html", pago=pago)

# -------------------------------------------------------------
# 👁️ VISUALIZAR COMPROBANTE
# -------------------------------------------------------------
@bp.route("/comprobante/<int:pago_id>", endpoint="ver_comprobante")
@login_required
def ver_comprobante(pago_id):
    pago = Pago.query.get_or_404(pago_id)
    
    if not pago.comprobante_path or not os.path.exists(pago.comprobante_path):
        abort(404)
    
    return send_file(pago.comprobante_path, as_attachment=False)

# -------------------------------------------------------------
# 📥 DESCARGAR COMPROBANTE
# -------------------------------------------------------------
@bp.route("/descargar/<int:pago_id>", endpoint="descargar_comprobante")
@login_required
def descargar_comprobante(pago_id):
    pago = Pago.query.get_or_404(pago_id)
    
    if not pago.comprobante_path or not os.path.exists(pago.comprobante_path):
        abort(404)
    
    return send_file(pago.comprobante_path, as_attachment=True, download_name=os.path.basename(pago.comprobante_path))