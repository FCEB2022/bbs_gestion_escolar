from datetime import datetime
import click
from flask.cli import with_appcontext
from app import db
from app.usuarios.models import Usuario, Role

@click.command("seed-datos-iniciales")
@with_appcontext
def seed_datos_iniciales():
    """Crea roles base y un usuario administrador inicial"""
    click.echo("⏳ Creando roles base...")

    roles = ["Administrador", "Administrativo", "Supervisor"]
    for nombre in roles:
        if not Role.query.filter_by(nombre=nombre).first():
            db.session.add(Role(nombre=nombre))
    db.session.commit()

    click.echo("✅ Roles: Administrador, Administrativo, Supervisor")

    # Crear usuario administrador
    if not Usuario.query.filter_by(username="admin").first():
        admin = Usuario(
            username="admin",
            full_name="Administrador del Sistema",
            email="admin@bbs.edu",
            activo=True,
            sesion_activa=False,
            ultimo_login=datetime.utcnow(),
        )
        admin.set_password("admin123")

        rol_admin = Role.query.filter_by(nombre="Administrador").first()
        if rol_admin:
            admin.roles.append(rol_admin)

        db.session.add(admin)
        db.session.commit()
        click.echo("✅ Usuario administrador creado: admin / admin123")
    else:
        click.echo("ℹ️  El usuario administrador ya existe.")
