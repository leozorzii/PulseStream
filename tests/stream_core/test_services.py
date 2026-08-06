import pytest
from django.utils import timezone
from apps.stream_core.services import create_content_source
from apps.stream_core.services import  bulk_create_raw_posts
from django.core.exceptions import ValidationError
from apps.stream_core.models import ContentSource, RawPost


@pytest.mark.django_db
def test_create_content_source():
    #Act chama o service pra criar uma fonte
    fonte = create_content_source(
        name="Canal BitGamer",
        plataform="YOUTUBE",
        external_id="UC123bitgamer"
        )
    
    #verifica se a fonte foi mesmo pro banco
    assert ContentSource.objects.count() == 1 #caso tenha pelo menos um registro no banco, setta que ja tem algo como uma consulta no db
    assert fonte.name == "Canal BitGamer" #os dados batem de acordo com a fonte
    assert fonte.external_id == "UC123bitgamer"
    
    
@pytest.mark.django_db
def test_not_create_content_source_duplicate():
    # Arrange - cria a primeira fonte
    create_content_source(
        name="Canal BitGamer",
        plataform="YOUTUBE",
        external_id="UC123bitgamer")
    
    #Act + assert - tenta criar de novo a fonte com mesmo external_id e espera que ela relate um erro
    with pytest.raises(ValidationError):
        create_content_source(
            name="Canal BitGamer",
            plataform="YOUTUBE",
            external_id="UC123bitgamer")
        

#Insere varios registros no banco de uma so vez
@pytest.mark.django_db
def test_bulk_create_raw_posts_creates_multiple():
    fonte = create_content_source(name="Canal", plataform="YOUTUBE", external_id="UC_bulk")
    
    posts_data = [
        {"external_id": "p1", "text_content": "primeiro", "published_at": timezone.now()},
        {"external_id": "p2", "text_content": "segundo", "published_at": timezone.now()}
    ]
    
    bulk_create_raw_posts(source=fonte, posts_data=posts_data)
    
    assert RawPost.objects.count() == 2
    
