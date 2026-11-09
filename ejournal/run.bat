@echo off
chcp 65001 >nul
call venv\Scripts\activate.bat
python manage.py makemigrations || goto :error
python manage.py migrate || goto :error
python manage.py seed_demo
echo Open http://127.0.0.1:8000/admin/  (admin / Admin12345)
python manage.py runserver
exit /b 0
:error
echo Migration failed: check PostgreSQL is running and .env settings are correct.
pause
exit /b 1
