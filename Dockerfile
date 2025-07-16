FROM python:3.11-slim

# Actualizar sistema y instalar dependencias necesarias
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip a la última versión
RUN pip install --upgrade pip setuptools wheel

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python con retry en caso de fallo
RUN pip install --no-cache-dir --retries 3 --timeout 300 -r requirements.txt || \
    (echo "Instalación falló, intentando con --no-deps..." && \
     pip install --no-cache-dir --no-deps -r requirements.txt)

# Verificar instalaciones críticas
RUN python -c "import fastapi, uvicorn, openai; print('Dependencias críticas instaladas correctamente')"

# Copiar código fuente
COPY src/ ./src/
COPY config/ ./config/
COPY start.sh ./
COPY start.bat ./

# Hacer ejecutables los scripts
RUN chmod +x start.sh

# Crear directorios necesarios
RUN mkdir -p data logs

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Exponer puertos
EXPOSE 8080 3000

# Comando por defecto con manejo de errores
CMD ["python", "-u", "src/main.py"]
