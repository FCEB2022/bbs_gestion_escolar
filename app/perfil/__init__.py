from flask import Blueprint

bp = Blueprint("perfil", __name__, template_folder="templates")

from app.perfil import routes  # noqa
