import pytest
from django.utils import timezone
from apps.stream_core.services import create_content_source
from apps.stream_core.services import  bulk_create_raw_posts
from apps.stream_core.services import  save_sentiment_analysis
from apps.stream_core.services import mark_source_collected
from django.core.exceptions import ValidationError
from apps.stream_core.models import ContentSource, RawPost, SentimentAnalysis


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
    
@pytest.mark.django_db
def test_save_sentiment_analysis_creates_and_mark_as_processed():
    fonte = create_content_source(name="Canal", plataform="YOUTUBE", external_id="UC_x")
    post = RawPost.objects.create(
        source = fonte, external_id = "post_x", text_content = "video otimo",
        published_at=timezone.now(), is_processed=False,
    )
    
    save_sentiment_analysis(post=post, polarity_score=0.8, label="POS", keywords=["video", "otimo"])
    
    post.refresh_from_db() # recarrega o db
    assert post.is_processed is True  # se o post ja foi marcado como processado
    assert SentimentAnalysis.objects.count() == 1  # analise foi criada  como feita

#----------------------MARCACAO DE COLETA---------------------------

@pytest.mark.django_db
def test_mark_source_collected_grava_o_instante():
    #Arrange(cenario) - fonte nunca coletada nasce com o campo nulo, que e o
    #que distingue "nunca coletou" de "coletou faz tempo"
    fonte = create_content_source(name="Canal", plataform="NEWS", external_id="UC_mark")
    assert fonte.last_collected_at is None

    #Act(executa)
    antes = timezone.now()
    mark_source_collected(fonte)

    #assert(verifica se o resultado bateu)
    fonte.refresh_from_db() #le do banco, nao confia no objeto em memoria
    assert fonte.last_collected_at is not None
    assert fonte.last_collected_at >= antes


@pytest.mark.django_db
def test_mark_source_collected_nao_pisa_nos_outros_campos():
    #Arrange - alguem desativa a fonte pelo admin enquanto uma coleta corre.
    #O objeto que a coleta carrega na memoria ainda tem is_active=True
    fonte = create_content_source(name="Canal", plataform="NEWS", external_id="UC_mark2")
    ContentSource.objects.filter(id=fonte.id).update(is_active=False)

    #Act - marca usando o objeto DESATUALIZADO
    mark_source_collected(fonte)

    #assert - a desativacao sobrevive. Um save() cheio gravaria os 6 campos do
    #objeto velho por cima e ressuscitaria a fonte em silencio; por isso o
    #service salva com update_fields
    fonte.refresh_from_db()
    assert fonte.is_active is False
    assert fonte.last_collected_at is not None
