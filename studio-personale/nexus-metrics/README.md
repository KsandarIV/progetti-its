# Nexus Metrics

> **In breve.** Progetto personale: una pipeline in Python, tutta in locale, che scarica dalla Riot API la mia cronologia di partite di League of Legends (926 partite, nov 2025 – ott 2026), la trasforma in tabelle e la mostra in una dashboard Streamlit, con 29 test offline.
>
> **La visione** ([roadmap](project_roadmap.md)) è andare oltre le statistiche descrittive: una domanda di machine learning ben definita sui miei dati e un assistente RAG locale (ad esempio con Ollama) che risponde alle domande sulle mie partite citando i dati da cui ricava la risposta, senza servizi a pagamento.
>
> I dati delle partite e la chiave API non sono pubblicati. Sviluppato con l'assistenza di LLM; scelte, verifiche e roadmap sono mie.

## Current status

- Riot Match-V5 ingestion has downloaded 926 match-detail files and 926 timelines.
- The 926 downloaded matches span 2025-11-08 through 2026-10-09 UTC. All cached match IDs have a detail file and a timeline, and every detail file parsed successfully. Availability does not guarantee complete lifetime history.
- The raw JSON occupies about 799 MB (decimal), mostly due to timelines.
- A Python analysis command exports a flat per-match table plus month, patch, champion, position, and queue summaries.
- A local neon-dark Streamlit dashboard provides filters, charts, match history, report rebuilding, and a user-triggered Riot sync.
- The 29 unit tests pass in the project's Conda Python 3.10.22 environment; the Streamlit smoke test renders all tabs without exceptions.

## Requirements and secrets

- Python 3.10 in the project's Conda environment
- Install the dependencies from `requirements.txt` into the project Conda environment
- A valid personal Riot API key stored only in the local `.env`

`.env.example` is an optional, secret-free setup template. Copy it to `.env` for a new local checkout and replace the placeholder. The application reads `.env`, not `.env.example`. Optional `RIOT_GAME_NAME` and `RIOT_TAG_LINE` values can override the target account. Never share `.env` or generated personal match data. `.gitignore` excludes credentials, datasets, and common Python build/test artifacts.

## Offline tests

From the project directory, with the Conda Python 3.10 environment active:

```powershell
python -m unittest discover -s tests -v
```

Tests must remain deterministic, mock HTTP, and require neither a valid Riot key nor internet access.

## Data ingestion

To run a small controlled extraction:

```powershell
python main.py --limit 3
```

Review the generated JSON, dates, logs, and idempotency before choosing a larger batch, for example:

```powershell
python main.py --limit 100
```

Each run resolves the account and incrementally checks Match-V5 IDs from newest to oldest. The complete local ID archive in `data/<game_name>_match_ids.json` is the deduplication ledger; keeping all IDs is safer than a rolling last-10 cache and is negligible in size compared with raw match data. Scanning stops after a page contains only archived IDs. Newly discovered IDs are atomically prepended to the archive, then the downloader resumes the oldest incomplete match files in batches of up to 100. Complete detail/timeline pairs are never downloaded again. Use `--full-rescan` occasionally if Riot may have exposed historical matches retroactively; it scans every available ID page. The local limiter is paced below 10 requests/second and 90 requests/120 seconds. A persistent `429` stops the download batch; completed pairs remain available for a later resume.

To check for new matches and download up to 100 pending matches:

```powershell
python main.py
```

To look for retroactively available older matches:

```powershell
python main.py --full-rescan
```

## Local dashboard

Start the Python-only Streamlit UI from the project directory:

```powershell
python -m streamlit run dashboard.py
```

The dashboard binds to `127.0.0.1`. It reads local CSV reports on page load and makes **no Riot requests** unless `Sync matches` is pressed. Sync uses the same tested workflow as `main.py`, honours the configured rate limits, deduplicates against the full ID archive, and resumes incomplete detail/timeline pairs. After a successful sync it refreshes local reports. `Rebuild local reports` only reparses local match-detail JSON. Raw match JSON remains the source of truth; reports can always be regenerated.

The 926-match detail files occupy about 76 MB; timelines are about 724 MB and remain available for future event-level analysis. Keep the JSON files as the immutable source layer and query the compact `matches.csv` with pandas. Do not flatten the large timelines into CSV. SQLite is a reasonable next step if relational queries or application state grow; Parquet is worth considering if analytical tables become much larger. PostgreSQL is unnecessary for this local, single-user MVP.

The UI theme is defined in `src/visualization/theme.py` and `.streamlit/config.toml`. It uses the requested neon palette on a dark cyberpunk-inspired background and local system fonts, without third-party font requests. The current visualizations are descriptive only; sample size and missing calendar months should be considered before interpreting trends.

## Local analysis

Build/update the CSV reports from downloaded match details without making Riot API requests:

```powershell
python analyze.py
```

Output files are written to `data/processed/`:

- `matches.csv` — one row per identified player match
- `by_month.csv` — calendar-month aggregates
- `by_patch.csv` — game-version aggregates
- `by_champion.csv` — champion aggregates
- `by_position.csv` — position aggregates
- `by_queue.csv` — queue aggregates

Match-V5 data used here provides calendar timestamps and game versions, not a canonical League season label. Do not treat patch or calendar year as an official season; add an explicit, sourced season mapping before reporting seasonal comparisons. Interpret small champion/position groups cautiously; a win rate from only a few matches is noisy.

Monthly coverage in this sample has no returned matches from April through July 2026. Treat that absence as a property of the returned dataset unless checks show missing IDs or files.

## Maintained structure

- `src/clients/` — Riot API and other external interfaces
- `src/core/` — shared logic independent of transport
- `src/extractors/` — raw-data ingestion and persistence
- `src/analytics/` — deterministic transformations of local match records
- `src/services/` — shared synchronization and report-generation workflows
- `src/visualization/` — reusable plot theme and visualization support
- `dashboard.py` — local Streamlit presentation layer
- `.streamlit/config.toml` — dark theme, usage telemetry off, loopback-only server binding
- `tests/` — offline behavioral tests
- `data/` — private generated local data, excluded from Git
- `project_roadmap.md` — strategic goals and milestone state

Python modules under `src/` are canonical.
