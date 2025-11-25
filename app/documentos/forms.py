from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, FileField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class EntradaForm(FlaskForm):
    numero_referencia = StringField("Nº Referencia", validators=[DataRequired(), Length(max=40)])
    fecha_recepcion = DateField("Fecha de recepción", validators=[DataRequired()])
    remitente = StringField("Remitente", validators=[DataRequired(), Length(max=200)])
    descripcion = TextAreaField("Descripción", validators=[DataRequired(), Length(max=2000)])
    observaciones = TextAreaField("Observaciones", validators=[Optional(), Length(max=2000)])
    archivo = FileField("Archivo (PDF/Imagen)", validators=[DataRequired()])
    submit = SubmitField("Guardar entrada")

class SalidaForm(FlaskForm):
    numero_referencia = StringField("Nº Referencia", validators=[DataRequired(), Length(max=40)])
    fecha_despacho = DateField("Fecha de despacho", validators=[DataRequired()])
    destinatario = StringField("Destinatario", validators=[DataRequired(), Length(max=200)])
    remitente_interno = StringField("Remitente interno", validators=[Optional(), Length(max=200)])
    descripcion = TextAreaField("Descripción", validators=[DataRequired(), Length(max=2000)])
    observaciones = TextAreaField("Observaciones", validators=[Optional(), Length(max=2000)])
    archivo = FileField("Archivo (PDF/Imagen)", validators=[DataRequired()])
    submit = SubmitField("Guardar salida")
