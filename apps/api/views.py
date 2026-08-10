from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from apps.stream_core.models import ContentSource
from apps.stream_core.selectors import get_active_sources, get_unprocessed_posts, get_sentiment_summary_by_source
from apps.api.serializers import ContentSourceSerializer, RawPostSerializer
class ActiveSourceListView(APIView):
    """Endpoint que lista as fontes de conteudo ativas (GET)."""
    #responde a requisicoes GET
    def get(self, request):
        """Retorna a lista de fontes de conteúdo ativas em JSON."""
        fontes = get_active_sources() #chama o seletor
        serializer = ContentSourceSerializer(fontes, many=True) #traduz para JSON, o many demonstra que sao varios 
        return Response(serializer.data) #devolve

class UnprocessedPostsListView(APIView):
    """Endpoint que lista os posts ainda nao processados (GET)"""
    def get(self, request):
        posts = get_unprocessed_posts()
        serializer = RawPostSerializer(posts, many=True)
        return Response(serializer.data) 
    
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
            
        #valida se a fonte existe
        if not ContentSource.objects.filter(id=source_id).exists():
            return Response(
                {"erro": "fonte nao encotrada"},
                status=status.HTTP_404_NOT_FOUND,
            )      
              
        #passado as verificacoes, dispara a coleta real    
        return Response(
            {"msg": f"coleta disparada para a fonte {source_id}"},
            status=status.HTTP_200_OK,
        )