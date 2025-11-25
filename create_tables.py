from app import create_app, db
from app.matriculas.models import Calificacion

app = create_app()

with app.app_context():
    print("Creando tablas faltantes...")
    db.create_all()
    print("Tablas creadas exitosamente.")
