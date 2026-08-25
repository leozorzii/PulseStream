import os
from celery import Celery

#define local do celery nas settings do Djando
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

#cria a instancia do Celery(app)
app = Celery("pulsestream")

#le as config do django  que comecam com celery
app.config_from_object("django.conf:settings", namespace="CELERY")

#descobre tasks.py automaticamente em cada app instalado
app.autodiscover_tasks()