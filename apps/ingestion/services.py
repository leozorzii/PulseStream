from apps.stream_core.services import bulk_create_raw_posts, mark_source_collected


def run_ingestion(source, adapter):
    """Orquestra o fluxo de ingestao de uma fonte

    Nao coleta e nao persiste por conta propria: so amarra os componentes
    que ja existem. O adapter chega por injecao de dependencia, entao o
    service funciona com RSS, Youtube ou qualquer outro que siga o BaseAdapter.

    Args:
        source (ContentSource): a fonte que os posts pertencem
        adapter (BaseAdapter): quem sabe buscar e traduzir os dados da fonte

    Returns:
        list[RawPost]: os posts gravados no banco
    """
    entries = adapter.fetch()  #dados crus da fonte
    posts_data = adapter.parse(entries)  #traduz para o formato do RawPost
    posts = bulk_create_raw_posts(source, posts_data)  #reusa a persistencia do stream_core

    #marca DEPOIS de persistir, e nunca antes: se o fetch estourar (feed fora do
    #ar), a excecao sobe daqui e a fonte continua com a data antiga — que e a
    #informacao verdadeira. Marcar no comeco faria o indicador de defasagem
    #dizer "coletado agora" justamente enquanto o feed esta fora do ar, que e
    #exatamente quando alguem olha para aquele campo.
    #
    #Marca tambem quando posts vem vazio: o campo mede o frescor da CONSULTA,
    #nao o do dado. Um feed estavel sem novidade foi consultado com sucesso, e
    #so marcar quando ha post novo o faria parecer abandonado na tela.
    mark_source_collected(source)
    return posts
