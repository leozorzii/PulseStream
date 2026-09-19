from datetime import datetime, time, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.stream_core.models import ContentSource, RawPost, SentimentAnalysis
from apps.stream_core.services import create_content_source

#----------------------OVERVIEW DO KPI (#29)---------------------------
#
#GET /api/analytics/overview/ entrega os numeros do cabecalho do painel numa
#requisicao so. Sem ela o KPI precisaria de uma chamada por fonte mais a fila
#de pendentes inteira, para desenhar quatro inteiros.


def _post(fonte, external_id, label=None, polarity=0.0, published_at=None):
    """Cria um post, analisado se vier label.

    Args:
        fonte (ContentSource): dona do post
        external_id (str): id unico do post
        label (str | None): "POS"/"NEU"/"NEG", ou None para pendente
        polarity (float): polarity_score da analise
        published_at (datetime | None): quando foi publicado; padrao agora

    Returns:
        RawPost: o post criado
    """
    post = RawPost.objects.create(
        source=fonte, external_id=external_id, text_content="x",
        published_at=published_at or timezone.now(), is_processed=label is not None,
    )
    if label is not None:
        SentimentAnalysis.objects.create(post=post, polarity_score=polarity, label=label)
    return post


def _as_2330_de(dias_atras):
    """23:30 no fuso do projeto, `dias_atras` dias antes de hoje.

    23:30 de proposito: em America/Sao_Paulo isso ja e o dia seguinte em UTC.
    Um recorte de janela feito com .date() no valor UTC empurraria o post para
    o dia seguinte — e para a janela errada, se ele estiver na borda.
    """
    dia = timezone.localdate() - timedelta(days=dias_atras)
    return timezone.make_aware(datetime.combine(dia, time(23, 30)))


@pytest.mark.django_db
def test_overview_tem_a_forma_do_kpi():
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    _post(fonte, "a", label="POS", polarity=1.0)
    _post(fonte, "b", label="NEG", polarity=-1.0)
    _post(fonte, "c", label="POS", polarity=1.0)
    _post(fonte, "pendente")

    response = APIClient().get("/api/analytics/overview/")

    assert response.status_code == 200
    corpo = response.data
    assert set(corpo) == {
        "total_posts", "analyzed_posts", "pending_posts", "active_sources",
        "sentiment", "avg_polarity", "last_collected_at", "trend",
    }
    assert corpo["total_posts"] == 4
    assert corpo["analyzed_posts"] == 3
    assert corpo["pending_posts"] == 1
    assert corpo["sentiment"]["POS"] == pytest.approx(66.666, rel=1e-3)
    assert corpo["avg_polarity"] == pytest.approx(1 / 3)


@pytest.mark.django_db
def test_overview_concorda_com_o_summary_geral():
    #as duas rotas mostram o sentimento global; se divergirem, o KPI e o
    #grafico do mesmo painel contam historias diferentes
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    for i, label in enumerate(["POS", "NEG", "NEU", "NEU"]):
        _post(fonte, f"p{i}", label=label, polarity={"POS": 1.0, "NEG": -1.0, "NEU": 0.0}[label])

    client = APIClient()
    overview = client.get("/api/analytics/overview/").data
    summary = client.get("/api/analytics/summary/").data

    assert overview["sentiment"] == summary["sentiment"]
    assert overview["avg_polarity"] == summary["avg_polarity"]


@pytest.mark.django_db
def test_overview_conta_so_fontes_ativas_e_pega_a_coleta_mais_recente():
    recente = timezone.now() - timedelta(hours=1)
    ContentSource.objects.create(
        name="Ativa", plataform="NEWS", external_id="ativa",
        last_collected_at=timezone.now() - timedelta(days=3),
    )
    ContentSource.objects.create(
        name="Ativa recente", plataform="NEWS", external_id="ativa2", last_collected_at=recente,
    )
    ContentSource.objects.create(name="Pausada", plataform="NEWS", external_id="p", is_active=False)

    corpo = APIClient().get("/api/analytics/overview/").data

    assert corpo["active_sources"] == 2
    assert corpo["last_collected_at"] == timezone.localtime(recente).isoformat()


@pytest.mark.django_db
def test_overview_de_banco_vazio_nao_inventa_numero():
    #null e nao zero: avg_polarity 0.0 leria como "opiniao perfeitamente neutra"
    #sobre dado que nao existe, e last_collected_at vazio e "nunca coletou",
    #que e diferente de "coletou faz tempo"
    corpo = APIClient().get("/api/analytics/overview/").data

    assert corpo["total_posts"] == 0
    assert corpo["sentiment"] is None
    assert corpo["avg_polarity"] is None
    assert corpo["last_collected_at"] is None
    assert corpo["trend"]["avg_polarity_current_period"] is None
    assert corpo["trend"]["avg_polarity_previous_period"] is None


#----------------------TREND---------------------------

@pytest.mark.django_db
def test_trend_compara_duas_janelas_do_mesmo_tamanho():
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    agora = timezone.now()
    #janela atual (ultimos 7 dias)
    _post(fonte, "atual-1", label="POS", polarity=1.0, published_at=agora)
    _post(fonte, "atual-2", label="NEU", polarity=0.0, published_at=agora - timedelta(days=6))
    #janela anterior (os 7 dias antes dessa)
    _post(fonte, "anterior", label="NEG", polarity=-1.0, published_at=agora - timedelta(days=10))
    #fora das duas: nao pode entrar em media nenhuma
    _post(fonte, "antigo", label="POS", polarity=1.0, published_at=agora - timedelta(days=30))

    trend = APIClient().get("/api/analytics/overview/").data["trend"]

    assert trend == {
        "window_days": 7,
        "avg_polarity_current_period": 0.5,
        "avg_polarity_previous_period": -1.0,
    }


@pytest.mark.django_db
def test_trend_recorta_a_janela_no_fuso_do_projeto():
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    #23:30 local do ultimo dia da janela ANTERIOR. Em UTC ja e o primeiro dia
    #da janela atual — um recorte em UTC poria este post no lugar errado
    _post(fonte, "borda", label="NEG", polarity=-1.0, published_at=_as_2330_de(7))

    trend = APIClient().get("/api/analytics/overview/").data["trend"]

    assert trend["avg_polarity_previous_period"] == -1.0
    assert trend["avg_polarity_current_period"] is None


@pytest.mark.django_db
def test_trend_aceita_a_janela_do_seletor_de_periodo():
    #o painel escolhe 7, 30 ou 90 dias; um trend fixo em 7 contradiria o
    #seletor que esta na mesma tela
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    _post(fonte, "p", label="POS", polarity=1.0, published_at=timezone.now() - timedelta(days=20))

    trend = APIClient().get("/api/analytics/overview/?days=30").data["trend"]

    assert trend["window_days"] == 30
    assert trend["avg_polarity_current_period"] == 1.0


@pytest.mark.django_db
def test_trend_limita_a_janela():
    trend = APIClient().get("/api/analytics/overview/?days=999999").data["trend"]

    assert trend["window_days"] == 365


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["?days=abc", "?days="])
def test_overview_com_days_invalido_retorna_400(query):
    response = APIClient().get(f"/api/analytics/overview/{query}")

    assert response.status_code == 400
    assert "erro" in response.data


@pytest.mark.django_db
def test_overview_nao_cresce_em_consultas(django_assert_num_queries):
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    for i in range(30):
        _post(fonte, f"p{i}", label="NEU")

    #4 do summary geral (reaproveitado) + 1 total de posts + 1 fontes (ativas e
    #ultima coleta juntas) + 1 as duas medias de janela juntas. Fixo: nao
    #depende de quantos posts ou fontes existem
    with django_assert_num_queries(7):
        APIClient().get("/api/analytics/overview/")
