import pytest
from django.utils import timezone
from apps.stream_core.services import create_content_source
from apps.stream_core.selectors import get_active_sources
from apps.stream_core.selectors import get_unprocessed_posts
from apps.stream_core.models import ContentSource
from apps.stream_core.models import RawPost
#CORRECAO: removido o import de bulk_create_raw_posts - ela virou service,
#entao o teste dela foi para tests/stream_core/test_services.py



@pytest.mark.django_db
def test_get_active_source_atives():
    create_content_source(name="Ativa", plataform="YOUTUBE",external_id="UC_ativa")
    ContentSource.objects.create(
        name="Inativa",
        plataform="YOUTUBE",
        external_id="UC_inativa",
        is_active=False
    )
    response = get_active_sources()
    #so a ativa deve vir
    assert response.count() == 1
    assert response.first().name == "Ativa" 
    
@pytest.mark.django_db
def test_get_unprocessed_posts_returns_only_unprocessed():
    #Arrange(cenario) - primeiro a fonte por que os posts precisam dela
    fonte = create_content_source(name="Canal", plataform="YOUTUBE", external_id="UC_test")
    
    #para um post nao processado
    RawPost.objects.create(
        source = fonte,
        external_id = "post_pending",
        text_content = "new_coment",
        published_at = timezone.now(),
        is_processed = False,
    )
    
    #para post ja processado
    RawPost.objects.create(
        source = fonte,
        external_id = "post_processed",
        text_content = "old_coment",
        published_at = timezone.now(),
        is_processed = True,
     )
    #Act(executa)
    response = get_unprocessed_posts()
    
    #assert(verfiica se o resultado bateu)
    assert response.count() == 1
    assert response.first().external_id == "post_pending"
    
    

    