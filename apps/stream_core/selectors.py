from apps.stream_core.models import ContentSource,SentimentAnalysis, RawPost
from collections import Counter #contador automatico

def get_active_sources():
    """Metodo que retorna todas as fontes ativas, em ordem estavel

    A ordenacao NAO e cosmetica: paginacao exige ordem deterministica. Sem
    order_by o banco nao garante a mesma sequencia entre duas consultas, entao
    ao paginar um item pode sair na pagina 1 E na 2, e outro em nenhuma. O DRF
    avisa disso com UnorderedObjectListWarning.

    Por nome porque e a ordem util na interface (lista alfabetica de fontes),
    com id como desempate — nome nao e unico no model, e sem o desempate duas
    fontes homonimas voltariam ao problema de ordem instavel entre elas.

    Returns:
        QuerySet[ContentSource]: fontes com is_active=True, ordenadas por nome
    """
    return ContentSource.objects.filter(is_active=True).order_by("name", "id")


def get_unprocessed_posts():
    """Metodo que retorna os posts nao processados, ordenados do mais antigo ao mais novo

    Returns:
        QuerySet[ContentSource]: post com is_processed = false, ordenados por published_at
    """ 
    return RawPost.objects.filter(is_processed=False).order_by("published_at")


def get_sentiment_summary_by_source(source_id):
    """Retorna o percentual de cada sentimento com POS, NEU, NEG de uma fonte de dados analisada

    Args:
        source_id (int): id da fonte do conteudo a ser resumido
        
    Returns: 
        dict: percentuais por label, ou dicionario vazio {} se a fonte nao tiver analise
    """
    analises = SentimentAnalysis.objects.filter(post__source_id=source_id) # o __ serve para atravessar relacionamentos
    total = analises.count()
    if total == 0:
        return {}
    
                    # Dentro do Counter: list comprehension "para cada analise a em analises, me da o a.label". ex ["POS", "POS", "NEU", "NEG"]
    cont = Counter(a.label for a in analises) #cont =  faz a contagem e devolve por exemplo ({"POS": 2, "NEU": 1, "NEG": 1})
    
    res = {}
    #pega cada par do contador e transforma em percentual
    for label, qtd in cont.items(): 
        res[label] = (qtd / total) * 100
    return res


def get_sentiment_summary(source_id=None):
    """Retorna o resumo de sentimento com o ESTADO explicito, de uma fonte ou do banco inteiro

    COMO FUNCIONA
    Monta dois querysets base — as analises e os posts — e, se veio source_id,
    filtra os dois por ela. O resto e derivado desses dois: total_analyzed e a
    contagem das analises, total_pending e a dos posts com is_processed=False,
    e os percentuais saem de um Counter sobre os labels. Nenhuma consulta e
    disparada ate a primeira contagem, porque queryset e preguicoso; sao 3
    consultas no caminho comum (contar analises, contar pendentes, ler labels).

    POR QUE ELE EXISTE EM VEZ DE GENERALIZAR get_sentiment_summary_by_source
    Aquele selector e chamado direto pelo mcp_server/server.py, que trata o {}
    dele com uma mensagem propria para a IA. Mudar a forma de retorno dele
    quebraria o servidor MCP em silencio — nenhum teste cobre aquele caminho.
    Os dois convivem: o antigo devolve so percentuais, este devolve o contrato.

    COMO O ESTADO E DECIDIDO
    A ordem da decisao e por total_analyzed primeiro, e nao pela contagem de
    pendentes:

        total_analyzed > 0   -> "ready"       ha o que resumir
        senao, existe post   -> "processing"  coletou, o worker ainda nao passou
        senao                -> "empty"       nunca coletou; "colete para comecar"

    Testar total_analyzed antes fecha um buraco das tres definicoes: uma fonte
    com posts todos marcados is_processed=True e ZERO analises nao seria
    nenhuma das tres (nao e vazia, nao tem pendente, nao tem analise). Pelo
    pipeline isso nao acontece — save_sentiment_analysis grava a analise e
    marca o post no MESMO transaction.atomic() — mas acontece se alguem apagar
    uma SentimentAnalysis pelo admin. Cai em "processing", que e o mais honesto
    dos tres, em vez de criar um quarto valor do enum que o cliente nao conhece.

    POR QUE sentiment E None FORA DE "ready"
    Zerado leria como resultado calculado quando nada foi calculado, e {} e
    exatamente o vazio mudo que este contrato existe para eliminar. None diz
    "nao se aplica", que e a informacao verdadeira.

    POR QUE OS TRES LABELS SEMPRE APARECEM QUANDO PRONTO
    O Counter so produz chave de label que ocorreu, entao uma fonte 100%
    positiva devolvia {"POS": 100.0} e o cliente tinha que lembrar de completar
    o resto — um grafico desenhado direto da resposta perdia duas series sem
    erro nenhum. As chaves vem de SentimentAnalysis.SENTIMENTOS, e nao de uma
    lista escrita aqui, para que um label novo no model apareca sozinho no
    payload em vez de virar uma segunda fonte de verdade para manter em sincronia.

    NAO decide sobre a EXISTENCIA da fonte: com um source_id que nao existe no
    banco, os filtros so nao casam com nada e o retorno e "empty". Quem
    distingue "nao existe" (404) de "existe e esta vazia" (200) e a view, porque
    isso e semantica de HTTP e nao do dominio.

    Args:
        source_id (int | None): id da fonte a resumir. None resume o banco
            inteiro, que e o escopo do painel geral

    Returns:
        dict: {"source_id", "state", "total_analyzed", "total_pending",
            "sentiment"}, onde state e "ready" | "processing" | "empty" e
            sentiment e o dict de percentuais por label ou None fora de "ready"
    """
    analises = SentimentAnalysis.objects.all()
    posts = RawPost.objects.all()

    #o mesmo corpo serve aos dois escopos: sem source_id os querysets ficam
    #abertos e as contagens valem para o banco todo. Duplicar em duas funcoes
    #criaria dois lugares para a regra de estado divergir
    if source_id is not None:
        analises = analises.filter(post__source_id=source_id) # __ atravessa o relacionamento
        posts = posts.filter(source_id=source_id)

    total_analyzed = analises.count()
    total_pending = posts.filter(is_processed=False).count()

    if total_analyzed > 0:
        state = "ready"
    elif posts.exists(): #exists() para no primeiro registro, nao conta a tabela
        state = "processing"
    else:
        state = "empty"

    sentiment = None
    if state == "ready":
        #values_list em vez de iterar as instancias: so o label vem do banco,
        #sem construir um objeto SentimentAnalysis por linha para ler um campo
        cont = Counter(analises.values_list("label", flat=True))
        sentiment = {
            label: (cont[label] / total_analyzed) * 100
            for label, _ in SentimentAnalysis.SENTIMENTOS
        }

    return {
        "source_id": source_id,
        "state": state,
        "total_analyzed": total_analyzed,
        "total_pending": total_pending,
        "sentiment": sentiment,
    }
    