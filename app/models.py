from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db

user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
)

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Role {self.name}>"

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    roles = db.relationship("Role", secondary=user_roles, backref="users", lazy="joined")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def has_role(self, name: str) -> bool:
        return any(r.name == name for r in self.roles)

    def __repr__(self):
        return f"<User {self.username}>"

# ---- Modelos vacíos mínimos (se ampliarán por módulos) ----
class Documento(db.Model):
    __tablename__ = "documentos"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Acta(db.Model):
    __tablename__ = "actas"
    id = db.Column(db.Integer, primary_key=True)
    referencia = db.Column(db.String(100), nullable=False)

class Expediente(db.Model):
    __tablename__ = "expedientes"
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(100), nullable=False)

class Validacion(db.Model):
    __tablename__ = "validaciones"
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(50), nullable=False, default="pendiente")

class Proyecto(db.Model):
    __tablename__ = "proyectos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
