# 1. Usamos Python 3.13 (la versión que tienes) en su versión ligera (slim)
FROM python:3.13-slim

# 2. Configuración para ver los logs de error inmediatamente en la consola
ENV PYTHONUNBUFFERED=1

# 3. Creamos una carpeta de trabajo dentro del contenedor llamada "app"
WORKDIR /app

# 4. INSTALACIÓN DE HERRAMIENTAS DEL SISTEMA (Importante para MySQL)
# Django necesita gcc y librerías de mysql para poder conectarse a la base de datos
RUN apt-get update && apt-get install -y \
    pkg-config \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copiamos tu lista de librerías e instalamos todo
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 6. Copiamos todo el resto de tu código (manage.py, carpetas, etc.)
COPY . /app/

# 7. Abrimos el puerto 8000 para que puedas entrar desde el navegador
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]