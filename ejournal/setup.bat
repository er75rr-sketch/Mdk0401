@echo off
chcp 65001 >nul
rem Find a real Python: first the "py" launcher, then python in PATH
set PY=
py -3.12 --version >nul 2>&1 && set PY=py -3.12
if not defined PY py -3 --version >nul 2>&1 && set PY=py -3
if not defined PY python -c "import sys" >nul 2>&1 && set PY=python
if not defined PY goto :nopython

echo Using: %PY%
%PY% --version
echo [1/3] Creating virtual environment...
%PY% -m venv venv || goto :error
call venv\Scripts\activate.bat
echo [2/3] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt || goto :error
echo [3/3] Done. Next: run check.bat
pause
exit /b 0

:nopython
echo.
echo Python is NOT installed.
echo Install it with:  winget install -e --id Python.Python.3.12
echo or from https://www.python.org/downloads/  (check "Add python.exe to PATH")
echo Then CLOSE this window, open a new one and run setup.bat again.
pause
exit /b 1

:error
echo ERROR, see messages above.
pause
exit /b 1
