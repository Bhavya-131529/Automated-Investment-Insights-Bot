@echo off
echo Starting InvestAI Application...

:: Start Backend
start "InvestAI Backend" cmd /k ".\venv\Scripts\activate && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

:: Start Frontend
start "InvestAI Frontend" cmd /k ".\venv\Scripts\activate && python -m http.server 3000 --directory frontend"

echo Servers are starting!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Please ensure your OPENAI_API_KEY is set in the .env file in the root directory.
pause
