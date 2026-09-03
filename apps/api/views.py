from rest_framework.views import APIView
from rest_framework.response import Response
from apps.stream_core.models import ContentSource
from apps.api.serializers import ContentSourceSerializer, RawPostSerializer
from apps.ingestion.adapters.rss import RSSAdapter
from apps.stream_core.selectors import get_active_sources, get_unprocessed_posts, get_sentiment_summary_by_source
from apps.ingestion.services import run_ingestion
from rest_framework import status
from apps.ingestion.exceptions import FeedFetchError
from apps.ingestion.tasks import processar_sentimentos
from apps.api.pagination import StandardPagination
class ActiveSourceListView(APIView):
    """Endpoint que lista as fontes de conteudo ativas (GET)."""
    #responde a requisicoes GET
    def get(self, request):
        """Retorna a lista de fontes de conteúdo ativas, paginada."""
        fontes = get_active_sources() #chama o seletor

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
    
class SentimentSummaryView(APIView):
    """Endpoint que retorna o resumo de sentimento de uma fonte (GET ?source_id)
    """
    def get(self, request):
        source_id = request.query_params.get("source_id") #pega o ?source_id 
        #caso de borda, caso nao vier o source_id, por isso a escolha do query_parameter
        if source_id is None:
            return Response(
              {"erro": "informe o parametro source_id"},
              status=status.HTTP_400_BAD_REQUEST, #req mal informada
            )
            
        resume = get_sentiment_summary_by_source(source_id) #seletor
        return Response(resume) #o dict vira JSON
    
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