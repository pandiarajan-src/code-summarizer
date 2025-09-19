@echo off
REM Simple Windows Deployment Script for Code Summarizer
REM This script runs the API and Frontend without Docker

echo ====================================
echo Code Summarizer Windows Deployment
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.12+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Creating .env from .env.example...
    if exist .env.example (
        copy .env.example .env
        echo Please edit .env file and add your OPENAI_API_KEY
        notepad .env
        pause
    ) else (
        echo Creating basic .env file...
        echo OPENAI_API_KEY=your_api_key_here > .env
        echo Please edit .env file and add your actual OPENAI_API_KEY
        notepad .env
        pause
    )
)

REM Install uv if not present
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing uv package manager...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo Failed to install uv, trying with pip...
        pip install uv
    )
)

REM Install dependencies
echo.
echo Installing Python dependencies...
uv sync --frozen --no-dev
if %errorlevel% neq 0 (
    echo Failed with uv, trying pip...
    pip install -r requirements.txt
)

REM Kill any existing processes on ports 8000 and 8080
echo.
echo Checking for existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000"') do (
    echo Killing process on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080"') do (
    echo Killing process on port 8080...
    taskkill /F /PID %%a >nul 2>&1
)

REM Start the API server in a new window
echo.
echo Starting API server on port 8000...
start "Code Summarizer API" cmd /k "set PYTHONPATH=app&& uv run uvicorn app.api_main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for API to start
echo Waiting for API to start...
timeout /t 5 /nobreak >nul

REM Check if API is running
curl -f http://127.0.0.1:8000/api/health >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: API might not have started properly
    echo Check the API window for errors
) else (
    echo API is running successfully!
)

REM Start the frontend server in a new window
echo.
echo Starting Frontend server on port 8080...
cd frontend
start "Code Summarizer Frontend" cmd /k "python -m http.server 8080"
cd ..

echo.
echo ====================================
echo Deployment Complete!
echo ====================================
echo.
echo API is running at: http://localhost:8000
echo Frontend is running at: http://localhost:8080
echo API Documentation: http://localhost:8000/docs
echo.
echo To stop the servers, close the command windows or press Ctrl+C in each window
echo.
pause