@echo off
REM TESTIA AI Agent - Windows CLI Script

set PYTHONPATH=%cd%\src

REM Load environment variables
if exist .env (
    for /f "delims=" %%i in (.env) do set %%i
)

REM Run CLI
python src\cli\main.py %*
