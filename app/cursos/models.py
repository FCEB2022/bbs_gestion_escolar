from datetime import datetime, date, timedelta
import math
from dataclasses import dataclass
from app.extensions import db
from app.usuarios.models import Usuario

CURSO_TIPO_FP = "FP"
CURSO_TIPO_INTENSIVO = "INTENSIVO"

ESTADO_BORRADOR = "BORRADOR"
ESTADO_VALIDADO = "VALIDADO"
ESTADO_PROGRAMADO = "PROGRAMADO"

PROG_PENDIENTE = "PENDIENTE"
PROG_VALIDADA = "VALIDADA"


ESTADO_PENDIENTE_VALIDACION = "PENDIENTE_VALIDACION"  # ← Agregar si no existe
ESTADO_RECHAZADO = "RECHAZADO"  # ← Agregar si no existe

class Curso(db.Model):
    __tablename__ = "cursos"
    __table_args__ = {'extend_existing': True}  # ✅ AGREGAR ESTA LÍNEA

    id = db.Column(db.Integer, primary_key=True)
    # 🔴 Antes: unique=True, index=True
    # nombre = db.Column(db.String(200), nullable=False, unique=True, index=True)

    # ✅ Ahora: sin UNIQUE; mantenemos index para búsquedas
    nombre = db.Column(db.String(200), nullable=False, index=True)

    tipo = db.Column(db.String(20), nullable=False)  # FP | INTENSIVO
    horas_totales = db.Column(db.Integer, nullable=False)
    horas_semanales = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default=ESTADO_BORRADOR)
    es_plantilla = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    created_by = db.relationship(Usuario, backref="cursos_creados")

    modulos = db.relationship("Modulo", backref="curso", cascade="all, delete-orphan")
    programacion = db.relationship("Programacion", backref="curso", uselist=False, cascade="all, delete-orphan")
    def puede_editar(self) -> bool:
        return self.estado in (ESTADO_BORRADOR, ESTADO_VALIDADO)

    def puede_validar(self) -> bool:
        return self.estado == ESTADO_BORRADOR

    def puede_programar(self) -> bool:
        return self.estado == ESTADO_VALIDADO


class Modulo(db.Model):
    __tablename__ = "cursos_modulos"
    __table_args__ = {'extend_existing': True}  # ✅ AGREGAR ESTA LÍNEA

    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(db.Integer, db.ForeignKey("cursos.id"), nullable=False)

    nombre = db.Column(db.String(200), nullable=False)
    horas_modulo = db.Column(db.Integer, nullable=False)
    docente_nombre = db.Column(db.String(200), nullable=True)
    temario = db.Column(db.Text, nullable=True)

    # Solo FP:
    anio_fp = db.Column(db.Integer, nullable=True)      # 1 | 2
    semestre_fp = db.Column(db.Integer, nullable=True)  # 1 | 2

    def es_fp(self) -> bool:
        return self.curso and self.curso.tipo == CURSO_TIPO_FP


class Programacion(db.Model):
    __tablename__ = "cursos_programaciones"
    __table_args__ = {'extend_existing': True}  # ✅ AGREGAR ESTA LÍNEA

    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(db.Integer, db.ForeignKey("cursos.id"), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # cache del tipo del curso

    # FP
    anio_escolar_inicio = db.Column(db.String(9), nullable=True)  # "YYYY-YYYY"
    anio_escolar_fin = db.Column(db.String(9), nullable=True)

    # Intensivo
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_fin = db.Column(db.Date, nullable=True)

    estado_programacion = db.Column(db.String(20), nullable=False, default=PROG_PENDIENTE)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    @staticmethod
    def calcular_fin_intensivo(fecha_inicio: date, horas_totales: int, horas_semanales: int) -> date:
        # semanas = ceil(horas_totales / horas_semanales)
        semanas = max(1, math.ceil(horas_totales / max(1, horas_semanales)))
        return fecha_inicio + timedelta(weeks=semanas)
