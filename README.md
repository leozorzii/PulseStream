# PulseStream

> An intelligent hub for **sentiment analysis** and **trend detection** across social media and entertainment content.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-DRF-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-Redis-37814A?style=for-the-badge&logo=celery&logoColor=white)
![pytest](https://img.shields.io/badge/tested_with-pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

![Status](https://img.shields.io/badge/status-in_development-yellow?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## What is PulseStream?

The internet never stops talking. Millions of people comment on movies, games, brands and public figures every second — far more than any human could ever read.

**PulseStream is a system that listens to that conversation for you.** It continuously collects public posts and comments, cleans and analyzes the text, and answers three questions:

1. **What is being talked about?** — the trending topics right now.
2. **Is the reception positive or negative?** — the overall sentiment.
3. **Is it growing or fading?** — how engagement and sentiment change over time.

The name says it all: **Pulse** (the heartbeat of a topic) + **Stream** (the constant flow of messages).

### Who is it for?

- **Brands** measuring how a product launch is being received.
- **Media & entertainment** gauging audience reaction to a trailer or release.
- **Analysts & investors** tracking public perception of a company or asset.

---

## Architecture

PulseStream is built as a **Modular Monolith** following the **Service–Selector pattern** ([HackSoft Django Styleguide](https://github.com/HackSoftware/Django-Styleguide)), with the data-science layer fully **decoupled from Django/ORM** so it stays pure, portable and easy to test.

Think of it as a factory with an assembly line — raw comments come in one end, useful insight comes out the other:

```mermaid
flowchart LR
    subgraph External[" Public Sources"]
        X[X / Twitter]
        YT[YouTube]
        RSS[News RSS]
    end

    subgraph PulseStream[" PulseStream"]
        ING[" Ingestion<br/>(apps/ingestion)<br/>fetch &amp; parse"]
        CORE[" Domain + Persistence<br/>(apps/stream_core)<br/>services / selectors"]
        DB[("PostgreSQL")]
        ANALYTICS[" Analytics Engine<br/>(apps/analytics)<br/>pure Python, no ORM"]
        API[" REST API<br/>(apps/api)<br/>DRF endpoints"]
        MCP[" MCP Server<br/>(mcp_server)<br/>natural-language access"]
    end

    Consumer[" Dashboards /<br/>Integrations"]
    LLM[" AI Assistants<br/>(LLMs)"]

    X & YT & RSS --> ING
    ING --> CORE
    CORE <--> DB
    CORE --> ANALYTICS
    ANALYTICS --> CORE
    CORE --> API
    CORE --> MCP
    API --> Consumer
    MCP --> LLM
```

| Module             | Role                                                                         | Analogy                   |
| ------------------ | ---------------------------------------------------------------------------- | ------------------------- |
| `apps/ingestion`   | Connects to public APIs / scrapers and pulls raw posts                       | The collector at the door |
| `apps/stream_core` | Domain rules: reads (`selectors`) and writes (`services`) to the DB          | The warehouse             |
| `apps/analytics`   | Pure-Python NLP: cleaning, keywords, sentiment, metrics                      | The analyst               |
| `apps/api`         | Django REST Framework endpoints for external consumers                       | The service counter       |
| `mcp_server`       | Model Context Protocol server so LLMs can query the data in natural language | The AI translator         |

---

## Tech Stack

- **Backend:** Python 3.14, Django, Django REST Framework
- **Database:** PostgreSQL
- **Async / Scheduling:** Celery + Redis
- **NLP / Data Science:** pure Python (frequency-based), with spaCy / Hugging Face planned for advanced features
- **Testing:** pytest (Test-Driven Development)
- **Infra:** Docker + Docker Compose
- **AI Integration:** Model Context Protocol (MCP)

---

## Project Status

PulseStream is under **active development**. This section is kept honest — it reflects what actually works today, not what is planned.

**Foundation** ✅

- [x] Modular project structure
- [x] Virtual environment & dependencies
- [x] Django settings & app registration
- [x] Data models (`ContentSource`, `RawPost`, `SentimentAnalysis`)
- [x] Initial database migrations

**Phase 1 — Domain & Persistence** (`stream_core`) ✅

- [x] Selectors (`get_active_sources`, `get_unprocessed_posts`, ...)
- [x] Services (`create_content_source`, `bulk_create_raw_posts`, ...)

**Phase 2 — Ingestion / ETL** (`ingestion`) ✅

- [x] Base adapter interface (`BaseAdapter`) + RSS connector (`RSSAdapter`) · _fully tested_
- [x] Ingestion service (`run_ingestion`) + `POST /api/ingestion/trigger/` endpoint
- [x] Celery task for background sentiment processing (`processar_sentimentos`)
- [x] Dispatch the task after a successful ingestion (`.delay()` from the trigger endpoint)
- [x] Periodic draining of pending posts (Celery Beat, every 5 min)

**Phase 3 — Analytics Engine** (`analytics`) 🚧 _in progress_

- [x] `limpar_texto` — text cleaning (HTML strip + normalization) · _fully tested_
- [x] `extrair_palavras_chave` — keyword extraction (frequency + stopwords) · _fully tested_
- [x] `classificar_sentimento` — sentiment classification, returns `(label, polarity_score)` · _fully tested_
- [ ] Topic modeling
- [ ] Statistical metrics

**Phase 4 — REST API** (`api`) ⬜

- [x] Serializers, views & endpoints

**Phase 5 — MCP Server** (`mcp_server`) ⬜

- [ ] Server init + exposed analytical tools

**Phase 6 — DevOps & Quality** 🚧 _in progress_

- [x] Test suite (pytest) — analytics, `stream_core`, ingestion & API layers
- [x] Dockerization (`Dockerfile` + `docker-compose.yml`)
- [ ] CI/CD with GitHub Actions

---

## Getting Started

> ⚠️ The project is mid-development. Today you can run the **API, the RSS ingestion pipeline and the full test suite**. Background processing requires a running Redis broker; MCP server and Docker are still pending.

```bash
# 1. Clone
git clone https://github.com/<your-username>/PulseStream.git
cd PulseStream

# 2. Create & activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the tests
python -m pytest
```

---

## 🧪 Testing Philosophy

This project treats tests as first-class citizens. The analytics layer is developed with a strict **Red → Green → Refactor** cycle:

1. **Red** — write a failing test that describes the desired behavior.
2. **Green** — write the minimum code to make it pass.
3. **Refactor** — improve the code while the tests keep it safe.

Because the analytics functions are **pure** (same input → same output, no side effects), tests are fast, deterministic, and don't need a database or network.

```bash
python -m pytest
```

---

## Roadmap

The next milestones, in order of priority:

1. Finish the `analytics` engine (sentiment classification + metrics).
2. Build the `stream_core` domain layer (services & selectors).
3. Implement data ingestion with Celery.
4. Expose everything through the REST API and the MCP server.
5. Containerize and wire up CI/CD.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
