from flask import Blueprint
bp = Blueprint("estadisticas", __name__, template_folder="templates")
from . import routes  # noqa

from app.estadisticas import routes
