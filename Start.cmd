@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto run
where py >nul 2>nul
if errorlevel 1 goto fallback
py -3 -m venv .venv
if errorlevel 1 goto failed
goto install
:fallback
python -m venv .venv
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
:run
".venv\Scripts\python.exe" -c "import flask, openpyxl, docx, pypdf, waitress" >nul 2>nul
if not errorlevel 1 goto start
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
:start
".venv\Scripts\python.exe" scripts\run.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo ArborSynapse could not start. Check the message above. Python 3.10+ and Node.js 22.12+ are required.
pause
exit /b 1
