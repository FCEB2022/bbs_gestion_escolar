from flask import Blueprint

bp = Blueprint("usuarios", __name__, template_folder="templates")

from . import routes  # noqa
