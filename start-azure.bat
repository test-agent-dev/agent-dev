@echo off
REM TESTIA AI Agent - Azure Windows Setup Script

echo 🔧 Configuring TESTIA for Azure OpenAI...

REM Copy Azure environment file
if not exist .env (
    copy .env.azure .env
    echo ✅ Copied Azure configuration to .env
) else (
    echo ⚠️  .env already exists, skipping copy
)

echo 🔍 Verifying Azure OpenAI configuration...

findstr /C:"AZURE_OPENAI_API_KEY=DFNfL" .env >nul
if %errorlevel%==0 (
    echo ✅ Azure OpenAI API Key configured
) else (
    echo ❌ Azure OpenAI API Key not found in .env
)

findstr /C:"arqhub9744923851.openai.azure.com" .env >nul
if %errorlevel%==0 (
    echo ✅ Azure OpenAI Endpoint configured
) else (
    echo ❌ Azure OpenAI Endpoint not found in .env
)

echo 🚀 Starting TESTIA with Azure OpenAI...

REM Set Python path
set PYTHONPATH=%cd%\src

REM Create necessary directories
if not exist data mkdir data
if not exist logs mkdir logs

REM Load environment variables
for /f "delims=" %%i in (.env) do set %%i

REM Start the application
python src\main.py

pause
