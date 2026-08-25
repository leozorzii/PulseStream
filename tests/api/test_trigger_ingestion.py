import pytest
from unittest.mock import patch
from rest_framework.test import APIClient

from apps.stream_core.models import ContentSource
from apps.ingestion.exceptions import FeedFetchError


@pytest.mark.django_db
def test_trigger_missing_source_id():
    #sem source_id no corpo, a view nem chega a consultar o banco
    client = APIClient()
    response = client.post("/api/ingestion/trigger/", {}, format="json")

    assert response.status_code == 400
    assert response.data["erro"] == "informe o source_id"


@pytest.mark.django_db
def test_trigger_source_not_found():
    #id que nao existe no banco
    client = APIClient()
    response = client.post(
        "/api/ingestion/trigger/",
        {"source_id": 999999},
        format="json",
    )

    assert response.status_code == 404
    assert response.data["erro"] == "fonte nao encontrada"


@pytest.mark.django_db
def test_trigger_source_without_feed_url():
    #fonte existe, mas nao da pra coletar por RSS sem a url do feed
    fonte = ContentSource.objects.create(
        name="Canal sem feed",
        plataform="YOUTUBE",
        external_id="UC_sem_feed",
        feed_url=None,
    )

    client = APIClient()
    response = client.post(
        "/api/ingestion/trigger/",
        {"source_id": fonte.id},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["erro"] == "fonte nao possui feed_url configurada"


@pytest.mark.django_db
def test_trigger_success():
    #fonte completa, com feed_url configurada
    fonte = ContentSource.objects.create(
        name="G1",
        plataform="NEWS",
        external_id="g1_feed",
        feed_url="https://g1.globo.com/rss/g1/",
    )

    #mocka o run_ingestion no namespace da VIEW, que e onde ele foi importado.
    #assim o teste nao depende de internet nem do feed real do G1.
    #a task tambem entra no mock: a view chama .delay() no caminho de sucesso,
    #e sem isso o teste tenta falar com o Redis de verdade — passando so em
    #maquina com broker no ar e travando ~2min onde nao tem
    with (
        patch("apps.api.views.run_ingestion") as mock_run,
        patch("apps.api.views.processar_sentimentos"),
    ):
        mock_run.return_value = ["post_falso_1", "post_falso_2"]

        client = APIClient()
        response = client.post(
            "/api/ingestion/trigger/",
            {"source_id": fonte.id},
            format="json",
        )

    assert response.status_code == 200
    assert response.data["posts_coletados"] == 2
    #a view tem que ter chamado o service de fato
    mock_run.assert_called_once()
    
@pytest.mark.django_db
def test_trigger_retorna_502_quando_feed_inacessivel():
    # fonte valida, com feed_url preenchida
    source = ContentSource.objects.create(
        name="G1 Teste",
        plataform="NEWS",
        external_id="g1-teste-502",
        feed_url="https://exemplo.com/feed",
    )

    client = APIClient()

    # mocka run_ingestion pra LEVANTAR a exceção (simula feed inacessível)
    with patch("apps.api.views.run_ingestion", side_effect=FeedFetchError("SSL falhou")):
        response = client.post(
            "/api/ingestion/trigger/",
            {"source_id": source.id},
            format="json",
        )
    assert response.status_code == 502


@pytest.mark.django_db
def test_trigger_dispatches_sentiment_task_after_ingestion():
    #fonte completa, com feed_url configurada
    fonte = ContentSource.objects.create(
        name="G1 Task",
        plataform="NEWS",
        external_id="g1-dispara-task",
        feed_url="https://exemplo.com/feed",
    )

    #os dois mocks vivem no namespace da VIEW, que e onde os nomes foram
    #importados. run_ingestion mockado mantem o teste offline; a task mockada
    #evita depender de broker (Redis) rodando durante a suite
    with patch("apps.api.views.run_ingestion") as mock_run, \
         patch("apps.api.views.processar_sentimentos") as mock_task:
        mock_run.return_value = ["post_falso_1", "post_falso_2"]

        client = APIClient()
        response = client.post(
            "/api/ingestion/trigger/",
            {"source_id": fonte.id},
            format="json",
        )

    assert response.status_code == 200
    #a analise tem que ser ENFILEIRADA (.delay), nao executada na request:
    #rodar sincrono aqui deixaria a resposta HTTP lenta
    mock_task.delay.assert_called_once_with()


@pytest.mark.django_db
def test_trigger_nao_dispara_task_quando_ingestao_falha():
    """Teste guardiao: se a coleta falhou, nao ha o que analisar.

    Enfileirar a task mesmo assim gastaria worker a toa e, pior, mascararia
    a falha: a fila pareceria saudavel enquanto nenhum post novo entrou.
    """
    fonte = ContentSource.objects.create(
        name="G1 Falha",
        plataform="NEWS",
        external_id="g1-falha-nao-dispara",
        feed_url="https://exemplo.com/feed",
    )

    with patch("apps.api.views.run_ingestion", side_effect=FeedFetchError("SSL falhou")), \
         patch("apps.api.views.processar_sentimentos") as mock_task:
        client = APIClient()
        response = client.post(
            "/api/ingestion/trigger/",
            {"source_id": fonte.id},
            format="json",
        )

    assert response.status_code == 502
    #o caminho do 502 retorna antes, entao a task nunca deve ser enfileirada
    mock_task.delay.assert_not_called()
