# app/matriculas/forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    RadioField,
    TextAreaField,
    SubmitField,
    HiddenField,
    FloatField,
    IntegerField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired

# -------------------------------------------------------------------
# OPCIONES DE CAMPUS
# -------------------------------------------------------------------
CAMPUS_CHOICES = [("BATA", "BATA"), ("MALABO", "MALABO")]

# -------------------------------------------------------------------
# FORMULARIO DE FILTROS (para la vista de lista)
# -------------------------------------------------------------------
class FiltrosTablaForm(FlaskForm):
    """Filtros para la tabla de matrículas"""
    q = StringField("Buscar", validators=[Optional()])
    campus = SelectField("Campus", choices=[("", "Todos")] + CAMPUS_CHOICES, validators=[Optional()])
    estado = SelectField(
        "Estado",
        choices=[
            ("", "Todos"),
            ("PENDIENTE_VALIDACION", "Pendiente"),
            ("VALIDADA", "Validada"),
            ("RECHAZADA", "Rechazada"),
        ],
        validators=[Optional()],
    )

# -------------------------------------------------------------------
# FORMULARIO BASE DE MATRÍCULA (común para FP e Intensivo)
# -------------------------------------------------------------------
class MatriculaBaseForm(FlaskForm):
    """Formulario base de matrícula (datos personales + documentos requeridos)"""

    # Datos personales
    estudiante_nombre = StringField("Nombre completo", validators=[DataRequired(), Length(max=150)])
    doc_identidad = StringField("Documento de identidad", validators=[Optional(), Length(max=64)])
    telefono = StringField("Teléfono", validators=[Optional(), Length(max=32)])
    email = StringField("Correo electrónico", validators=[Optional(), Length(max=120)])
    direccion = StringField("Dirección", validators=[Optional(), Length(max=200)])
    campus = SelectField("Campus", choices=[("BATA", "BATA"), ("MALABO", "MALABO")], validators=[DataRequired()])

    # Coste total y número de plazos
    coste_total = FloatField(
        "Coste total de la matrícula (XAF)",
        validators=[DataRequired(), NumberRange(min=0, message="Debe ser un valor positivo")],
    )
    
    numero_plazos = IntegerField(
        "Número de plazos de pago",
        validators=[DataRequired(), NumberRange(min=1, max=24, message="Debe ser entre 1 y 24 plazos")],
        default=1
    )

    # ✅ NUEVO CAMPO: Monto del pago inicial
    monto_inicial = FloatField(
        "Monto del primer pago (XAF)",
        validators=[DataRequired(), NumberRange(min=0, message="Debe ser un valor positivo")],
    )

    # Documentos requeridos
    expediente_academico = FileField(
        "Expediente Académico (PDF)",
        validators=[
            FileRequired(message="Debe adjuntar el expediente académico."),
            FileAllowed(["pdf"], "Solo se permiten archivos PDF.")
        ],
    )

    factura_primer_pago = FileField(
        "Factura del Primer Pago (PDF)",
        validators=[
            FileRequired(message="Debe adjuntar la factura del primer pago."),
            FileAllowed(["pdf"], "Solo se permiten archivos PDF.")
        ],
    )

    enviar = SubmitField("Guardar matrícula")
# -------------------------------------------------------------------
# FORMULARIO FP (añade campo para año académico)
# -------------------------------------------------------------------
class MatriculaFPForm(MatriculaBaseForm):
    """Formulario para matrículas de Formación Profesional"""
    tipo_fp_anho = RadioField(
        "¿A qué año se matricula?",
        choices=[
            ("PRIMER_ANO", "Primer año"),
            ("SEGUNDO_ANO", "Segundo año")
        ],
        validators=[DataRequired()],
    )
    no_esta_en_lista = HiddenField()

# -------------------------------------------------------------------
# FORMULARIO INTENSIVO (hereda directamente de base)
# -------------------------------------------------------------------
class MatriculaIntensivoForm(MatriculaBaseForm):
    """Formulario para matrículas de cursos intensivos"""
    pass

# -------------------------------------------------------------------
# FORMULARIOS DE VALIDACIÓN / RECHAZO (administración)
# -------------------------------------------------------------------
class ValidarForm(FlaskForm):
    confirmar = SubmitField("Validar matrícula")

class RechazoForm(FlaskForm):
    motivo = TextAreaField(
        "Motivo del rechazo",
        validators=[DataRequired(), Length(min=5, message="Debe indicar al menos 5 caracteres.")],
    )
    rechazar = SubmitField("Rechazar matrícula")


from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, RadioField, TextAreaField, 
    SubmitField, HiddenField, FloatField, IntegerField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired

class MatriculaBaseForm(FlaskForm):
    """Formulario base de matrícula (datos personales + documentos requeridos)"""

    # Datos personales
    estudiante_nombre = StringField("Nombre completo", validators=[DataRequired(), Length(max=150)])
    doc_identidad = StringField("Documento de identidad", validators=[Optional(), Length(max=64)])
    telefono = StringField("Teléfono", validators=[Optional(), Length(max=32)])
    email = StringField("Correo electrónico", validators=[Optional(), Length(max=120)])
    direccion = StringField("Dirección", validators=[Optional(), Length(max=200)])
    campus = SelectField("Campus", choices=[("BATA", "BATA"), ("MALABO", "MALABO")], validators=[DataRequired()])

    # Coste total y número de plazos
    coste_total = FloatField(
        "Coste total de la matrícula (XAF)",
        validators=[DataRequired(), NumberRange(min=0, message="Debe ser un valor positivo")],
    )
    
    numero_plazos = IntegerField(
        "Número de plazos de pago",
        validators=[DataRequired(), NumberRange(min=1, max=24, message="Debe ser entre 1 y 24 plazos")],
        default=1
    )

    # ✅ NUEVO CAMPO: Monto del pago inicial
    monto_inicial = FloatField(
        "Monto del primer pago (XAF)",
        validators=[DataRequired(), NumberRange(min=0, message="Debe ser un valor positivo")],
    )

    # Documentos requeridos
    expediente_academico = FileField(
        "Expediente Académico (PDF)",
        validators=[
            FileRequired(message="Debe adjuntar el expediente académico."),
            FileAllowed(["pdf"], "Solo se permiten archivos PDF.")
        ],
    )

    factura_primer_pago = FileField(
        "Factura del Primer Pago (PDF)",
        validators=[
            FileRequired(message="Debe adjuntar la factura del primer pago."),
            FileAllowed(["pdf"], "Solo se permiten archivos PDF.")
        ],
    )

    enviar = SubmitField("Guardar matrícula")

# -------------------------------------------------------------------
# FORMULARIO DE CALIFICACIONES
# -------------------------------------------------------------------
class CalificacionForm(FlaskForm):
    """Formulario para agregar calificaciones"""
    tipo = SelectField(
        "Tipo de Evaluación",
        choices=[
            ("ORDINARIO", "Examen Ordinario (10%)"),
            ("PARCIAL", "Examen Parcial (30%)"),
            ("FINAL", "Examen Final (60%)"),
            ("RECUPERACION", "Recuperación (Definitiva)")
        ],
        validators=[DataRequired()]
    )
    valor = FloatField(
        "Nota (0 - 10)",
        validators=[DataRequired(), NumberRange(min=0, max=10, message="La nota debe estar entre 0 y 10")]
    )
    observacion = StringField("Observación (Opcional)", validators=[Optional(), Length(max=200)])
    submit = SubmitField("Guardar")