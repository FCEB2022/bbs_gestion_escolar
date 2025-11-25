from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, IntegerField, SelectField,
    FieldList, FormField, HiddenField, SubmitField, DateField
)
from wtforms.validators import DataRequired, NumberRange, Optional, Length

from .models import CURSO_TIPO_FP, CURSO_TIPO_INTENSIVO


# ---------------- SUBFORMULARIO DE MÓDULO ----------------
class ModuloForm(FlaskForm):
    """Subformulario para agregar módulos a un curso."""
    class Meta:
        csrf = False  # 🔹 Desactiva CSRF en los subformularios internos

    _row_id = HiddenField()
    nombre = StringField("Nombre del módulo", validators=[DataRequired(), Length(max=200)])
    horas_modulo = IntegerField("Horas del módulo", validators=[DataRequired(), NumberRange(min=1)])
    docente_nombre = StringField("Docente", validators=[Optional(), Length(max=200)])
    temario = TextAreaField("Temario", validators=[Optional(), Length(max=10000)])

    anio_fp = SelectField(
        "Año (FP)",
        choices=[("", "—"), ("1", "1º"), ("2", "2º")],
        validators=[Optional()]
    )
    semestre_fp = SelectField(
        "Semestre (FP)",
        choices=[("", "—"), ("1", "1º"), ("2", "2º")],
        validators=[Optional()]
    )

# ---------------- CREACIÓN DE CURSO DESDE CERO ----------------
class CursoNuevoForm(FlaskForm):
    """Formulario principal para crear un curso desde cero."""
    nombre = StringField("Nombre del curso", validators=[DataRequired(), Length(max=200)])
    tipo = SelectField(
        "Tipo de curso",
        choices=[
            (CURSO_TIPO_FP, "Formación Profesional (FP)"),
            (CURSO_TIPO_INTENSIVO, "Curso Intensivo")
        ],
        validators=[DataRequired()],
    )
    horas_totales = IntegerField("Horas totales", validators=[DataRequired(), NumberRange(min=1)])
    horas_semanales = IntegerField("Horas semanales", validators=[DataRequired(), NumberRange(min=1)])

    # Lista de módulos (al menos uno)
    modulos = FieldList(FormField(ModuloForm), min_entries=1)

    submit = SubmitField("Guardar")


# ---------------- CREACIÓN DE CURSO DESDE PLANTILLA ----------------
class CursoDesdePlantillaForm(FlaskForm):
    """Formulario para crear un curso usando otra plantilla existente."""
    nombre = StringField("Nombre del nuevo curso", validators=[DataRequired(), Length(max=200)])
    plantilla_id = SelectField("Plantilla", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Crear desde plantilla")


# ---------------- PROGRAMAR CURSO FP ----------------
class ProgramarFPForm(FlaskForm):
    anio_escolar_inicio = StringField(
        "Año escolar inicial (formato YYYY-YYYY)",
        validators=[DataRequired(), Length(min=9, max=9, message="Usa formato YYYY-YYYY")]
    )
    fecha_inicio_anio1 = DateField("Fecha de inicio del primer año", validators=[DataRequired()])
    fecha_inicio_anio2 = DateField("Fecha de inicio del segundo año", validators=[DataRequired()])
    
    guardar = SubmitField("Guardar programación")

class CancelarCursoForm(FlaskForm):
    motivo = TextAreaField("Motivo de cancelación", validators=[DataRequired()])
    confirmar = SubmitField("Confirmar cancelación")

class CerrarCursoForm(FlaskForm):
    confirmar = SubmitField("Confirmar cierre")


# ---------------- PROGRAMAR CURSO INTENSIVO ----------------
class ProgramarIntensivoForm(FlaskForm):
    """Formulario para programar cursos intensivos."""
    fecha_inicio = DateField("Fecha de inicio", validators=[DataRequired()])
    submit = SubmitField("Programar curso intensivo")
