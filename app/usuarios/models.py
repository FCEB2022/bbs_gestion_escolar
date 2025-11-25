from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
from app.models_shared import user_roles, ActividadUsuario

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)  # sin validación por ahora
    password_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    sesion_activa = db.Column(db.Boolean, default=False)
    ultimo_login = db.Column(db.DateTime, nullable=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    roles = db.relationship(
        "Role",
        secondary=user_roles,
        backref=db.backref("usuarios", lazy="dynamic"),
        lazy="joined",
    )

    # Relación con actividades (coherente con back_populates en ActividadUsuario)
    actividades = db.relationship("ActividadUsuario", back_populates="usuario", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Usuario {self.username}>"

class Role(db.Model):
    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<Role {self.nombre}>"
