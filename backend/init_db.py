from database import Base, engine
from models import Usuario, Subasta, Puja

def init_db():
    Base.metadata.drop_all(bind=engine)  # Elimina todas las tablas
    Base.metadata.create_all(bind=engine)  # Las vuelve a crear
    print("Base de datos inicializada correctamente")

if __name__ == "__main__":
    init_db()