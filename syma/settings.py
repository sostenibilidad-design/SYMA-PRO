import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

GOOGLE_CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'coral-app-g5qh8.ondigitalocean.app', 
    'syma-pro.me', 
    'www.syma-pro.me', 
    'localhost', 
    '127.0.0.1'
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'django.contrib.sites',
    'django.contrib.humanize',
    'anymail',
    'django_apscheduler',
    'core',
    'personal',
    'usuario',
    'medicion_rendimiento',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'syma.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.template.context_processors.debug",
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'syma.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# === MODIFICACIÓN INTELIGENTE AQUÍ ===
# Detectamos si existe la variable de la nube para decidir qué base de datos usar

database_url = os.environ.get('DATABASE_URL')

if database_url:
    db_config = dj_database_url.config(
        default=database_url,
        conn_max_age=600,
        ssl_require=True
    )
    
    if 'OPTIONS' in db_config:
        db_config['OPTIONS'].pop('sslmode', None)
        db_config['OPTIONS'].pop('ssl-mode', None)
        
        db_config['OPTIONS']['ssl_mode'] = 'REQUIRED'
    
    DATABASES = {
        'default': db_config
    }
else:
    # 💻 CONFIGURACIÓN PARA LOCAL (Tu PC)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('MYSQL_DATABASE', 'syma_db'),
            'USER': os.environ.get('MYSQL_USER', 'root'),
            'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'root'),
            'HOST': os.environ.get('MYSQL_HOST', 'localhost'),
            'PORT': os.environ.get('MYSQL_PORT', '3306'),
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True


# ARCHIVOS ESTÁTICOS

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticFiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'usuario.Usuario'

AUTHENTICATION_BACKENDS = [
    'usuario.backends.CorreoBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# --- CONFIGURACIÓN DE CORREO (BREVO API) ---
# Esto le dice a Django que use la API HTTPS en lugar del puerto 587
EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"

ANYMAIL = {
    "BREVO_API_KEY": os.environ.get("BREVO_API_KEY"),
}

# Configuración predeterminada
DEFAULT_FROM_EMAIL = "sostenibilidad@syma.com.co"
SERVER_EMAIL = "sostenibilidad@syma.com.co"

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

SITE_ID = 2

# 1. ESTA ES LA LÍNEA QUE FALTA: Dile a Django que confíe en Nginx
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


csrf_trusted = os.environ.get("CSRF_TRUSTED_ORIGINS")

if csrf_trusted:
    CSRF_TRUSTED_ORIGINS = csrf_trusted.split(",")
else:
    CSRF_TRUSTED_ORIGINS = []

CSRF_TRUSTED_ORIGINS.extend(['https://' + os.environ.get('App_Domain', '*')])

# === CONFIGURACIÓN CELERY ===
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_TIMEZONE = 'America/Bogota' 
CELERY_ENABLE_UTC = True

FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5.0 MB

# --- BLINDAJE DE SEGURIDAD EXTRA ---
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Solo usamos Spaces si estamos en Producción (DEBUG = False)
if 'AWS_ACCESS_KEY_ID' in os.environ:
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    AWS_STORAGE_BUCKET_NAME = 'syma-media-files'  
    AWS_S3_ENDPOINT_URL = 'https://nyc3.digitaloceanspaces.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    
    AWS_LOCATION = 'media'
    AWS_DEFAULT_ACL = 'public-read' # Para que las fotos se puedan ver
    
    # Le decimos a Django que use esto en lugar del disco local
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # La URL pública de tus fotos
    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{AWS_LOCATION}/'