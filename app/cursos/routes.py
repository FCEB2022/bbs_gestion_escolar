from datetime import date, timedelta
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.usuarios.models import Usuario
from . import bp
from .models import (
    Curso, Modulo, Programacion,
    CURSO_TIPO_FP, CURSO_TIPO_INTENSIVO,
    ESTADO_BORRADOR, ESTADO_VALIDADO, ESTADO_PROGRAMADO,
    PROG_PENDIENTE, PROG_VALIDADA,
)
from .forms import (
    CursoNuevoForm, CursoDesdePlantillaForm,
    ProgramarFPForm, ProgramarIntensivoForm, CancelarCursoForm, CerrarCursoForm
)
from flask_wtf import FlaskForm

# IMPORT ADICIONAL: modelo para borrar asignaturas ligadas a módulos
from app.matriculas.models import MatriculaAsignatura

# IMPORT PARA REGISTRO DE ACTIVIDAD
from app.models_shared import registrar_actividad

# ✅ formulario vacío para poder usar csrf_token() en templates
class DummyForm(FlaskForm):
    """Formulario vacío solo para incluir token CSRF en vistas informativas."""
    pass
# ----------------- helpers permisos -----------------
def es_admin() -> bool:
    return any(r.nombre == "Administrador" for r in current_user.roles)

def es_administrativo() -> bool:
    return any(r.nombre == "Administrativo" for r in current_user.roles)

def puede_crear_o_editar() -> bool:
    return es_admin() or es_administrativo()


def _flash_form_errors(form):
    """Muestra mensajes de error de validación."""
    for field, errors in form.errors.items():
        for err in errors:
            flash(f"{getattr(form, field).label.text}: {err}", "danger")


# ----------------- INDEX -----------------
@bp.route("/")
@login_required
def index():
    # ✅ Traer todos los cursos, sin importar estado
    cursos_fp = (Curso.query
                 .filter(Curso.tipo == CURSO_TIPO_FP)
                 .order_by(Curso.created_at.desc())
                 .all())

    cursos_int = (Curso.query
                  .filter(Curso.tipo == CURSO_TIPO_INTENSIVO)
                  .order_by(Curso.created_at.desc())
                  .all())

    # Filtro de búsqueda opcional
    filtro = request.args.get("q", "").strip()
    if filtro:
        like = f"%{filtro}%"
        cursos_fp = [c for c in cursos_fp if filtro.lower() in c.nombre.lower()]
        cursos_int = [c for c in cursos_int if filtro.lower() in c.nombre.lower()]

    # ✅ Métricas globales (no cambian)
    total_validados = Curso.query.filter(Curso.estado == ESTADO_VALIDADO).count()
    total_borrador = Curso.query.filter(Curso.estado == ESTADO_BORRADOR).count()
    total_programados = Curso.query.filter(Curso.estado == ESTADO_PROGRAMADO).count()
    total_cancelados = Curso.query.filter(Curso.estado == "CANCELADO").count()
    total_cerrados = Curso.query.filter(Curso.estado == "CERRADO").count()

    return render_template(
        "cursos/index.html",
        cursos_fp=cursos_fp,
        cursos_int=cursos_int,
        total_validados=total_validados,
        total_borrador=total_borrador,
        total_programados=total_programados,
        total_cancelados=total_cancelados,
        total_cerrados=total_cerrados
    )

# ----------------- CREAR -----------------
@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if not puede_crear_o_editar():
        abort(403)

    modo = request.args.get("modo", "vacio")  # "vacio" o "plantilla"

    # ----- desde plantilla -----
    if modo == "plantilla":
        form = CursoDesdePlantillaForm()
        plantillas = (Curso.query
                      .filter(Curso.estado == ESTADO_VALIDADO, Curso.es_plantilla.is_(True))
                      .order_by(Curso.nombre.asc())
                      .all())
        form.plantilla_id.choices = [(c.id, c.nombre) for c in plantillas]

        if request.method == "POST":
            if form.validate_on_submit():
                plantilla = db.session.get(Curso, form.plantilla_id.data)
                if not plantilla or plantilla.estado != ESTADO_VALIDADO or not plantilla.es_plantilla:
                    flash("Plantilla no válida.", "danger")
                    return render_template("cursos/nuevo.html", modo=modo, form=form)

                nuevo = Curso(
                    nombre=form.nombre.data.strip(),
                    tipo=plantilla.tipo,
                    horas_totales=plantilla.horas_totales,
                    horas_semanales=plantilla.horas_semanales,
                    estado=ESTADO_BORRADOR,
                    es_plantilla=False,
                    created_by=current_user,
                )
                db.session.add(nuevo)
                db.session.flush()

                for m in plantilla.modulos:
                    db.session.add(Modulo(
                        curso_id=nuevo.id,
                        nombre=m.nombre,
                        horas_modulo=m.horas_modulo,
                        docente_nombre=m.docente_nombre,
                        temario=m.temario,
                        anio_fp=m.anio_fp,
                        semestre_fp=m.semestre_fp,
                    ))

                db.session.commit()
                # Registrar actividad de creación de curso (opcional, seguro)
                try:
                    registrar_actividad(current_user, f"Creó curso {nuevo.nombre}")
                except Exception:
                    pass

                flash("Curso creado desde plantilla. Ahora puedes ajustarlo.", "success")
                return redirect(url_for("cursos.detalle", curso_id=nuevo.id))
            else:
                _flash_form_errors(form)

        return render_template("cursos/nuevo.html", modo=modo, form=form)

    # ----- curso en blanco -----
    form = CursoNuevoForm()

    # asegurar al menos un módulo visible al cargar el formulario
    if request.method == "GET" and not form.modulos.entries:
        form.modulos.append_entry()

    if request.method == "POST":
        if form.validate_on_submit():
            # ✅ Ya NO comprobamos duplicado de nombre
            curso = Curso(
                nombre=form.nombre.data.strip(),
                tipo=form.tipo.data,
                horas_totales=form.horas_totales.data,
                horas_semanales=form.horas_semanales.data,
                estado=ESTADO_BORRADOR,
                es_plantilla=False,
                created_by=current_user,
            )
            db.session.add(curso)
            db.session.flush()

            # módulos
            for f in form.modulos.entries:
                anio_fp = int(f.anio_fp.data) if f.anio_fp.data else None
                semestre_fp = int(f.semestre_fp.data) if f.semestre_fp.data else None
                if form.tipo.data == CURSO_TIPO_INTENSIVO:
                    anio_fp = None
                    semestre_fp = None

                db.session.add(Modulo(
                    curso_id=curso.id,
                    nombre=f.nombre.data.strip(),
                    horas_modulo=f.horas_modulo.data,
                    docente_nombre=(f.docente_nombre.data or "").strip(),
                    temario=(f.temario.data or "").strip(),
                    anio_fp=anio_fp,
                    semestre_fp=semestre_fp,
                ))

            db.session.commit()
            # Registrar actividad de creación de curso (opcional, seguro)
            try:
                registrar_actividad(current_user, f"Creó curso {curso.nombre}")
            except Exception:
                pass

            flash("Curso creado correctamente (borrador).", "success")
            return redirect(url_for("cursos.detalle", curso_id=curso.id))
        else:
            _flash_form_errors(form)

    return render_template("cursos/nuevo.html", modo="vacio", form=form)


# ----------------- DETALLE -----------------
from flask_wtf import FlaskForm

class DummyForm(FlaskForm):
    """Formulario vacío solo para CSRF en acciones POST."""
    pass


@bp.route("/<int:curso_id>")
@login_required
def detalle(curso_id):
    curso = db.session.get(Curso, curso_id) or abort(404)

    # Inicializamos grupos de forma segura
    grupos = {}

    if curso.tipo == CURSO_TIPO_FP:
        grupos = {1: {1: [], 2: []}, 2: {1: [], 2: []}}
        for m in curso.modulos:
            if m.anio_fp in (1, 2) and m.semestre_fp in (1, 2):
                grupos[m.anio_fp][m.semestre_fp].append(m)

    # Para intensivos o cursos sin módulos FP, grupos se queda vacío
    form = DummyForm()
    return render_template("cursos/detalle.html", curso=curso, grupos=grupos, form=form)
# ----------------- EDITAR -----------------
@bp.route("/<int:curso_id>/editar", methods=["GET", "POST"])
@login_required
def editar(curso_id):
    curso = db.session.get(Curso, curso_id) or abort(404)

    # Modificación: permitir que tanto Administrador como Administrativo editen cursos
    if curso.estado in (ESTADO_VALIDADO, ESTADO_PROGRAMADO) and not (es_admin() or es_administrativo()):
        abort(403)

    form = CursoNuevoForm()

    if request.method == "GET":
        form.nombre.data = curso.nombre
        form.tipo.data = curso.tipo
        form.horas_totales.data = curso.horas_totales
        form.horas_semanales.data = curso.horas_semanales

        form.modulos.entries = []
        for m in curso.modulos:
            f = form.modulos.append_entry()
            f.nombre.data = m.nombre
            f.horas_modulo.data = m.horas_modulo
            f.docente_nombre.data = m.docente_nombre
            f.temario.data = m.temario
            f.anio_fp.data = m.anio_fp
            f.semestre_fp.data = m.semestre_fp

        return render_template("cursos/editar.html", form=form, curso=curso)

    if form.validate_on_submit():
        curso.nombre = form.nombre.data.strip()
        curso.tipo = form.tipo.data
        curso.horas_totales = form.horas_totales.data
        curso.horas_semanales = form.horas_semanales.data

        # ===== CAMBIO CRÍTICO (previene IntegrityError) =====
        # Borrar todas las MatriculaAsignatura que referencian a los módulos actuales
        # del curso antes de eliminar los módulos en sí. Esto evita que SQLAlchemy intente
        # hacer un UPDATE poniendo modulo_id = NULL y con ello romper la restricción NOT NULL.
        try:
            module_ids = [m.id for m in curso.modulos if getattr(m, "id", None) is not None]
            if module_ids:
                MatriculaAsignatura.query.filter(MatriculaAsignatura.modulo_id.in_(module_ids)).delete(synchronize_session=False)
        except Exception as e:
            # No hacemos rollback aquí; registramos mensaje y seguimos — la excepción se lanzará en flush si algo va mal.
            flash("Advertencia al limpiar asignaciones anteriores: " + str(e), "warning")

        # Ahora sí limpiamos los módulos y añadimos los nuevos
        curso.modulos.clear()
        db.session.flush()

        for f in form.modulos.entries:
            anio_fp = int(f.anio_fp.data) if f.anio_fp.data else None
            semestre_fp = int(f.semestre_fp.data) if f.semestre_fp.data else None
            if curso.tipo == CURSO_TIPO_INTENSIVO:
                anio_fp = None
                semestre_fp = None

            db.session.add(Modulo(
                curso_id=curso.id,
                nombre=f.nombre.data.strip(),
                horas_modulo=f.horas_modulo.data,
                docente_nombre=(f.docente_nombre.data or "").strip(),
                temario=(f.temario.data or "").strip(),
                anio_fp=anio_fp,
                semestre_fp=semestre_fp,
            ))

        if curso.estado in (ESTADO_VALIDADO, ESTADO_PROGRAMADO):
            curso.estado = ESTADO_BORRADOR
            if curso.programacion:
                curso.programacion.estado_programacion = PROG_PENDIENTE

        db.session.commit()

        # Registrar actividad de edición del curso (audit trail)
        try:
            registrar_actividad(current_user, f"Editó curso {curso.nombre}")
        except Exception:
            # No fallamos si el logger de actividad da error
            pass

        flash("Curso actualizado correctamente.", "success")
        return redirect(url_for("cursos.detalle", curso_id=curso.id))

    _flash_form_errors(form)
    return render_template("cursos/editar.html", form=form, curso=curso)


# ----------------- VALIDAR (solo admin) -----------------
@bp.route("/<int:curso_id>/validar", methods=["POST"])
@login_required
def validar(curso_id):
    if not es_admin():
        abort(403)
    curso = db.session.get(Curso, curso_id) or abort(404)
    if curso.estado != ESTADO_BORRADOR:
        flash("El curso no está en estado BORRADOR.", "warning")
        return redirect(url_for("cursos.detalle", curso_id=curso.id))

    total_mod = sum(m.horas_modulo for m in curso.modulos)
    if total_mod != curso.horas_totales:
        flash("Atención: la suma de horas de módulos no coincide con las horas del curso.", "warning")

    curso.estado = ESTADO_VALIDADO
    db.session.commit()
    flash("Curso validado correctamente.", "success")
    return redirect(url_for("cursos.detalle", curso_id=curso.id))


# ----------------- TOGGLE PLANTILLA -----------------
@bp.route("/<int:curso_id>/toggle-plantilla", methods=["POST"])
@login_required
def toggle_plantilla(curso_id):
    if not es_admin():
        abort(403)
    curso = db.session.get(Curso, curso_id) or abort(404)
    if curso.estado != ESTADO_VALIDADO:
        flash("Solo cursos validados pueden ser marcados como plantilla.", "warning")
        return redirect(url_for("cursos.detalle", curso_id=curso.id))
    curso.es_plantilla = not curso.es_plantilla
    db.session.commit()
    flash(("Marcado" if curso.es_plantilla else "Desmarcado") + " como plantilla.", "success")
    return redirect(url_for("cursos.detalle", curso_id=curso.id))


# ----------------- PROGRAMAR -----------------
@bp.route("/<int:curso_id>/programar", methods=["GET", "POST"])
@login_required
def programar(curso_id):
    curso = db.session.get(Curso, curso_id) or abort(404)
    if not es_admin():
        abort(403)
    if curso.estado != ESTADO_VALIDADO:
        flash("Solo cursos validados pueden programarse.", "warning")
        return redirect(url_for("cursos.detalle", curso_id=curso.id))

    if curso.tipo == CURSO_TIPO_FP:
        form = ProgramarFPForm()
        if form.validate_on_submit():
            ini = (form.anio_escolar_inicio.data or "").strip()
            # Validamos formato simple YYYY-YYYY
            try:
                y1, y2 = ini.split("-")
                y1i, y2i = int(y1), int(y2)
                if y2i != y1i + 1:  # p.ej. 2025-2026
                    raise ValueError
            except Exception:
                flash("Formato de año escolar inválido. Usa 'YYYY-YYYY' (ej. 2025-2026).", "danger")
                return render_template("cursos/programar.html", curso=curso, form=form)

            anio_fin = f"{y2i}-{y2i + 1}"

            prog = Programacion(
                curso=curso,
                tipo=curso.tipo,
                anio_escolar_inicio=ini,
                anio_escolar_fin=anio_fin,
                estado_programacion=PROG_PENDIENTE,  # siempre inicia pendiente
            )

            # ✅ Si tu modelo ya tiene fecha_inicio_anio1/fecha_inicio_anio2, las guardamos.
            #    Si aún no existen en tu tabla, esto no rompe (se ignora en flush).
            setattr(prog, "fecha_inicio_anio1", form.fecha_inicio_anio1.data)
            setattr(prog, "fecha_inicio_anio2", form.fecha_inicio_anio2.data)

            db.session.add(prog)
            db.session.commit()
            return redirect(url_for("cursos.programacion_revision", curso_id=curso.id))

        return render_template("cursos/programar.html", curso=curso, form=form)

    # Intensivo
    form = ProgramarIntensivoForm()
    if form.validate_on_submit():
        fi = form.fecha_inicio.data
        ff = Programacion.calcular_fin_intensivo(fi, curso.horas_totales, curso.horas_semanales)
        prog = Programacion(
            curso=curso,
            tipo=curso.tipo,
            fecha_inicio=fi,
            fecha_fin=ff,
            estado_programacion=PROG_PENDIENTE,
        )
        db.session.add(prog)
        db.session.commit()
        return redirect(url_for("cursos.programacion_revision", curso_id=curso.id))
    return render_template("cursos/programar.html", curso=curso, form=form)


# -------- revisión de programación (rejilla por meses) --------
@bp.route("/<int:curso_id>/programacion/revision")
@login_required
def programacion_revision(curso_id):
    curso = db.session.get(Curso, curso_id) or abort(404)
    prog = curso.programacion or abort(404)

    semanas_por_mes = None
    if curso.tipo == CURSO_TIPO_INTENSIVO and prog.fecha_inicio and prog.fecha_fin:
        cur = prog.fecha_inicio
        semanas = []
        while cur <= prog.fecha_fin:
            inicio_sem = cur - timedelta(days=cur.weekday())
            fin_sem = inicio_sem + timedelta(days=6)
            semanas.append((inicio_sem, fin_sem))
            cur = fin_sem + timedelta(days=1)

        semanas_por_mes = {}
        for ini, fin in semanas:
            mkey = ini.strftime("%Y-%m")
            semanas_por_mes.setdefault(mkey, []).append((ini, fin))

    return render_template("cursos/programacion_revision.html",
                           curso=curso, prog=prog, semanas_por_mes=semanas_por_mes)


# -------- validar programación --------
@bp.route("/<int:curso_id>/programacion/validar", methods=["POST"])
@login_required
def programacion_validar(curso_id):
    if not es_admin():
        abort(403)
    curso = db.session.get(Curso, curso_id) or abort(404)
    prog = curso.programacion or abort(404)

    prog.estado_programacion = PROG_VALIDADA
    curso.estado = ESTADO_PROGRAMADO
    db.session.commit()
    flash("Programación validada correctamente.", "success")
    return redirect(url_for("cursos.detalle", curso_id=curso.id))

# --- DESPROGRAMAR ---
@bp.route("/<int:curso_id>/desprogramar", methods=["POST"])
@login_required
def desprogramar(curso_id):
    curso = Curso.query.get_or_404(curso_id)

    # ✅ Comprobamos permisos usando las funciones helper definidas arriba
    if not (es_admin() or es_administrativo()):
        flash("No tienes permisos para desprogramar cursos.", "danger")
        return redirect(url_for("cursos.detalle", curso_id=curso.id))

    # ✅ Desprogramación limpia y segura
    if curso.programacion:
        db.session.delete(curso.programacion)
        curso.programacion = None

    curso.estado = ESTADO_VALIDADO  # vuelve al estado anterior para permitir reprogramar
    db.session.commit()

    flash("Curso desprogramado correctamente. Puedes reprogramarlo con nuevas fechas.", "success")
    return redirect(url_for("cursos.detalle", curso_id=curso.id))

# --- CANCELAR ---
@bp.route("/<int:curso_id>/cancelar", methods=["GET", "POST"])
@login_required
def cancelar(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    form = CancelarCursoForm()

    # ✅ Control de permisos
    if not (es_admin() or es_administrativo()):
        flash("No tienes permisos para cancelar cursos.", "danger")
        return redirect(url_for("cursos.detalle", curso_id=curso.id))

    # ✅ Si el formulario se envía correctamente
    if form.validate_on_submit():
        curso.estado = "CANCELADO"
        curso.motivo_cancelacion = form.motivo.data.strip()
        db.session.commit()
        flash("Curso cancelado correctamente. En espera de validación.", "warning")
        return redirect(url_for("cursos.detalle", curso_id=curso.id))

    return render_template("cursos/cancelar.html", curso=curso, form=form)


# --- CERRAR ---
@bp.route("/<int:curso_id>/cerrar", methods=["GET", "POST"])
@login_required
def cerrar(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    form = CerrarCursoForm()

    # ✅ Control de permisos
    if not (es_admin() or es_administrativo()):
        flash("No tienes permisos para cerrar cursos.", "danger")
        return redirect(url_for("cursos.detalle", curso_id=curso.id))

    if form.validate_on_submit():
        curso.estado = "CERRADO"
        db.session.commit()
        flash("Curso cerrado exitosamente.", "success")
        return redirect(url_for("cursos.detalle", curso_id=curso.id))

    return render_template("cursos/cerrar.html", curso=curso, form=form)


@bp.route("/desde_plantilla")
@login_required
def desde_plantilla():
    """Crear un nuevo curso basado en una plantilla existente"""
    # Recuperamos las plantillas disponibles
    plantillas = Curso.query.filter_by(es_plantilla=True).all()
    return render_template("cursos/desde_plantilla.html", plantillas=plantillas)