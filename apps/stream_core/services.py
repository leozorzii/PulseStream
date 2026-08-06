from apps.stream_core.models import ContentSource, RawPost
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

#CORRECAO: funcao veio de selectors.py para ca.
#ela escreve no banco (bulk_create), entao pertence a camada de service.
def bulk_create_raw_posts(source, posts_data):
    """metodo que insere varios registros no banco de uma so vez

    Args:
        source (ContentSource): a fonte que todos os posts pertencem
        posts_data (List[dict]): lista de dicionarios, cada um com campos de um post
        
    Returns:
        list[Raw_Post]: os posts criados no banco
    """
    objects = []
    for dados in posts_data:
        objects.append(RawPost(source=source, **dados)) #monta o objeto sem salvar
    return RawPost.objects.bulk_create(objects) # grava todos de uma vez so, se vierem 50 posts, salva todos