from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.stream_core.models import ContentSource, RawPost, SentimentAnalysis
from apps.stream_core.services import create_content_source

#----------------------FEED DE EVIDENCIAS (#26)---------------------------
#
#GET /api/posts/ devolve o post JUNTO do sentimento que ele recebeu. E a rota
#que deixa o painel mostrar a frase por tras do "64% negativo" — sem ela o
#numero nao tem como ser conferido.


def _post(fonte, external_id, label=None, polarity=0.0, keywords=None, published_at=None, **extra):
    """Cria um post e, se vier label, a analise dele.

    Args:
        fonte (ContentSource): dona do post
        external_id (str): id unico do post
        label (str | None): "POS"/"NEU"/"NEG", ou None para um post pendente
        polarity (float): polarity_score da analise
        keywords (list[str] | None): extracted_keywords da analise
        published_at (datetime | None): quando o post foi publicado
        **extra: campos adicionais do RawPost (author, engagement_score)

    Returns:
        RawPost: o post criado
    """
    post = RawPost.objects.create(
        source=fonte, external_id=external_id, text_content=f"texto {external_id}",
        published_at=published_at or timezone.now(), is_processed=label is not None,
        **extra,
    )
    if label is not None:
        SentimentAnalysis.objects.create(
            post=post, polarity_score=polarity, label=label, extracted_keywords=keywords or [],
        )
    return post


@pytest.mark.django_db
def test_feed_devolve_envelope_so_com_posts_analisados():
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    _post(fonte, "analisado", label="NEG")
    _post(fonte, "pendente")  #sem analise: nao tem o que mostrar como evidencia

    response = APIClient().get("/api/posts/")

    assert response.status_code == 200
    #lista ilimitada por natureza: envelope paginado, como as outras listas
    assert set(response.data) == {"count", "next", "previous", "results"}
    assert response.data["count"] == 1
    assert response.data["results"][0]["external_id"] == "analisado"


@pytest.mark.django_db
def test_feed_tem_a_forma_que_o_painel_espera():
    fonte = create_content_source(name="G1 Tecnologia", plataform="NEWS", external_id="g1t")
    _post(
        fonte, "p1", label="NEG", polarity=-0.67, keywords=["preço", "atraso"],
        author="Redação", engagement_score=12,
    )

    item = APIClient().get("/api/posts/").data["results"][0]

    assert set(item) == {
        "id", "external_id", "text_content", "author", "engagement_score",
        "published_at", "source", "sentiment",
    }
    #fonte ANINHADA e nao um id: o cliente nao precisa cruzar com /api/sources/
    assert item["source"] == {"id": fonte.id, "name": "G1 Tecnologia", "plataform": "NEWS"}
    #polarity_score e o item que faltava da #25
    assert item["sentiment"] == {
        "label": "NEG", "polarity_score": -0.67, "extracted_keywords": ["preço", "atraso"],
    }
    assert item["author"] == "Redação"
    assert item["engagement_score"] == 12


@pytest.mark.django_db
def test_feed_traz_post_de_fonte_pausada_com_a_fonte_resolvida():
    #o motivo de aninhar a fonte: /api/sources/ so lista as ativas por padrao,
    #entao um cliente que cruzasse o id nao acharia a fonte pausada
    pausada = ContentSource.objects.create(
        name="Pausada", plataform="NEWS", external_id="pausada", is_active=False,
    )
    _post(pausada, "antigo", label="POS")

    item = APIClient().get("/api/posts/").data["results"][0]

    assert item["source"]["name"] == "Pausada"


@pytest.mark.django_db
def test_feed_filtra_por_fonte():
    a = create_content_source(name="A", plataform="NEWS", external_id="a")
    b = create_content_source(name="B", plataform="NEWS", external_id="b")
    _post(a, "da-a", label="POS")
    _post(b, "da-b", label="POS")

    response = APIClient().get(f"/api/posts/?source_id={a.id}")

    assert [p["external_id"] for p in response.data["results"]] == ["da-a"]


@pytest.mark.django_db
def test_feed_filtra_por_label():
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    _post(fonte, "bom", label="POS")
    _post(fonte, "ruim", label="NEG")

    response = APIClient().get("/api/posts/?label=NEG")

    assert [p["external_id"] for p in response.data["results"]] == ["ruim"]


@pytest.mark.django_db
def test_feed_aceita_label_em_minusculas():
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    _post(fonte, "ruim", label="NEG")

    response = APIClient().get("/api/posts/?label=neg")

    assert response.data["count"] == 1


@pytest.mark.django_db
def test_feed_vem_do_mais_recente_para_o_mais_antigo():
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    agora = timezone.now()
    _post(fonte, "velho", label="NEU", published_at=agora - timedelta(days=2))
    _post(fonte, "novo", label="NEU", published_at=agora)
    #mesmo instante do "novo": o desempate por id e o que torna a paginacao
    #deterministica, senao um item pode aparecer em duas paginas ou em nenhuma
    _post(fonte, "novo-empatado", label="NEU", published_at=agora)

    ids = [p["external_id"] for p in APIClient().get("/api/posts/").data["results"]]

    assert ids == ["novo-empatado", "novo", "velho"]


@pytest.mark.django_db
def test_feed_nao_cresce_em_consultas_com_o_numero_de_posts(django_assert_num_queries):
    fonte = create_content_source(name="G1", plataform="NEWS", external_id="g1")
    for i in range(15):
        _post(fonte, f"p{i}", label="NEU")

    #2 = o COUNT do paginador + a pagina, com fonte e analise no mesmo JOIN.
    #Sem select_related seriam 2 + 2 por post: 32 consultas para esta pagina
    with django_assert_num_queries(2):
        response = APIClient().get("/api/posts/")

    assert response.data["count"] == 15


#----------------------VALIDACAO---------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("query", ["?label=RAIVA", "?label="])
def test_feed_com_label_invalido_retorna_400(query):
    response = APIClient().get(f"/api/posts/{query}")

    assert response.status_code == 400
    assert "erro" in response.data


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["?source_id=abc", "?source_id="])
def test_feed_com_source_id_invalido_retorna_400(query):
    #vazio e 400 e nao "todas as fontes": mesma regra do summary — ausente e
    #vazio sao pedidos diferentes
    response = APIClient().get(f"/api/posts/{query}")

    assert response.status_code == 400
    assert "erro" in response.data


@pytest.mark.django_db
def test_feed_de_fonte_inexistente_retorna_404():
    #uma lista vazia faria um id errado parecer uma fonte real sem posts
    response = APIClient().get("/api/posts/?source_id=99999")

    assert response.status_code == 404
    assert response.data == {"erro": "fonte nao encontrada"}
