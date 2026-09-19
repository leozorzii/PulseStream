import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.stream_core.models import RawPost, SentimentAnalysis
from apps.stream_core.services import create_content_source

#----------------------KEYWORDS AGREGADAS (#27)---------------------------
#
#GET /api/analytics/keywords/ junta o extracted_keywords de todas as analises
#e responde QUAIS assuntos aparecem e COM QUE HUMOR. A contagem sozinha diz do
#que se fala; o dominant_label diz como as pessoas se sentem sobre aquilo.


def _analise(fonte, external_id, label, keywords):
    """Cria um post ja analisado com as keywords dadas.

    Args:
        fonte (ContentSource): dona do post
        external_id (str): id unico do post
        label (str): "POS"/"NEU"/"NEG"
        keywords (list[str]): extracted_keywords da analise

    Returns:
        SentimentAnalysis: a analise criada
    """
    post = RawPost.objects.create(
        source=fonte, external_id=external_id, text_content="x",
        published_at=timezone.now(), is_processed=True,
    )
    return SentimentAnalysis.objects.create(
        post=post, polarity_score=0.0, label=label, extracted_keywords=keywords,
    )


@pytest.mark.django_db
def test_keywords_conta_termos_e_diz_o_humor_dominante():
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    _analise(fonte, "p1", "NEG", ["golpe", "pix"])
    _analise(fonte, "p2", "NEG", ["golpe", "banco"])
    _analise(fonte, "p3", "POS", ["golpe", "pix"])

    response = APIClient().get("/api/analytics/keywords/")

    assert response.status_code == 200
    #array cru, e nao envelope: e um ranking de tamanho pedido, nao uma colecao
    assert response.data[0] == {"term": "golpe", "count": 3, "dominant_label": "NEG"}


@pytest.mark.django_db
def test_keywords_ordena_por_contagem_e_desempata_pelo_termo():
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    _analise(fonte, "p1", "NEU", ["zebra", "abelha", "meta"])
    _analise(fonte, "p2", "NEU", ["meta"])

    termos = [k["term"] for k in APIClient().get("/api/analytics/keywords/").data]

    #empate em 1 resolvido em ordem alfabetica: sem desempate a ordem entre
    #"zebra" e "abelha" mudaria de uma requisicao para outra e o grafico piscaria
    assert termos == ["meta", "abelha", "zebra"]


@pytest.mark.django_db
def test_keywords_empate_de_humor_e_neutro():
    #mesma regra do classificador: empate entre as contagens e NEU. Escolher
    #um lado pintaria de vermelho (ou verde) um termo sobre o qual a opiniao
    #esta literalmente dividida
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    _analise(fonte, "p1", "POS", ["discord"])
    _analise(fonte, "p2", "NEG", ["discord"])

    item = APIClient().get("/api/analytics/keywords/").data[0]

    assert item == {"term": "discord", "count": 2, "dominant_label": "NEU"}


@pytest.mark.django_db
def test_keywords_filtra_por_fonte():
    a = create_content_source(name="A", plataform="NEWS", external_id="a")
    b = create_content_source(name="B", plataform="NEWS", external_id="b")
    _analise(a, "pa", "POS", ["foguete"])
    _analise(b, "pb", "NEG", ["vazamento"])

    response = APIClient().get(f"/api/analytics/keywords/?source_id={a.id}")

    assert [k["term"] for k in response.data] == ["foguete"]


@pytest.mark.django_db
def test_keywords_respeita_o_limite_pedido():
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    _analise(fonte, "p1", "NEU", ["a1", "a2", "a3", "a4", "a5"])

    response = APIClient().get("/api/analytics/keywords/?limit=2")

    assert len(response.data) == 2


@pytest.mark.django_db
def test_keywords_limita_o_tamanho_da_resposta():
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    for i in range(12):
        _analise(fonte, f"p{i}", "NEU", [f"t{i}a", f"t{i}b", f"t{i}c", f"t{i}d", f"t{i}e"])

    #60 termos distintos no banco, pedido absurdo: o teto e 50
    response = APIClient().get("/api/analytics/keywords/?limit=100000")

    assert len(response.data) == 50


@pytest.mark.django_db
def test_keywords_sem_analise_devolve_lista_vazia():
    #aqui lista vazia e a resposta certa, e nao um null: "nenhum termo" e um
    #ranking valido, e o grafico ja sabe desenhar zero barras
    create_content_source(name="G1", plataform="NEWS", external_id="g1")

    response = APIClient().get("/api/analytics/keywords/")

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_keywords_custa_uma_consulta(django_assert_num_queries):
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    for i in range(10):
        _analise(fonte, f"p{i}", "NEU", ["termo"])

    #o banco devolve so as duas colunas (keywords e label) numa ida; a contagem
    #acontece em Python porque o SQLite nao desaninha JSON pelo ORM
    with django_assert_num_queries(1):
        APIClient().get("/api/analytics/keywords/")


#----------------------VALIDACAO---------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("query", ["?limit=abc", "?limit="])
def test_keywords_com_limit_invalido_retorna_400(query):
    response = APIClient().get(f"/api/analytics/keywords/{query}")

    assert response.status_code == 400
    assert "erro" in response.data


@pytest.mark.django_db
def test_keywords_de_fonte_inexistente_retorna_404():
    response = APIClient().get("/api/analytics/keywords/?source_id=99999")

    assert response.status_code == 404
    assert response.data == {"erro": "fonte nao encontrada"}
