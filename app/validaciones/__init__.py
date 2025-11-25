from flask import Blueprint

bp = Blueprint("validaciones", __name__, template_folder="templates")

from . import routes
