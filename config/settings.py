import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "apps"))


SECRET_KEY = 'django-insecure-1^nej1%%roup9b2f_+1&go55(!exxx5edte9tgm6_$hh3+rvo8'
WSGI_APPLICATION = 'config.wsgi.application' 
ROOT_URLCONF = 'config.urls'
DEBUG = True


STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS = [
   # Apps nativas do Django...
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'apps.stream_core'
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',       # Gerencia sessões de usuário
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',     # Autenticação/Logins
    'django.contrib.messages.middleware.MessageMiddleware',         # Mensagens de alerta no painel
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

LANGUAGE_CODE = 'pt-br'          
TIME_ZONE = 'America/Sao_Paulo'  
USE_I18N = True
USE_TZ = True