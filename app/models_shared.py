"""
models_shared.py
Centraliza tablas compartidas y auditoría.
"""

from datetime import datetime
from .extensions import db



# Tabla intermedia Usuario <-> Role (una sola definición global)
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("usuarios.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    extend_existing=True
)

class ActividadUsuario(db.Model):
    __tablename__ = "actividades_usuario"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    accion = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(100))
    agente = db.Column(db.String(255))
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)
    detalles = db.Column(db.Text)

    # Relación bidireccional limpia con Usuario
    usuario = db.relationship("Usuario", back_populates="actividades")

    def __repr__(self):
        return f"<ActividadUsuario {self.accion} - {self.usuario_id}>"

def registrar_actividad(usuario, accion, ip=None, navegador=None, detalles=None):
    if not usuario:
        return
    act = ActividadUsuario(
        usuario_id=usuario.id,
        accion=accion,
        ip=ip,
        navegador=navegador,
        detalles=detalles
    )
    db.session.add(act)
    db.session.commit()
