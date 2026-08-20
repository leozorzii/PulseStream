import time
import pytest
from types import SimpleNamespace
from datetime import datetime, timezone as dt_timezone
from apps.ingestion.adapters.rss import RSSAdapter
from apps.ingestion.exceptions import FeedFetchError
from urllib.error import URLError
from unittest.mock import patch, MagicMock

def test_parse_entries_for_rawpost():
    # Entry fake, imita o que feedparser devolve
    fake_entry = SimpleNamespace(
        id="https://g1.globo.com/noticia-123",
        title="Titulo da noticia",
        subtitle="Resumo limpo da noticia",
        published_parsed=time.struct_time((2026,8,10,16,13,21,0,222,0)), #formato de data que o parse usa
    )
    
    #act
    adapter = RSSAdapter(url="https://qualquer.com/feed")
    response = adapter.parse([fake_entry])
    
    assert len(response) == 1
    post = response[0]
    assert post["external_id"] == "https://g1.globo.com/noticia-123"
    assert post["text_content"] == "Titulo da noticia. Resumo limpo da noticia"
    assert isinstance(post["published_at"], datetime) #verifica se virou datetime, verifica o tipo
    
def test_fetch_return_entries():
    #monta o feed falso(duble de dados)
    feed_false = MagicMock()
    feed_false.entries = ["noticiafake1", "noticiafake2"] 
    #sequestra o feed parser
    with patch("apps.ingestion.adapters.rss.feedparser.parse") as mock_parse:
        mock_parse.return_value = feed_false
        #roda o codigo e usa o duble(mock)
        adapter = RSSAdapter("http://url-de-teste.com/feed")#faz com que o teste nao dependa de internet
        response = adapter.fetch()
        
        #verificacao
    assert response == ["noticiafake1", "noticiafake2"]
        
        
def test_parse_process_multiply_entries():
    # Fabrica duas entries falsas (dados puros, sem mock de comportamento)
    entries = [
        SimpleNamespace(
            id="post-1",
            title="Primeira notícia",
            subtitle="Resumo um",
            published_parsed=(2026, 8, 20, 12, 0, 0, 0, 0, 0),
        ),
        SimpleNamespace(
            id="post-2",
            title="Segunda notícia",
            subtitle="Resumo dois",
            published_parsed=(2026, 8, 20, 13, 0, 0, 0, 0, 0),
        ),
    ]

    adapter = RSSAdapter("http://url-irrelevante.com/feed")
    resultado = adapter.parse(entries)

    # A verificação-chave: processou AS DUAS, não só a primeira
    assert len(resultado) == 2
    assert resultado[0]["external_id"] == "post-1"
    assert resultado[1]["external_id"] == "post-2"
    assert resultado[0]["text_content"] == "Primeira notícia. Resumo um"
    
from datetime import timezone as dt_timezone

def test_parse_converte_published_at_for_utc():
    entry = SimpleNamespace(
        id="post-1",
        title="Notícia",
        subtitle="Resumo",
        published_parsed=(2026, 8, 20, 12, 0, 0, 0, 0, 0),
    )

    adapter = RSSAdapter("http://url-irrelevante.com/feed")
    resultado = adapter.parse([entry])

    published = resultado[0]["published_at"]
    # O output DEVE ter timezone UTC anexado (não pode ser "naive")
    assert published.tzinfo == dt_timezone.utc    
    
def test_parse_lida_com_subtitle_ausente():
    # Entry SEM o atributo subtitle — simula feed real incompleto
    entry = SimpleNamespace(
        id="post-sem-subtitle",
        title="Notícia sem resumo",
        published_parsed=(2026, 8, 20, 12, 0, 0, 0, 0, 0),
    )

    adapter = RSSAdapter("http://url-irrelevante.com/feed")
    resultado = adapter.parse([entry])

    # Não deve quebrar; deve processar usando só o título
    assert len(resultado) == 1
    assert resultado[0]["text_content"] == "Notícia sem resumo. "
    
    
import pytest

def test_fetch_levanta_erro_quando_feed_inacessivel():
    # monta um feed falso que simula falha de acesso
    feed_falho = MagicMock()
    feed_falho.bozo = True
    feed_falho.entries = []
    feed_falho.bozo_exception = URLError("simulando TLS/rede quebrada")

    with patch("apps.ingestion.adapters.rss.feedparser.parse") as mock_parse:
        mock_parse.return_value = feed_falho

        adapter = RSSAdapter("http://url-qualquer.com/feed")

        # espera que fetch() levante a exceção
        with pytest.raises(FeedFetchError):
            adapter.fetch()   