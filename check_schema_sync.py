# check_schema_sync.py
"""
Verificador de sincronización entre los modelos SQLAlchemy y la base de datos SQLite.
Detecta columnas faltantes o sobrantes entre los modelos y la base de datos.
Compatible con Flask (usa contexto de aplicación automáticamente).
"""

import os
from app import create_app, db
from sqlalchemy import inspect

DB_PATH = os.path.join("instance", "app.db")

def check_schema():
    print("🔍 Comprobando sincronización entre modelos y base de datos...")
    inspector = inspect(db.engine)
    inconsistencias = False

    for model_class in db.Model.__subclasses__():
        if not hasattr(model_class, "__tablename__"):
            continue

        table_name = model_class.__tablename__
        print(f"\n🧱 Tabla: {table_name}")

        try:
            db_columns = {col["name"] for col in inspector.get_columns(table_name)}
        except Exception:
            print("  ⚠️ La tabla no existe en la base de datos.")
            inconsistencias = True
            continue

        model_columns = {col.name for col in model_class.__table__.columns}
        faltantes = model_columns - db_columns
        sobrantes = db_columns - model_columns

        if faltantes:
            inconsistencias = True
            print(f"  ⚠️ Faltan en la base de datos: {', '.join(sorted(faltantes))}")
        if sobrantes:
            inconsistencias = True
            print(f"  ⚠️ Sobran en la base de datos: {', '.join(sorted(sobrantes))}")
        if not faltantes and not sobrantes:
            print("  ✅ Sincronizada correctamente.")

    if inconsistencias:
        print("\n❌ Se detectaron diferencias. Ejecuta una migración con:")
        print("   flask db migrate -m 'sync schema' && flask db upgrade")
    else:
        print("\n✅ Todos los modelos coinciden con la base de datos.")


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"❌ No se encontró la base de datos en: {DB_PATH}")
    else:
        app = create_app()  # Inicializa la app Flask
        with app.app_context():  # Usa el contexto de aplicación
            check_schema()
