import json
import os
import django
import sys
from pathlib import Path
from asgiref.sync import sync_to_async
#garante que a raiz do projeto esteja no sys.path
# para que o 'config' e 'apps' sejam encontrados independente de onde o script for executado
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
# aponta pro settings do Django e inicializa o app registry
# TEM que vir antes de qualquer import de models/selectors, senão dá AppRegistryNotReady
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings") #diz ao django onde estao as config
django.setup()#inicializa o Django

#agora com django de pe, importa o que toca o ORM
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent
from apps.stream_core.models import ContentSource
from apps.stream_core.selectors import get_active_sources, get_sentiment_summary_by_source


def _erro_de_tool(payload):
    """Monta uma resposta de erro de tool a partir de um dicionario.

    Devolver CallToolResult e o unico jeito de ter isError=True COM um corpo
    JSON proprio: levantar excecao tambem marca isError, mas o texto vira
    "Error executing tool ...: <msg>" e deixa de ser desserializavel. O
    lowlevel server repassa um CallToolResult inteiro sem tocar, e o
    convert_result do FastMCP tem um ramo explicito para ele.

    isError e o que importa aqui, nao a chave "erro": um campo chamado erro
    dentro de uma resposta bem-sucedida e algo que o modelo narra como dado;
    um erro de tool e sinal que ele precisa tratar.

    Args:
        payload (dict): o corpo a serializar

    Returns:
        CallToolResult: resultado marcado como erro
    """
    #ensure_ascii=False porque as mensagens sao em portugues e o cliente le UTF-8
    texto = json.dumps(payload, ensure_ascii=False, indent=2)
    return CallToolResult(content=[TextContent(type="text", text=texto)], isError=True)


#cria a instancia do servidor MCP
mcp = FastMCP("pulsestream")#nome que aparece pras IAs ao identificar meu server mcp


@mcp.tool()#decorador que diz que essa funcao é uma tool
async def listar_fontes() -> list[dict]:
    """Lista as fontes de conteúdo ativas monitoradas pelo PulseStream.

    Use esta ferramenta para descobrir quais fontes de notícias/conteúdo
    estão disponíveis antes de consultar o sentimento de uma delas.

    Returns:
        Lista de fontes, cada uma com seu id, nome e plataforma.
    """
    # o ORM do Django é síncrono; sync_to_async faz a ponte para o
    # contexto async do MCP, evitando "You cannot call this from an async context"
    fontes = await sync_to_async(list)(get_active_sources())
    return [
        {
        "id": fonte.id,
        "nome": fonte.name,
        "plataforma": fonte.get_plataform_display(),
        }
        for fonte in fontes
    ]

@mcp.tool()
async def resumo_sentimento_fonte(source_id: int) -> dict:
    """Retorna o resumo de sentimento de uma fonte de conteúdo específica.

    Dado o id de uma fonte (obtido via listar_fontes), retorna o percentual
    de posts classificados como positivos, neutros e negativos daquela fonte.

    Args:
        source_id: id da fonte de conteúdo a consultar.

    Returns:
        Um resumo com os percentuais por sentimento (já com o nome legível),
        ou uma mensagem indicando que a fonte ainda não tem posts analisados.
        Fonte inexistente vira erro de tool, nao resposta.
    """
    #existencia e uma pergunta que o selector nao responde: ele filtra e conta,
    #e zero linhas e o que um id inexistente e uma fonte sem analises produzem
    #igualmente. Sem esta consulta a tool escolhe a leitura mais simpatica e
    #afirma que a fonte existe. Mesmo corte da view da API, que checa existencia
    #antes de chamar o selector, e mesmo texto de erro, para as duas portas do
    #dominio nao discordarem sobre o que e "fonte desconhecida".
    existe = await sync_to_async(ContentSource.objects.filter(id=source_id).exists)()
    if not existe:
        return _erro_de_tool({"source_id": source_id, "erro": "fonte nao encontrada"})

    resumo = await sync_to_async(get_sentiment_summary_by_source)(source_id)
    #selector devolve {} quando nao tem analises, o que torna ambiguo para a IA
    #entao deixo o estado explicito
    if not resumo:
        return{
            "source_id": source_id,
            "mensagem" : "Fonte ainda não possui posts analisados",
            "resumo": {},
        }
    #traduz os compactos para nomes legiveis
    legiveis = {"POS": "Positivo", "NEU": "Neutro", "NEG": "Negativo"}
    resumo_formatado = {
        legiveis.get(label, label): round(percentual,1)
        for label, percentual in resumo.items()
        }
    return{
        "source_id": source_id,
        "resumo": resumo_formatado
    }
    
    
    
if __name__ == "__main__":
    mcp.run()