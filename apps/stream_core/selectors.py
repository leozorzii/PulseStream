from apps.stream_core.models import ContentSource,SentimentAnalysis, RawPost
from collections import Counter #contador automatico

def get_active_sources():
    """Metodo que retorna todas as fontes ativas, em ordem estavel

    A ordenacao NAO e cosmetica: paginacao exige ordem deterministica. Sem
    order_by o banco nao garante a mesma sequencia entre duas consultas, entao
    ao paginar um item pode sair na pagina 1 E na 2, e outro em nenhuma. O DRF
    avisa disso com UnorderedObjectListWarning.

    Por nome porque e a ordem util na interface (lista alfabetica de fontes),
    com id como desempate — nome nao e unico no model, e sem o desempate duas
    fontes homonimas voltariam ao problema de ordem instavel entre elas.

    Returns:
        QuerySet[ContentSource]: fontes com is_active=True, ordenadas por nome
    """
    return ContentSource.objects.filter(is_active=True).order_by("name", "id")


def get_unprocessed_posts():
    """Metodo que retorna os posts nao processados, ordenados do mais antigo ao mais novo

    Returns:
        QuerySet[ContentSource]: post com is_processed = false, ordenados por published_at
    """ 
    return RawPost.objects.filter(is_processed=False).order_by("published_at")


def get_sentiment_summary_by_source(source_id):
    """Retorna o percentual de cada sentimento com POS, NEU, NEG de uma fonte de dados analisada

    Args:
        source_id (int): id da fonte do conteudo a ser resumido
        
    Returns: 
        dict: percentuais por label, ou dicionario vazio {} se a fonte nao tiver analise
    """
    analises = SentimentAnalysis.objects.filter(post__source_id=source_id) # o __ serve para atravessar relacionamentos
    total = analises.count()
    if total == 0:
        return {}
    
                    # Dentro do Counter: list comprehension "para cada analise a em analises, me da o a.label". ex ["POS", "POS", "NEU", "NEG"]
    cont = Counter(a.label for a in analises) #cont =  faz a contagem e devolve por exemplo ({"POS": 2, "NEU": 1, "NEG": 1})
    
    res = {}
    #pega cada par do contador e transforma em percentual
    for label, qtd in cont.items(): 
        res[label] = (qtd / total) * 100
    return res
    