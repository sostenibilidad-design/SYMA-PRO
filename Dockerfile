# 1. Usamos Python 3.13 slim
FROM python:3.13-slim

# 2. Variables de entorno para optimización
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 3. Directorio de trabajo
WORKDIR /app

# 4. Instalación de dependencias del sistema (necesarias para MySQL y compilación)
RUN apt-get update && apt-get install -y \
    pkg-config \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el código
COPY . /app/

# 7. CRÍTICO: Recolectar estáticos. 
# Esto toma todos los CSS de admin y tus apps y los pone en /app/staticFiles
# Si no haces esto, Nginx no encuentra nada.
RUN python manage.py collectstatic --noinput

# 8. Exponemos el puerto (informativo)
EXPOSE 8000

# 9. COMANDO REAL DE PRODUCCIÓN
# Quitamos runserver. Usamos gunicorn.
# Asegúrate de que tu carpeta principal se llame 'syma' (donde está wsgi.py)
CMD ["gunicorn", "syma.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]