import pytest
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
