# Arbiter: LLM Output Arbitration System

> A system where AI models audit each other's work. Three specialized critics, each running on a different model, independently evaluate any LLM output. An adjudicator resolves their disagreements into one confidence-scored verdict with actionable callouts.

**Status:** scaffold (Phase 0). See [Roadmap](#roadmap).

## Architecture

```
                    ┌─► accuracy_critic     (GPT-4o)        ─┐
parse_input ─► fan-out ─► logic_critic      (Claude)        ─┼─► collect ─► detect_disagreements
                    └─► completeness_critic (Llama, Ollama) ─┘                    │
                                                                    all clean? ───┤
                                                           yes ◄──────────────────┘
                                                            │            │ no
                                                  short_circuit_pass   adjudicate ─► verdict ─► persist
```

**Why different models per critic?** Models from the same family share blind spots. Disagreement between them is the most valuable signal in the system.

**Why a deterministic disagreement detector?** It is pure Python, unit-testable, and keeps the adjudicator focused on real conflicts instead of noise.

**Graceful degradation:** if a critic fails after retries, a verdict is still produced from the remaining critics, flagged `degraded` with a confidence penalty.

## Quickstart

### Option A: Docker (recommended)

```bash
cp .env.example .env          # add OPENAI_API_KEY / ANTHROPIC_API_KEY
docker compose up --build
```

- API docs: http://localhost:8000/docs
- UI: http://localhost:8501

**No paid keys?** Use three local Ollama models:

```bash
# in .env
ARBITER_CONFIG=config.ollama-only.yaml
# in docker-compose.yml, extend the ollama-init command:
#   ollama pull llama3.1:8b && ollama pull qwen2.5:7b && ollama pull mistral:7b
```

### Option B: Local development

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# for local runs, set OLLAMA_BASE_URL=http://localhost:11434/v1 and ARBITER_DB_PATH=data/arbiter.db
make api      # terminal 1
make ui       # terminal 2
make test
```

### Try it

```bash
curl -X POST http://localhost:8000/v1/arbitrate \
  -H "x-api-key: dev-key-change-me" -H "Content-Type: application/json" \
  -d '{"prompt":"When did the Berlin Wall fall?","output":"The Berlin Wall fell in 1991."}'
```

## Project layout

```
arbiter/
├── app/
│   ├── api/            FastAPI routes and auth
│   ├── graph/          LangGraph state, nodes, disagreement detector
│   ├── critics/        per-critic prompts and runner
│   ├── adjudicator/    adjudication prompt, resolvers, search tool
│   ├── llm/            provider clients wrapped with instructor
│   ├── storage/        SQLite schema and repositories
│   ├── analytics/      critic-behavior SQL queries
│   ├── schemas.py      all Pydantic models (single source of truth)
│   └── settings.py     env + config.yaml loading
├── ui/app.py           Streamlit verdict explorer
├── eval/               labeled benchmark + scoring harness
├── tests/              mocked-LLM unit tests
├── config.yaml         critic → provider/model mapping
├── config.ollama-only.yaml
├── docker-compose.yml  api + ui + ollama (+ model pull)
└── Makefile
```

## API

| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/health` | liveness probe | done |
| POST | `/v1/arbitrate` | evaluate one output | stub |
| POST | `/v1/arbitrate/batch` | submit many, returns `batch_id` | todo |
| GET | `/v1/batches/{id}` | batch progress | todo |
| GET | `/v1/arbitrations/{id}` | fetch a past verdict | todo |
| GET | `/v1/analytics/summary` | critic behavior stats | todo |

## Configuration

Critics are mapped to models in `config.yaml`; no code changes needed to swap providers. Secrets live in `.env`. Every arbitration stores a `prompt_version` so analytics stay comparable across prompt changes.

## Roadmap

- [x] **Phase 0:** repo scaffold, schemas, config, Docker, stubs
- [ ] **Phase 1:** critic prompts, `instructor` structured output, substring-validated quotes, single-model baseline
- [ ] **Phase 2:** parallel fan-out verified with timestamps, disagreement rules 1-3, retries, degraded mode
- [ ] **Phase 3:** adjudicator with type-specific resolution (web search / step tracing / requirement checklist)
- [ ] **Phase 4:** verdict explorer (inline highlights, critic comparison, batch mode)
- [ ] **Phase 5:** SQLite persistence, batch endpoints, analytics, full Docker flow
- [ ] **Phase 6:** 40-60 item benchmark, results table, showcase cases, demo video

## Evaluation

*Results go here after Phase 6.* Compare single-model baseline vs. 3-critic ensemble vs. ensemble + adjudicator on issue recall, precision, false-positive rate (clean set), score separation, cost and latency.

| Condition | Recall | Precision | FP rate | Cost / item | Latency |
|---|---|---|---|---|---|
| Single model | | | | | |
| 3 critics | | | | | |
| 3 critics + adjudicator | | | | | |

## Security note

Evaluated text is treated as untrusted. Prompts wrap it in delimiters and instruct critics to ignore embedded instructions. An injection test case belongs in `eval/dataset.jsonl`.

## Known limitations

Adjudicator bias, correlated errors within model families, search-tool coverage, and a small benchmark. Results should be read as indicative, not statistically conclusive.

## License

MIT
