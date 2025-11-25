# app/matriculas/models.py
from datetime import datetime
from app.extensions import db

ESTADO_MAT_PENDIENTE = "PENDIENTE_VALIDACION"
ESTADO_MAT_VALIDADA  = "VALIDADA"
ESTADO_MAT_RECHAZADA = "RECHAZADA"

CAMPUS_BATA   = "BATA"
CAMPUS_MALABO = "MALABO"

TIPO_FP_PRIMERO = "PRIMER_ANO"
TIPO_FP_SEGUNDO = "SEGUNDO_ANO"


from datetime import datetime
from app import db


class Matricula(db.Model):
    __tablename__ = "matriculas"
    __table_args__ = {'extend_existing': True}  # ✅ AGREGAR ESTA LÍNEA

    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(db.Integer, db.ForeignKey("cursos.id"), nullable=False)
    
    # Datos básicos del alumno
    estudiante_nombre = db.Column(db.String(150), nullable=False)
    doc_identidad = db.Column(db.String(64), nullable=True, index=True)
    telefono = db.Column(db.String(32), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)

    campus = db.Column(db.String(16), nullable=False)
    tipo_fp_anho = db.Column(db.String(16), nullable=True)

    # Estado y control
    estado = db.Column(db.String(24), nullable=False, default=ESTADO_MAT_VALIDADA)
    motivo_rechazo = db.Column(db.Text, nullable=True)

    # Campos financieros
    coste_total = db.Column(db.Float, nullable=False, default=0.0)
    numero_plazos = db.Column(db.Integer, nullable=False, default=1)
    # ✅ NUEVO CAMPO: Monto del pago inicial
    monto_inicial = db.Column(db.Float, nullable=False, default=0.0)

    # Auditoría
    created_by_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relaciones
    curso = db.relationship("Curso", backref=db.backref("matriculas", lazy="dynamic"))
    documentos = db.relationship("MatriculaDocumento", cascade="all, delete-orphan", lazy="dynamic")
    asignaturas = db.relationship("MatriculaAsignatura", back_populates="matricula", cascade="all, delete-orphan")
    pagos = db.relationship("Pago", back_populates="matricula", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Matricula {self.estudiante_nombre} ({self.campus})>"


class MatriculaDocumento(db.Model):
    __tablename__ = "matricula_documentos"
    __table_args__ = {'extend_existing': True}  # ✅ AGREGAR ESTA LÍNEA

    id = db.Column(db.Integer, primary_key=True)
    matricula_id = db.Column(db.Integer, db.ForeignKey("matriculas.id"), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'EXPEDIENTE_ACADEMICO' o 'FACTURA_PRIMER_PAGO'
    filename = db.Column(db.String(200), nullable=False)
    path = db.Column(db.String(300), nullable=False)


class MatriculaAsignatura(db.Model):
    __tablename__ = "matricula_asignaturas"
    __table_args__ = {'extend_existing': True}  # ✅ AGREGAR ESTA LÍNEA

    id = db.Column(db.Integer, primary_key=True)
    matricula_id = db.Column(db.Integer, db.ForeignKey("matriculas.id"), nullable=False)
    modulo_id = db.Column(db.Integer, db.ForeignKey("cursos_modulos.id", ondelete="CASCADE"), nullable=False)

    matricula = db.relationship("Matricula", back_populates="asignaturas")
    modulo = db.relationship("Modulo", backref=db.backref("matriculas_asignadas", lazy=True))

    nota = db.Column(db.Float, nullable=True)
    estado = db.Column(db.String(20), nullable=True)

    # Relación con calificaciones detalladas
    calificaciones = db.relationship("Calificacion", backref="asignatura", cascade="all, delete-orphan")

    def calcular_nota_final(self):
        """
        Calcula la nota final basada en las calificaciones registradas.
        Lógica:
        - Si hay RECUPERACION -> Nota Final = Nota Recuperación.
        - Si no:
            - Media Ordinarios * 10%
            - Media Parciales * 30%
            - Examen Final * 60%
        """
        califs = self.calificaciones
        
        # 1. Buscar Recuperación
        recuperacion = next((c for c in califs if c.tipo == TIPO_CALIF_RECUPERACION), None)
        if recuperacion:
            self.nota = recuperacion.valor
            self.estado = "APROBADO" if self.nota >= 5 else "SUSPENSO"
            return

        # 2. Calcular medias
        ordinarios = [c.valor for c in califs if c.tipo == TIPO_CALIF_ORDINARIO]
        parciales = [c.valor for c in califs if c.tipo == TIPO_CALIF_PARCIAL]
        final = next((c for c in califs if c.tipo == TIPO_CALIF_FINAL), None)

        media_ord = sum(ordinarios) / len(ordinarios) if ordinarios else 0.0
        media_parc = sum(parciales) / len(parciales) if parciales else 0.0
        nota_final_examen = final.valor if final else 0.0

        # 3. Aplicar ponderaciones
        # Si no hay notas en alguna categoría, esa parte suma 0.
        # Ajuste: Si falta el examen final, ¿la nota es 0 o se calcula con lo que hay?
        # Asumimos cálculo estricto: si falta final, esa parte es 0.
        
        nota_calculada = (media_ord * 0.10) + (media_parc * 0.30) + (nota_final_examen * 0.60)
        
        self.nota = round(nota_calculada, 2)
        self.estado = "APROBADO" if self.nota >= 5 else "SUSPENSO"


# Tipos de Calificación
TIPO_CALIF_ORDINARIO = "ORDINARIO"
TIPO_CALIF_PARCIAL = "PARCIAL"
TIPO_CALIF_FINAL = "FINAL"
TIPO_CALIF_RECUPERACION = "RECUPERACION"

class Calificacion(db.Model):
    __tablename__ = "calificaciones"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    matricula_asignatura_id = db.Column(db.Integer, db.ForeignKey("matricula_asignaturas.id"), nullable=False)
    
    tipo = db.Column(db.String(20), nullable=False) # ORDINARIO, PARCIAL, FINAL, RECUPERACION
    valor = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    observacion = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<Calificacion {self.tipo}: {self.valor}>"





