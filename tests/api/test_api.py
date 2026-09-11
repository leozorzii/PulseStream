import pytest
from rest_framework.test import APIClient
from apps.stream_core.models import SentimentAnalysis, RawPost, ContentSource
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


#----------------------METADADOS DA FONTE---------------------------

def _fonte(nome, external_id, feed_url=None, ativa=True, pendentes=0, labels=()):
    """Cria uma fonte com posts pendentes e analisados.

    Args:
        nome (str): nome da fonte
        external_id (str): identificador unico
        feed_url (str | None): url do feed, ou None para fonte nao coletavel
        ativa (bool): valor de is_active
        pendentes (int): quantos posts sem processar criar
        labels (tuple[str]): um post analisado por label

    Returns:
        ContentSource: a fonte criada
    """
    fonte = ContentSource.objects.create(
        name=nome, plataform="NEWS", external_id=external_id,
        feed_url=feed_url, is_active=ativa,
    )
    for i in range(pendentes):
        RawPost.objects.create(
            source=fonte, external_id=f"{external_id}_p{i}", text_content="x",
            published_at=timezone.now(), is_processed=False,
        )
    for i, label in enumerate(labels):
        post = RawPost.objects.create(
            source=fonte, external_id=f"{external_id}_a{i}", text_content="x",
            published_at=timezone.now(), is_processed=True,
        )
        SentimentAnalysis.objects.create(post=post, polarity_score=0.0, label=label)
    return fonte


@pytest.mark.django_db
def test_sources_traz_feed_url_e_metadados_de_coleta():
    #Arrange(cenario) - 1 pendente e 3 analisados (2 POS, 1 NEG)
    fonte = _fonte(
        "G1", "g1_meta", feed_url="https://g1.globo.com/rss/",
        pendentes=1, labels=("POS", "POS", "NEG"),
    )

    #Act(executa)
    client = APIClient()
    response = client.get("/api/sources/")

    #assert(verifica se o resultado bateu)
    assert response.status_code == 200
    dados = response.data["results"][0]
    #feed_url presente e o que deixa a UI DESABILITAR "coletar" numa fonte sem
    #feed, em vez de oferecer uma acao que so falha depois do clique
    assert dados["feed_url"] == "https://g1.globo.com/rss/"
    #nunca coletada ainda: nulo, e nao uma data qualquer
    assert dados["last_collected_at"] is None
    assert dados["post_count"] == 4
    assert dados["pending_count"] == 1
    assert dados["sentiment"] == {"POS": 66.66666666666666, "NEU": 0.0, "NEG": 33.33333333333333}
    assert dados["id"] == fonte.id


@pytest.mark.django_db
def test_sources_diz_null_no_sentiment_quando_nao_ha_analise():
    #Arrange - fonte coletada, worker ainda nao passou
    _fonte("Coletando", "coletando", pendentes=2)

    #Act
    client = APIClient()
    response = client.get("/api/sources/")

    #assert - null, e NAO {POS: 0, NEU: 0, NEG: 0}: zerado leria como resultado
    #calculado quando nada foi calculado. Mesma decisao ja tomada em
    #/api/analytics/summary/ na issue #31 — as duas rotas concordam
    assert response.data["results"][0]["sentiment"] is None


@pytest.mark.django_db
def test_sources_esconde_inativas_por_padrao():
    #Arrange
    _fonte("Ativa", "ativa_d")
    _fonte("Pausada", "pausada_d", ativa=False)

    #Act
    client = APIClient()
    response = client.get("/api/sources/")

    #assert - o padrao nao muda o que a rota ja devolvia
    assert response.data["count"] == 1
    assert response.data["results"][0]["name"] == "Ativa"


@pytest.mark.django_db
def test_sources_inclui_inativas_com_o_query_param():
    #Arrange
    _fonte("Ativa", "ativa_q")
    _fonte("Pausada", "pausada_q", ativa=False)

    #Act
    client = APIClient()
    response = client.get("/api/sources/?include_inactive=true")

    #assert - sem isto a fonte pausada e invisivel para a API inteira, e uma
    #tela de gerenciamento nao teria como oferecer "reativar"
    assert response.data["count"] == 2
    nomes = [f["name"] for f in response.data["results"]]
    assert nomes == ["Ativa", "Pausada"]
    assert response.data["results"][1]["is_active"] is False


#----------------------POLARIDADE NO ENDPOINT---------------------------

@pytest.mark.django_db
def test_summary_expoe_media_e_histograma_de_polaridade():
    #Arrange(cenario) - scores nas duas pontas e no centro. Media zero, e uma
    #analise em cada extremo do dominio
    fonte = create_content_source(name="Canal", plataform="NEWS", external_id="UC_api_pol")
    for i, score in enumerate([-1.0, 0.0, 1.0]):
        post = RawPost.objects.create(
            source=fonte, external_id=f"api_pol_{i}", text_content="x",
            published_at=timezone.now(), is_processed=True,
        )
        SentimentAnalysis.objects.create(post=post, polarity_score=score, label="NEU")

    #Act(executa)
    client = APIClient()
    response = client.get(f"/api/analytics/summary/?source_id={fonte.id}")

    #assert(verifica se o resultado bateu)
    assert response.status_code == 200
    assert response.data["avg_polarity"] == 0.0
    #o histograma e o que separa "opiniao polarizada" de "opiniao morna": estes
    #tres scores dao a mesma media que tres zeros dariam, e so a distribuicao
    #mostra que a massa esta nas pontas
    assert response.data["histogram"] == [1, 0, 0, 0, 0, 1, 0, 0, 0, 1]


@pytest.mark.django_db
def test_summary_sem_analise_nao_inventa_polaridade():
    #Arrange - fonte sem post nenhum
    fonte = create_content_source(name="Vazia", plataform="NEWS", external_id="UC_api_pol_v")

    #Act
    client = APIClient()
    response = client.get(f"/api/analytics/summary/?source_id={fonte.id}")

    #assert - None nos tres, pela mesma razao: media 0.0 leria como "opiniao
    #perfeitamente neutra" e dez zeros como "distribuicao medida e vazia"
    assert response.data["state"] == "empty"
    assert response.data["sentiment"] is None
    assert response.data["avg_polarity"] is None
    assert response.data["histogram"] is None


#----------------------SERIE TEMPORAL---------------------------

@pytest.mark.django_db
def test_timeseries_devolve_array_cru_e_nao_envelope_paginado():
    #Arrange(cenario)
    fonte = create_content_source(name="Canal", plataform="NEWS", external_id="UC_api_ts")

    #Act(executa)
    client = APIClient()
    response = client.get(f"/api/analytics/timeseries/?source_id={fonte.id}&days=30")

    #assert(verifica se o resultado bateu) - ESTA ROTA E EXCECAO a regra do
    #envelope. A resposta e uma JANELA DE TAMANHO FIXO que o cliente pediu
    #(days, com teto de 365), nao uma colecao ilimitada. Paginada em 20, uma
    #serie de 30 dias viraria duas paginas e o grafico desenharia 20 dias
    #achando que sao 30 — truncado, sem erro nenhum. O MOCK_TIMESERIES do front
    #tambem e array cru
    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) == 30


@pytest.mark.django_db
def test_timeseries_tem_a_forma_que_o_grafico_espera():
    #Arrange
    fonte = create_content_source(name="Canal", plataform="NEWS", external_id="UC_api_ts2")
    post = RawPost.objects.create(
        source=fonte, external_id="api_ts2_0", text_content="x",
        published_at=timezone.localtime(), is_processed=True,
    )
    SentimentAnalysis.objects.create(post=post, polarity_score=0.5, label="POS")

    #Act
    client = APIClient()
    response = client.get(f"/api/analytics/timeseries/?source_id={fonte.id}&days=1")

    #assert
    ponto = response.data[0]
    assert set(ponto) == {"date", "POS", "NEU", "NEG", "avg_polarity"}
    assert ponto["date"] == timezone.localdate().isoformat()
    assert ponto["POS"] == 1
    assert ponto["avg_polarity"] == 0.5


@pytest.mark.django_db
def test_timeseries_limita_a_janela_pedida():
    #Act - pede uma janela absurda
    client = APIClient()
    response = client.get("/api/analytics/timeseries/?days=999999")

    #assert - o tamanho da resposta e ditado pelo PARAMETRO, nao pelo dado,
    #porque os dias vazios sao preenchidos. Sem teto isto devolveria um milhao
    #de linhas a partir de um banco vazio
    assert response.status_code == 200
    assert len(response.data) == 365


@pytest.mark.django_db
def test_timeseries_com_days_nao_numerico_retorna_400():
    #Act
    client = APIClient()
    response = client.get("/api/analytics/timeseries/?days=abc")

    #assert - mesma forma de erro do resto da API, e JSON e nao HTML
    assert response.status_code == 400
    assert "erro" in response.data


@pytest.mark.django_db
def test_timeseries_de_fonte_inexistente_retorna_404():
    #Act
    client = APIClient()
    response = client.get("/api/analytics/timeseries/?source_id=999")

    #assert - mesma decisao do summary: o id inexistente e bug de quem chama, e
    #uma serie de zeros faria isso parecer uma fonte real e silenciosa
    assert response.status_code == 404
    assert "erro" in response.data
