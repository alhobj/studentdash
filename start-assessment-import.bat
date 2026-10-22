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
".venv\Scripts\python.exe" -c "import flask, jinja2, openpyxl, pypdf, docx" >nul 2>nul
if not errorlevel 1 goto run
".venv\Scripts\python.exe" -m pip install -r archive\legacy\requirements.txt
if errorlevel 1 goto failed
:run
if not defined STUDENTDASH_WORKBOOK set "STUDENTDASH_WORKBOOK=%CD%\data\classroom.xlsx"
if not defined STUDENTDASH_OUTPUT set "STUDENTDASH_OUTPUT=%CD%\output"
echo Open http://127.0.0.1:5000/classes and select your class, then Import assessment.
echo Stop any other Studentdash server first. Press Ctrl+C to stop this server.
".venv\Scripts\python.exe" archive\legacy\teacher.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo Studentdash could not start. Install Python 3.10 or newer and check the message above.
pause
exit /b 1
