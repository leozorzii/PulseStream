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
    #os percentuais desceram um nivel: o corpo agora e o contrato inteiro
    #(estado + contagens + sentiment), e nao so o dict de labels
    assert response.data["sentiment"]["POS"] == 50
    assert response.data["sentiment"]["NEG"] == 50


#REMOVIDO: test_summary_without_source_id_returns_400 afirmava que o endpoint
#recusa requisicao sem source_id. Isso deixou de ser verdade de proposito —
#requisicao sem o parametro agora e o ESCOPO GERAL, que o painel de visao geral
#usa. O 400 continua coberto, so que nos casos em que ele ainda vale:
#test_summary_com_source_id_vazio_retorna_400 e o _nao_numerico_.



#----------------------CONTRATO DO RESUMO---------------------------
#Vindos de tests/stream_core/test_selectors.py: batem no endpoint via APIClient,
#entao sao testes de view e o lugar deles e aqui. A maquina de estados em si
#(ready/processing/empty) esta testada no selector, que e mais barato de exercitar.

@pytest.mark.django_db
def test_summary_de_fonte_pronta_traz_o_contrato_completo():
    #Arrange(cenario) - uma fonte com uma analise ja gravada
    fonte = create_content_source(name="Canal", plataform="YOUTUBE", external_id="UC_contrato")
    post = RawPost.objects.create(
        source=fonte, external_id="contrato_0", text_content="x",
        published_at=timezone.now(), is_processed=True,
    )
    SentimentAnalysis.objects.create(post=post, polarity_score=0.5, label="POS")

    #Act(executa)
    client = APIClient()
    response = client.get(f"/api/analytics/summary/?source_id={fonte.id}")

    #assert(verifica se o resultado bateu) - as cinco chaves do contrato,
    #porque o cliente le todas e uma ausencia so apareceria na tela
    assert response.status_code == 200
    assert response.data["source_id"] == fonte.id
    assert response.data["state"] == "ready"
    assert response.data["total_analyzed"] == 1
    assert response.data["total_pending"] == 0
    assert response.data["sentiment"] == {"POS": 100.0, "NEU": 0.0, "NEG": 0.0}


@pytest.mark.django_db
def test_summary_de_fonte_inexistente_retorna_404():
    #Arrange - nenhuma fonte criada, entao o id 999 nao existe mesmo

    #Act
    client = APIClient()
    response = client.get("/api/analytics/summary/?source_id=999")

    #assert - 404, e NAO 200 com state "empty": o enum descreve a situacao dos
    #dados de uma fonte que EXISTE, nao a existencia dela. Antes as duas coisas
    #chegavam como 200 {} e um bug de quem chama ficava indistinguivel de
    #operacao normal. Mesma forma de erro que o trigger ja usa.
    assert response.status_code == 404
    assert "erro" in response.data


@pytest.mark.django_db
def test_summary_com_source_id_nao_numerico_retorna_400():
    #Act
    client = APIClient()
    response = client.get("/api/analytics/summary/?source_id=abc")

    #assert - o corpo e JSON com a mensagem, e nao a pagina HTML de erro do
    #Django. Todo caminho de erro do front le response.data.erro, entao um 500
    #com HTML aparece la como falha de parse de JSON, escondendo o problema real
    assert response.status_code == 400
    assert "erro" in response.data


@pytest.mark.django_db
def test_summary_com_source_id_vazio_retorna_400():
    #Act - ?source_id= e o que um <select> sem selecao emite; "" nao e None,
    #entao passava batido pelo guard antigo e explodia no ORM
    client = APIClient()
    response = client.get("/api/analytics/summary/?source_id=")

    #assert - vazio nao e o mesmo que ausente: houve intencao de escolher uma
    #fonte, e devolver o panorama global aqui mostraria dado geral fingindo ser
    #dado da fonte
    assert response.status_code == 400
    assert "erro" in response.data


@pytest.mark.django_db
def test_summary_sem_source_id_retorna_o_escopo_geral():
    #Arrange - duas fontes diferentes, uma analise em cada, labels opostos.
    #Se o escopo geral filtrasse por alguma fonte, o percentual daria 100/0
    primeira = create_content_source(name="Fonte A", plataform="NEWS", external_id="UC_esc_a")
    segunda = create_content_source(name="Fonte B", plataform="REDDIT", external_id="UC_esc_b")
    for i, (fonte, label) in enumerate([(primeira, "POS"), (segunda, "NEG")]):
        post = RawPost.objects.create(
            source=fonte, external_id=f"esc_{i}", text_content="x",
            published_at=timezone.now(), is_processed=True,
        )
        SentimentAnalysis.objects.create(post=post, polarity_score=0.0, label=label)

    #Act - sem query param nenhum
    client = APIClient()
    response = client.get("/api/analytics/summary/")

    #assert - source_id None e o que sinaliza escopo geral no corpo
    assert response.status_code == 200
    assert response.data["source_id"] is None
    assert response.data["total_analyzed"] == 2
    assert response.data["sentiment"]["POS"] == 50.0
    assert response.data["sentiment"]["NEG"] == 50.0


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
