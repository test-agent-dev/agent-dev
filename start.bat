@echo off
REM TESTIA AI Agent - Windows Startup Script

echo 🚀 Starting TESTIA AI Agent...

REM Set Python path
set PYTHONPATH=%cd%\src

REM Load environment variables if .env exists
if exist .env (
    echo 📝 Loading environment variables...
    for /f "delims=" %%i in (.env) do set %%i
)

REM Check for API keys
if "%OPENAI_API_KEY%"=="" if "%ANTHROPIC_API_KEY%"=="" (
    echo ⚠️  Warning: No API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY
)

REM Create necessary directories
if not exist data mkdir data
if not exist logs mkdir logs

REM Start the application
echo 🎯 Starting TESTIA...
python src\main.py

pause
