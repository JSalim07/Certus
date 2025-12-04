# Imagen base
FROM python:3.11-slim

# Carpeta dentro del contenedor
WORKDIR /app

# Copiar requirements
COPY backend/requirements.txt /app/requirements.txt

# Instalar dependencias
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar todo el backend (incluyendo templates)
COPY backend /app

# Exponer el puerto
EXPOSE 8000

# Comando de ejecución
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
