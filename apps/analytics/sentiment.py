import re
import unicodedata
from collections import Counter  # lib de contagem de itens numa lista

#PALAVRAS FUNCIONAIS DO PORTUGUES
#A lista antiga tinha dez palavras, e o top de keywords dos 100 posts reais
#do G1 era em, para, como, com, por, diz: conectivo, nao assunto. Aqui entram
#artigos, preposicoes e suas contracoes, pronomes, conjuncoes, adverbios de
#intensidade e as formas mais comuns de ser/estar/ter/ir/poder. "não" e
#stopword para as keywords mas continua em NEGACOES: sao usos diferentes, e o
#classificador nao olha esta lista.
STOPWORDS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "num", "numa", "dum", "duma", "ao", "aos", "à", "às",
    "por", "pelo", "pela", "pelos", "pelas", "para", "pra", "com", "sem",
    "sobre", "entre", "até", "após", "desde", "contra", "sob", "perante",
    "e", "ou", "mas", "nem", "que", "se", "como", "quando", "onde", "porque",
    "pois", "porém", "enquanto", "embora", "também", "já", "ainda", "só",
    "apenas", "mais", "menos", "muito", "muita", "muitos", "muitas", "pouco",
    "tão", "bem", "não", "sim", "lá", "aqui", "agora", "então", "assim",
    "eu", "tu", "ele", "ela", "nós", "eles", "elas", "você", "vocês",
    "me", "te", "lhe", "lhes", "vos", "seu", "sua", "seus", "suas",
    "meu", "minha", "nosso", "nossa", "dele", "dela", "deles", "delas",
    "este", "esta", "estes", "estas", "esse", "essa", "esses", "essas",
    "aquele", "aquela", "isto", "isso", "aquilo", "qual", "quais", "quem",
    "outro", "outra", "outros", "outras", "todo", "toda", "todos", "todas",
    "cada", "mesmo", "mesma", "algum", "alguma", "alguns", "algumas",
    "é", "são", "era", "foi", "foram", "ser", "sido", "será", "serão", "seria",
    "está", "estão", "estava", "estar", "esteve", "tem", "têm", "tinha",
    "ter", "teve", "tido", "terá", "há", "havia", "vai", "vão", "ir",
    "pode", "podem", "poderá", "poderão", "deve", "devem", "deverá",
    "faz", "fazer", "fez", "feito",
    #vocabulario de manchete: verbo de atribuicao e chamada editorial. Em
    #noticia aparecem em quase todo post ("diz agência", "veja", "entenda") e
    #nao dizem do que o post trata
    "diz", "dizem", "disse", "afirma", "afirmou", "segundo",
    "veja", "entenda", "saiba", "conheça", "relembre",
    #sobra de moeda: "US$ 1,2" vira os tokens us, 1, 2
    "us",
}

#VOCABULARIO COM CARGA
#As listas antigas eram de resenha ("adorei", "odiei") e nao cobriam noticia:
#nenhuma palavra delas aparecia nos 100 posts reais. As novas entradas vem do
#vocabulario de noticia de tecnologia e so incluem palavras cuja carga nao
#depende do contexto. Ficaram de fora de proposito, por serem ambiguas:
#"segurança" (aparece em "falha de segurança"), "proteção", "alta" (de preço
#ou hospitalar), "corte" (tribunal), "crítica" ("infraestrutura crítica"),
#"alerta", "ganha" ("Instagram ganha nova identidade").
#As flexoes vao escritas por extenso: o analisador nao faz radicalizacao, e
#um stemmer ingenuo em portugues junta palavras de sentido oposto.
POSITIVAS = {
    "bom", "boa", "bons", "boas", "ótimo", "ótima", "ótimos", "ótimas",
    "excelente", "excelentes", "maravilhoso", "maravilhosa", "incrível", "incríveis",
    "adorei", "amei", "gostei", "melhor", "melhores", "melhora", "melhorou",
    "melhoria", "melhorias", "sucesso", "sucessos", "recorde", "recordes",
    "conquista", "conquistas", "conquistou", "vitória", "vitórias", "venceu",
    "avanço", "avanços", "avança", "crescimento", "cresce", "crescem", "cresceu",
    "lucro", "lucros", "lucrativo", "lucrativa", "ganho", "ganhos",
    "eficiente", "eficientes", "inovação", "inovador", "inovadora", "inédito",
    "inédita", "benefício", "benefícios", "valorizado", "valorizada",
    "valorizados", "valorizadas", "favorável", "positivo", "positiva",
    "celebra", "comemora", "unicórnio",
}
NEGATIVAS = {
    "ruim", "ruins", "péssimo", "péssima", "horrível", "horríveis", "terrível",
    "terríveis", "odiei", "detestei", "lixo",
    "golpe", "golpes", "golpista", "golpistas", "fraude", "fraudes",
    "crime", "crimes", "criminoso", "criminosa", "criminosos", "criminosas",
    "vazamento", "vazamentos", "vazou", "falha", "falhas", "falhou",
    "ataque", "ataques", "ataca", "atacam", "invasão", "invadir", "invadiu",
    "invadirem", "invadindo", "ameaça", "ameaças", "risco", "riscos",
    "prejuízo", "prejuízos", "prejudica", "prejudicar", "perda", "perdas",
    "perder", "perdeu", "morte", "mortes", "morreu", "morrido", "mata", "matar",
    "suicídio", "violência", "abuso", "ódio", "extremista", "extremistas",
    "explosivos", "desinformação", "falso", "falsa", "falsos", "falsas", "fake",
    "punição", "suspensão", "crise", "vítima", "vítimas", "dano", "danos",
    "vício", "dependência", "injusto", "injusta", "injustas", "demissões",
}
NEGACOES = {"não", "nao", "nunca", "nem", "jamais"}

#palavra = letras/digitos, com hifen INTERNO opcional. O hifen fica porque
#"cães-robôs" e "avião-arraia" sao um assunto so; partir em dois viraria
#duas keywords que isoladas nao querem dizer nada
_PADRAO_PALAVRA = re.compile(r"\w+(?:-\w+)*")


def _sem_acento(palavra):
    """Remove acentos para a comparacao com as listas.

    Texto de rede social perde acento o tempo todo, e "pessimo" tem a mesma
    carga que "péssimo". Antes isso era resolvido a mao, com "horrivel" e
    "horrível" os dois na lista; dobrar toda entrada nao escala. So a
    COMPARACAO usa esta forma: tokens e keywords seguem com acento, que e o
    que a tela mostra.

    Args:
        palavra (str): palavra ja em minusculas

    Returns:
        str: a mesma palavra sem diacriticos
    """
    decomposto = unicodedata.normalize("NFD", palavra)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


#as listas sao comparadas sem acento; calculado uma vez, na carga do modulo
_STOPWORDS = {_sem_acento(p) for p in STOPWORDS}
_POSITIVAS = {_sem_acento(p) for p in POSITIVAS}
_NEGATIVAS = {_sem_acento(p) for p in NEGATIVAS}
_NEGACOES = {_sem_acento(p) for p in NEGACOES}

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


def tokenizar(texto):
    """Quebra o texto em palavras, sem pontuacao grudada.

    Substitui o .split(), que so corta em espaco: com ele "ótimo," e "ótimo."
    nunca batiam com "ótimo" na lista, e "discord:" virava keyword diferente de
    "discord". Era a maior causa dos 100 de 100 posts reais saindo NEU.

    Args:
        texto (str): texto bruto, pode ter HTML

    Returns:
        list[str]: palavras em minusculas, com acento, na ordem do texto
    """
    return _PADRAO_PALAVRA.findall(limpar_texto(texto))




def extrair_palavras_chave(texto):
    """Extrai as palavras-chave mais frequentes de um texto.

    Args:
        texto (str): Texto a ser analisado.

    Returns:
        list[str]: Lista com até cinco palavras mais frequentes, excluindo stopwords.
    """
    palavras_filtradas = []
    for palavra in tokenizar(texto):
        if _sem_acento(palavra) in _STOPWORDS:
            continue
        #numero puro e letra solta nao sao assunto: "R$ 1,2 bilhão" deixaria
        #r, 1 e 2 disputando as cinco vagas com "bilhão"
        if palavra.isdigit() or len(palavra) < 2:
            continue
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
    
    #compara sem acento: "pessimo" e "péssimo" tem a mesma carga
    palavras = [_sem_acento(p) for p in tokenizar(texto)]
    
    positivas = 0
    negativas = 0
    negar = False
    
    #flag que verifica se a frase é positiva negativa. Ex: Não é bom 
    for palavra in palavras:
        if palavra in _NEGACOES:
            negar = True
            continue
    
        if palavra in _POSITIVAS:
            if negar:
                negativas += 1
            else:
                positivas += 1
            negar = False
            
        if palavra in _NEGATIVAS:
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