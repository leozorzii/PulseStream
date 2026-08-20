#Classe Abstrata, nao coleta nada so define o contrato com as subs

from abc import ABC, abstractmethod #Abstract Class Base

class BaseAdapter(ABC):
    """Contrato base para todos os adapters de fonte de dados

    toda fonte, Youtube, RSS, etc..., vai herdar dessa classe e implementar o fetch()
    e parse()
    """
    #decorador = metodo obrigatorio nas Subclasses
    @abstractmethod
    def fetch(self):
        """busca os dados crus da fonte(xml do RSS, Json da API)"""
        ...
        
        
    @abstractmethod
    def parse(self, raw_data):
        """Traduz os dados crus para o formato padrao do sistema
        
        Returns:
        list[dict]: lista de posts no formato que o RawPost espera
        """
        ...