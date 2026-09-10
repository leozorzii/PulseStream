import json

import pytest
from asgiref.sync import sync_to_async
from django.utils import timezone
from mcp.shared.memory import create_connected_server_and_client_session

from apps.stream_core.models import ContentSource, RawPost, SentimentAnalysis
from apps.stream_core.services import create_content_source
from mcp_server.server import mcp

#----------------------COMO ESTES TESTES RODAM---------------------------
#
#CLIENTE IN-MEMORY, SEM TRANSPORTE
#create_connected_server_and_client_session liga um cliente ao servidor por
#streams de memoria: sem socket, sem subprocesso, sem stdio. E o equivalente
#oficial do `Client(mcp)` do pacote standalone `fastmcp`, que NAO esta
#instalado aqui — o SDK oficial (mcp==1.29.1) traz este helper e nao aquela
#classe. Chamar pelo nome da tool, e nao a funcao Python direto, e o ponto:
#assim o teste cobre o registro no @mcp.tool(), a validacao do argumento e a
#serializacao da resposta. Chamar listar_fontes() direto pularia as tres.
#
#POR QUE transaction=True E NAO O django_db SIMPLES
#As tools chamam o ORM via sync_to_async, que executa noutra conexao — fora do
#bloco atomico que o django_db abre. O rollback do teste nao alcanca aquelas
#escritas: elas commitam de verdade e VAZAM para o teste seguinte, que quebra
#com external_id duplicado. Conferido rodando. transaction=True commita e
#limpa as tabelas entre os testes, que e o unico isolamento que funciona
#quando o trabalho atravessa thread.
#
#POR QUE O ARRANGE VAI DENTRO DE sync_to_async
#O corpo do teste e async, entao tocar o ORM direto levanta
#SynchronousOnlyOperation. O cenario fica numa funcao sincrona comum e o teste
#a atravessa uma vez so, em vez de embrulhar chamada por chamada.


def _payload(resultado):
    """Le o corpo JSON de uma tool que devolve um dicionario.

    Le content, e nao structuredContent, porque resumo_sentimento_fonte e
    anotada `-> dict`: um dict pelado nao gera schema de saida, entao o FastMCP
    deixa structuredContent como None e o payload existe so aqui. content e
    tambem o que um cliente real recebe pela rede, entao a asercao nao depende
    da inferencia de schema do framework.

    Args:
        resultado (CallToolResult): o que session.call_tool devolveu

    Returns:
        dict: o corpo da resposta ja desserializado
    """
    return json.loads(resultado.content[0].text)


def _lista(resultado):
    """Le o corpo de uma tool que devolve uma lista de dicionarios.

    O FastMCP quebra a lista em um bloco de texto por item, entao a montagem
    de volta e por bloco.

    Args:
        resultado (CallToolResult): o que session.call_tool devolveu

    Returns:
        list[dict]: os itens da lista ja desserializados
    """
    return [json.loads(bloco.text) for bloco in resultado.content]


#----------------------LISTAR FONTES---------------------------

def _cenario_fontes():
    """Cria uma fonte ativa e uma inativa. Sincrona de proposito: e chamada
    atraves de sync_to_async, porque o teste que a usa e async.

    Returns:
        ContentSource: a fonte ativa, que e a unica que a tool deve devolver
    """
    ativa = create_content_source(name="Canal Ativo", plataform="YOUTUBE", external_id="UC_mcp_ativa")
    #inativa criada pelo ORM direto: o service nao aceita is_active
    ContentSource.objects.create(
        name="Canal Inativo", plataform="YOUTUBE", external_id="UC_mcp_inativa", is_active=False
    )
    return ativa


@pytest.mark.django_db(transaction=True)
async def test_listar_fontes_devolve_so_as_ativas_com_plataforma_legivel():
    #Arrange(cenario)
    ativa = await sync_to_async(_cenario_fontes)()

    #Act(executa) - pelo nome da tool, como um modelo do outro lado faria
    async with create_connected_server_and_client_session(mcp) as session:
        resultado = await session.call_tool("listar_fontes", {})

    #assert(verifica se o resultado bateu)
    fontes = _lista(resultado)
    assert len(fontes) == 1 #a inativa nao pode aparecer
    assert fontes[0] == {
        "id": ativa.id,
        "nome": "Canal Ativo",
        "plataforma": "Youtube", #get_plataform_display(), nao o codigo "YOUTUBE"
    }


@pytest.mark.django_db(transaction=True)
async def test_listar_fontes_traduz_o_codigo_da_plataforma():
    #Arrange - o valor gravado e "NEWS"; a tool tem que entregar o rotulo humano.
    #Sem isso o modelo do outro lado recebe uma sigla do banco e passa a
    #inventar traducao por conta propria
    await sync_to_async(create_content_source)(
        name="Portal", plataform="NEWS", external_id="UC_mcp_news"
    )

    #Act
    async with create_connected_server_and_client_session(mcp) as session:
        resultado = await session.call_tool("listar_fontes", {})

    #assert
    assert _lista(resultado)[0]["plataforma"] == "Portal de Noticias"


#----------------------RESUMO DE SENTIMENTO---------------------------

def _cenario_com_analises():
    """Cria uma fonte com 6 analises: 3 POS, 2 NEU, 1 NEG.

    Seis, e nao quatro, porque 2/6 e 1/6 dao dizimas (33.333... e 16.666...) e
    e isso que exercita o round(...,1) da tool. Com quatro analises os
    percentuais sairiam redondos sozinhos e o arredondamento passaria sem
    teste. Os tres rotulos aparecem para cobrir as tres traducoes.

    Returns:
        ContentSource: a fonte criada
    """
    fonte = create_content_source(name="Com analise", plataform="REDDIT", external_id="UC_mcp_cheia")
    for i, label in enumerate(["POS", "POS", "POS", "NEU", "NEU", "NEG"]):
        post = RawPost.objects.create(
            source=fonte,
            external_id=f"mcp_post_{i}",
            text_content="x",
            published_at=timezone.now(),
            is_processed=True,
        )
        SentimentAnalysis.objects.create(post=post, polarity_score=0.0, label=label)
    return fonte


@pytest.mark.django_db(transaction=True)
async def test_resumo_de_fonte_com_analises_traz_percentuais_legiveis():
    #Arrange(cenario)
    fonte = await sync_to_async(_cenario_com_analises)()

    #Act(executa)
    async with create_connected_server_and_client_session(mcp) as session:
        resultado = await session.call_tool("resumo_sentimento_fonte", {"source_id": fonte.id})

    #assert(verifica se o resultado bateu)
    corpo = _payload(resultado)
    assert corpo["source_id"] == fonte.id
    #chaves com nome por extenso, nao os codigos POS/NEU/NEG do banco
    assert corpo["resumo"] == {"Positivo": 50.0, "Neutro": 33.3, "Negativo": 16.7}


@pytest.mark.django_db(transaction=True)
async def test_resumo_de_fonte_sem_analises_traz_mensagem_explicita():
    #Arrange - fonte existe e nunca teve post analisado. O selector devolve {}
    #para este caso, e um {} pelado nao diz NADA a quem le do outro lado:
    #"nao tem dado" e "deu erro" ficam com a mesma cara
    fonte = await sync_to_async(create_content_source)(
        name="Sem analise", plataform="NEWS", external_id="UC_mcp_vazia"
    )

    #Act
    async with create_connected_server_and_client_session(mcp) as session:
        resultado = await session.call_tool("resumo_sentimento_fonte", {"source_id": fonte.id})

    #assert - ESTE E O TESTE GUARDIAO. Traduzir o {} mudo numa frase explicita
    #e a unica razao de a camada de tool existir por cima do selector; se
    #alguem "simplificar" isso devolvendo o resumo cru, a tool perde a funcao
    #dela e nada mais no projeto percebe
    corpo = _payload(resultado)
    assert corpo["mensagem"] == "Fonte ainda não possui posts analisados"
    assert corpo["source_id"] == fonte.id
    assert corpo["resumo"] == {}
    assert resultado.isError is False #ausencia de dado nao e falha da tool
