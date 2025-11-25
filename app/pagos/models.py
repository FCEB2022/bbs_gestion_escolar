from datetime import datetime, date
from sqlalchemy.types import TypeDecorator, Date
from app.extensions import db

# Estados de pago
ESTADO_PAGO_PENDIENTE = "PENDIENTE"
ESTADO_PAGO_VALIDADO = "VALIDADO"
ESTADO_PAGO_RECHAZADO = "RECHAZADO"
ESTADO_PAGO_INICIAL = "INICIAL"
ESTADO_PAGO_PENDIENTE_VALIDACION = "PENDIENTE_VALIDACION"

class SafeDate(TypeDecorator):
    """Tipo de columna que maneja de forma segura diferentes formatos de fecha"""
    impl = Date
    
    def process_result_value(self, value, dialect):
        """Convierte valores de la base de datos a objetos date de Python"""
        if value is None:
            return None
        
        if isinstance(value, date):
            return value
        
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, str):
            try:
                # Intentar formato YYYY-MM-DD
                if ' ' in value:
                    # Si tiene espacio, es formato datetime
                    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f').date()
                else:
                    # Formato date simple
                    return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                # Si falla, intentar otros formatos comunes
                try:
                    return datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError:
                    print(f"⚠️ No se pudo parsear la fecha: {value}")
                    return None
        
        return value

# Actualizar el modelo Pago para usar SafeDate
class Pago(db.Model):
    __tablename__ = "pagos"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    matricula_id = db.Column(db.Integer, db.ForeignKey("matriculas.id"), nullable=False)
    numero_cuota = db.Column(db.Integer, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default=ESTADO_PAGO_PENDIENTE)
    
    # Campos para pago inicial
    es_pago_inicial = db.Column(db.Boolean, default=False)
    monto_inicial = db.Column(db.Float, nullable=True)
    
    # Campos para control de validación - USAR SafeDate
    fecha_vencimiento = db.Column(SafeDate, nullable=True)
    fecha_pago = db.Column(SafeDate, nullable=True)
    comprobante_path = db.Column(db.String(300), nullable=True)
    motivo_rechazo = db.Column(db.Text, nullable=True)
    
    # Campos legacy para compatibilidad
    factura_nombre = db.Column(db.String(200), nullable=True)
    factura_path = db.Column(db.String(300), nullable=True)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relación
    matricula = db.relationship("Matricula", back_populates="pagos")

    def __repr__(self):
        return f"<Pago {self.numero_cuota} - {self.estado}>"

    def esta_vencido(self):
        """Verifica si el pago está fuera de plazo"""
        if not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento < date.today() and self.estado in [ESTADO_PAGO_PENDIENTE, ESTADO_PAGO_PENDIENTE_VALIDACION]

    def get_estado_display(self):
        """Retorna el estado para mostrar en la interfaz"""
        if self.estado == ESTADO_PAGO_VALIDADO:
            return "Validado"
        elif self.estado == ESTADO_PAGO_RECHAZADO:
            return "Rechazado"
        elif self.estado == ESTADO_PAGO_INICIAL:
            return "Pago Inicial"
        elif self.estado == ESTADO_PAGO_PENDIENTE_VALIDACION:
            return "Pendiente de Validación"
        elif self.esta_vencido():
            return "Fuera de Plazo"
        else:
            return "Pendiente"