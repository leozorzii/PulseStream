from .celery import app as celery_app

#quando o django inicia essa instancia ja inicia o celery tambem
__all__ = ("celery_app",)