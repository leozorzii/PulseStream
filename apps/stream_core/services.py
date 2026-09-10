from apps.stream_core.models import ContentSource, RawPost, SentimentAnalysis
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

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


def mark_source_collected(source):
    """Marca a fonte como coletada agora.

    COMO FUNCIONA
    Grava timezone.now() em last_collected_at e salva SO esse campo. Uma linha
    de escrita, sem regra nenhuma — a regra de QUANDO chamar mora em quem
    orquestra a coleta.

    POR QUE E UM SERVICE, E NAO UM source.save() DENTRO DO run_ingestion
    O docstring do run_ingestion diz que ele nao persiste por conta propria, so
    amarra os componentes que ja existem. Gravar direto la contradiria o
    contrato que ele mesmo documenta, e a escrita ficaria longe do model que
    ela toca. Aqui ela fica junto das outras escritas de stream_core.

    POR QUE update_fields
    Sem ele, o save() grava os SEIS campos do objeto em memoria. Se alguem
    desativou a fonte pelo admin depois que a coleta comecou, o objeto que a
    coleta carrega ainda tem is_active=True e a gravacao ressuscitaria a fonte
    em silencio. Com update_fields o UPDATE toca uma coluna so, e o resto do
    que estiver no banco fica como esta.

    Args:
        source (ContentSource): a fonte que acabou de ser coletada com sucesso

    Returns:
        ContentSource: a mesma instancia, ja com last_collected_at preenchido
    """
    source.last_collected_at = timezone.now()
    source.save(update_fields=["last_collected_at"])
    return source


def save_sentiment_analysis(post, polarity_score, label, keywords):
    """salva a analise de sentimento e marca como processado(utiliza transaction atomic = 'tudo ou nada')
    Executa duas operacoes numa transacao atomica ('tudo ou nada') se qualquer falhar, nenhuma é persistida
    Args:
        post (RawPost): post que teve o sentimento analisado
        polarity_score (float_): pontuacao de polaridade, de negativo a positivo
        label (str): rotulo do sentimento ("POS", "NEU", "NEG")
        keywords (list[str]):palavras chave extraidas do texto
        
        
    Returns:
        SentimentAnalysis: analise do sentimento criada, com o post marcado como processado
    """
    with transaction.atomic():
        analise = SentimentAnalysis.objects.create(
            post = post,
            polarity_score = polarity_score,
            label = label,
            extracted_keywords = keywords,
        )
        post.is_processed = True
        post.save()
    return analise