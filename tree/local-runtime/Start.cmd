@echo off
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -File "%~dp0Start.ps1"
if errorlevel 1 (
  echo The launcher could not start. See LOCAL_STUDENT_GUIDE.md.
  pause
)
