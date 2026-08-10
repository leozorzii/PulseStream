import pytest
from rest_framework.test import APIClient
from apps.stream_core.models import SentimentAnalysis
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
    
    
@pytest.mark.django_db
def test_summary_one_source():
    fonte = create_content_source(name="Canal", plataform="YOUTUBE", external_id="sum")
    #cria os posts
    for i, lbl in enumerate(["POS", "NEG"]):
        post = RawPost.objects.create(
            source = fonte, external_id = f"p{i}", text_content="x", published_at = timezone.now()
        ) 
        SentimentAnalysis.objects.create(post=post, polarity_score=0.0, label=lbl)
        
    client = APIClient()
    response = client.get(f"/api/analytics/summary/?source_id={fonte.id}") #QueryParam
    
    assert response.status_code == 200
    assert response.data["POS"] == 50
    assert response.data["NEG"] == 50
    
    
@pytest.mark.django_db
def test_summary_without_source_id_returns_400():
    client = APIClient()
    response = client.get("/api/analytics/summary/")
    
    assert response.status_code == 400