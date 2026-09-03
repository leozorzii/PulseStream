import pytest
from rest_framework.test import APIClient
from apps.stream_core.models import SentimentAnalysis, RawPost
from apps.stream_core.services import create_content_source
from django.utils import timezone

#----------------------POSTS---------------------------

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
    #o endpoint passou a devolver envelope paginado, entao a lista vive em
    #"results" — len(response.data) contaria as 4 chaves do envelope, nao os posts
    assert response.data["count"] == 1
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["external_id"] == "pendente"


@pytest.mark.django_db
def test_summary_one_source():
    fonte = create_content_source(name="Canal", plataform="YOUTUBE", external_id="UC_sum")
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
  
  
#----------------------PAGINACAO---------------------------

@pytest.mark.django_db
def test_active_sources_retorna_resposta_paginada():
    #duas fontes ativas, o suficiente para o count ter o que contar
    create_content_source(name="Canal A", plataform="YOUTUBE", external_id="UC_pag_a")
    create_content_source(name="Canal B", plataform="NEWS", external_id="UC_pag_b")

    client = APIClient()
    response = client.get("/api/sources/")

    assert response.status_code == 200

    #o contrato do DRF paginado: envelope com as quatro chaves, e nao array cru
    assert "count" in response.data
    assert "next" in response.data
    assert "previous" in response.data
    assert "results" in response.data

    #o teste e de que a view aplica paginacao, nao de que a paginacao do
    #DRF funciona — por isso duas fontes e nao 25 para conferir a pagina 2.
    #Aquilo seria testar biblioteca de terceiro.
    assert response.data["count"] == 2
    assert len(response.data["results"]) == 2


#----------------------ORDENACAO---------------------------

@pytest.mark.django_db
def test_active_sources_vem_ordenadas_por_nome():
    #Arrange(cenario) - criadas FORA de ordem alfabetica de proposito: se o
    #order_by sumir, o banco tende a devolver na ordem de insercao e o teste
    #pega. Criar ja em ordem passaria mesmo sem ordenacao nenhuma.
    create_content_source(name="Zebra", plataform="NEWS", external_id="UC_ord_z")
    create_content_source(name="Alfa", plataform="YOUTUBE", external_id="UC_ord_a")
    create_content_source(name="Meio", plataform="REDDIT", external_id="UC_ord_m")

    #Act(executa)
    client = APIClient()
    response = client.get("/api/sources/")

    #assert(verifica se o resultado bateu)
    assert response.status_code == 200
    nomes = [fonte["name"] for fonte in response.data["results"]]
    assert nomes == ["Alfa", "Meio", "Zebra"]


@pytest.mark.django_db
def test_active_sources_desempata_por_id():
    #Arrange - duas fontes com o MESMO nome. name nao e unique no model, entao
    #sem o segundo criterio a ordem entre elas ficaria por conta do banco.
    #
    #ATENCAO ao que este teste NAO prova: conferido por mutacao, ele continua
    #passando se o order_by inteiro for removido, porque sem ordenacao o SQLite
    #devolve na ordem de insercao — que aqui coincide com a ordem de id. Quem
    #pega a remocao do order_by e o teste de cima, com nomes fora de ordem.
    #O que este aqui trava e a DIRECAO do desempate: pegaria uma troca para
    #"-id", nao a ausencia de ordenacao.
    primeira = create_content_source(name="Repetida", plataform="NEWS", external_id="UC_dup_1")
    segunda = create_content_source(name="Repetida", plataform="NEWS", external_id="UC_dup_2")

    #Act
    client = APIClient()
    response = client.get("/api/sources/")

    #assert - o id menor vem primeiro, sempre
    ids = [fonte["id"] for fonte in response.data["results"]]
    assert ids == [primeira.id, segunda.id]
