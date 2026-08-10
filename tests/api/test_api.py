import pytest
from rest_framework.test import APIClient
from apps.stream_core.services import create_content_source
from apps.stream_core.models import RawPost
from django.utils import timezone

@pytest.mark.django_db
def test_list_posts_unprocessed():
    fonte = create_content_source(name="Canal", plataform="YOUTUBE", external_id="UC_api")
    RawPost.objects.create(
        source=fonte, external_id="pendente", text_content="novo",
        published_at=timezone.now(), is_processed = False,
    )
    RawPost.objects.create(
            source=fonte, external_id="processando", text_content="velho",
            published_at=timezone.now(), is_processed = True,
    )
    
    #act que simula requisicao HTTP GET no endpoint
    client = APIClient()
    response = client.get("/api/posts/unprocessed/")
    
    assert response.status_code == 200
    assert len(response.data) == 1