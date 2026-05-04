# InvestAI

InvestAI is an AI-powered Investment Insights Chatbot application. It consists of a modular FastAPI backend and a web-based frontend interface.

## Prerequisites

- Python 3.x
- OpenAI API Key

## Setup

1. Create a `.env` file in the root directory and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

2. Activate the virtual environment:
   ```cmd
   .\venv\Scripts\activate
   ```

3. Install dependencies (if not already installed):
   ```cmd
   pip install -r requirements.txt
   ```

## Running the Application

You can start both the backend and frontend simultaneously using the provided batch script:

```cmd
run_app.bat
```

Alternatively, you can start them manually:

### Start Backend

```cmd
.\venv\Scripts\activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Backend will run at http://localhost:8000

### Start Frontend

```cmd
.\venv\Scripts\activate
python -m http.server 3000 --directory frontend
```
Frontend will run at http://localhost:3000

## Architecture

- **Backend**: FastAPI with RAG pipeline for financial literacy and data integration (e.g., yfinance, Alpha Vantage).
- **Frontend**: Vanilla JS/HTML client.
- **Database**: SQLite (`investments.db`) for user profiling and state management.
