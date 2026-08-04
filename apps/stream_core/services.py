from apps.stream_core.models import ContentSource
from django.core.exceptions import ValidationError

def create_content_source(name,plataform, external_id):
    """Cria uma nova fonte de conteudo no banco de dados

    Args:
        name (str): nome legivel da fonte
        plataform (str): plataforma(ContentSource.PLATAFORMAS)
        external_id (str): identificador unico de fonte da plataforma
    
    Returns:
        ContentSource: a instancia criada
    """
    #verifica duplicidade
    if ContentSource.objects.filter(external_id=external_id).exists():
        raise ValidationError(f"ja existe fonte com esse external_id '{external_id}' ")
    fonte = ContentSource.objects.create(
        name=name,
        plataform=plataform,
        external_id=external_id
    )
    return fonte