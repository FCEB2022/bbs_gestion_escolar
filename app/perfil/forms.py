from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional


class PerfilForm(FlaskForm):
    nombre_completo = StringField(
        "Nombre completo",
        validators=[DataRequired(message="Campo obligatorio"), Length(min=2, max=120)]
    )
    username = StringField(
        "Nombre de usuario",
        validators=[DataRequired(message="Campo obligatorio"), Length(min=3, max=50)]
    )
    email = StringField(
        "Correo electrónico",
        validators=[Optional(), Email(message="Correo inválido")]
    )

    submit = SubmitField("Guardar Cambios")


class CambiarContrasenaForm(FlaskForm):
    contrasena_actual = PasswordField(
        "Contraseña actual",
        validators=[DataRequired(message="Campo obligatorio")]
    )
    nueva_contrasena = PasswordField(
        "Nueva contraseña",
        validators=[
            DataRequired(message="Campo obligatorio"),
            Length(min=6, message="Debe tener al menos 6 caracteres")
        ]
    )
    confirmar_contrasena = PasswordField(
        "Confirmar nueva contraseña",
        validators=[
            DataRequired(message="Campo obligatorio"),
            EqualTo("nueva_contrasena", message="Las contraseñas no coinciden")
        ]
    )

    submit = SubmitField("Actualizar Contraseña")
