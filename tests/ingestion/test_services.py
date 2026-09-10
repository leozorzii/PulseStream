import pytest
from django.utils import timezone
from unittest.mock import MagicMock

from apps.ingestion.services import run_ingestion
from apps.stream_core.models import ContentSource, RawPost
from apps.ingestion.exceptions import FeedFetchError


@pytest.mark.django_db
def test_run_ingestion_persists_posts():
    #Arrange - fonte real no banco, os posts precisam dela
    fonte = ContentSource.objects.create(
        name="G1",
        plataform="NEWS",
        external_id="g1_feed",
    )

    #adapter falso(duble): nao acessa internet, so devolve o que mandamos
    fake_adapter = MagicMock()
    fake_adapter.fetch.return_value = ["entry_cru_1", "entry_cru_2"]
    fake_adapter.parse.return_value = [
        {
            "external_id": "post-1",
            "text_content": "Primeira noticia. Resumo um",
            "published_at": timezone.now(),
        },
        {
            "external_id": "post-2",
            "text_content": "Segunda noticia. Resumo dois",
            "published_at": timezone.now(),
        },
    ]

    #Act - o service orquestra: fetch -> parse -> persiste
    run_ingestion(fonte, fake_adapter)

    #Assert - os 2 posts foram parar no banco, ligados a fonte certa
    assert RawPost.objects.filter(source=fonte).count() == 2

    #o service tem que USAR o adapter injetado, nao criar um por dentro
    fake_adapter.fetch.assert_called_once()
    #e o parse tem que receber exatamente o que o fetch devolveu(fluxo amarrado)
    fake_adapter.parse.assert_called_once_with(["entry_cru_1", "entry_cru_2"])


#----------------------MARCACAO DE COLETA---------------------------

def _adapter_falso(posts_data):
    """Duble de adapter: nao acessa rede, devolve o que o teste mandar.

    Args:
        posts_data (list[dict]): o que o parse deve devolver

    Returns:
        MagicMock: adapter pronto para injetar no run_ingestion
    """
    adapter = MagicMock()
    adapter.fetch.return_value = ["cru"]
    adapter.parse.return_value = posts_data
    return adapter


@pytest.mark.django_db
def test_run_ingestion_marca_a_fonte_como_coletada():
    #Arrange(cenario)
    fonte = ContentSource.objects.create(name="G1", plataform="NEWS", external_id="g1_marca")
    adapter = _adapter_falso([
        {"external_id": "marca-1", "text_content": "x", "published_at": timezone.now()},
    ])

    #Act(executa)
    run_ingestion(fonte, adapter)

    #assert(verifica se o resultado bateu)
    fonte.refresh_from_db()
    assert fonte.last_collected_at is not None


@pytest.mark.django_db
def test_run_ingestion_marca_mesmo_sem_post_novo():
    #Arrange - feed no ar e sem novidade nenhuma: parse devolve lista vazia.
    #E o caso comum de uma fonte estavel, nao um caso raro
    fonte = ContentSource.objects.create(name="G1", plataform="NEWS", external_id="g1_vazio")
    adapter = _adapter_falso([])

    #Act
    run_ingestion(fonte, adapter)

    #assert - o campo mede o frescor da CONSULTA, nao o do dado. Marcar so
    #quando vem post novo faria uma fonte sem novidade parecer abandonada na
    #tela, e o usuario iria coletar de novo atras de um problema que nao existe
    fonte.refresh_from_db()
    assert fonte.last_collected_at is not None


@pytest.mark.django_db
def test_run_ingestion_nao_marca_quando_a_coleta_falha():
    #Arrange - o feed esta fora do ar; o adapter estoura no fetch
    fonte = ContentSource.objects.create(name="G1", plataform="NEWS", external_id="g1_falha")
    adapter = MagicMock()
    adapter.fetch.side_effect = FeedFetchError("feed fora do ar")

    #Act - o service deixa a excecao subir; quem traduz em 502 e a view
    with pytest.raises(FeedFetchError):
        run_ingestion(fonte, adapter)

    #assert - ESTE E O TESTE QUE IMPORTA. Se a falha marcasse a fonte como
    #coletada, o indicador de defasagem mentiria no pior momento possivel:
    #diria "coletado agora" justamente enquanto o feed esta fora do ar ha dias,
    #que e exatamente quando alguem olha para aquele campo
    fonte.refresh_from_db()
    assert fonte.last_collected_at is None
