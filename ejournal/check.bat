@echo off
chcp 65001 >nul
rem Full self-check on a temporary SQLite database (PostgreSQL is not required)
call venv\Scripts\activate.bat
set DB_ENGINE=sqlite
echo === makemigrations (creates 0001_initial on first run) ===
python manage.py makemigrations || goto :error
echo === django check ===
python manage.py check || goto :error
echo === tests ===
python manage.py test apps -v 2 || goto :error
echo.
echo ALL CHECKS PASSED
pause
exit /b 0
:error
echo CHECK FAILED, see messages above.
pause
exit /b 1
