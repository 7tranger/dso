# Idea Kanban API

Минимальный Kanban-сервис для идей и мини-проектов (FastAPI + SQLAlchemy + SQLite/Postgres).

## Тесты

```bash
py -m pytest -v
```

## Быстрый старт (локально)

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # PowerShell, для bash: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
py -m uvicorn src.main:app --reload
```

После запуска:
- API: `http://127.0.0.1:8000/api/v1/...`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Docker / Compose

```bash
docker build -t idea-kanban .
docker run --rm -p 8000:8000 idea-kanban
# или
docker compose up --build
```

Контейнер также открывает Swagger на `http://127.0.0.1:8000/docs`.

## Переменные окружения

- `DATABASE_URL` — строка подключения к БД:
  - по умолчанию: `sqlite:///./idea_kanban.db`
  - пример Postgres: `postgresql+psycopg2://user:pass@localhost:5432/idea_kanban`
- `JWT_SECRET` — обязательный секрет для подписи JWT (мин. 16 символов).
- `SCORE_API_BASE` — базовый URL внешнего сервиса скоринга (по умолчанию `https://example.com`).

## Тесты и качество

- **Регистрация**
  - `POST /api/v1/auth/register`
  - Тело:
    ```json
    { "email": "user@example.com", "password": "password123" }
    ```
  - Ответ `201`:
    ```json
    { "id": 1, "email": "user@example.com", "role": "user", "created_at": "..." }
    ```

- **Логин**
  - `POST /api/v1/auth/login` (формат `application/x-www-form-urlencoded` — стандартный OAuth2)
  - Тело:
    ```text
    username=user@example.com&password=password123
    ```
  - Ответ `200`:
    ```json
    { "access_token": "<JWT>", "token_type": "bearer" }
    ```

- **Logout**
  - `POST /api/v1/auth/logout` — заглушка (для JWT настоящая инвалидция делается на стороне клиента).

Во все защищённые эндпойнты передаём заголовок:

```http
Authorization: Bearer <JWT>
```

### Доски (multi-board)

- `POST /api/v1/boards` — создать доску текущему пользователю:
  ```json
  { "code": "FORBIDDEN", "message": "Access denied", "details": {} }
  ```
- `GET /api/v1/boards` — список досок:
  - роль `user`: только свои;
  - роль `admin`: все доски.

### Карточки (`cards`)

Модель: `Card(title, column, order_idx, board_id, owner_id)`

Колонки (`column`): `backlog | todo | in_progress | done`.

- **Создать карточку**
  - `POST /api/v1/cards`
  - Тело:
    ```json
    {
      "title": "First idea",
      "column": "backlog",
      "order_idx": 0,
      "board_id": 1
    }
    ```

- **Получить карточку**
  - `GET /api/v1/cards/{id}`
  - Доступ: только владелец (`owner_id`) или роль `admin`.

- **Список карточек**
  - `GET /api/v1/cards?limit=&offset=&column=&board_id=`
  - Пагинация: `limit`, `offset`
  - Фильтрация (опц.): `column`, `board_id`
  - Для `user`: только свои карточки, для `admin`: все.

- **Обновить карточку**
  - `PATCH /api/v1/cards/{id}`
  - Частичное обновление:
    ```json
    { "title": "Updated", "column": "in_progress", "order_idx": 1 }
    ```

- **Удалить карточку**
  - `DELETE /api/v1/cards/{id}` → `204 No Content`

- **Переместить карточку**
  - `PATCH /api/v1/cards/{id}/move`
  - Тело:
    ```json
    { "column": "done", "order_idx": 5 }
    ```
- **Получить внешнюю оценку идеи**
  - `POST /api/v1/cards/{id}/score`
  - Тело:
    ```json
    { "context": "optional rationale" }
    ```
  - Возвращает `{ "score": <float> }` или `502`, если внешний сервис недоступен.

### Формат ошибок для `/api/v1`

Все ошибки Kanban API возвращаются в структурированном виде:

```json
{ "code": "SOME_ERROR", "message": "Human readable message", "details": {} }
```

Примеры:

- Неверные учётные данные:
  ```json
  { "code": "INVALID_CREDENTIALS", "message": "Incorrect email or password", "details": {} }
  ```
- Отсутствующий токен:
  ```json
  { "code": "UNAUTHORIZED", "message": "Not authenticated", "details": {} }
  ```
- Валидация тела запроса:
  ```json
  {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": { "errors": [ /* список ошибок Pydantic */ ] }
  }
  ```

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
