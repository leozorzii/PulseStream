# Guia de Sobrevivência — PulseStream

Teu manual pessoal pra resolver as coisas sem depender de ninguém. Baseado em tudo que a gente construiu.

---

## 🚦 Antes de começar a codar (SEMPRE)

```bash
# 1. Entra na pasta do projeto (comandos só funcionam AQUI dentro)
cd C:\Users\leomz\OneDrive\Documentos\python\PulseStream

# 2. Ativa o venv (o prompt deve mostrar "(venv)")
venv\Scripts\activate

# 3. Confere que tá tudo verde antes de mexer
python -m pytest
```

> ⚠️ **Regra de ouro:** `pytest`, `runserver` e `manage.py` só funcionam **de dentro da pasta do projeto**. Se rodar de fora, dá erro de `No module named 'apps'` ou varre projeto errado. Sempre confere o `cd` primeiro.

---

## 🔄 O Ciclo TDD (como a gente trabalha)

Toda função nova segue **Red → Green → Refactor**:

1. **🔴 Red** — escreve o teste PRIMEIRO. Ele falha (a função não existe ainda). Isso é bom.
2. **🟢 Green** — escreve o MÍNIMO de código pra passar. Nada de perfeição.
3. **🔵 Refactor** — melhora o código com os testes te protegendo.

**Função vazia pra começar** (pra não dar `IndentationError`):
```python
def minha_funcao():
    pass   # placeholder: existe mas não faz nada
```

**Anatomia de um teste (AAA):**
```python
def test_algo():
    entrada = "..."              # Arrange (prepara)
    resultado = funcao(entrada)  # Act (executa)
    assert resultado == "..."    # Assert (verifica)
```

> 💡 **Teste sem contraste não testa nada.** Pra provar que algo filtra, cria dado que DEVE aparecer E dado que NÃO deve. Se só tiver o que aparece, um bug que "traz tudo" passaria despercebido.

---

## 🐘 Comandos Django essenciais

```bash
python manage.py check              # check-up: settings/models estão ok?
python manage.py migrate            # aplica migrations (cria tabelas no banco real)
python manage.py makemigrations     # gera migrations quando muda um model
python manage.py migrate --check    # tem migration pendente? (silêncio = tudo aplicado)
python manage.py runserver          # sobe o servidor local (http://127.0.0.1:8000/)
python manage.py shell              # Python interativo COM o Django carregado
```

> ⚠️ **`runserver` trava o terminal** — é normal, é o servidor ligado. Pra rodar outra coisa, abre OUTRO terminal. Pra desligar: `Ctrl+C`.

**Criar dados de teste no shell:**
```python
python manage.py shell
>>> from apps.stream_core.services import create_content_source
>>> create_content_source(name="Canal", plataform="YOUTUBE", external_id="UC_x")
>>> exit()
```

---

## 🧪 Comandos pytest

```bash
python -m pytest                                    # roda tudo
python -m pytest -v                                 # verbose (lista cada teste)
python -m pytest caminho/test_x.py                  # só um arquivo
python -m pytest caminho/test_x.py::test_nome       # só um teste
python -m pytest -s                                 # mostra os print() (debug)
```

**Placar que aparece:**
- `passed` = 🟢 passou
- `failed` = 🔴 falhou (assert deu errado)
- `xfailed` = falhou como ESPERADO (limitação documentada com `@pytest.mark.xfail`) — não é problema
- `error` = quebrou antes de rodar (import errado, etc.)

**Marcadores úteis:**
```python
@pytest.mark.django_db      # OBRIGATÓRIO em teste que toca o banco
@pytest.mark.xfail(reason="motivo")   # marca limitação conhecida
```

---

## 🗂️ Padrão Service / Selector (o coração do projeto)

| | Faz o quê | Onde mora | Exemplos |
|---|---|---|---|
| **Service** | ESCREVE + regras de negócio | `services.py` | `create_`, `bulk_create_`, `save_` |
| **Selector** | LÊ (só consulta, não muda nada) | `selectors.py` | `get_active_`, `get_unprocessed_` |

> 💡 A **View/API fica BURRA**: ela só chama o service/selector e devolve. A lógica mora nos services/selectors, nunca na view.

**Onde vai o teste?** Espelha o código: service → `test_services.py`, selector → `test_selectors.py`.

---

## 🔌 Anatomia de um endpoint (API / Fase 4)

Fluxo: **URL → View → Selector → Serializer → JSON**

São 4 peças:

1. **Serializer** (`apps/api/serializers.py`) — traduz objeto Python ↔ JSON
```python
class XSerializer(serializers.ModelSerializer):
    class Meta:
        model = X
        fields = ["id", "campo1", "campo2"]   # escolhe o que expor (segurança!)
```

2. **View** (`apps/api/views.py`) — atende a requisição
```python
class XListView(APIView):
    def get(self, request):
        dados = meu_selector()
        serializer = XSerializer(dados, many=True)   # many=True se for lista
        return Response(serializer.data)
```

3. **URL do app** (`apps/api/urls.py`)
```python
urlpatterns = [
    path("rota/", XListView.as_view(), name="nome"),   # .as_view() é obrigatório!
]
```

4. **URL do projeto** (`config/urls.py`) — liga o prefixo `/api/`
```python
path("api/", include("apps.api.urls")),   # precisa importar 'include'
```

> URL final = prefixo do config (`api/`) + rota do app (`rota/`) = `/api/rota/`

---

## 🌿 Fluxo Git (Conventional Commits)

```bash
git status                    # SEMPRE antes de commitar: vê o que vai entrar
git add arquivo1 arquivo2     # adiciona específico (melhor que "git add .")
git commit -m "tipo(escopo): descrição em inglês no imperativo"
git push                      # envia pro GitHub
```

**Tipos de commit:**
| Tipo | Quando usar |
|---|---|
| `feat` | funcionalidade nova |
| `fix` | corrige bug |
| `test` | adiciona/muda testes |
| `refactor` | reorganiza sem mudar comportamento |
| `chore` | manutenção (deps, config) |
| `docs` | documentação |

**Nova fase = nova branch:**
```bash
git checkout main && git pull        # atualiza a main
git checkout -b feat/nome-da-fase    # cria e entra na branch
# ... trabalha, commita ...
# abre PR no GitHub e mergeia
```

**Higiene pós-merge:**
```bash
git checkout main && git pull
git branch -d feat/nome     # (-D maiúsculo se reclamar de "not fully merged")
```

> ⚠️ Antes de `git add .`, confere no `git status` que **`db.sqlite3` NÃO** vai junto (banco local fica de fora, o `.gitignore` cobre).

---

## 🩹 Erros comuns e como resolver (teu histórico real)

| Erro | O que significa | Conserto |
|---|---|---|
| `No module named 'apps'` | rodou de fora da pasta, ou `pythonpath` não configurado | `cd` pra dentro do PulseStream |
| `No module named 'pytest'` / `'django'` | pacote não instalado no venv | `pip install X` + `pip freeze > requirements.txt` |
| `IndentationError: expected an indented block` | função com `def` mas corpo vazio | põe `pass` dentro |
| `ImportError: cannot import name 'X'` | achou o arquivo mas não a função (typo ou não existe) | confere o nome / cria a função |
| `ModuleNotFoundError: No module named 'X'` | typo no import ou pacote não existe | lê o nome com atenção (typo!) |
| `AttributeError: 'NoneType' has no attribute` | função retornou `None` (faltou `return`) | adiciona o `return` |
| `IntegrityError: UNIQUE constraint failed` | tentou criar duplicata (`unique=True`) | usa external_id diferente / valida antes |
| `RuntimeError: doesn't declare an explicit app_label` | app não está no `INSTALLED_APPS` (ou nome errado) | registra `apps.nome_do_app` no settings |
| `TypeError: unsupported operand for /` | dividindo por tipo errado (ex: QuerySet) | usa `.count()` pra pegar o número |
| `Page not found (404)` na API | rota não registrada | adiciona `include` no `config/urls.py` |
| `ALLOWED_HOSTS if DEBUG is False` | modo produção sem hosts | `DEBUG = True` (desenvolvimento) |
| venv não ativa | terminal errado ou pasta errada | Git Bash: `source venv/Scripts/activate` |

> 💡 **Como ler um erro:** olha a **ÚLTIMA linha** primeiro (o tipo do erro e a mensagem). Depois sobe pra ver ONDE aconteceu. O Python é literal — se o nome tá errado, ele procura o errado. Erro que MUDA ao rodar sozinho vs junto = contaminação entre testes (ou estado sujo, roda de novo limpo).

---

## 🧠 Princípios que a gente firmou

- **Um passo de cada vez.** Não morde dois problemas difíceis juntos.
- **Investiga antes de escrever.** Lê o model antes de usar os campos.
- **Valide o input na fronteira.** GET de leitura não precisa validar; POST que recebe dados, sim. Service valida regra de negócio.
- **Defesa em camadas.** Service checa antes (erro limpo) + banco garante (`unique`, `OneToOne`). Cinto e suspensório.
- **Nem todo problema tem que ser resolvido — alguns têm que ser reconhecidos e documentados** (ex: sarcasmo com `xfail`).
- **Vazio ≠ erro.** Fonte sem dados retorna `{}`/`[]`, não explode.
- **Transação atômica** (`with transaction.atomic():`) pra operações que precisam acontecer juntas (tudo ou nada).
- **Confia no verde, não no "acho que arrumei".** Roda o teste.
- **Docstring descreve o que AQUELA coisa faz** (classe não tem `Args`; função tem).

---

## 📍 Onde parei

**Feito:** Analytics completo (3 funções) · Stream Core / Fase 1 completa (3 services + 3 selectors) · API primeiro endpoint (`GET /api/sources/`) · settings reconstruído · 20 testes + 1 xfailed

**Próximo:** mais endpoints da Fase 4 — `posts/unprocessed/`, `analytics/summary/` (leitura, iguais ao que já fiz) e `ingestion/trigger/` (POST, recebe dados → valida)

**Dívida técnica anotada:** configurar `DEBUG` via variável de ambiente ANTES de ir pro servidor Ubuntu

**Depois:** Fase 2 (Ingestion + Celery) · Fase 5 (MCP) · Fase 6 (Docker + deploy no servidor Ubuntu)

---

*Feito pra eu resolver sozinho. Quando travar: lê o erro (última linha primeiro), confere a pasta, confere o venv, roda o teste.* 🚀