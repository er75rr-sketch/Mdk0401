# Электронный журнал (ПР6, МДК.04.01)

Web-приложение на **Python 3.12 + Django 5.0 + Django REST Framework + PostgreSQL 16**, авторизация по **JWT**.

## Модули (apps/)

| Модуль | Назначение | Модели |
|---|---|---|
| `accounts` | авторизация (JWT), пользователи и роли | `User` (роль: администратор, куратор, преподаватель, студент) |
| `students` | группы и студенты | `StudyGroup`, `Student` |
| `subjects` | дисциплины и нагрузка преподавателей | `Subject`, `TeacherAssignment` |
| `journal` | занятия, оценки, посещаемость | `Lesson`, `Grade`, `Attendance` |
| `reports` | KPI, отчёты по группе и студенту | — (считает по данным других модулей) |
| `cabinet` | веб-интерфейс: кабинет студента и рабочее место преподавателя | — (работает с данными `journal` и `reports`) |

Связи: `journal` использует `students` (кто), `subjects` (что и кто ведёт) и `accounts` (права); `reports` читает данные всех модулей.

**Каскад:** при выставлении оценки студент автоматически отмечается как присутствовавший; поставить оценку отсутствующему («н») нельзя.

## Быстрый запуск (Windows)

1. Установить Python 3.12 и PostgreSQL 16.
2. Создать базу (pgAdmin или psql):
   ```sql
   CREATE DATABASE ejournal ENCODING 'UTF8';
   ```
3. В файле `.env` указать свой `DB_PASSWORD`.
4. Запустить `setup.bat` (venv + зависимости).
5. Запустить `check.bat` — миграции, `manage.py check` и все тесты (на временной SQLite, PostgreSQL не нужен). В конце должно быть `ALL CHECKS PASSED`.
6. Запустить `run.bat` — миграции в PostgreSQL, демо-данные, сервер на http://127.0.0.1:8000/

То же вручную:
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

## Демо-учётки (после `seed_demo`)

| Логин | Пароль | Роль |
|---|---|---|
| admin | Admin12345 | администратор (суперпользователь) |
| petrova | Teacher12345 | преподаватель-куратор ИС-21 (математика) |
| orlov | Teacher12345 | преподаватель (базы данных) |
| belova | Teacher12345 | куратор ИС-22 (веб-программирование) |
| ivanov | Student12345 | студент ИС-21 |

## Веб-интерфейс (http://127.0.0.1:8000/)

**Преподаватель** (`petrova` / `Teacher12345`): «Мои занятия» — нагрузка, кнопка «Новое занятие», ведомость занятия (посещаемость и оценки по всей группе одной кнопкой «Сохранить»), отчёт по группе. Чужие дисциплины изменить нельзя.

**Студент:**

http://127.0.0.1:8000/ → вход (`ivanov` / `Student12345`) → «Мой дневник»: средний балл, пропуски, процент посещаемости, оценки по каждой дисциплине и последние занятия с отметками.
Администратора главная страница перенаправляет в `/admin/`. Админка — только для администратора.

## API

Список всех эндпоинтов: http://127.0.0.1:8000/api/

| Метод | URL | Что делает |
|---|---|---|
| POST | `/api/auth/login/` | логин → `access`, `refresh`, данные пользователя |
| POST | `/api/auth/refresh/` | новый access по refresh |
| GET | `/api/auth/me/` | текущий пользователь |
| CRUD | `/api/users/` | пользователи (только администратор) |
| CRUD | `/api/groups/` | группы (`?course=`); `GET /api/groups/{id}/students/` |
| CRUD | `/api/students/` | студенты (`?group=`, `?search=`) |
| CRUD | `/api/subjects/` | дисциплины |
| CRUD | `/api/assignments/` | нагрузка (`?group=`, `?teacher=`) |
| CRUD | `/api/lessons/` | занятия (`?group=`, `?subject=`, `?date_from=`, `?date_to=`); `GET /api/lessons/{id}/sheet/` — ведомость |
| CRUD | `/api/grades/` | оценки (`?lesson=`, `?student=`, `?group=`) |
| CRUD | `/api/attendance/` | посещаемость |
| GET | `/api/reports/kpi/` | сводные показатели |
| GET | `/api/reports/groups/{id}/` | успеваемость и пропуски группы |
| GET | `/api/reports/students/{id}/` | средние баллы студента по дисциплинам |

Пример:
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ -H "Content-Type: application/json" -d "{\"username\":\"petrova\",\"password\":\"Teacher12345\"}"
curl http://127.0.0.1:8000/api/reports/kpi/ -H "Authorization: Bearer <access>"
```

## Права доступа

- **Администратор** — всё.
- **Преподаватель / куратор** — читает данные; создаёт и меняет занятия, оценки и посещаемость **только по своим дисциплинам**; куратор дополнительно видит журнал своей группы.
- **Студент** — видит только свою группу, свои оценки и свой отчёт.

## Тесты

```bat
python manage.py test apps -v 2
```
49 тестов: авторизация и JWT, права ролей, CRUD, проверки журнала (чужая группа, «н», дубль оценки, неверная оценка), каскад оценка → посещаемость, пересчёт KPI, кабинет студента, ведомость преподавателя.
Для тестов на PostgreSQL пользователю БД нужно право `CREATEDB`.

## Частые проблемы

| Проблема | Решение |
|---|---|
| `No module named 'apps.X'` | запускать команды из корня проекта, где лежит `manage.py` |
| `UnicodeDecodeError` при подключении | обычно неверный пароль в `.env` или БД не в UTF-8 — пересоздать с `ENCODING 'UTF8'` |
| `relation ... does not exist` | `python manage.py makemigrations` и `python manage.py migrate` |
| `401 Unauthorized` | нет или истёк токен — заново `/api/auth/login/` |
| `403 Forbidden` | у роли нет прав (например, преподаватель меняет чужую дисциплину) |
