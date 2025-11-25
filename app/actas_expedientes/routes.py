from flask import render_template, request, abort
from flask_login import login_required
from app.extensions import db
from app.matriculas.models import Matricula, MatriculaAsignatura, ESTADO_MAT_VALIDADA
from . import bp

@bp.route("/")
@login_required
def index():
    """
    Listado de 'Expedientes' (Estudiantes únicos).
    Dado que no hay tabla de Estudiantes, agrupamos por doc_identidad.
    """
    search = request.args.get("search", "").strip()

    # Consulta base: solo matrículas validadas (o todas, según criterio)
    # Para expedientes, tiene sentido ver a cualquiera que haya estado matriculado alguna vez.
    query = db.session.query(
        Matricula.doc_identidad,
        Matricula.estudiante_nombre,
        db.func.count(Matricula.id).label("num_matriculas"),
        db.func.max(Matricula.created_at).label("ultimo_registro")
    ).group_by(Matricula.doc_identidad, Matricula.estudiante_nombre)

    if search:
        query = query.filter(
            db.or_(
                Matricula.estudiante_nombre.ilike(f"%{search}%"),
                Matricula.doc_identidad.ilike(f"%{search}%")
            )
        )
    
    # Ordenar por el registro más reciente
    estudiantes = query.order_by(db.desc("ultimo_registro")).all()

    return render_template("actas_expedientes/index.html", estudiantes=estudiantes, search=search)


@bp.route("/expediente/<path:doc_identidad>")
@login_required
def detalle(doc_identidad):
    """
    Ver el historial académico completo de un estudiante (agrupado por DNI).
    """
    # Obtener todas las matrículas de este documento
    matriculas = Matricula.query.filter_by(doc_identidad=doc_identidad).order_by(Matricula.created_at.desc()).all()

    if not matriculas:
        abort(404)

    # Datos personales tomados de la matrícula más reciente
    estudiante = {
        "nombre": matriculas[0].estudiante_nombre,
        "doc_identidad": matriculas[0].doc_identidad,
        "email": matriculas[0].email,
        "telefono": matriculas[0].telefono,
        "direccion": matriculas[0].direccion,
    }

    # Estructurar historial académico
    historial = []
    for m in matriculas:
        asignaturas = MatriculaAsignatura.query.filter_by(matricula_id=m.id).all()
        
        # Calcular promedio si hay notas
        notas = [a.nota for a in asignaturas if a.nota is not None]
        promedio = sum(notas) / len(notas) if notas else None

        historial.append({
            "matricula": m,
            "curso": m.curso,
            "asignaturas": asignaturas,
            "promedio": promedio
        })

    return render_template("actas_expedientes/detalle.html", estudiante=estudiante, historial=historial)

