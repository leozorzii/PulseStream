from celery import shared_task

from apps.analytics.sentiment import classificar_sentimento, extrair_palavras_chave
from apps.stream_core.selectors import get_unprocessed_posts
from apps.stream_core.services import save_sentiment_analysis


@shared_task #transforma funcao comum em uma task celery
def somar(a,b):
    """Task boba de teste: soma dois numeros em background"""
    return a + b


@shared_task
def processar_sentimentos():
    """Classifica em background todos os posts que ainda nao foram processados.

    Task fina: nao implementa regra nenhuma, so amarra as pecas que ja existem
    (selector -> analytics -> service). A analise de sentimento vive em
    apps.analytics e a persistencia em stream_core; duplicar qualquer uma das
    duas aqui criaria uma segunda fonte de verdade para manter em sincronia.

    Nao recebe argumentos de proposito. Uma task agendada nao sabe, no momento
    em que e escrita, quais posts vao estar pendentes quando ela rodar: ela
    consulta o estado atual do banco na hora da execucao. Passar uma lista de
    ids na chamada tornaria a task fragil, porque os ids poderiam ter sido
    processados (ou deletados) entre o agendamento e a execucao.

    Returns:
        int: quantidade de posts processados nesta execucao, util para log
            e para monitorar se a fila esta drenando
    """
    #snapshot dos pendentes no momento da execucao. o selector ja filtra por
    #is_processed=False, entao a task nao precisa saber como "pendente" e definido
    posts_pendentes = get_unprocessed_posts()

    processados = 0
    for post in posts_pendentes:
        #a funcao ja devolve o label no codigo canonico do banco ("POS"/"NEU"/"NEG"),
        #entao nao ha traducao no meio do caminho para divergir das choices do model
        label, polarity_score = classificar_sentimento(post.text_content)
        keywords = extrair_palavras_chave(post.text_content)

        #o service grava a analise e marca o post como processado numa transacao
        #atomica. e ele quem garante que um post nunca fique marcado como
        #processado sem ter a analise correspondente salva
        save_sentiment_analysis(post, polarity_score, label, keywords)
        processados += 1

    return processados
