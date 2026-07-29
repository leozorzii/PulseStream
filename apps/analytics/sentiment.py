import re

def limpar_texto(texto):
    sem_html = re.sub(r"<[^>]+>", "", texto)
    response = sem_html.lower()
    return response