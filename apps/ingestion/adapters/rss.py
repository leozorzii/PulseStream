import time
from datetime import datetime, timezone as dt_timezone

import feedparser
from apps.ingestion.adapters.base import BaseAdapter
from apps.ingestion.exceptions import FeedFetchError


#herda do contrato, obrigada a ter fetch e parse
class RSSAdapter(BaseAdapter):
    """Adapter que coleta e traduz noticias de um feed"""
    
    def __init__(self, url):
        """Construtor"""
        self.url = url
        
    def fetch(self):
        """Busca o feed RSS da URL e retorna os entries crus(sem traducao)"""
        feed = feedparser.parse(self.url)
        #verificao usando excecao
        if feed.bozo and not feed.entries:
            raise FeedFetchError(f"Falha ao acessar o feed {self.url}:  {feed.bozo_exception}")
        
        return feed.entries
    
    def parse(self,entries):
        """Traduz as entries do feedparser para o formato RawPost
        
        Args:
            entries(list): itens do feed
        
        
        Returns:
            list[dict]: posts com external_id, text_content e published_at
        """
        posts = []
        for entry in entries:
            timestamp = time.mktime(entry.published_parsed)
            published = datetime.fromtimestamp(timestamp, tz=dt_timezone.utc)
            posts.append({
                "external_id":entry.id,
                "text_content":f"{entry.title}. {getattr(entry, "subtitle", '')}", #pega o subtitle, se nao existir, usa '' para nao estourar
                "published_at":published,
            })
        return posts