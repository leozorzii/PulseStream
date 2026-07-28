Estrutura de Pastas
pulsestream/
├── .github/
│   └── workflows/
│       └── ci.yml                 # Automação de testes e linter a cada commit
├── apps/
│   ├── analytics/                 # Módulo de Data Science puro (NLP, Machine Learning)
│   │   ├── __init__.py
│   │   ├── exceptions.py          # Exceções customizadas da camada analítica
│   │   ├── metrics.py             # Estatísticas de engajamento e distribuições
│   │   ├── sentiment.py           # Pipeline de NLP e análise de sentimento
│   │   └── topic_model.py         # Descobrimento de tópicos via Machine Learning
│   ├── api/                       # Camada de comunicação externa (Endpoints REST)
│   │   ├── __init__.py
│   │   ├── urls.py                # Mapeamento de rotas HTTP/REST
│   │   ├── views.py               # Views da API (orquestração de chamadas)
│   │   └── serializers.py         # Validação e serialização de dados (DRF)
│   ├── ingestion/                 # Pipeline de ETL e coleta de dados
│   │   ├── __init__.py
│   │   ├── adapters/              # Conectores com APIs externas ou Web Scraping
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Classe abstrata para novos leitores de dados
│   │   │   └── social_adapter.py  # Coletor específico para redes/comentários
│   │   ├── services.py            # Lógica de negócio para tratamento do dado bruto
│   │   └── tasks.py               # Tarefas agendadas para execução em segundo plano (Celery)
│   ├── mcp_server/                # Camada de integração com IA Generativa (MCP)
│   │   ├── __init__.py
│   │   ├── server.py              # Inicialização do servidor MCP
│   │   └── tools.py               # Definição das ferramentas expostas para LLMs
│   └── stream_core/               # Domínio principal e Banco de Dados (Django App)
│       ├── __init__.py
│       ├── apps.py                # Configuração da app no Django
│       ├── models.py              # Definição de entidades e esquemas da base de dados
│       ├── selectors.py           # Queries complexas no banco (Apenas Leitura)
│       └── services.py            # Mutações no banco e regras de negócio
├── config/                        # Configurações do projeto Django
│   ├── __init__.py
│   ├── asgi.py                    # Suporte a requisições assíncronas
│   ├── celery.py                  # Configuração da fila de tarefas assíncronas
│   ├── settings.py                # Variáveis de ambiente e apps registradas
│   ├── urls.py                    # Roteador principal da aplicação
│   └── wsgi.py                    # Entrada para servidores de produção
├── notebooks/                     # Espaço para prototipagem de Data Science
│   └── 01_exploratory_nlp.ipynb   # Análise exploratória de dados antes de ir pro código
├── tests/                         # Suíte de testes automatizados
│   ├── analytics/                 # Testes unitários do módulo de Data Science
│   ├── ingestion/                 # Testes dos coletores de dados
│   └── stream_core/               # Testes das regras de negócio do Django
├── .env.example                   # Exemplo de variáveis de ambiente do sistema
├── .gitignore                     # Arquivos ignorados pelo Git
├── docker-compose.yml             # Orquestração de containers (PostgreSQL, Redis, Django, Celery)
├── Dockerfile                     # Imagem Docker da aplicação Python
├── manage.py                      # Utilitário de linha de comando do Django
├── Pyproject.toml / requirements.txt # Dependências e bibliotecas do projeto
└── README.md                      # Documentação profissional do repositório
