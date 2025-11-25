from flask import render_template, redirect, url_for
from flask_login import login_required

from . import bp

@bp.route('/')
@login_required
def index():
    """Página principal del sistema - Dashboard"""
    return render_template('core/dashboard.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """
    Endpoint de compatibilidad para el dashboard.
    Redirige al endpoint principal index.
    """
    return redirect(url_for('core.index'))