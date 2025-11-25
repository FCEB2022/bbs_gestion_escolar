from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.usuarios.models import Usuario

class UsuarioForm(FlaskForm):
    username = StringField(
        "Nombre de usuario",
        validators=[DataRequired(), Length(min=3, max=50)]
    )
    full_name = StringField("Nombre completo", validators=[DataRequired()])
    email = StringField("Correo electrónico (opcional)")  # sin Email()
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirmar contraseña",
        validators=[DataRequired(), EqualTo("password", message="Las contraseñas no coinciden.")]
    )
    activo = BooleanField("Activo", default=True)
    roles = SelectMultipleField("Roles", coerce=int)
    submit = SubmitField("Guardar")

    def validate_username(self, username):
        if Usuario.query.filter_by(username=username.data).first():
            raise ValidationError("Ese nombre de usuario ya existe.")

class EditarUsuarioForm(FlaskForm):
    username = StringField("Nombre de usuario", validators=[DataRequired()])
    full_name = StringField("Nombre completo", validators=[DataRequired()])
    email = StringField("Correo electrónico (opcional)")
    activo = BooleanField("Activo")
    roles = SelectMultipleField("Roles", coerce=int)
    submit = SubmitField("Actualizar")
