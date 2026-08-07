# JobApplicationIASystem

A compact README describing the current project layout, setup, and quick run instructions.

## Project Structure

- `app/`
  - `main.py` — application entrypoint
  - `config/` — configuration and settings (`settings.py`)
  - `models/` — data models (`api.py`, `job.py`)
  - `scraper/` — scrapers and parser (`base.py`, `linkedin.py`, `data_mock.py`, `parser.py`)
  - `utils/` — utility helpers
- `data/` — sample and generated data (resume JSON files)
- `workflows/` — exported n8n workflow(s)
- `requirements.text` — Python dependency list (note: filename uses `.text`)
- `README.md` — this file

## Overview

This project collects job postings (scraping), processes job details, evaluates fit against canonical resumes, and supports automation via an n8n workflow that can append approved matches to Google Sheets.

Key components:

- Scrapers in `app/scraper/` (real + mock)
- Resume data stored under `data/` (example: `resume_software_engineer_java.json`)
- API entrypoint at `app/main.py` to expose search/process endpoints

## Quickstart

1. (Optional) Create and activate a virtual environment:

```bash
python -m venv .venv
.\\.venv\\Scripts\\activate
```

2. Install dependencies (file in repo is `requirements.text`):

```bash
pip install -r requirements.text
```

3. (Optional) Populate sample resumes (if script exists):

```bash
python app/scraper/data_mock.py
``` 

4. Run the API (either directly or with Uvicorn):

```bash
python app/main.py
# or (if using FastAPI/uvicorn)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Import `workflows/Pipeline Autônomo de Vagas - IA e Workspace no n8n (Corrigido).json` into n8n and configure the HTTP nodes to point to your API host (use `http://host.docker.internal:8000` if n8n runs in Docker).

## Files of interest

- `data/` — contains example resumes used for matching
- `app/scraper/data_mock.py` — quick mock scraper for development
- `workflows/` — exported n8n workflow

## Notes & Recommendations

- Consider renaming `requirements.text` to `requirements.txt` or create a proper `pyproject.toml` for dependency management.
- If you plan to run the real LinkedIn scraper, configure Playwright and credentials and be mindful of terms of service.

---

If you want, I can also:

- convert `requirements.text` → `requirements.txt` and pin versions,
- add a short `Makefile` or `scripts/` runner for common tasks,
- generate a minimal `Dockerfile` and `docker-compose.yml` for local testing.

Tell me which next step you'd like.

