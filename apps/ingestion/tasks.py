from celery import shared_task

@shared_task #transforma funcao comum em uma task celery
def somar(a,b):
    """Task boba de teste: soma dois numeros em background"""
    return a + b
    