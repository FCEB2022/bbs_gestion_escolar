from flask import Blueprint
bp = Blueprint("proyectos", __name__, template_folder="templates")
from . import routes  # noqa
