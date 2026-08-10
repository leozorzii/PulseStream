from rest_framework.views import APIView
from rest_framework.response import Response
from apps.stream_core.selectors import get_active_sources
from apps.api.serializers import ContentSourceSerializer

class ActiveSourceListView(APIView):
    """Endpoint que lista as fontes de conteudo ativas usando GET."""
    #responde a requisicoes GET
    def get(self, request):
        """Retorna a lista de fontes de conteúdo ativas em JSON."""
        fontes = get_active_sources() #chama o seletor
        serializer = ContentSourceSerializer(fontes, many=True) #traduz para JSON, o many demonstra que sao varios 
        return Response(serializer.data) #devolve