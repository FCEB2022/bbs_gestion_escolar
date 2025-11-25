from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.perfil.forms import PerfilForm, CambiarContrasenaForm

from app.perfil import bp


@bp.route("/ver")
@login_required
def ver_perfil():
    return render_template("perfil/ver.html", usuario=current_user)


@bp.route("/editar", methods=["GET", "POST"])
@login_required
def editar_perfil():
    form = PerfilForm(obj=current_user)
    if form.validate_on_submit():
        current_user.nombre_completo = form.nombre_completo.data
        current_user.username = form.username.data
        current_user.contacto = form.contacto.data
        db.session.commit()
        flash("Perfil actualizado correctamente.", "success")
        return redirect(url_for("perfil.ver_perfil"))
    return render_template("perfil/editar.html", form=form)


@bp.route("/cambiar-contrasena", methods=["GET", "POST"])
@login_required
def cambiar_contrasena():
    form = CambiarContrasenaForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.contrasena_actual.data):
            flash("La contraseña actual no es correcta.", "danger")
        else:
            current_user.set_password(form.nueva_contrasena.data)
            db.session.commit()
            flash("Contraseña actualizada correctamente.", "success")
            return redirect(url_for("perfil.ver_perfil"))
    return render_template("perfil/cambiar_contrasena.html", form=form)
