# TalentHub

TalentHub — русскоязычный MVP платформы образовательных событий, портфолио учащихся и партнёрств между учреждениями, компаниями и академиями.

## Требования

- Python 3.13 и `uv`;
- Node.js 22.12+ и npm;
- проект Supabase PostgreSQL.

Для `DATABASE_URL` используйте **Session pooler** из Supabase Connect. Замените схему на `postgresql+psycopg://` и добавьте `?sslmode=require`.

## Настройка

```bash
cp backend/.env.example backend/.env
```

Обязательные переменные в `backend/.env`:

| Переменная | Значение |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy URL Session pooler Supabase |
| `JWT_SECRET` | случайная строка длиной от 32 символов |
| `MOCK_DATA_PASSWORD` | пароль от 8 символов для всех mock-аккаунтов |
| `TRUSTED_ORIGINS` | разрешённые browser origins через запятую |
| `COOKIE_SECURE` | `false` локально, `true` на HTTPS |

`DEMO_*_PASSWORD` нужны только для трёх отдельных аккаунтов из `seed_demo`. Сидер не заменяет уже изменённые пароли.

## Установка и данные

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.scripts.seed_mock

cd ../frontend
npm install
```

`seed_mock` можно запускать повторно. Он не создаёт дубликаты, не меняет существующие пароли и сохраняет изменённые пользователем профильные поля и события. После первого запуска доступны:

- 9 тематических категорий;
- основной учащийся, 8 mock-учащихся и 6 представителей организаций;
- 6 организаций всех типов;
- 20 будущих, прошедших, опубликованных и черновых событий;
- заявки во всех статусах и подтверждённые достижения;
- публичные и адресные партнёрские запросы;
- завершённое партнёрство и объясняющая история престижа.

`student@talenthub.by` и `mock.student01@talenthub.by` получают подготовленный demo-сценарий: будущие заявки, завершённые заявки, интересы, рекомендации и подтверждённое достижение.

Основные аккаунты:

| Роль | Email | Пароль |
| --- | --- | --- |
| Основной учащийся | `student@talenthub.by` | `DEMO_STUDENT_PASSWORD`; при создании без него — `MOCK_DATA_PASSWORD` |
| Mock-учащийся | `mock.student01@talenthub.by` | `MOCK_DATA_PASSWORD` |
| Учреждение | `horizon.rep@talenthub.by` | значение `MOCK_DATA_PASSWORD` |
| Компания | `novalab.rep@talenthub.by` | значение `MOCK_DATA_PASSWORD` |

Если после первого сидинга вы изменили `MOCK_DATA_PASSWORD`, хэши существующих аккаунтов намеренно не меняются. Явный сброс выполняется командой:

```bash
cd backend
uv run python -m app.scripts.reset_mock_passwords
```

Сброс обновляет только отдельные mock-аккаунты и представителей mock-организаций. Пароль `student@talenthub.by` не изменяется.

## Запуск

Из корня репозитория:

```bash
./dev.sh
```

Скрипт применяет миграции и запускает FastAPI и Vite. Данные автоматически не пересоздаются. Откройте `http://localhost:5173`.

Ручной запуск в двух терминалах:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

```bash
cd frontend
npm run dev
```

## Реализованные сценарии

- публичная регистрация и JWT-сессия в HttpOnly cookie;
- профили учащихся и организаций;
- интересы и рекомендации по категориям;
- каталог событий с поиском и фильтрами;
- создание, редактирование, публикация и отмена событий;
- заявки учащихся, ручной отбор и подтверждение посещения;
- автоматическое портфолио из подтверждённых участий;
- каталог организаций и прозрачная история престижа;
- публичные и адресные партнёрские инициативы в обоих направлениях;
- принятие отклика, двойное подтверждение завершения и однократное начисление одного балла каждой стороне;
- адаптивная навигация и отдельные public/student/organization экраны.

Не входят в milestone: уведомления, админка, модерация, родители, чат, платежи, ML, файлы и рейтинг учащихся.

## Проверка

```bash
cd backend
uv run pytest

cd ../frontend
npm run typecheck
npm run build
```

Production-style запуск после frontend build:

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

FastAPI раздаёт `frontend/dist`, сохраняет API 404 и поддерживает прямой переход на frontend-маршруты.
