from apps.analytics.sentiment import limpar_texto
from apps.analytics.sentiment import extrair_palavras_chave

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
    
    
def text_extrai_palavra_frequente():
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
    
