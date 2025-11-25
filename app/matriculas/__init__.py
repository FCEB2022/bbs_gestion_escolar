# app/matriculas/__init__.py
from flask import Blueprint

bp = Blueprint(
    "matriculas",
    __name__,
    template_folder="templates",
    static_folder="static"  # por si luego añadimos js/css propios
)

from . import routes  # noqa: E402,F401
