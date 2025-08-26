# Garden Guide

Minimal, friendly garden assistant with progress tracking for elements (plants, beds, etc.), notes, images, and bloom events.

## Features
- Ask AI for garden advice with optional images
- Track elements with optional images (upload or generated sample)
- Attach plain-text notes per element
- Track bloom events (start/end)
- Dashboard stats (totals, by type, currently blooming, recent notes)

## Setup
1. Python 3.9+
2. Create venv and install deps:
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```
3. Optional: set OpenAI key for advice
```bash
export OPENAI_API_KEY=sk-...
```

## Run the app
```bash
streamlit run streamlit_app.py
```

## Tests
- Unit tests:
```bash
pytest -q
```
- E2E (Playwright): ensure app is running, then
```bash
ENABLE_E2E=1 pytest -q tests/test_e2e_playwright.py --headed
```
If browsers not installed:
```bash
playwright install
```

## Project structure
- `db.py`: SQLite schema, CRUD for elements/notes/blooms, stats
- `storage.py`: image saving and sample image generation
- `streamlit_app.py`: UI tabs (Ask, History, Design, Elements, Dashboard)
- `tests/`: unit tests, e2e
- `data/`: local database and media storage

## Defaults
- Types: flower, shrub, tree, bed, planter
- Notes: plain text
- Images: PNG/JPG up to ~5MB (saved as PNG), sample generator available

## Roadmap
- Accessibility and keyboard navigation improvements
- More charts (bloom timeline)
- Data export/import
