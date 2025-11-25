import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.usuarios.models import Usuario
from . import bp
from .models import Documento
from .forms import EntradaForm, SalidaForm

# ====== Configuración de subida ======
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_MB = 20

def ensure_upload_dir():
    """Crea (si no existe) la carpeta de subida."""
    updir = current_app.config.get(
        "UPLOAD_FOLDER",
        os.path.join(current_app.instance_path, "uploads", "documentos")
    )
    os.makedirs(updir, exist_ok=True)
    return updir

def allowed_file(filename: str) -> bool:
    """Comprueba si la extensión es válida."""
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


# ====== Landing del módulo: tarjetas ENTRADAS / SALIDAS / ESTADÍSTICAS ======
@bp.route("/")
@login_required
def index():
    total_entradas = db.session.query(Documento).filter_by(tipo="entrada").count()
    total_salidas = db.session.query(Documento).filter_by(tipo="salida").count()
    return render_template(
        "documentos/index.html",
        total_entradas=total_entradas,
        total_salidas=total_salidas
    )


# ====== Listados con filtros ======
@bp.route("/entradas")
@login_required
def entradas():
    q = Documento.query.filter_by(tipo="entrada")

    # filtros
    f_ini = request.args.get("fecha_inicio")
    f_fin = request.args.get("fecha_fin")
    if f_ini:
        q = q.filter(Documento.fecha >= datetime.fromisoformat(f_ini).date())
    if f_fin:
        q = q.filter(Documento.fecha <= datetime.fromisoformat(f_fin).date())

    term = request.args.get("q", "").strip()
    if term:
        like = f"%{term}%"
        q = q.filter(
            db.or_(
                Documento.numero_referencia.ilike(like),
                Documento.remitente.ilike(like),
                Documento.descripcion.ilike(like),
                Documento.observaciones.ilike(like),
            )
        )

    docs = q.order_by(Documento.created_at.desc()).all()
    return render_template("documentos/entradas.html", docs=docs)


@bp.route("/salidas")
@login_required
def salidas():
    q = Documento.query.filter_by(tipo="salida")
    f_ini = request.args.get("fecha_inicio")
    f_fin = request.args.get("fecha_fin")
    if f_ini:
        q = q.filter(Documento.fecha >= datetime.fromisoformat(f_ini).date())
    if f_fin:
        q = q.filter(Documento.fecha <= datetime.fromisoformat(f_fin).date())

    term = request.args.get("q", "").strip()
    if term:
        like = f"%{term}%"
        q = q.filter(
            db.or_(
                Documento.numero_referencia.ilike(like),
                Documento.destinatario.ilike(like),
                Documento.remitente_interno.ilike(like),
                Documento.descripcion.ilike(like),
                Documento.observaciones.ilike(like),
            )
        )

    docs = q.order_by(Documento.created_at.desc()).all()
    return render_template("documentos/salidas.html", docs=docs)


# ====== Crear nuevo registro (entradas/salidas) ======
@bp.route("/nuevo/<string:tipo>", methods=["GET", "POST"])
@login_required
def nuevo(tipo):
    if tipo not in ("entrada", "salida"):
        abort(404)

    form = EntradaForm() if tipo == "entrada" else SalidaForm()

    # Autogenerar referencia al cargar el formulario
    if request.method == "GET":
        form.numero_referencia.data = Documento.generar_referencia(tipo)

    if form.validate_on_submit():
        file = request.files.get("archivo")
        if not file or file.filename == "":
            flash("Debes seleccionar un archivo.", "warning")
            return render_template("documentos/nuevo.html", form=form, tipo=tipo)

        filename = secure_filename(file.filename)
        if not allowed_file(filename):
            flash("Tipo de archivo no permitido. Solo PDF, JPG o PNG.", "danger")
            return render_template("documentos/nuevo.html", form=form, tipo=tipo)

        file.seek(0, os.SEEK_END)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        if size_mb > MAX_FILE_MB:
            flash(f"El archivo supera {MAX_FILE_MB} MB.", "danger")
            return render_template("documentos/nuevo.html", form=form, tipo=tipo)

        # Crear registro
        doc = Documento(
            numero_referencia=form.numero_referencia.data.strip(),
            tipo=tipo,
            fecha=(form.fecha_recepcion.data if tipo == "entrada" else form.fecha_despacho.data),
            remitente=(form.remitente.data if tipo == "entrada" else None),
            destinatario=(form.destinatario.data if tipo == "salida" else None),
            remitente_interno=(form.remitente_interno.data if tipo == "salida" else None),
            descripcion=form.descripcion.data.strip(),
            observaciones=(form.observaciones.data or "").strip(),
            filename=filename,
            version=1,
            created_by=current_user,
        )
        db.session.add(doc)
        db.session.commit()

        # Guardar archivo físico
        updir = ensure_upload_dir()
        ext = os.path.splitext(filename)[1].lower()
        target = os.path.join(updir, f"{doc.numero_referencia}_v1{ext}")
        file.save(target)

        flash("Registro guardado correctamente.", "success")
        return redirect(url_for("documentos.entradas" if tipo == "entrada" else "documentos.salidas"))

    return render_template("documentos/nuevo.html", form=form, tipo=tipo)


# ====== Ver detalle ======
@bp.route("/detalle/<int:doc_id>")
@login_required
def detalle(doc_id):
    doc = db.session.get(Documento, doc_id) or abort(404)
    return render_template("documentos/detalle.html", doc=doc)


# ====== Editar ======
@bp.route("/editar/<int:doc_id>", methods=["GET", "POST"])
@login_required
def editar(doc_id):
    doc = db.session.get(Documento, doc_id) or abort(404)
    form = EntradaForm() if doc.tipo == "entrada" else SalidaForm()

    # Mapear valores al formulario
    if request.method == "GET":
        form.numero_referencia.data = doc.numero_referencia
        if doc.tipo == "entrada":
            form.fecha_recepcion.data = doc.fecha
            form.remitente.data = doc.remitente or ""
        else:
            form.fecha_despacho.data = doc.fecha
            form.destinatario.data = doc.destinatario or ""
            form.remitente_interno.data = doc.remitente_interno or ""
        form.descripcion.data = doc.descripcion
        form.observaciones.data = doc.observaciones or ""

    if form.validate_on_submit():
        file = request.files.get("archivo")
        if file and file.filename:
            filename = secure_filename(file.filename)
            if not allowed_file(filename):
                flash("Tipo de archivo no permitido.", "danger")
                return render_template("documentos/nuevo.html", form=form, tipo=doc.tipo)

            file.seek(0, os.SEEK_END)
            size_mb = file.tell() / (1024 * 1024)
            file.seek(0)
            if size_mb > MAX_FILE_MB:
                flash(f"El archivo supera {MAX_FILE_MB}MB.", "danger")
                return render_template("documentos/nuevo.html", form=form, tipo=doc.tipo)

            # Nueva versión
            doc.version += 1
            doc.filename = filename
            updir = ensure_upload_dir()
            ext = os.path.splitext(filename)[1].lower()
            target = os.path.join(updir, f"{doc.numero_referencia}_v{doc.version}{ext}")
            file.save(target)

        # Actualizar datos
        doc.fecha = form.fecha_recepcion.data if doc.tipo == "entrada" else form.fecha_despacho.data
        doc.remitente = form.remitente.data if doc.tipo == "entrada" else None
        doc.destinatario = form.destinatario.data if doc.tipo == "salida" else None
        doc.remitente_interno = form.remitente_interno.data if doc.tipo == "salida" else None
        doc.descripcion = form.descripcion.data.strip()
        doc.observaciones = (form.observaciones.data or "").strip()

        db.session.commit()
        flash("Registro actualizado correctamente.", "success")
        return redirect(url_for("documentos.detalle", doc_id=doc.id))

    return render_template("documentos/nuevo.html", form=form, tipo=doc.tipo)


# ====== Eliminar (solo admin) ======
@bp.route("/eliminar/<int:doc_id>", methods=["POST"])
@login_required
def eliminar(doc_id):
    if "Administrador" not in {r.nombre for r in current_user.roles}:
        abort(403)
    doc = db.session.get(Documento, doc_id) or abort(404)
    db.session.delete(doc)
    db.session.commit()
    flash("Registro eliminado.", "success")
    return redirect(url_for("documentos.entradas" if doc.tipo == "entrada" else "documentos.salidas"))


# ====== Visualizar/Descargar ======
@bp.route("/ver/<int:doc_id>")
@login_required
def ver_archivo(doc_id):
    doc = db.session.get(Documento, doc_id) or abort(404)
    path = doc.file_path
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=False)


@bp.route("/descargar/<int:doc_id>")
@login_required
def descargar(doc_id):
    doc = db.session.get(Documento, doc_id) or abort(404)
    path = doc.file_path
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=os.path.basename(path))


# ====== Estadísticas ======
@bp.route("/estadisticas")
@login_required
def estadisticas():
    total_entradas = db.session.query(Documento).filter_by(tipo="entrada").count()
    total_salidas = db.session.query(Documento).filter_by(tipo="salida").count()
    return render_template(
        "documentos/estadisticas.html",
        total_entradas=total_entradas,
        total_salidas=total_salidas
    )
