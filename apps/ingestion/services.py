from apps.stream_core.services import bulk_create_raw_posts


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
    return bulk_create_raw_posts(source, posts_data)  #reusa a persistencia do stream_core
