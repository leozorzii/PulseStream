import pytest
from django.utils import timezone
from apps.stream_core.services import create_content_source
from apps.stream_core.selectors import get_active_sources
from apps.stream_core.selectors import get_unprocessed_posts
from apps.stream_core.selectors import get_sentiment_summary_by_source
from apps.stream_core.selectors import get_sentiment_summary
from apps.stream_core.selectors import get_sources
from apps.stream_core.selectors import get_sentiment_timeseries
from datetime import timedelta, datetime, time as dt_time
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

#----------------------LISTAGEM DE FONTES COM METADADOS---------------------------
#get_sources e um selector NOVO, ao lado de get_active_sources, que continua
#intocado: o mcp_server/server.py chama aquele direto e mudar a assinatura dele
#quebraria o servidor MCP. Mesmo padrao do get_sentiment_summary.

def _fonte_com_posts(nome, external_id, pendentes, labels, ativa=True):
    """Cria uma fonte com posts pendentes e posts ja analisados.

    Args:
        nome (str): nome da fonte
        external_id (str): identificador unico
        pendentes (int): quantos posts sem processar criar
        labels (list[str]): um post analisado por label da lista
        ativa (bool): valor de is_active

    Returns:
        ContentSource: a fonte criada
    """
    fonte = ContentSource.objects.create(
        name=nome, plataform="NEWS", external_id=external_id, is_active=ativa
    )
    for i in range(pendentes):
        RawPost.objects.create(
            source=fonte, external_id=f"{external_id}_pend_{i}", text_content="x",
            published_at=timezone.now(), is_processed=False,
        )
    for i, label in enumerate(labels):
        post = RawPost.objects.create(
            source=fonte, external_id=f"{external_id}_an_{i}", text_content="x",
            published_at=timezone.now(), is_processed=True,
        )
        SentimentAnalysis.objects.create(post=post, polarity_score=0.0, label=label)
    return fonte


@pytest.mark.django_db
def test_get_sources_esconde_inativas_por_padrao():
    #Arrange(cenario)
    _fonte_com_posts("Ativa", "UC_src_a", pendentes=0, labels=[])
    _fonte_com_posts("Inativa", "UC_src_i", pendentes=0, labels=[], ativa=False)

    #Act(executa)
    res = get_sources()

    #assert(verifica se o resultado bateu) - o padrao continua sendo so ativas,
    #para nao mudar o que /api/sources/ ja devolve hoje sem ninguem pedir
    assert [f.name for f in res] == ["Ativa"]


@pytest.mark.django_db
def test_get_sources_inclui_inativas_quando_pedido():
    #Arrange
    _fonte_com_posts("Ativa", "UC_src_a2", pendentes=0, labels=[])
    _fonte_com_posts("Inativa", "UC_src_i2", pendentes=0, labels=[], ativa=False)

    #Act
    res = get_sources(include_inactive=True)

    #assert - sem isto uma tela de gerenciamento nao teria como oferecer
    #"reativar": a fonte pausada e invisivel para a API inteira
    assert [f.name for f in res] == ["Ativa", "Inativa"] #ordem alfabetica


@pytest.mark.django_db
def test_get_sources_conta_posts_e_pendentes_por_fonte():
    #Arrange - 2 pendentes e 3 analisados = 5 posts
    _fonte_com_posts("Canal", "UC_src_cont", pendentes=2, labels=["POS", "POS", "NEG"])

    #Act
    fonte = get_sources().first()

    #assert - contagens por anotacao, numa consulta so. Uma requisicao por linha
    #da tabela para descobrir isso e exatamente o que a issue #28 evita
    assert fonte.post_count == 5
    assert fonte.pending_count == 2


@pytest.mark.django_db
def test_get_sources_conta_os_labels_sem_multiplicar_no_join():
    #Arrange - o risco aqui e silencioso: varias anotacoes Count sobre o mesmo
    #caminho de join podem multiplicar linhas e inflar TODAS as contagens.
    #Com 4 analises e 1 pendente os numeros so batem se o join estiver correto
    _fonte_com_posts("Canal", "UC_src_join", pendentes=1, labels=["POS", "POS", "NEU", "NEG"])

    #Act
    fonte = get_sources().first()

    #assert
    assert fonte.post_count == 5
    assert fonte.pending_count == 1
    assert fonte.pos_count == 2
    assert fonte.neu_count == 1
    assert fonte.neg_count == 1


#----------------------DISTRIBUICAO DE POLARIDADE---------------------------

def _com_scores(external_id, scores):
    """Cria uma fonte com uma analise por score informado.

    Args:
        external_id (str): identificador unico da fonte
        scores (list[float]): um polarity_score por analise a criar

    Returns:
        ContentSource: a fonte criada
    """
    fonte = ContentSource.objects.create(
        name=f"Fonte {external_id}", plataform="NEWS", external_id=external_id
    )
    for i, score in enumerate(scores):
        post = RawPost.objects.create(
            source=fonte, external_id=f"{external_id}_p{i}", text_content="x",
            published_at=timezone.now(), is_processed=True,
        )
        #o label nao importa para o histograma, que le so o score
        SentimentAnalysis.objects.create(post=post, polarity_score=score, label="NEU")
    return fonte


@pytest.mark.django_db
def test_summary_traz_media_de_polaridade():
    #Arrange(cenario) - media de 1.0, -1.0 e 0.0 e zero
    fonte = _com_scores("UC_avg", [1.0, -1.0, 0.0])

    #Act(executa)
    res = get_sentiment_summary(fonte.id)

    #assert(verifica se o resultado bateu)
    assert res["avg_polarity"] == 0.0


@pytest.mark.django_db
def test_histograma_tem_dez_baldes_que_somam_o_total():
    #Arrange
    fonte = _com_scores("UC_hist", [-1.0, -0.5, 0.0, 0.5, 1.0])

    #Act
    res = get_sentiment_summary(fonte.id)

    #assert - dez baldes FIXOS mantem o eixo x estavel entre fontes e deixam o
    #cliente burro; e a soma tem que fechar com o total, senao alguma analise
    #caiu fora de todo balde
    assert len(res["histogram"]) == 10
    assert sum(res["histogram"]) == res["total_analyzed"] == 5


@pytest.mark.django_db
def test_histograma_poe_o_zero_no_balde_5():
    #Arrange - so scores exatamente zero. Este e O teste do contrato: o
    #classificador produz 0.0 EXATO em todo empate e em todo texto sem palavra
    #carregada, entao a maior massa do histograma real mora nesta borda
    fonte = _com_scores("UC_zero", [0.0, 0.0, 0.0])

    #Act
    res = get_sentiment_summary(fonte.id)

    #assert - com 10 baldes sobre [-1,+1] o zero nao e interior de balde nenhum:
    #e a BORDA entre o 4 e o 5. O intervalo e [inicio, fim), entao ele cai no 5,
    #o primeiro a direita do divisor — que e onde o PolarityHistogram do front
    #desenha a linha tracejada "neutro (0,0)". Se cair no 4, a barra aparece do
    #lado errado do divisor e o grafico afirma que a opiniao e negativa
    assert res["histogram"] == [0, 0, 0, 0, 0, 3, 0, 0, 0, 0]


@pytest.mark.django_db
def test_histograma_acomoda_os_dois_extremos():
    #Arrange - -1.0 e +1.0 sao valores que o classificador produz de verdade
    #(texto com carga so de um sinal), nao casos hipoteticos
    fonte = _com_scores("UC_ext", [-1.0, 1.0])

    #Act
    res = get_sentiment_summary(fonte.id)

    #assert - o -1.0 abre o primeiro balde e o +1.0 fecha o ultimo. O ultimo e
    #fechado a direita de proposito: com [inicio, fim) em todos, o +1.0 cairia
    #fora da faixa e sumiria da contagem
    assert res["histogram"][0] == 1
    assert res["histogram"][9] == 1
    assert sum(res["histogram"]) == 2


@pytest.mark.django_db
def test_polaridade_e_none_quando_nao_ha_analise():
    #Arrange - fonte com post pendente, nada analisado
    fonte = ContentSource.objects.create(name="Pend", plataform="NEWS", external_id="UC_pol_none")
    RawPost.objects.create(
        source=fonte, external_id="pol_none_0", text_content="x",
        published_at=timezone.now(), is_processed=False,
    )

    #Act
    res = get_sentiment_summary(fonte.id)

    #assert - mesma regra do sentiment: None diz "nao se aplica". Um
    #avg_polarity 0.0 aqui leria como "opiniao perfeitamente neutra", que e uma
    #afirmacao sobre dado que nao existe
    assert res["state"] == "processing"
    assert res["avg_polarity"] is None
    assert res["histogram"] is None


#----------------------SERIE TEMPORAL---------------------------

def _analise_em(fonte, external_id, quando, label="POS", score=1.0):
    """Cria um post publicado em `quando`, ja analisado.

    Args:
        fonte (ContentSource): dona do post
        external_id (str): identificador unico do post
        quando (datetime): published_at, aware
        label (str): rotulo da analise
        score (float): polarity_score da analise

    Returns:
        SentimentAnalysis: a analise criada
    """
    post = RawPost.objects.create(
        source=fonte, external_id=external_id, text_content="x",
        published_at=quando, is_processed=True,
    )
    return SentimentAnalysis.objects.create(post=post, polarity_score=score, label=label)


@pytest.mark.django_db
def test_timeseries_conta_por_dia_e_nao_percentual():
    #Arrange(cenario) - 2 POS e 1 NEG no mesmo dia
    fonte = ContentSource.objects.create(name="F", plataform="NEWS", external_id="UC_ts_1")
    hoje = timezone.localtime()
    for i, label in enumerate(["POS", "POS", "NEG"]):
        _analise_em(fonte, f"ts1_{i}", hoje, label=label)

    #Act(executa)
    serie = get_sentiment_timeseries(fonte.id, days=1)

    #assert(verifica se o resultado bateu) - CONTAGEM, nao percentual: um dia
    #com 2 posts e um com 200 leriam igual em "50% positivo", e o cliente
    #consegue derivar o percentual mas nunca a contagem
    assert len(serie) == 1
    assert serie[0]["POS"] == 2
    assert serie[0]["NEG"] == 1
    assert serie[0]["NEU"] == 0


@pytest.mark.django_db
def test_timeseries_agrupa_por_published_at_e_nao_processed_at():
    #Arrange - post PUBLICADO ha 3 dias, analisado agora (worker drenando
    #backlog). processed_at e sempre "agora" porque o campo e auto_now_add
    fonte = ContentSource.objects.create(name="F", plataform="NEWS", external_id="UC_ts_2")
    tres_dias_atras = timezone.localtime() - timedelta(days=3)
    _analise_em(fonte, "ts2_0", tres_dias_atras)

    #Act
    serie = get_sentiment_timeseries(fonte.id, days=5)

    #assert - interessa QUANDO A OPINIAO FOI EXPRESSA, nao quando o worker
    #classificou. Agrupar por processed_at empilharia um mes de backlog drenado
    #numa tarde num unico dia, inventando um pico que nunca existiu
    por_dia = {p["date"]: p for p in serie}
    dia_publicacao = tres_dias_atras.date().isoformat()
    assert por_dia[dia_publicacao]["POS"] == 1
    assert por_dia[timezone.localdate().isoformat()]["POS"] == 0


@pytest.mark.django_db
def test_timeseries_emite_dias_vazios_como_zero():
    #Arrange - uma analise so, ha 4 dias; os outros dias nao existem no banco
    fonte = ContentSource.objects.create(name="F", plataform="NEWS", external_id="UC_ts_3")
    _analise_em(fonte, "ts3_0", timezone.localtime() - timedelta(days=4))

    #Act
    serie = get_sentiment_timeseries(fonte.id, days=5)

    #assert - os 5 dias presentes, com zero explicito nos vazios. Sem isso o
    #grafico liga o ponto de 4 dias atras direto no de hoje com uma reta,
    #desenhando continuidade sobre o que na verdade foi silencio
    assert len(serie) == 5
    assert sum(p["POS"] for p in serie) == 1
    assert [p["POS"] for p in serie].count(0) == 4


@pytest.mark.django_db
def test_timeseries_traz_media_de_polaridade_do_dia():
    #Arrange - +1.0 e -1.0 no mesmo dia: media zero
    fonte = ContentSource.objects.create(name="F", plataform="NEWS", external_id="UC_ts_4")
    hoje = timezone.localtime()
    _analise_em(fonte, "ts4_0", hoje, label="POS", score=1.0)
    _analise_em(fonte, "ts4_1", hoje, label="NEG", score=-1.0)

    #Act
    serie = get_sentiment_timeseries(fonte.id, days=1)

    #assert - e o avg_polarity que viabiliza um grafico de linha unica em vez
    #de tres areas empilhadas
    assert serie[0]["avg_polarity"] == 0.0


@pytest.mark.django_db
def test_timeseries_dia_vazio_tem_polaridade_none_e_nao_zero():
    #Arrange - nada publicado em lugar nenhum
    fonte = ContentSource.objects.create(name="F", plataform="NEWS", external_id="UC_ts_5")

    #Act
    serie = get_sentiment_timeseries(fonte.id, days=3)

    #assert - None, e nao 0.0. Zero e uma polaridade VALIDA, que significa
    #"opiniao medida e neutra"; um dia sem post nenhum nao mediu nada. Com 0.0
    #a linha do grafico desceria ate o centro em todo dia de silencio,
    #desenhando uma queda de sentimento que nunca aconteceu
    assert all(p["avg_polarity"] is None for p in serie)
    assert all(p["POS"] == 0 for p in serie)


@pytest.mark.django_db
def test_timeseries_usa_o_fuso_local_e_nao_utc():
    #Arrange - post publicado as 23:30 no horario de Sao Paulo. Em UTC isso ja
    #e 02:30 do DIA SEGUINTE (UTC-3)
    fonte = ContentSource.objects.create(name="F", plataform="NEWS", external_id="UC_ts_6")
    hoje_local = timezone.localdate()
    tarde_da_noite = timezone.make_aware(
        datetime.combine(hoje_local, dt_time(23, 30))
    )
    _analise_em(fonte, "ts6_0", tarde_da_noite)

    #Act
    serie = get_sentiment_timeseries(fonte.id, days=2)

    #assert - o post conta no dia LOCAL em que foi publicado. Este teste passa
    #verde se os posts do cenario forem criados no meio do dia, e so falha com
    #horario de borda — que e por que ele existe com 23:30 fixo. Agrupar pela
    #data do datetime que o ORM devolve (UTC) jogaria todo post depois das 21h
    #para o dia seguinte, em silencio
    por_dia = {p["date"]: p for p in serie}
    assert por_dia[hoje_local.isoformat()]["POS"] == 1


@pytest.mark.django_db
def test_timeseries_sem_source_id_agrega_todas_as_fontes():
    #Arrange - duas fontes, uma analise em cada, no mesmo dia
    hoje = timezone.localtime()
    for n in range(2):
        f = ContentSource.objects.create(name=f"F{n}", plataform="NEWS", external_id=f"UC_ts_7_{n}")
        _analise_em(f, f"ts7_{n}", hoje)

    #Act - sem source_id
    serie = get_sentiment_timeseries(days=1)

    #assert
    assert serie[0]["POS"] == 2
