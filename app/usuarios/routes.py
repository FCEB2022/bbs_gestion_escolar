# app/usuarios/routes.py
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user, login_user, logout_user
from datetime import datetime
from app import db
from app.usuarios import bp
from app.usuarios.models import Usuario, Role
from app.usuarios.forms import UsuarioForm, EditarUsuarioForm
from app.models_shared import ActividadUsuario

# ===== Definir LoginForm directamente aquí para evitar problemas de importación =====
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

from functools import wraps

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('Iniciar Sesión')

# ===== Utilidad de registro de actividad =====
def registrar_actividad(usuario, accion, detalles=None):
    if not usuario:
        return
    act = ActividadUsuario(
        usuario_id=usuario.id,
        accion=accion,
        ip=request.remote_addr,
        agente=request.user_agent.string[:255] if request.user_agent.string else None,
        detalles=detalles,
    )
    db.session.add(act)
    db.session.commit()

# ===== Helper de permisos =====
def is_admin_user():
    """Devuelve True si current_user tiene el rol 'Administrador'"""
    if not current_user or not getattr(current_user, "is_authenticated", False):
        return False
    try:
        return any(getattr(r, "nombre", "") == "Administrador" for r in current_user.roles)
    except Exception:
        return False

def admin_required(f):
    """Decorator que aborta con 403 si el usuario no es administrador"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin_user():
            abort(403)
        return f(*args, **kwargs)
    return decorated

# ===== Listado =====
@bp.route("/")
@login_required
@admin_required
def index():
    usuarios = Usuario.query.order_by(Usuario.id.desc()).all()
    roles = Role.query.order_by(Role.nombre.asc()).all()
    return render_template("usuarios/index.html", usuarios=usuarios, roles=roles)

# ===== Crear =====
@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@admin_required
def nuevo():
    form = UsuarioForm()
    form.roles.choices = [(r.id, r.nombre) for r in Role.query.order_by(Role.nombre.asc()).all()]
    if form.validate_on_submit():
        u = Usuario(
            username=form.username.data,
            full_name=form.full_name.data,
            email=form.email.data,
            activo=form.activo.data
        )
        u.set_password(form.password.data)
        u.roles = [Role.query.get(rid) for rid in form.roles.data]
        db.session.add(u)
        db.session.commit()
        registrar_actividad(current_user, f"Creó usuario {u.username}")
        flash("Usuario creado correctamente.", "success")
        return redirect(url_for("usuarios.index"))
    return render_template("usuarios/nuevo.html", form=form)

# ===== Editar =====
@bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def editar(id):
    usuario = Usuario.query.get_or_404(id)
    form = EditarUsuarioForm(obj=usuario)
    form.roles.choices = [(r.id, r.nombre) for r in Role.query.order_by(Role.nombre.asc()).all()]
    if form.validate_on_submit():
        usuario.username = form.username.data
        usuario.full_name = form.full_name.data
        usuario.email = form.email.data
        usuario.activo = form.activo.data
        usuario.roles = [Role.query.get(rid) for rid in form.roles.data]
        db.session.commit()
        registrar_actividad(current_user, f"Editó usuario {usuario.username}")
        flash("Usuario actualizado.", "success")
        return redirect(url_for("usuarios.index"))
    # pre-selección de roles
    form.roles.data = [r.id for r in usuario.roles]
    return render_template("usuarios/editar.html", form=form, usuario=usuario)

# ===== Bloquear / activar =====
@bp.route("/bloquear/<int:id>")
@login_required
@admin_required
def bloquear(id):
    usuario = Usuario.query.get_or_404(id)
    usuario.activo = not usuario.activo
    db.session.commit()
    estado = "activó" if usuario.activo else "bloqueó"
    registrar_actividad(current_user, f"{estado} usuario {usuario.username}")
    flash(f"Usuario {estado} correctamente.", "info")
    return redirect(url_for("usuarios.index"))

# ===== Login =====
@bp.route("/login", methods=["GET", "POST"])
def login():
    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for("core.dashboard"))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        user = Usuario.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.activo:
            login_user(user, remember=True)
            user.ultimo_login = datetime.utcnow()
            user.sesion_activa = True
            db.session.commit()
            registrar_actividad(user, "Inicio de sesión", request.remote_addr)
            flash("Bienvenido.", "success")
            return redirect(url_for("core.dashboard"))
        else:
            # registrar_actividad(None, "Intento fallido de inicio de sesión", request.remote_addr)
            # No registrar actividad con usuario None para evitar errores en activiadad table
            flash("Credenciales inválidas o usuario inactivo.", "error")
    
    return render_template("usuarios/login.html", form=form)

# ===== Logout =====
@bp.route("/logout")
@login_required
def logout():
    registrar_actividad(current_user, "Cierre de sesión")
    current_user.sesion_activa = False
    db.session.commit()
    logout_user()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("usuarios.login"))

# ===== Ruta auxiliar para redirección de edición desde otros módulos (mantener pero protegida) =====
@bp.route("/editar-redirect/<int:id>")
@login_required
@admin_required
def editar_usuario(id):
    # redirige al editor de perfil/usuario del admin
    return redirect(url_for("perfil.editar_perfil", id=id))