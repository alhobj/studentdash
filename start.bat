@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto dependencies
where py >nul 2>nul
if errorlevel 1 goto python_fallback
py -3 -m venv .venv
if errorlevel 1 goto failed
goto dependencies
:python_fallback
python -m venv .venv
if errorlevel 1 goto failed
:dependencies
".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -c "import flask, jinja2, openpyxl" >nul 2>nul
if not errorlevel 1 goto run
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
:run
echo Open http://127.0.0.1:5000 in your browser. Close this window or press Ctrl+C to stop.
".venv\Scripts\python.exe" teacher.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo Studentdash could not start. Install Python 3.10 or newer and check the message above.
pause
exit /b 1
