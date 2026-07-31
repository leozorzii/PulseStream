import re
from collections import Counter  # lib de contagem de itens numa lista


def limpar_texto(texto):
    """Remove tags HTML e normaliza o texto para minúsculas.

    Args:
        texto (str): Texto de entrada que pode conter marcações HTML.

    Returns:
        str: Texto limpo, sem tags HTML e em letras minúsculas.
    """
    sem_html = re.sub(r"<[^>]+>", "", texto)
    response = sem_html.lower()
    return response


STOPWORDS = {"o", "a", "de", "e", "no", "na", "é", "que", "do", "da"}


def extrair_palavras_chave(texto):
    """Extrai as palavras-chave mais frequentes de um texto.

    Args:
        texto (str): Texto a ser analisado.

    Returns:
        list[str]: Lista com até cinco palavras mais frequentes, excluindo stopwords.
    """
    texto_limpo = limpar_texto(texto)
    palavras = texto_limpo.split()

    palavras_filtradas = []
    for palavra in palavras:
        if palavra not in STOPWORDS:
            palavras_filtradas.append(palavra)

    contador_palavras = Counter(palavras_filtradas)
    mais_comuns = contador_palavras.most_common(5)
    response = [par[0] for par in mais_comuns]
    return response