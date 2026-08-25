import pytest
from datetime import timedelta
from django.utils import timezone

from apps.ingestion.tasks import processar_sentimentos
from apps.stream_core.models import ContentSource, RawPost, SentimentAnalysis


@pytest.mark.django_db
def test_processar_sentimentos_processes_pending_posts():
    #Arrange - fonte real, os posts precisam dela
    fonte = ContentSource.objects.create(
        name="G1 Tecnologia",
        plataform="NEWS",
        external_id="g1_task_test",
    )

    #dois posts pendentes com texto de sentimento conhecido, para que o
    #resultado seja previsivel sem depender do algoritmo em detalhe
    post_bom = RawPost.objects.create(
        source=fonte,
        external_id="post-positivo",
        text_content="esse filme é ótimo, adorei",
        published_at=timezone.now(),
        is_processed=False,
    )
    post_ruim = RawPost.objects.create(
        source=fonte,
        external_id="post-negativo",
        text_content="esse filme é horrivel, odiei",
        published_at=timezone.now(),
        is_processed=False,
    )

    #Act - chama a funcao direto, sem .delay(): o teste valida a LOGICA da
    #task, nao o transporte do Celery (que exigiria broker rodando)
    processar_sentimentos()

    #Assert - cada post pendente virou uma analise no banco
    assert SentimentAnalysis.objects.count() == 2

    #e os posts foram marcados como processados, para nao serem pegos de novo
    post_bom.refresh_from_db()
    post_ruim.refresh_from_db()
    assert post_bom.is_processed is True
    assert post_ruim.is_processed is True

    #o sentimento persistido bate com o texto de cada um
    assert SentimentAnalysis.objects.get(post=post_bom).label == "POS"
    assert SentimentAnalysis.objects.get(post=post_ruim).label == "NEG"


@pytest.mark.django_db
def test_processar_sentimentos_skips_already_analyzed_post():
    """Simula a corrida entre o Beat e o dispatch do endpoint.

    Os dois podem pegar o MESMO post pendente: um worker termina e grava a
    analise, enquanto o outro ainda carrega o snapshot antigo e tenta gravar
    de novo. O OneToOneField protege o DADO (nao deixa duplicar), mas sozinho
    ele derruba a task com IntegrityError e os posts seguintes ficam sem
    processar. Aqui o post ja analisado deve ser pulado e o resto continuar.
    """
    fonte = ContentSource.objects.create(
        name="G1 Corrida",
        plataform="NEWS",
        external_id="g1-race",
    )

    #o publicado antes vem primeiro no selector (ordena por published_at),
    #entao a colisao acontece no INICIO do loop e sobra post depois dela
    post_ja_analisado = RawPost.objects.create(
        source=fonte,
        external_id="post-ja-analisado",
        text_content="esse filme é ótimo, adorei",
        published_at=timezone.now() - timedelta(hours=1),
        is_processed=False,
    )
    post_pendente = RawPost.objects.create(
        source=fonte,
        external_id="post-ainda-pendente",
        text_content="esse filme é horrivel, odiei",
        published_at=timezone.now(),
        is_processed=False,
    )

    #estado exato que o worker atrasado enxerga: a analise ja existe, mas o
    #post continua marcado como pendente no snapshot dele
    SentimentAnalysis.objects.create(
        post=post_ja_analisado,
        polarity_score=1.0,
        label="POS",
        extracted_keywords=["ótimo"],
    )

    #Act - nao pode levantar; se levantar, o teste falha aqui mesmo
    processados = processar_sentimentos()

    #o post que ainda faltava foi processado normalmente, apesar da colisao
    post_pendente.refresh_from_db()
    assert post_pendente.is_processed is True
    assert SentimentAnalysis.objects.filter(post=post_pendente).exists()
    assert SentimentAnalysis.objects.get(post=post_pendente).label == "NEG"

    #nenhuma analise duplicada: a que ja existia continua unica
    assert SentimentAnalysis.objects.count() == 2
    assert SentimentAnalysis.objects.filter(post=post_ja_analisado).count() == 1

    #so um post foi realmente processado nesta execucao
    assert processados == 1
