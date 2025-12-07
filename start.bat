@echo off
REM Qubic Risk Radar - One Command Startup Script (Windows)
REM This script sets up and runs the entire application with a single command

echo ========================================
echo  Qubic Risk Radar - Starting...
echo ========================================
echo.

REM Check if .env file exists
if not exist .env (
    echo [WARNING] No .env file found. Creating from .env.example...
    copy .env.example .env
    echo [OK] Created .env file. Please edit it with your configuration.
    echo.
    echo Required environment variables:
    echo    - POSTGRES_PASSWORD
    echo    - JWT_SECRET
    echo    - GEMINI_API_KEY
    echo.
    pause
)

echo [INFO] Building and starting services...
echo.

REM Build and start all services
docker-compose up --build -d

echo.
echo [INFO] Waiting for services to be healthy...
timeout /t 10 /nobreak > nul

echo.
echo ========================================
echo  Application is ready!
echo ========================================
echo.
echo Access points:
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo Services running:
docker-compose ps
echo.
echo To view logs:
echo    docker-compose logs -f
echo.
echo To stop all services:
echo    docker-compose down
echo.
pause
