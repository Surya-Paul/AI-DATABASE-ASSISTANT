@echo off
echo ===================================================
echo Starting AI SQL Assistant
echo ===================================================
echo.

:: Clear old random data
if exist "backend\data.db" (
    echo Deleting old database...
    del "backend\data.db"
)

:: Start Backend in a new window
echo Starting Backend (FastAPI)...
start cmd /k "cd backend && python -m uvicorn main:app --reload"

:: Start Frontend in a new window
echo Starting Frontend (Python HTTP Server)...
start cmd /k "cd frontend && python -m http.server 5173 --bind 127.0.0.1"


echo.
echo Both servers have been launched in separate windows!
echo Please open your browser and go to: http://localhost:5173
echo.
pause
