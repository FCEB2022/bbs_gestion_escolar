# app/pagos/forms.py
from flask_wtf import FlaskForm
from wtforms import FloatField, FileField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional, Length
from flask_wtf.file import FileAllowed

class RegistrarPagoForm(FlaskForm):
    """Formulario para registrar un pago"""
    monto = FloatField(
        "Monto del pago (XAF)",
        validators=[DataRequired(), NumberRange(min=1, message="El monto debe ser mayor a 0")]
    )
    factura = FileField(
        "Factura (PDF)",
        validators=[
            DataRequired(message="Debe adjuntar la factura del pago."),
            FileAllowed(["pdf"], "Solo se permiten archivos PDF.")
        ]
    )
    registrar = SubmitField("Registrar Pago")

class ValidarPagoForm(FlaskForm):
    """Formulario para validar/rechazar pagos"""
    motivo = TextAreaField(
        "Motivo del rechazo",
        validators=[Optional(), Length(min=5, message="Debe indicar al menos 5 caracteres.")]
    )
    validar = SubmitField("Validar Pago")
    rechazar = SubmitField("Rechazar Pago")