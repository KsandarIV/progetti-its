# Nexus Metrics — Project Roadmap

## Vision

Build a local-first platform for analyzing the user's League of Legends match history, exploring statistical learning, and querying grounded match insights through a locally hosted RAG/LLM workflow. Keep the project Python-only and avoid paid services.

## Current status — 2026-10-10

- Riot ID resolution, Match-V5 ID pagination, and detail/timeline ingestion are implemented.
- Retrieved 926 unique match IDs; all 926 detail files and 926 timelines are now present.
- All detail JSON files parse successfully. The returned date range is 2025-11-08 through 2026-10-09 UTC.
- Raw data occupies about 799 MB (decimal); timelines dominate storage.
- Twenty-nine offline unit tests pass using Conda Python 3.10.22; the Streamlit app-test smoke check renders with no exceptions.
- The full extraction completed using cached IDs and conservative request pacing; the completion output contained no `429` warnings.
- Default ingestion now checks newest Match-V5 pages on each run, stops at a fully archived page, merges new IDs atomically, and resumes incomplete detail/timeline pairs. `--full-rescan` is available for retroactive history changes.
- Implemented the first analysis pass: per-match CSV plus month, patch, champion, position, and queue summaries.
- Added a neon-dark Python dashboard with compact interactive filters, performance charts, match-history view, data integrity summary, local report rebuild, and explicitly user-triggered Riot sync. The server binds to loopback and loads no remote font assets.
- Kept the 76 MB match details and 724 MB timelines as raw JSON; generated CSV remains the compact pandas-queryable layer. PostgreSQL is not justified at the current local scale.
- Added root-level `Python_Starter_Kit/` examples for palette, EDA, common imports, tabular ML, and CNN experiments.
- Current 926-match overview: 462 wins, 464 losses (49.89%). Monthly coverage is uneven and has no returned matches from April through July 2026.
- Next: continue desktop/narrow viewport visual QA, then improve metric quality (especially CS normalization and unknown positions) before adding more charts.

API availability does not prove complete lifetime history. Match-V5 match details expose calendar timestamps and versions used here, not an official season label; add a sourced season mapping before claiming season-by-season results.

## Architecture

- **Riot Bridge:** Riot API transport, routing, authentication, rate limits, and response errors.
- **Core:** shared rules independent of external services.
- **Extractors:** retrieve raw match data and persist it locally.
- **Analytics:** deterministic transformations of raw records into tested tables and summaries.
- **Visualization and local AI:** separate Python modules, added only when their behavior and evaluation criteria are clear.

Keep secrets in `.env`, non-secret settings in Python configuration, and generated or identifying data under ignored `data/`. Avoid duplicating configuration across formats.

## Milestones

### 1. Ingestion — MVP complete; maintain and expand carefully

- [x] Configure the Conda Python 3.10 environment and base dependencies.
- [x] Resolve Riot ID to PUUID and paginate Match-V5 IDs.
- [x] Download match details and timelines with timeouts, local rate limiting, and retry handling for `429`.
- [x] Verify the live extraction and profile the full set of 926 returned IDs locally.
- [x] Add offline tests for URL construction, pagination, retries, persistence, and partial failures.
- [x] Resume incrementally and fetch all 926 IDs returned by the saved Match-V5 ID list.
- [x] Add a persistent full-ID deduplication ledger and overlap-based incremental sync.
- [ ] Periodically run `--full-rescan` only when checking for retroactively surfaced history is useful.

### 2. Storage

- [ ] Keep raw JSON as an immutable source layer and document safe reprocessing.
- [ ] Evaluate SQLite only when query volume or workflow needs justify it; current sample is manageable as files.
- [ ] Define stable schemas and migration/versioning before adopting a database.

### 3. Analytics — initial table export complete

- [x] Extract player-level match rows with timestamp, patch, queue, position, result, KDA, CS/minute, damage, and vision score.
- [x] Export deterministic per-match and grouped CSV reports.
- [ ] Add data-quality checks, season mapping with an authoritative source, and more robust multi-batch ingest coverage.
- [ ] Compare trends by month, season, queue, role, and champion only when sample sizes support useful interpretation.

### 4. Visualization

- [x] Choose Streamlit and Plotly as the Python-native dashboard/plotting stack with dependency ranges compatible with Python 3.10.
- [x] Add a shared root-level Python starter kit for reusable visualization, EDA, imports, tabular ML, and CNN patterns.
- [x] Plot monthly trends, champion/role summaries, and sample counts with context.
- [x] Keep Riot API sync explicit and reports locally rebuildable from raw data.
- [ ] Run visual QA at desktop and narrow viewport sizes and refine accessibility/contrast.
- [ ] Keep visual output local and avoid implying causal conclusions from descriptive statistics.

### 5. Local ML and RAG

- [ ] Define a concrete ML question and valid dataset before selecting a model; add CNN only for a justified image task.
- [ ] Evaluate local embedding and vector-store choices only after defining retrieval needs.
- [ ] Integrate a local model (for example via Ollama) without requiring paid APIs.
- [ ] Evaluate retrieval separately from generation; ground answers in match records, show evidence, and state uncertainty.

### 6. Delivery and maintenance

- [ ] Keep the issue backlog prioritized and changes small, tested, and reviewable.
- [ ] Add CI, branch protection, changelog, and release tags after deciding whether this project stays in the parent repository or moves to its own repository.
- [ ] Re-check Riot Developer Policies and API limits as they change.

## Definition of Done

- The change has focused offline tests and passes on supported Python 3.10.
- No secrets, PUUIDs, raw match data, or generated artifacts enter Git or logs.
- Failure and partial completion are visible; no false success message is emitted.
- Documentation, roadmap state, and acceptance criteria reflect verified behavior rather than intention.