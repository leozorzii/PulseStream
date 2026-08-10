import time
from datetime import datetime, timezone as dt_timezone

import feedparser
from apps.ingestion.adapters.base import BaseAdapter

#herda do contrato, obrigada a ter fetch e parse
class RSSAdapter(BaseAdapter):
    """Adapter que coleta e traduz noticias de um feed"""
    
    def __init__(self, url):
        """Construtor"""
        self.url = url
        
    def fetch(self):
        """Busca o feed RSS da URL e retorna os entries crus(sem traducao)"""
        feed = feedparser.parse(self.url)
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
                "text_content":f"{entry.title}. {entry.subtitle}",
                "published_at":published,
            })
            return posts