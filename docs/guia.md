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

## 🐳 Docker — o jeito principal de rodar tudo hoje

Um comando sobe o sistema inteiro. Não precisa de venv ativo nem de Redis instalado na máquina.

```bash
docker compose up              # sobe tudo, logs na tela (Ctrl+C derruba)
docker compose up -d           # sobe em background (detached)
docker compose logs -f         # acompanha os logs quando subiu com -d
docker compose logs -f worker  # só de um serviço
docker compose down            # derruba tudo
```

**Os quatro serviços que sobem juntos:**

| Serviço | O que é | Detalhe |
|---|---|---|
| `redis` | broker do Celery | imagem `redis:7`, porta 6379 |
| `web` | Django (`runserver`) | http://localhost:8000 |
| `worker` | Celery worker | executa as tasks (`--pool=solo`, exigência do Windows) |
| `beat` | Celery beat | dispara `processar_sentimentos` a cada 5 min |

### Quando rebuildar

```bash
docker compose up --build
```

O `docker-compose.yml` monta o código como volume (`.:/app`), então **mudança em `.py` NÃO precisa de rebuild** — o runserver recarrega sozinho. Rebuilda só quando mudar:

- `requirements.txt` (dependência nova)
- `Dockerfile`
- versão do Python

### Rodar comando avulso dentro do container

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python -m pytest
docker compose exec web bash            # shell dentro do container

# com tudo derrubado (cria container temporário e some depois)
docker compose run --rm web python manage.py migrate
```

> `exec` = entra num container **que já está rodando**. `run` = cria um novo. Se der "service not running", usa `run --rm`.

---

## 🖐️ Rodando sem Docker (o jeito manual)

Serve pra debugar quando o Docker atrapalha, ou pra rodar teste rápido. Precisa de **4 terminais**, todos com o venv ativo e dentro da pasta do projeto.

```bash
# terminal 1 — Redis (precisa estar instalado, ou sobe só ele via docker)
redis-server
# alternativa: docker compose up redis

# terminal 2 — Django
venv\Scripts\activate
python manage.py runserver

# terminal 3 — Celery worker
venv\Scripts\activate
celery -A config worker --loglevel=info --pool=solo

# terminal 4 — Celery beat
venv\Scripts\activate
celery -A config beat --loglevel=info
```

> ⚠️ **`--pool=solo` é obrigatório no Windows.** Sem ele o worker aceita a task e morre com erro de permissão/fork — o Celery usa `prefork` por padrão, que depende de `fork()`, coisa que o Windows não tem.

---

## 🔌 Servidor MCP

O servidor vive em `mcp_server/server.py` (na **raiz**, não dentro de `apps/`) e expõe os dados do PulseStream pra uma IA consultar em linguagem natural.

### As duas tools

| Tool | O que faz |
|---|---|
| `listar_fontes()` | lista as fontes ativas (id, nome, plataforma) |
| `resumo_sentimento_fonte(source_id)` | percentual de POS/NEU/NEG daquela fonte |

O fluxo esperado da IA é: chama `listar_fontes` pra descobrir os ids, depois `resumo_sentimento_fonte` com o id escolhido.

### Testar com o Inspector

```bash
# da raiz do projeto, com o venv ativo
npx @modelcontextprotocol/inspector python mcp_server/server.py
```

Abre uma UI no navegador onde dá pra listar as tools e executar cada uma com parâmetros, sem precisar de IA nenhuma.

### Dois detalhes que fazem o servidor funcionar

**`django.setup()` antes de tudo.** O script não é iniciado pelo `manage.py`, então o Django não está de pé sozinho. O `server.py` faz o `sys.path.insert`, aponta o `DJANGO_SETTINGS_MODULE` e chama `django.setup()` — e só **depois** importa os selectors. Importar model antes disso dá `AppRegistryNotReady`.

**`sync_to_async` nas tools.** As tools do MCP são `async`, mas o ORM do Django é síncrono. Chamar o ORM direto de contexto async dá `SynchronousOnlyOperation` ("You cannot call this from an async context"). Por isso:

```python
fontes = await sync_to_async(list)(get_active_sources())
```

O `list` é importante: sem ele, o QuerySet é preguiçoso e só bateria no banco depois, de volta no contexto async — o erro voltaria.

### Onde o MCP funciona hoje

| Cenário | Status |
|---|---|
| Inspector local | ✅ funciona |
| Claude Desktop (chat local) | ✅ dá pra conectar via `claude_desktop_config.json` |
| Remoto / HTTP (Cowork, web) | ⬜ passo futuro — exige expor via HTTP, não stdio |

---

## 🧪 Testes e CI

```bash
python -m pytest          # roda tudo
python -m pytest -v       # mostra nome de cada teste
```

**A suíte é offline.** Todo Celery é mockado (`.delay()` com `patch`), o `feedparser` é mockado, e nada toca internet nem broker. Ou seja: **não precisa de Redis rodando pra testar**. Se um teste passar a exigir Redis, ele quebra no CI — e isso é proposital, é o sinal de que alguém acoplou o teste em infra externa.

### O CI (GitHub Actions)

Roda em **todo Pull Request** e em push na `main`. Está em `.github/workflows/tests.yml`.

Três passos: instala as dependências → `makemigrations --check` → `pytest -v`.

- O `makemigrations --check` pega model alterado sem migration gerada. Sem ele, o erro só apareceria no deploy.
- **O `SECRET_KEY` é injetado como valor dummy no workflow.** O Django não boota sem ele, e o CI é efêmero e não assina nada real — então não precisa ser segredo de verdade.
- Não há serviço de Redis no CI, de propósito (ver o parágrafo acima).

---

## ⚙️ Configuração e `.env` (12-factor)

O `settings.py` lê a configuração do ambiente, não do código:

```python
SECRET_KEY = config("SECRET_KEY")                      # sem default: obrigatório
DEBUG = config("DEBUG", default=False, cast=bool)      # seguro por padrão
```

O arquivo `.env` fica na raiz e está no `.gitignore` **e** no `.dockerignore` — nunca vai pro repo nem pra imagem.

```bash
# .env
SECRET_KEY=cole-a-chave-aqui
DEBUG=True
```

> ⚠️ **Clone novo não roda sem `.env`.** Como o `SECRET_KEY` não tem default, sem o arquivo o Django morre com `decouple.UndefinedValueError: SECRET_KEY not found`. É o primeiro passo depois de clonar.

### Gerar um SECRET_KEY novo

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### A pegadinha do `$$` no docker-compose

O Docker Compose trata `$` como início de variável. Se o `SECRET_KEY` tiver `$` e for escrito **direto no `docker-compose.yml`**, o Compose tenta expandir e a chave chega truncada ou vazia.

- Dentro do `docker-compose.yml`: escreve `$$` pra representar um `$` literal.
- Dentro do `.env`: `$` normal, **não** duplica — o `env_file` não expande.

Como hoje o compose usa `env_file: .env`, o caminho seguro é deixar a chave no `.env` e não escrever segredo inline no YAML.

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
| Worker do Celery morre ao pegar task (Windows) | pool `prefork` precisa de `fork()`, que o Windows não tem | sobe com `--pool=solo` |
| `Error 111 connecting to localhost:6379` dentro do Docker | container não enxerga `localhost` do host | usa o nome do serviço: `redis://redis:6379/0` |
| `port is already allocated` na 6379 | sobrou container avulso de `docker run` | `docker ps` → `docker stop <id>` → sobe de novo |
| `decouple.UndefinedValueError: SECRET_KEY not found` | falta o `.env` (clone novo) | cria o `.env` com `SECRET_KEY` e `DEBUG` |
| `SynchronousOnlyOperation` no MCP | chamou o ORM direto de função `async` | envolve com `sync_to_async(list)(...)` |
| `AppRegistryNotReady` no MCP | importou model antes do `django.setup()` | move o import pra depois do `setup()` |
| `CERTIFICATE_VERIFY_FAILED` no pip / feedparser | antivírus interceptando TLS (Avast Web Shield) | ver a seção de diagnóstico abaixo |

> 💡 **Como ler um erro:** olha a **ÚLTIMA linha** primeiro (o tipo do erro e a mensagem). Depois sobe pra ver ONDE aconteceu. O Python é literal — se o nome tá errado, ele procura o errado. Erro que MUDA ao rodar sozinho vs junto = contaminação entre testes (ou estado sujo, roda de novo limpo).

---

### 🔍 Diagnosticar antivírus quebrando pip / feeds

Sintoma: `pip install` falha com erro de certificado, ou o `feedparser` volta `entries: 0` mesmo com internet funcionando. O `curl` funciona, o Python não — porque o `curl` usa o repositório de certificados do Windows e o Python usa o próprio.

**Descobre quem está emitindo o certificado:**

```bash
echo | openssl s_client -connect pypi.org:443 -servername pypi.org 2>/dev/null | grep issuer=
```

- Se aparecer uma CA real (Sectigo, DigiCert, Let's Encrypt) → o problema é outro.
- Se aparecer algo como `Avast Web/Mail Shield Root` → é o antivírus fazendo MITM.

**Conserto:** Avast → Menu → Configurações → Proteção → Proteções Principais → Agente Web → desmarcar **"Ativar verificação de HTTPS"**.

> Trocar de rede **não** resolve: a interceptação é local, na máquina. Já perdi tempo achando que era a rede corporativa.

**Escape de emergência** (só pro pip, sem verificação de certificado):
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org <pacote>
```

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

**Feito:**
- **Fase 1 — stream_core:** services + selectors, com `save_sentiment_analysis` atômico
- **Fase 2 — ingestion:** `RSSAdapter` (fetch/parse com `FeedFetchError`), `run_ingestion`, endpoint `POST /api/ingestion/trigger/`, task Celery `processar_sentimentos`, Beat drenando a cada 5 min
- **Fase 3 — analytics:** `limpar_texto`, `extrair_palavras_chave`, `classificar_sentimento` (devolve `(label, score)` com códigos canônicos `POS`/`NEU`/`NEG`)
- **Fase 4 — API:** 4 endpoints (sources, posts/unprocessed, analytics/summary, ingestion/trigger)
- **Fase 5 — MCP:** servidor com 2 tools
- **Fase 6 (parcial):** Docker + Compose, CI de testes em todo PR

**Suíte:** 43 passed, 1 xfailed (o xfail é o sarcasmo, limitação conhecida e documentada)

**Próximo:**
- Fase 3 tem dois buracos: `topic_model.py` e `metrics.py` estão vazios
- Issue #15 — expandir listas de palavras e stopwords (melhorar precisão)
- Issue #16 — spike: análise de sentimento com LLM
- Fase 6 — CD (deploy automatizado); o CI já roda

**Dívida técnica anotada:**
- MCP só funciona local (stdio). Remoto/HTTP é passo futuro.
- Banco ainda é SQLite; o README fala em PostgreSQL como alvo.
- `apps/analytics/exceptions.py` e `apps/ingestion/adapters/social_adapter.py` estão vazios.

---

*Feito pra eu resolver sozinho. Quando travar: lê o erro (última linha primeiro), confere a pasta, confere o venv, roda o teste.* 🚀
