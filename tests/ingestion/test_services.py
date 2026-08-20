import pytest
from django.utils import timezone
from unittest.mock import MagicMock

from apps.ingestion.services import run_ingestion
from apps.stream_core.models import ContentSource, RawPost


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
