from apps.analytics.sentiment import limpar_texto
from apps.analytics.sentiment import extrair_palavras_chave
from apps.analytics.sentiment import classificar_sentimento
from apps.analytics.sentiment import tokenizar
from apps.stream_core.models import SentimentAnalysis

import pytest


# --------------- LIMPAR TEXTO -----------------------

def test_remove_tag_preservando_maior_menor():
    entrada = '<p>lucro do 3º tri > expectativa dos analistas</p>' #Arrange
    response = limpar_texto(entrada)#Act
    assert response == "lucro do 3º tri > expectativa dos analistas" #Assert
    
def test_deixa_minusculo_com_cedilha_e_acento():
    entrada = "AÇAÍ É ÓTIMO"
    response = limpar_texto(entrada)
    assert response == "açaí é ótimo"
    
def test_remove_tag_com_atributos():
    entrada = '<a href="https://site.com">clica aqui</a>'
    response = limpar_texto(entrada)
    assert response == "clica aqui"    
    
def test_remove_duas_tags_na_mesma_linha():
    entrada = "<b>preço</b> subiu"
    response = limpar_texto(entrada)
    assert response == "preço subiu"
    
#------------ EXTRAIR PALAVRA FREQUENTE -------------------------------  
 
def test_extrai_palavra_frequente():
    #chamava text_extrai_... e o pytest so coleta test_*: o teste existia e nunca rodou
    entrada = "ABACATE abacate Abacate melhor video"
    response = extrair_palavras_chave(entrada)
    assert "abacate" in response
    
def test_sem_stopwords():
    entrada = "o gato subiu no telhado e dormiu"
    response = extrair_palavras_chave(entrada)
    assert "o" not in response
    assert "e" not in response
    
    
def test_delimita_quantidade_palavras():
    entrada = "o gato subiu no telhado e dormiu"
    response = extrair_palavras_chave(entrada)
    assert len(response) <= 5 #no maximo 5 itens da lista
    
    
#------------------CLASSIFICAR SENTIMENTO -------------------------

#a funcao agora devolve uma tupla (label, polarity_score):
#  - label: codigo canonico do banco ("POS"/"NEU"/"NEG")
#  - polarity_score: normalizado entre -1.0 e +1.0

def test_texto_positivo():
    entrada = "esse filme é ótimo, adorei"
    label, score = classificar_sentimento(entrada)
    assert label == "POS"
    assert score == 1.0 #duas positivas, nenhuma negativa: (2-0)/2

def test_texto_negativo():
    entrada = "esse filme é horrivel, odiei"
    label, score = classificar_sentimento(entrada)
    assert label == "NEG"
    assert score == -1.0 #duas negativas, nenhuma positiva: (0-2)/2

def test_texto_neutro_com_empate():
    entrada = "o filme é bom mas o final é ruim"
    label, score = classificar_sentimento(entrada)
    assert label == "NEU"
    assert score == 0.0 #empate 1x1: (1-1)/2

def test_negacao_inverte_positivo():
    entrada = "esse filme nao é bom"
    label, score = classificar_sentimento(entrada)
    assert label == "NEG"
    assert score == -1.0

def test_negacao_com_acento():
    entrada = "esse filme não é bom"
    label, score = classificar_sentimento(entrada)
    assert label == "NEG"
    assert score == -1.0

def test_negacao_dupla_resulta_neutro():
    entrada = "esse filme não é bom nem ruim"
    label, score = classificar_sentimento(entrada)
    assert label == "NEU"
    assert score == 0.0


def test_texto_sem_palavras_de_sentimento_nao_estoura():
    """Texto sem nenhuma palavra com carga emocional cai na guarda de
    divisao por zero: sem denominador para normalizar, o score e 0.0."""
    entrada = "o gato subiu no telhado"
    label, score = classificar_sentimento(entrada)
    assert label == "NEU"
    assert score == 0.0 #se a guarda sumir, isso vira ZeroDivisionError


def test_score_fica_sempre_dentro_do_intervalo():
    """A normalizacao tem que manter o score no intervalo contratado."""
    for entrada in [
        "ótimo adorei amei excelente",
        "ruim péssimo odiei horrível",
        "o filme é bom mas o final é ruim",
        "texto sem carga nenhuma",
    ]:
        _, score = classificar_sentimento(entrada)
        assert -1.0 <= score <= 1.0


def test_label_pertence_as_choices_do_model():
    """Teste guardiao: o label tem que ser aceito por SentimentAnalysis.label.

    A funcao emite o codigo canonico justamente para ir direto ao banco.
    Se alguem trocar "POS" por "positivo" no futuro, o save quebraria so em
    runtime (ou truncaria, pois max_length=3); este teste falha antes disso.
    """
    validos = [codigo for codigo, _rotulo in SentimentAnalysis.SENTIMENTOS]

    for entrada in [
        "esse filme é ótimo, adorei",
        "esse filme é horrivel, odiei",
        "o gato subiu no telhado",
    ]:
        label, _ = classificar_sentimento(entrada)
        assert label in validos


@pytest.mark.xfail(reason="Sarcasmo não é detectável por análise baseada em listas de palavras")
def test_sarcasmo_e_limitacao_conhecida():
    entrada = "ótimo, adorei esperar três horas na fila"
    label, _ = classificar_sentimento(entrada)
    #um humano le isso como negativo (sarcasmo); o algoritmo le como positivo.
    #desempacotamos a tupla para que o xfail seja pelo SARCASMO e nao por
    #incompatibilidade de formato, que mascararia a limitacao real
    assert label == "NEG"


#------------------TOKENIZACAO (#15) -------------------------
#
#O analisador quebrava o texto com .split(), que corta so em espaco. A
#pontuacao ficava grudada na palavra: "ótimo," e "ótimo." nunca batiam com
#"ótimo" na lista, e "discord:" virava uma keyword diferente de "discord".
#Medido nos 100 posts reais do G1 Tecnologia: 100 de 100 saiam NEU, com
#score 0.0 em todos.

def test_tokenizar_separa_pontuacao_da_palavra():
    assert tokenizar("Discord: ótimo, péssimo.") == ["discord", "ótimo", "péssimo"]

def test_tokenizar_preserva_palavra_composta_com_hifen():
    #"cães-robôs" e um assunto so; separar viraria duas keywords sem sentido
    assert "cães-robôs" in tokenizar("os cães-robôs da China")

def test_palavra_com_pontuacao_ainda_carrega_sentimento():
    label, score = classificar_sentimento("O produto é ótimo.")
    assert label == "POS"
    assert score == 1.0

def test_negacao_funciona_com_pontuacao():
    label, _ = classificar_sentimento("Não é bom.")
    assert label == "NEG"

def test_palavra_sem_acento_ainda_carrega_sentimento():
    #texto de rede social perde acento o tempo todo; "pessimo" e "péssimo"
    #precisam valer o mesmo. Antes so "horrivel" tinha a versao sem acento,
    #escrita a mao na lista
    label, _ = classificar_sentimento("atendimento pessimo")
    assert label == "NEG"


#------------------KEYWORDS SEM RUIDO (#15) -------------------------

def test_keywords_nao_trazem_pontuacao():
    assert extrair_palavras_chave("Discord: Discord, discord.") == ["discord"]

def test_keywords_ignoram_palavras_funcionais_do_portugues():
    #as seis mais frequentes nos posts reais antes do #15 eram em, para,
    #como, com, por, diz — nenhuma diz do que o post trata
    entrada = "em para como com por diz pelo sobre mais pode será uma os as foguete"
    assert extrair_palavras_chave(entrada) == ["foguete"]

def test_keywords_ignoram_numeros_e_letras_soltas():
    #"R$ 1,2 bilhão" vira os tokens r, 1, 2, bilhão; so o ultimo e assunto
    assert extrair_palavras_chave("R$ 1,2 bilhão em 2025") == ["bilhão"]


#------------------VOCABULARIO DE NOTICIA (#15) -------------------------
#
#Trechos reais do feed G1 Tecnologia (o id do post no comentario). O rotulo
#esperado foi dado por leitura humana ANTES de rodar o analisador novo. Sao
#casos claros de proposito: um lexico de palavras nao lida com nuance, e o
#teste existe para travar a cobertura de vocabulario, nao para prometer
#leitura de contexto — isso e o #16.

@pytest.mark.parametrize("texto, esperado", [
    #287
    ("Vítima sofre prejuízo de R$ 600 mil após cair em golpe da falsa central bancária.", "NEG"),
    #216
    ("Vazamento de dados na Latam: falha permitiu acesso a dados pessoais e parte dos dados de cartões.", "NEG"),
    #219
    ("Hackers suspeitos de ligação com o Irã atacam sistemas de água. Agências alertam para uma ameaça ativa.", "NEG"),
    #208
    ("Robô chinês bate o recorde mundial de Usain Bolt nos 100 metros em teste.", "POS"),
    #230
    ("Empregos em tecnologia crescem mais fora do Sul e Sudeste; salários chegam a R$ 40,5 mil.", "POS"),
    #227
    ("Como algoritmos mudaram a maneira que interagimos.", "NEU"),
])
def test_vocabulario_de_noticia_real(texto, esperado):
    label, _ = classificar_sentimento(texto)
    assert label == esperado
