import time
import pytest
from types import SimpleNamespace
from datetime import datetime, timezone as dt_timezone
from apps.ingestion.adapters.rss import RSSAdapter

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