from flask import Blueprint

bp = Blueprint("pagos", __name__, 
               url_prefix="/pagos",
               template_folder="templates")  # ✅ Agregar template_folder

from . import routes  # ✅ Usar importación relativa