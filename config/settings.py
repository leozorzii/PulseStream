import sys
from pathlib import Path
from decouple import config


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "apps"))


SECRET_KEY = config("SECRET_KEY")
WSGI_APPLICATION = 'config.wsgi.application' 
ROOT_URLCONF = 'config.urls'
DEBUG = config("DEBUG", default=False, cast=bool)


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
    'apps.stream_core',
    'apps.ingestion',
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

#CELERY
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Sao_Paulo"

#CELERY BEAT - agendamento periodico
#o endpoint de trigger ja enfileira a analise depois de cada coleta bem sucedida.
#este agendamento e a rede de seguranca para o que escapa daquele caminho: posts
#ingeridos por outra rota, lote interrompido com o worker fora do ar, ou backlog
#anterior a fiacao. sem ele, esses posts ficam pendentes ate alguem chamar o
#endpoint de novo.
CELERY_BEAT_SCHEDULE = {
    "drain-pending-sentiments": {
        "task": "apps.ingestion.tasks.processar_sentimentos",
        #5 minutos: curto o bastante para o backlog nao acumular, longo o
        #bastante para nao martelar o banco. quando nao ha pendente a task e
        #praticamente um no-op (uma consulta que volta vazia), entao o custo
        #de rodar a toa e baixo
        "schedule": 300.0,
    },
}