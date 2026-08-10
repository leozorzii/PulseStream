from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
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
        