from apps.analytics.sentiment import limpar_texto

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