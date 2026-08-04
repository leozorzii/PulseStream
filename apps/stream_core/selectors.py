from apps.stream_core.models import ContentSource
from django.core.exceptions import ValidationError
from apps.stream_core.models import RawPost

def get_active_sources():
    """Metodo que retorna todas as fontes ativas
    
    
    Returns: 
        QuerySet[ContentSource]: fonte com is_active=True
    """
    return ContentSource.objects.filter(is_active=True)


def get_unprocessed_posts():
    """Metodo que retorna os posts nao processados, ordenados do mais antigo ao mais novo

    Returns:
        QuerySet[ContentSource]: post com is_processed = false, ordenados por published_at
    """ 
    return RawPost.objects.filter(is_processed=False).order_by("published_at")