from rest_framework.views import APIView
from rest_framework.response import Response
from apps.stream_core.models import ContentSource, SentimentAnalysis
from apps.api.serializers import ContentSourceSerializer, RawPostSerializer, PostAnalisadoSerializer
from apps.ingestion.adapters.rss import RSSAdapter
from apps.stream_core.selectors import (
    get_sources, get_unprocessed_posts, get_analyzed_posts, get_sentiment_summary, get_sentiment_timeseries,
    get_keyword_ranking, get_overview,
)
from apps.ingestion.services import run_ingestion
from rest_framework import serializers, status
from apps.ingestion.exceptions import FeedFetchError
from apps.ingestion.tasks import processar_sentimentos
from apps.api.pagination import StandardPagination


#labels aceitos no filtro do feed; sai das choices do model para nao divergir
LABELS_VALIDOS = {codigo for codigo, _rotulo in SentimentAnalysis.SENTIMENTOS}


def _ler_source_id(request):
    """Le e valida o ?source_id opcional, do jeito que toda rota de leitura faz.

    Extraido quando a terceira view (o feed) ia copiar o mesmo bloco pela
    terceira vez. Tres copias de uma regra de contrato divergem: basta uma
    delas esquecer o 404 para um id errado voltar a parecer fonte vazia.

    - ausente: None, escopo geral
    - vazio ou nao numerico: 400. Vazio e o que um <select> sem selecao emite;
      houve intencao de escolher uma fonte, e responder com o escopo geral
      mostraria dado global fingindo ser dado da fonte
    - numero de fonte que nao existe: 404, nunca uma resposta vazia, que faria
      um bug de quem chama parecer uma fonte real sem dados

    Args:
        request (Request): a requisicao do DRF

    Returns:
        tuple[int | None, Response | None]: (source_id, None) quando valido, ou
            (None, resposta de erro) para a view devolver direto
    """
    source_id = request.query_params.get("source_id")
    if source_id is None:
        return None, None

    #coage ANTES de consultar: filter(id="abc") levanta ValueError dentro do
    #ORM e vira 500 com corpo HTML, que o cliente le como falha de parse
    try:
        source_id = int(source_id)
    except ValueError:
        return None, Response(
            {"erro": "source_id deve ser um numero inteiro"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not ContentSource.objects.filter(id=source_id).exists():
        return None, Response(
            {"erro": "fonte nao encontrada"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return source_id, None

class SourceListView(APIView):
    """Endpoint que lista as fontes de conteudo (GET ?include_inactive opcional)."""
    #responde a requisicoes GET
    def get(self, request):
        """Retorna a lista de fontes com seus metadados, paginada.

        include_inactive=true traz tambem as fontes pausadas. Sem o parametro o
        padrao continua sendo so as ativas, para nao mudar o que esta rota ja
        devolvia para quem a consome hoje.

        A comparacao e com a string "true" e nao com o valor cru: query param
        chega SEMPRE como texto, e "false" e uma string nao vazia — um
        `if request.query_params.get("include_inactive")` trataria
        ?include_inactive=false como pedido para incluir, que e o oposto do que
        quem escreveu a URL quis.

        Returns:
            Response: envelope paginado do DRF com as fontes serializadas
        """
        #.lower() para aceitar True/TRUE/true — o cliente que monta a URL nao
        #deveria precisar adivinhar a caixa
        incluir_inativas = request.query_params.get("include_inactive", "").lower() == "true"
        fontes = get_sources(include_inactive=incluir_inativas) #chama o seletor

        # Paginacao aplicada A MAO. APIView nao pagina sozinha: quem le
        # DEFAULT_PAGINATION_CLASS e o mixin dos generics do DRF (ListAPIView e
        # afins), que estas views nao usam. Configurar aquilo no settings
        # ficaria sem efeito e daria a impressao de estar ligado.
        paginator = StandardPagination()

        # Pagina ANTES de serializar: paginate_queryset fatia o queryset, entao
        # o serializer so toca os 20 desta pagina. Serializar primeiro traria o
        # backlog inteiro do banco para a memoria para depois jogar fora quase
        # tudo — que e exatamente o problema que a issue #32 descreve.
        pagina = paginator.paginate_queryset(fontes, request)
        serializer = ContentSourceSerializer(pagina, many=True)
        return paginator.get_paginated_response(serializer.data)

class UnprocessedPostsListView(APIView):
    """Endpoint que lista os posts ainda nao processados (GET), paginado."""
    def get(self, request):
        posts = get_unprocessed_posts()

        # Mesma paginacao manual da view acima, pelo mesmo motivo. Aqui ela
        # importa ainda mais: a fila de nao processados e ilimitada por
        # natureza e cresce sozinha quando o worker fica fora do ar.
        paginator = StandardPagination()
        pagina = paginator.paginate_queryset(posts, request)
        serializer = RawPostSerializer(pagina, many=True)
        return paginator.get_paginated_response(serializer.data)
    
class AnalyzedPostsListView(APIView):
    """Feed de evidencias: posts com o sentimento que receberam (GET), paginado."""

    def get(self, request):
        """Retorna os posts analisados, do mais novo ao mais antigo.

        Filtros opcionais: ?source_id= (mesma validacao das outras rotas) e
        ?label=POS|NEU|NEG, sem diferenciar maiusculas. O filtro por label e o
        que faz "me mostra os negativos" ser uma requisicao so, em vez de baixar
        tudo e filtrar no cliente.

        Label vazio ou fora dos tres e 400, e nao "sem filtro": um label
        digitado errado devolvendo tudo faria o painel mostrar posts positivos
        embaixo do titulo "negativos".

        Paginada como as outras listas: o feed e ilimitado por natureza. A
        pagina e fatiada ANTES de serializar, entao o LIMIT chega ao banco.

        Returns:
            Response: envelope paginado, 400 se source_id ou label forem
                invalidos, ou 404 se a fonte nao existir
        """
        source_id, erro = _ler_source_id(request)
        if erro:
            return erro

        label = request.query_params.get("label")
        if label is not None:
            label = label.upper()
            if label not in LABELS_VALIDOS:
                return Response(
                    {"erro": "label deve ser POS, NEU ou NEG"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        posts = get_analyzed_posts(source_id=source_id, label=label)
        paginator = StandardPagination()
        pagina = paginator.paginate_queryset(posts, request)
        serializer = PostAnalisadoSerializer(pagina, many=True)
        return paginator.get_paginated_response(serializer.data)


class SentimentSummaryView(APIView):
    """Endpoint que retorna o resumo de sentimento (GET ?source_id opcional)"""

    def get(self, request):
        """Retorna o resumo de uma fonte, ou do banco inteiro se nao vier source_id.

        COMO FUNCIONA
        A view faz as duas perguntas que sao de HTTP e delega o resto: o
        source_id e um numero? a fonte existe? So depois disso chama o selector,
        que cuida do dominio (estado, contagens, percentuais).

        AUSENTE E DIFERENTE DE VAZIO
        Sem o parametro, o escopo e o geral — o painel de visao geral e uma tela
        real e nao deve precisar inventar um id. Ja `?source_id=` vazio e 400: e
        o que um <select> sem selecao emite, entao houve intencao de escolher uma
        fonte, e devolver o panorama global ali mostraria dado geral fingindo ser
        dado da fonte.

        POR QUE COAGIR PARA int ANTES DE QUALQUER CONSULTA
        `filter(id="abc")` levanta ValueError la dentro do ORM, sem captura, e o
        Django responde 500 com corpo HTML. Todo caminho de erro do front le
        response.data.erro, entao aquilo chegava la como falha de parse de JSON
        em vez do problema real. O int() no try devolve o mesmo formato {"erro"}
        dos outros guards.

        POR QUE 404 EM VEZ DE state "empty"
        O enum descreve a situacao dos DADOS de uma fonte que existe; nao
        descreve a existencia dela. Um id errado e bug de quem chama, e com 200
        ficava indistinguivel de operacao normal. Mesma forma de erro que o
        trigger ja usa ({"erro": "fonte nao encontrada"}).

        Usa exists() e nao get(): a view nao precisa do objeto, so da resposta
        sim/nao, e assim nao ha excecao para capturar no caminho normal.

        Returns:
            Response: 200 com o contrato do resumo, 400 se o source_id for
                invalido (nao numerico ou vazio) ou 404 se a fonte nao existir
        """
        source_id, erro = _ler_source_id(request)
        if erro:
            return erro

        resumo = get_sentiment_summary(source_id) #seletor
        return Response(resumo) #o dict vira JSON
    
class SentimentTimeseriesView(APIView):
    """Endpoint da serie temporal de sentimento (GET ?source_id &days opcionais)"""

    def get(self, request):
        """Retorna a contagem diaria por rotulo e a polaridade media de cada dia.

        POR QUE ESTA ROTA NAO PAGINA
        E a unica excecao a regra do envelope, e de proposito. A resposta e uma
        JANELA DE TAMANHO FIXO que o proprio cliente pediu — `days`, com teto de
        365 no selector — e nao uma colecao ilimitada como a fila de posts.
        Paginada em 20, uma serie de 30 dias viraria duas paginas e o grafico
        desenharia os 20 primeiros dias achando que sao 30: uma serie truncada,
        sem erro nenhum, com a tendencia do fim do periodo simplesmente ausente.
        O MOCK_TIMESERIES do front tambem e array cru.

        VALIDACAO
        Mesmos guards do summary, pelos mesmos motivos: `days` e `source_id`
        entram no ORM, entao um valor nao numerico viraria ValueError e 500 com
        corpo HTML, que o cliente le como falha de parse de JSON. E um
        source_id inexistente e 404, porque uma serie de zeros faria um id
        errado parecer uma fonte real e silenciosa.

        Returns:
            Response: 200 com a lista de pontos, 400 se days ou source_id forem
                invalidos, ou 404 se a fonte nao existir
        """
        source_id, erro = _ler_source_id(request)
        if erro:
            return erro

        #o default de 30 vive aqui, na fronteira HTTP, e nao no selector: e uma
        #escolha de produto (um mes de tendencia), nao regra de dominio
        try:
            days = int(request.query_params.get("days", 30))
        except ValueError:
            return Response(
                {"erro": "days deve ser um numero inteiro"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serie = get_sentiment_timeseries(source_id=source_id, days=days)
        return Response(serie)


class KeywordRankingView(APIView):
    """Endpoint do ranking de palavras-chave (GET ?source_id &limit opcionais)"""

    def get(self, request):
        """Retorna os termos mais citados com o humor dominante de cada um.

        POR QUE NAO PAGINA
        Mesma excecao da serie temporal: e um ranking de tamanho que o proprio
        cliente pediu (`limit`, com teto de 50 no selector), nao uma colecao
        ilimitada. "Pagina 2 do top 20" nao e uma pergunta que faca sentido, e
        o MOCK_KEYWORDS do front ja e array cru.

        VALIDACAO
        source_id pelo _ler_source_id, como as outras rotas. `limit` nao
        numerico ou vazio e 400; numerico fora da faixa e ajustado pelo selector,
        igual ao `days` da serie.

        Returns:
            Response: 200 com a lista (vazia se nao houver analise), 400 se
                source_id ou limit forem invalidos, ou 404 se a fonte nao existir
        """
        source_id, erro = _ler_source_id(request)
        if erro:
            return erro

        #o default de 20 vive na fronteira HTTP: e o tamanho de um grafico
        #legivel, escolha de produto e nao regra de dominio
        try:
            limit = int(request.query_params.get("limit", 20))
        except ValueError:
            return Response(
                {"erro": "limit deve ser um numero inteiro"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(get_keyword_ranking(source_id=source_id, limit=limit))


class OverviewView(APIView):
    """Endpoint dos numeros do cabecalho do painel (GET ?days opcional)"""

    def get(self, request):
        """Retorna os totais globais e a polaridade de duas janelas iguais.

        `days` e o tamanho de cada janela do trend: padrao 7, teto de 365 no
        selector, e 400 se nao for numero — mesma regra da serie temporal.

        last_collected_at passa pelo DateTimeField do DRF, e nao vai como
        datetime cru: e o que /api/sources/ ja usa para o mesmo campo, entao as
        duas rotas escrevem o horario do mesmo jeito (fuso do projeto). O
        encoder JSON formataria o valor em UTC, e o cliente veria dois
        horarios diferentes para a mesma coleta.

        Returns:
            Response: 200 com o overview, ou 400 se days for invalido
        """
        try:
            days = int(request.query_params.get("days", 7))
        except ValueError:
            return Response(
                {"erro": "days deve ser um numero inteiro"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        overview = get_overview(days=days)
        if overview["last_collected_at"] is not None:
            overview["last_collected_at"] = serializers.DateTimeField().to_representation(
                overview["last_collected_at"]
            )
        return Response(overview)


class TriggerIngestionView(APIView):
    """Endpoint que dispara a coleta de uma fonte (POST)"""
    def post(self, request):
        source_id = request.data.get("source_id")
        #valida se veio o source_id
        if source_id is None:
            return Response(
                {"erro": "informe o source_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        # busca a fonte (uma ida ao banco, com 404 customizado)
        try:
            source = ContentSource.objects.get(id=source_id)
        except ContentSource.DoesNotExist:
            return Response(
                {"erro": "fonte nao encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # sem feed_url nao tem o que coletar via RSS (fonte de Youtube/Twitter, por ex.)
        if not source.feed_url:
            return Response(
                {"erro": "fonte nao possui feed_url configurada"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # tenta coletar, se falhar responde com 502 e para aqui
        # se chegou ate embaixo, eh por que coletou, 200 responde com contagem
        adapter = RSSAdapter(source.feed_url)
        try:
            resultado = run_ingestion(source, adapter)
        except FeedFetchError as e:
           return Response(
               {"erro": f"nao foi possivel acessar feed da fonte: {e}"},
               status=status.HTTP_502_BAD_GATEWAY
           ) 
            
        # coleta deu certo: enfileira a analise de sentimento e responde na hora.
        # o dispatch mora AQUI, e nao dentro do run_ingestion, porque a view e a
        # fronteira de orquestracao: o service continua sem saber que Celery existe
        # e segue testavel/reusavel fora de um contexto com broker.
        # .delay() enfileira em vez de executar: analisar sincrono deixaria a
        # resposta HTTP presa esperando o NLP de todos os posts coletados.
        # sem argumentos porque a task drena os pendentes que encontrar no banco
        # na hora em que rodar (ver docstring de processar_sentimentos).
        processar_sentimentos.delay()

        return Response(
                {
                "msg": f"coleta disparada para a fonte {source_id}",
                "posts_coletados": len(resultado),
            },
            status=status.HTTP_200_OK,
        )