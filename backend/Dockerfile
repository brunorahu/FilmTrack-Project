# backend/Dockerfile

# Usamos una imagen oficial de Python como base
FROM python:3.11-slim

# --- PASOS NUEVOS: Instalar el Driver ODBC de Microsoft ---
# 1. Actualizamos los paquetes e instalamos herramientas necesarias
RUN apt-get update && apt-get install -y curl gnupg

# 2. Agregamos la llave de Microsoft para verificar los paquetes
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

# 3. Agregamos el repositorio de paquetes de Microsoft
RUN curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list

# 4. Actualizamos la lista de paquetes de nuevo y finalmente instalamos el driver
#    ACCEPT_EULA=Y es para aceptar los términos de licencia automáticamente
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev
# --- FIN DE LOS PASOS NUEVOS ---

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos el archivo de requerimientos primero para optimizar el cache
COPY requirements.txt .

# Instalamos las librerías de Python necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código de la aplicación
COPY . .

# Comando que se ejecutará cuando el contenedor inicie
CMD ["python", "main_api.py"]