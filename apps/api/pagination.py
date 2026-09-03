from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Paginacao padrao de todos os endpoints de lista da API.

    POR QUE CENTRALIZADA, E NAO page_size repetido em cada view
    O tamanho da pagina e parte do CONTRATO que o cliente enxerga: ele decide
    quantas requisicoes o front precisa fazer para montar uma tela. Espalhado
    view a view, um ajuste em `/api/sources/` deixaria `/api/posts/unprocessed/`
    com outro tamanho, e a diferenca so apareceria em producao, no cliente.
    Aqui e um numero so, num lugar so.

    POR QUE NAO DEFAULT_PAGINATION_CLASS NO SETTINGS
    Aquela chave so tem efeito em generics do DRF (ListAPIView e afins), que
    tem o mixin que a le. As views deste projeto sao APIView pura, entao o
    settings ficaria configurado, sem efeito nenhum, e daria a impressao de
    que a paginacao esta ligada. Cada view aplica esta classe a mao.

    20 itens: cabe numa tela de dashboard sem rolagem interminavel e mantem a
    resposta pequena o bastante para nao estourar o timeout de 10s que o
    cliente axios usa.
    """

    page_size = 20
