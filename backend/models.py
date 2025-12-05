from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timedelta


# ======================
#       USUARIOS
# ======================
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    correo = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # Nueva columna

    pujas = relationship("Puja", back_populates="usuario")


# ======================
#       SUBASTAS
# ======================
class Subasta(Base):
    __tablename__ = "subastas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(String(800), nullable=False)
    precio_inicial = Column(Float, nullable=False)
    precio_actual = Column(Float, nullable=False)

    fecha_inicio = Column(DateTime, default=datetime.now)
    duracion_horas = Column(Integer, default=24)

    pujas = relationship("Puja", back_populates="subasta")

    @property
    def fecha_fin(self):
        """Calcula la fecha de finalización"""
        return self.fecha_inicio + timedelta(hours=self.duracion_horas)


# ======================
#         PUJAS
# ======================
class Puja(Base):
    __tablename__ = "pujas"

    id = Column(Integer, primary_key=True, index=True)
    subasta_id = Column(Integer, ForeignKey("subastas.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime, default=datetime.now)

    subasta = relationship("Subasta", back_populates="pujas")
    usuario = relationship("Usuario", back_populates="pujas")