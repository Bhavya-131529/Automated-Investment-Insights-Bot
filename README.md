# Automated Investment Insights Bot

> **Disclaimer**: This is a prototype/demo ONLY. It does NOT constitute real financial advice. For educational use.

This project is a minimal prototype to deliver automated, tailored demographic investment suggestions using an AI Engine with deterministic rule-based fallbacks. It is composed of a FastAPI backend and a Streamlit frontend UI.

## Project Structure
```text
bot_prototype/
│
├── backend/
│   ├── main.py        # FastAPI application and endpoints
│   ├── ai_engine.py   # AI integration (HF Inference API) and fallback heuristics
│   ├── database.py    # SQLite connections and init routines
│   ├── models.py      # Pydantic schemas for data validation
│   └── tickers.json   # Seed data with ~30 robust ETFs and symbols
│
├── frontend/
│   └── app.py         # Streamlit dashboard and UI app
│
├── tests/
│   └── test_suggestions.py # Pytest assertions to validate math and endpoints
│
└── database/          # Auto-created upon backend run. Holds `bot.db`
```

## Features Complete
1. **User Authentication:** Fake signup/login forms that persist to the DB.
2. **Onboarding Questions:** Age, Savings, Contribution, Horizon, Risk, Goal.
3. **AI Logic Engine:** Plugs into HuggingFace Models or gracefully defaults to an intelligent deterministic rule-engine.
4. **Dashboard View:** Shows asset allocation bars, specific tickers & rationales, expected growth projections over time, risk warnings, and a checklist.
5. **Feedback Loop:** Save user helpful/unhelpful votes right back to SQLite.

## How to Run Locally

### 1. Prerequisites 
Ensure you have Python 3.8+ installed.

### 2. Environment Setup
Create a virtual environment and install via pip in the root directory:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run Backend (FastAPI)
Open a terminal, activate your environment, and spin up the server on port 8000:
```bash
cd backend
uvicorn main:app --reload --port 8000
```
*(Optionally export an HF API token for AI generation: `export HF_API_TOKEN="..."`)*

### 4. Run Frontend (Streamlit)
Open a *second* terminal, activate the same environment, and spin up the UI:
```bash
streamlit run frontend/app.py
```

### 5. Running Tests
You can verify the backend endpoints and formulas using standard Pytest:
```bash
pytest tests/
```
