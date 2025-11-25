from datetime import datetime
import os
from flask import current_app
from app.extensions import db
from app.usuarios.models import Usuario

# Tabla principal: registros de documentos (entradas/salidas) con versionado básico
class Documento(db.Model):
    __tablename__ = "documentos_registros"

    id = db.Column(db.Integer, primary_key=True)
    numero_referencia = db.Column(db.String(40), nullable=False, unique=True, index=True)
    tipo = db.Column(db.String(10), nullable=False)  # 'entrada' | 'salida'
    fecha = db.Column(db.Date, nullable=False)

    # Campos de metadatos
    remitente = db.Column(db.String(200))           # usado en ENTRADA
    destinatario = db.Column(db.String(200))        # usado en SALIDA
    remitente_interno = db.Column(db.String(200))   # usado en SALIDA
    descripcion = db.Column(db.Text, nullable=False)
    observaciones = db.Column(db.Text)

    # Archivo y versionado
    filename = db.Column(db.String(255), nullable=False)   # nombre base (última versión)
    version = db.Column(db.Integer, nullable=False, default=1)

    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    created_by = db.relationship(Usuario, backref="documentos_creados")

    # Ruta real del archivo de la versión actual
    @property
    def file_path(self) -> str:
        updir = current_app.config.get("UPLOAD_FOLDER", os.path.join(current_app.instance_path, "uploads", "documentos"))
        return os.path.join(updir, f"{self.numero_referencia}_v{self.version}{os.path.splitext(self.filename)[1].lower()}")

    # Generación de referencia estilo ENT-YYYYMMDD-#### / SAL-YYYYMMDD-####
    @staticmethod
    def generar_referencia(tipo: str) -> str:
        assert tipo in ("entrada", "salida")
        prefix = "ENT" if tipo == "entrada" else "SAL"
        hoy = datetime.utcnow().strftime("%Y%m%d")
        # Contar del día/tipo para un correlativo simple
        base = f"{prefix}-{hoy}-"
        sec = db.session.query(db.func.count(Documento.id)).filter(
            Documento.tipo == tipo,
            db.func.strftime('%Y%m%d', Documento.created_at) == hoy
        ).scalar() or 0
        return f"{base}{sec + 1:04d}"

    def next_version_filename(self) -> str:
        # Para versionado cuando se re-sube archivo en edición
        ext = os.path.splitext(self.filename)[1].lower()
        return f"{self.numero_referencia}_v{self.version + 1}{ext}"
