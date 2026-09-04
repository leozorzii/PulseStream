import pytest
from django.utils import timezone
from apps.stream_core.services import create_content_source
from apps.stream_core.selectors import get_active_sources
from apps.stream_core.selectors import get_unprocessed_posts
from apps.stream_core.selectors import get_sentiment_summary_by_source
from apps.stream_core.selectors import get_sentiment_summary
from apps.stream_core.models import ContentSource, SentimentAnalysis, RawPost
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
    
@pytest.mark.django_db
def test_get_sentiment_sumary_calc_percentages():
    fonte = create_content_source(name="Canal", plataform="YOUTUBE", external_id="UC_sum")
    
# criacao das 4 analises  = [2 POS, 1 NEU, 1 NEG] 50%, 25% e 25% respectivamente
    #Para cada rotulo na lista [POS, POS, NEU, NEG], me dá a posição dele (i) e o valor (label).
    for i, label in enumerate(["POS", "POS", "NEU", "NEG"]): #enumerate numera a lista ex: [0, "POS"]
        post = RawPost.objects.create(
            source=fonte,
            external_id=f"post_{i}", #precisa atribuir id aos posts para nao dar integrityError(duplicata)
            text_content = "x",
            published_at=timezone.now(),
        )
        SentimentAnalysis.objects.create(
            post=post,
            polarity_score=0.0,
            label = label,
        )
        
    res = get_sentiment_summary_by_source(fonte.id)
    
    assert res["POS"] == 50.0
    assert res["NEU"] == 25.0
    assert res["NEG"] == 25.0
    
    
@pytest.mark.django_db
def test_get_sentiment_summary_empty_source_returns_empty_dict():
    fonte = create_content_source(name="Canal", plataform="YOUTUBE", external_id="UC_vazia")
    res = get_sentiment_summary_by_source(fonte.id)
    
    assert res == {} # retorna um dicionario vazio caso nao tenha fonte 
    
#----------------------CONTRATO NOVO DO RESUMO---------------------------
#Os testes daqui para baixo sao do selector novo, get_sentiment_summary, que
#devolve o contrato inteiro (estado + contagens + percentuais). O antigo
#get_sentiment_summary_by_source continua testado acima e NAO muda: quem chama
#ele direto e o mcp_server/server.py, que trata o {} com mensagem propria.

@pytest.mark.django_db
def test_get_sentiment_summary_fonte_com_analises_vem_ready():
    #Arrange(cenario) - 2 POS e 2 NEG, para os percentuais darem 50/50
    fonte = create_content_source(name="Canal", plataform="YOUTUBE", external_id="UC_ready")
    for i, label in enumerate(["POS", "POS", "NEG", "NEG"]):
        post = RawPost.objects.create(
            source=fonte,
            external_id=f"ready_{i}",
            text_content="x",
            published_at=timezone.now(),
            is_processed=True, #analisado, entao nao conta como pendente
        )
        SentimentAnalysis.objects.create(post=post, polarity_score=0.0, label=label)

    #Act(executa)
    res = get_sentiment_summary(fonte.id)

    #assert(verifica se o resultado bateu)
    assert res["source_id"] == fonte.id
    assert res["state"] == "ready"
    assert res["total_analyzed"] == 4
    assert res["total_pending"] == 0
    assert res["sentiment"]["POS"] == 50.0
    assert res["sentiment"]["NEG"] == 50.0


@pytest.mark.django_db
def test_get_sentiment_summary_ready_traz_os_tres_labels_mesmo_zerados():
    #Arrange - fonte 100% positiva. O Counter so produz chave de label que
    #ocorreu, entao a versao antiga devolvia {"POS": 100.0} e o cliente tinha
    #que lembrar de completar NEU e NEG na mao — um grafico desenhado direto da
    #resposta perdia duas series sem erro nenhum.
    fonte = create_content_source(name="So boa noticia", plataform="NEWS", external_id="UC_sopos")
    post = RawPost.objects.create(
        source=fonte, external_id="sopos_0", text_content="x",
        published_at=timezone.now(), is_processed=True,
    )
    SentimentAnalysis.objects.create(post=post, polarity_score=1.0, label="POS")

    #Act
    res = get_sentiment_summary(fonte.id)

    #assert - as tres chaves SEMPRE presentes, as ausentes como 0.0
    assert res["sentiment"] == {"POS": 100.0, "NEU": 0.0, "NEG": 0.0}


@pytest.mark.django_db
def test_get_sentiment_summary_fonte_sem_posts_vem_empty():
    #Arrange - fonte recem criada, nunca coletada
    fonte = create_content_source(name="Nunca coletada", plataform="REDDIT", external_id="UC_empty")

    #Act
    res = get_sentiment_summary(fonte.id)

    #assert - "empty" quer dizer "colete para comecar", nao "deu erro"
    assert res["state"] == "empty"
    assert res["total_analyzed"] == 0
    assert res["total_pending"] == 0
    #sentiment e None, e nao zeros: zerado leria como resultado calculado, e
    #{} e exatamente o vazio mudo que este contrato existe para eliminar
    assert res["sentiment"] is None


@pytest.mark.django_db
def test_get_sentiment_summary_fonte_so_com_pendentes_vem_processing():
    #Arrange - tem post coletado, mas o worker ainda nao passou por ele
    fonte = create_content_source(name="Coletando", plataform="NEWS", external_id="UC_proc")
    RawPost.objects.create(
        source=fonte, external_id="proc_0", text_content="x",
        published_at=timezone.now(), is_processed=False,
    )

    #Act
    res = get_sentiment_summary(fonte.id)

    #assert - distinguir isto de "empty" e o ponto da issue: aqui a tela mostra
    #"processando", la mostra "colete para comecar". Antes os dois vinham como 200 {}
    assert res["state"] == "processing"
    assert res["total_analyzed"] == 0
    assert res["total_pending"] == 1
    assert res["sentiment"] is None


@pytest.mark.django_db
def test_get_sentiment_summary_geral_agrega_todas_as_fontes():
    #Arrange - duas fontes, uma analise em cada, com labels opostos. Se o
    #escopo geral estivesse filtrando por alguma fonte, o percentual daria 100/0
    primeira = create_content_source(name="Fonte A", plataform="NEWS", external_id="UC_geral_a")
    segunda = create_content_source(name="Fonte B", plataform="REDDIT", external_id="UC_geral_b")
    for i, (fonte, label) in enumerate([(primeira, "POS"), (segunda, "NEG")]):
        post = RawPost.objects.create(
            source=fonte, external_id=f"geral_{i}", text_content="x",
            published_at=timezone.now(), is_processed=True,
        )
        SentimentAnalysis.objects.create(post=post, polarity_score=0.0, label=label)

    #um pendente na segunda fonte, para conferir que total_pending soma o banco
    #inteiro no escopo geral, e nao so a fonte de alguem
    RawPost.objects.create(
        source=segunda, external_id="geral_pendente", text_content="x",
        published_at=timezone.now(), is_processed=False,
    )

    #Act - sem source_id nenhum
    res = get_sentiment_summary()

    #assert - source_id None e o que marca o escopo geral no corpo da resposta
    assert res["source_id"] is None
    assert res["state"] == "ready"
    assert res["total_analyzed"] == 2
    assert res["total_pending"] == 1
    assert res["sentiment"] == {"POS": 50.0, "NEU": 0.0, "NEG": 50.0}