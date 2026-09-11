from apps.stream_core.models import ContentSource,SentimentAnalysis, RawPost
from collections import Counter #contador automatico
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

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


def get_sources(include_inactive=False):
    """Lista as fontes com os metadados que a tabela do painel precisa, em ordem estavel

    COMO FUNCIONA
    Monta o queryset de fontes e pendura CINCO anotacoes nele: o total de posts,
    quantos estao pendentes, e a contagem de cada label de sentimento. As cinco
    saem numa consulta so — o banco agrupa e conta, e o Python nunca ve os posts.
    Medido: /api/sources/ com 8 fontes e 48 posts faz 2 consultas (o COUNT do
    paginador e a pagina), e esse numero nao cresce com a quantidade de fontes.

    POR QUE ANOTACAO, E NAO UMA CONTA POR LINHA
    A tabela de fontes mostra essas contagens em toda linha. Buscar post a post,
    ou chamar o resumo por fonte, seria uma requisicao por linha renderizada:
    dez fontes viram onze idas ao banco para desenhar uma tabela. E o problema
    que a issue #28 descreve.

    POR QUE distinct=True EM TODAS
    As cinco anotacoes andam pelo mesmo caminho de join (source -> posts ->
    sentiment). Sem distinct, o produto entre as linhas do join infla TODAS as
    contagens ao mesmo tempo, e o estrago e silencioso: os numeros continuam
    parecendo numeros, so que errados, e sem teste ninguem percebe. Ha um teste
    dedicado a isso, com quantidades diferentes em cada label justamente para
    que a inflacao nao passe despercebida.

    POR QUE UM SELECTOR NOVO, E NAO include_inactive NO get_active_sources
    O mcp_server/server.py chama get_active_sources direto, e nenhum teste
    cobria aquele caminho ate a #37. Mudar a assinatura de um selector que algo
    fora de apps/ importa e como se quebra um consumidor em silencio. Mesmo
    padrao ja usado entre get_sentiment_summary_by_source e get_sentiment_summary:
    o novo nasce ao lado, o antigo nao muda.

    A ordenacao repete a do get_active_sources porque a mesma regra vale: sem
    order_by deterministico a paginacao pode repetir um item numa pagina e sumir
    com ele na outra.

    Args:
        include_inactive (bool): False (padrao) lista so as fontes ativas, que
            e o que /api/sources/ ja devolvia. True traz as pausadas junto, para
            uma tela de gerenciamento poder oferecer "reativar" — sem isso a
            fonte inativa e invisivel para a API inteira

    Returns:
        QuerySet[ContentSource]: fontes ordenadas por nome, cada uma com os
            atributos post_count, pending_count, pos_count, neu_count e
            neg_count anotados
    """
    fontes = ContentSource.objects.all()

    if not include_inactive:
        fontes = fontes.filter(is_active=True)

    return fontes.annotate(
        post_count=Count("posts", distinct=True),
        pending_count=Count("posts", filter=Q(posts__is_processed=False), distinct=True),
        #os tres labels contados a parte, e nao um percentual pronto: o serializer
        #e que decide o formato, e contagem crua e o que permite dizer "nenhuma
        #analise ainda" em vez de fabricar 0% de cada coisa
        pos_count=Count("posts__sentiment", filter=Q(posts__sentiment__label="POS"), distinct=True),
        neu_count=Count("posts__sentiment", filter=Q(posts__sentiment__label="NEU"), distinct=True),
        neg_count=Count("posts__sentiment", filter=Q(posts__sentiment__label="NEG"), distinct=True),
    ).order_by("name", "id")


def get_unprocessed_posts():
    """Metodo que retorna os posts nao processados, ordenados do mais antigo ao mais novo

    Returns:
        QuerySet[ContentSource]: post com is_processed = false, ordenados por published_at
    """ 
    return RawPost.objects.filter(is_processed=False).order_by("published_at")


#Teto da janela da serie temporal. NAO e preciosismo: os dias vazios sao
#preenchidos com zero em Python, entao o tamanho da resposta e ditado pelo
#PARAMETRO e nao pelo dado — ?days=1000000 geraria um milhao de linhas a partir
#de um banco vazio. Um ano cobre qualquer leitura de tendencia deste painel.
MAX_DIAS_SERIE = 365


def get_sentiment_timeseries(source_id=None, days=30):
    """Serie diaria de sentimento: contagem por rotulo e polaridade media do dia

    COMO FUNCIONA
    Trunca published_at para a data, agrupa por ela e conta cada rotulo numa
    unica consulta agregada. O que volta do banco tem so os dias que existem;
    o preenchimento dos dias vazios acontece depois, em Python, porque o ORM
    nao inventa linha que nao esta na tabela.

    Medido com 300 analises espalhadas por 90 dias: 1 consulta, tanto para
    days=30 quanto para days=365. O agregado devolve no maximo uma linha por
    dia COM dado, e o preenchimento e um laco sobre a janela.

    CONTAGEM, E NAO PERCENTUAL
    Percentual esconde volume: um dia com 2 posts e um com 200 leem igual em
    "50% positivo". O cliente deriva o percentual a partir da contagem; nunca
    o contrario.

    AGRUPA POR published_at, NAO POR processed_at
    Interessa quando a OPINIAO FOI EXPRESSA, nao quando o worker classificou.
    processed_at e auto_now_add, entao um backlog de um mes drenado numa tarde
    empilharia tudo num unico dia e inventaria um pico que nunca existiu.

    O FUSO IMPORTA, E ERRA EM SILENCIO
    USE_TZ=True e TIME_ZONE=America/Sao_Paulo: o ORM guarda e devolve em UTC.
    Chamar .date() no datetime que volta jogaria todo post publicado depois das
    21h local para o dia seguinte. TruncDate converte para TIME_ZONE antes de
    truncar, que e o agrupamento que o usuario espera ver. Ha um teste com um
    post as 23:30 fixas — com posts criados no meio do dia o erro passa verde.

    DIA VAZIO TEM avg_polarity None, E NAO 0.0
    Zero e uma polaridade VALIDA: quer dizer "a opiniao foi medida e deu
    neutra". Um dia sem post nenhum nao mediu nada. Com 0.0 a linha do grafico
    desceria ao centro em todo dia de silencio, desenhando uma queda de
    sentimento que nunca aconteceu. As contagens, essas, sao 0 de verdade.

    Args:
        source_id (int | None): id da fonte. None agrega o banco inteiro
        days (int): tamanho da janela em dias, terminando hoje. Limitado a
            MAX_DIAS_SERIE, com minimo de 1

    Returns:
        list[dict]: um item por dia, do mais antigo ao mais recente, cada um
            com {"date" (ISO), "POS", "NEU", "NEG", "avg_polarity"}
    """
    #limita ANTES de qualquer conta: e este numero que decide o tamanho da
    #resposta, entao ele nao pode chegar do cliente sem teto
    days = max(1, min(int(days), MAX_DIAS_SERIE))

    fim = timezone.localdate()
    inicio = fim - timedelta(days=days - 1)

    analises = SentimentAnalysis.objects.all()
    if source_id is not None:
        analises = analises.filter(post__source_id=source_id)

    #__date no filtro tambem respeita TIME_ZONE, entao a janela e recortada no
    #mesmo fuso em que os dias sao agrupados. Se um usasse UTC e o outro local,
    #as pontas da serie ficariam com um dia a mais ou a menos
    linhas = (
        analises.filter(
            post__published_at__date__gte=inicio,
            post__published_at__date__lte=fim,
        )
        .annotate(dia=TruncDate("post__published_at"))
        .values("dia")
        .annotate(
            pos=Count("id", filter=Q(label="POS")),
            neu=Count("id", filter=Q(label="NEU")),
            neg=Count("id", filter=Q(label="NEG")),
            media=Avg("polarity_score"),
        )
    )

    #indexa o que veio do banco para o preenchimento nao virar O(dias x linhas)
    por_dia = {linha["dia"]: linha for linha in linhas}

    serie = []
    for i in range(days):
        dia = inicio + timedelta(days=i)
        linha = por_dia.get(dia)
        serie.append(
            {
                "date": dia.isoformat(),
                "POS": linha["pos"] if linha else 0,
                "NEU": linha["neu"] if linha else 0,
                "NEG": linha["neg"] if linha else 0,
                "avg_polarity": linha["media"] if linha else None,
            }
        )
    return serie


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


#Dez baldes FIXOS sobre [-1, +1]. Fixo, e nao calculado a partir dos dados,
#porque e o que mantem o eixo x estavel quando o usuario troca de fonte: com
#baldes variaveis, duas fontes viram dois graficos que nao dao para comparar.
BALDES_POLARIDADE = 10

#As bordas usam EXATAMENTE a mesma expressao do PolarityHistogram do front
#(-1 + i * 2/BALDES). Isso nao e coincidencia nem estilo: 2/10 nao tem
#representacao binaria exata, entao a borda 3 e -0.3999999999999999 e nao -0.4.
#Calcular do mesmo jeito nos dois lados faz os limites baterem bit a bit; usar
#-0.4 escrito a mao aqui deslocaria a fronteira e uma analise em cima dela
#cairia num balde no backend e noutro na leitura do grafico.
LARGURA_BALDE = 2 / BALDES_POLARIDADE


def _bordas_dos_baldes():
    """Devolve os pares (inicio, fim) dos dez baldes de polaridade.

    Returns:
        list[tuple[float, float]]: as faixas, do balde 0 ao 9
    """
    return [
        (-1 + i * LARGURA_BALDE, -1 + (i + 1) * LARGURA_BALDE)
        for i in range(BALDES_POLARIDADE)
    ]


def get_sentiment_summary(source_id=None):
    """Retorna o resumo de sentimento com o ESTADO explicito, de uma fonte ou do banco inteiro

    COMO FUNCIONA
    Monta dois querysets base — as analises e os posts — e, se veio source_id,
    filtra os dois por ela. O resto e derivado desses dois: total_analyzed e a
    contagem das analises, total_pending e a dos posts com is_processed=False,
    e os percentuais saem de um Counter sobre os labels. Nenhuma consulta e
    disparada ate a primeira contagem, porque queryset e preguicoso.

    Medido com 200 analises: 4 consultas em "ready" — contar analises, contar
    pendentes, ler os labels, e uma agregada que traz media e os dez baldes de
    uma vez. Fora de "ready" sao 2 ou 3, porque nada de polaridade e calculado.
    O numero nao cresce com o tamanho da tabela: o agregado devolve sempre uma
    linha com 11 numeros, tanto para 200 analises quanto para 200 mil.

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

    O QUE O HISTOGRAMA RESPONDE, E OS TRES PERCENTUAIS NAO
    "50% neutro" sai igual para opiniao MORNA (scores em torno de zero) e para
    opiniao POLARIZADA (metade perto de +1, metade perto de -1). Sao situacoes
    opostas para quem monitora uma marca. A distribuicao separa as duas.

    O ZERO E BORDA DE BALDE, E E ONDE MORA TODO O NEU
    O classificador rotula comparando contagens, sem banda morta: empate produz
    polarity_score 0.0 EXATO, e texto sem palavra carregada tambem. Com dez
    baldes sobre [-1,+1] o zero nao e interior de balde nenhum — e a fronteira
    entre o 4 e o 5. As faixas sao [inicio, fim), entao ele cai no balde 5, o
    primeiro a direita do divisor, que e onde o PolarityHistogram do front
    desenha a linha "neutro (0,0)". Jogar para o balde 4 poria a maior barra do
    grafico do lado errado do divisor, afirmando opiniao negativa.

    O ultimo balde e o unico fechado a direita, senao um score de +1.0 nao
    cairia em faixa nenhuma e sumiria da contagem.

    O QUE ESPERAR DO FORMATO DA DISTRIBUICAO
    polarity_score e (pos - neg) / (pos + neg) com contagens inteiras pequenas:
    em texto real o denominador raramente passa de 2 ou 3, entao os valores
    possiveis sao quase so {-1, -0.5, -0.33, 0, 0.33, 0.5, 1}. O histograma sai
    em picos, nao em curva, com um pico grande em zero. Isso e o analisador,
    nao defeito daqui — melhora quando a issue #15 expandir as listas.

    Args:
        source_id (int | None): id da fonte a resumir. None resume o banco
            inteiro, que e o escopo do painel geral

    Returns:
        dict: {"source_id", "state", "total_analyzed", "total_pending",
            "sentiment", "avg_polarity", "histogram"}, onde state e
            "ready" | "processing" | "empty". sentiment, avg_polarity e
            histogram sao None fora de "ready"; histogram e uma lista de dez
            contagens sobre [-1, +1]
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
    avg_polarity = None
    histogram = None
    if state == "ready":
        #values_list em vez de iterar as instancias: so o label vem do banco,
        #sem construir um objeto SentimentAnalysis por linha para ler um campo
        cont = Counter(analises.values_list("label", flat=True))
        sentiment = {
            label: (cont[label] / total_analyzed) * 100
            for label, _ in SentimentAnalysis.SENTIMENTOS
        }

        #media e os dez baldes numa UNICA consulta agregada. A alternativa —
        #trazer todos os polarity_score para o Python e contar aqui — carregaria
        #uma linha por analise so para jogar quase tudo fora; com o backlog
        #crescendo, o custo cresce junto. Aqui volta sempre a mesma linha, com
        #11 numeros, independente do tamanho da tabela.
        bordas = _bordas_dos_baldes()
        agregados = {"media": Avg("polarity_score")}
        for i, (inicio, fim) in enumerate(bordas):
            #o ULTIMO balde fecha a direita (lte); os outros ficam abertos (lt).
            #Com [inicio, fim) em todos, um score de exatamente +1.0 nao cairia
            #em balde nenhum e sumiria da contagem — e +1.0 e valor que o
            #classificador produz de verdade, em texto com carga de um sinal so.
            ultimo = i == BALDES_POLARIDADE - 1
            faixa = (
                Q(polarity_score__gte=inicio, polarity_score__lte=fim)
                if ultimo
                else Q(polarity_score__gte=inicio, polarity_score__lt=fim)
            )
            agregados[f"balde_{i}"] = Count("id", filter=faixa)

        resultado = analises.aggregate(**agregados)
        avg_polarity = resultado["media"]
        histogram = [resultado[f"balde_{i}"] for i in range(BALDES_POLARIDADE)]

    return {
        "source_id": source_id,
        "state": state,
        "total_analyzed": total_analyzed,
        "total_pending": total_pending,
        "sentiment": sentiment,
        #media e distribuicao seguem a mesma regra do sentiment: None fora de
        #"ready". Um avg_polarity 0.0 sem analise nenhuma leria como "opiniao
        #perfeitamente neutra", que e uma afirmacao sobre dado que nao existe
        "avg_polarity": avg_polarity,
        "histogram": histogram,
    }
    