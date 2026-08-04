from apps.stream_core.models import ContentSource
from django.core.exceptions import ValidationError

def get_active_sources():
    """Metodo que retorna todas as fontes ativas
    
    
    Returns: 
        QuerySet[ContentSource]: fonte com is_active=True
    """
    return ContentSource.objects.filter(is_active=True)