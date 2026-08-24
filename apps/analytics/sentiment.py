import re
from collections import Counter  # lib de contagem de itens numa lista

STOPWORDS = {"o", "a", "de", "e", "no", "na", "é", "que", "do", "da"}
POSITIVAS = {"bom", "ótimo", "adorei", "maravilhoso", "excelente", "amei", "incrível", "gostei"}
NEGATIVAS = {"ruim", "péssimo", "odiei", "horrível", "terrível", "lixo", "detestei", "horrivel"}
NEGACOES = {"não", "nao", "nunca", "nem", "jamais"}

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

def classificar_sentimento(texto):

    """Classifica o sentimento do texto e mede a intensidade dele.

        Devolve o rotulo ja no codigo canonico do banco ("POS"/"NEU"/"NEG"),
        e nao em palavras por extenso, para que o resultado possa ir direto
        para SentimentAnalysis.label sem nenhuma traducao no meio do caminho.
        Traduzir em outra camada seria mais um lugar para o valor divergir
        das choices do model.

        Args:
            texto (str): Texto a ser analisado.

        Returns:
            tuple[str, float]: (label, polarity_score), onde label e "POS",
                "NEU" ou "NEG" e polarity_score vai de -1.0 a +1.0
        """
    
    texto_limpo = limpar_texto(texto)
    palavras = texto_limpo.split()
    
    positivas = 0
    negativas = 0
    negar = False
    
    #flag que verifica se a frase é positiva negativa. Ex: Não é bom 
    for palavra in palavras:
        if palavra in NEGACOES:
            negar = True
            continue
    
        if palavra in POSITIVAS:
            if negar:
                negativas += 1
            else:
                positivas += 1
            negar = False
            
        if palavra in NEGATIVAS:
            if negar:
                positivas += 1
            else:
                negativas += 1
            negar = False
            
    #total de palavras com carga emocional; texto sem nenhuma delas da 0
    total = positivas + negativas

    #guarda contra divisao por zero: texto neutro nao tem denominador para
    #normalizar, entao a polaridade e exatamente 0.0 (nem positiva nem negativa)
    if total == 0:
        polarity_score = 0.0
    else:
        #normaliza entre -1.0 e +1.0 dividindo pelo total de palavras com carga.
        #o denominador e o total, e nao a contagem de palavras do texto, para que
        #a intensidade nao seja diluida pelo tamanho do texto: "otimo" e
        #"otimo, mas o resto do texto e enorme" tem a mesma polaridade
        polarity_score = (positivas - negativas) / total

    #o rotulo sai da comparacao das contagens, nao do sinal do score, para
    #preservar exatamente o criterio de empate que ja existia (empate = neutro)
    if positivas > negativas:
        label = "POS"
    elif negativas > positivas:
        label = "NEG"
    else:
        label = "NEU"

    return label, polarity_score