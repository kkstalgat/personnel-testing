# API Документация

## Базовый URL
```
http://localhost:8000/api/
```

## Аутентификация

Для большинства endpoints требуется аутентификация через сессию Django или токен.

## Accounts API

### Регистрация пользователя
**POST** `/accounts/users/register/`

**Тело запроса:**
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securepassword123",
  "phone": "+79991234567",
  "company_name": "ООО Тестовая Компания"
}
```

**Ответ:**
```json
{
  "message": "Регистрация успешна. Проверьте email для подтверждения."
}
```

### Подтверждение email
**POST** `/accounts/users/verify_email/`

**Тело запроса:**
```json
{
  "token": "verification_token_from_email"
}
```

**Ответ:**
```json
{
  "message": "Email успешно подтвержден"
}
```

### Авторизация
**POST** `/accounts/users/login/`

**Тело запроса:**
```json
{
  "email": "test@example.com",
  "password": "securepassword123"
}
```

**Ответ:**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "phone": "+79991234567",
  "company_name": "ООО Тестовая Компания",
  "is_email_verified": true,
  "is_phone_verified": false,
  "date_joined": "2024-01-01T12:00:00Z"
}
```

### Получить профиль
**GET** `/accounts/users/profile/`

**Требует:** Аутентификация

**Ответ:**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  ...
}
```

### Список тарифных планов
**GET** `/accounts/subscription-plans/`

**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Базовый",
    "description": "Базовый тарифный план",
    "price": "1000.00",
    "duration_days": 30,
    "tests_count": 10
  }
]
```

### Текущая подписка
**GET** `/accounts/subscriptions/current/`

**Требует:** Аутентификация

**Ответ:**
```json
{
  "id": 1,
  "plan": {
    "id": 1,
    "name": "Базовый",
    ...
  },
  "start_date": "2024-01-01T12:00:00Z",
  "end_date": "2024-01-31T12:00:00Z",
  "is_active": true,
  "remaining_tests": 8
}
```

## Tests API

### Список доступных тестов
**GET** `/tests/tests/`

**Ответ:**
```json
[
  {
    "id": 1,
    "test_type": "iq_test",
    "name": "Тест Равена (IQ)",
    "description": "...",
    "duration_minutes": 20,
    "questions_count": 60
  }
]
```

### Создать сессию тестирования
**POST** `/tests/sessions/create_session/`

**Требует:** Аутентификация

**Тело запроса:**
```json
{
  "test_id": 1,
  "candidate_email": "candidate@example.com",
  "candidate_name": "Иван Иванов",
  "candidate_age": 30
}
```

**Ответ:**
```json
{
  "id": "uuid-session-id",
  "test": {
    "id": 1,
    "name": "Тест Равена (IQ)",
    ...
  },
  "candidate_email": "candidate@example.com",
  "status": "pending",
  ...
}
```

**Примечание:** На указанный email будет отправлена ссылка для прохождения теста.

### Получить сессию тестирования
**GET** `/tests/sessions/{session_id}/`

**Параметры:**
- `session_id` - UUID сессии

**Ответ:**
```json
{
  "id": "uuid-session-id",
  "test": {...},
  "candidate_email": "candidate@example.com",
  "status": "pending",
  "answers_count": 0
}
```

### Начать тест
**POST** `/tests/sessions/{session_id}/start/`

**Ответ:**
```json
{
  "id": "uuid-session-id",
  "status": "in_progress",
  "started_at": "2024-01-01T12:00:00Z",
  ...
}
```

### Отправить ответ на вопрос
**POST** `/tests/sessions/{session_id}/submit_answer/`

**Тело запроса:**
```json
{
  "question_number": 1,
  "answer_value": 4,
  "series": "A"
}
```

**Для IQ теста:** `answer_value` - число от 1 до 6
**Для теста личностных качеств:** `answer_value` - "Да", "Нет", "Иногда"
**Для теста продуктивности:** `answer_value` - текст

**Ответ:**
```json
{
  "id": 1,
  "session": "uuid-session-id",
  "question_number": 1,
  "answer_value": "4",
  "series": "A",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Завершить тест
**POST** `/tests/sessions/{session_id}/complete/`

**Ответ:**
```json
{
  "id": 1,
  "session": {...},
  "raw_score": 45,
  "final_score": 45.0,
  "iq_score": 105,
  "iq_level": "Средний интеллект",
  "report": "## ОТЧЕТ ПО ТЕСТУ ИНТЕЛЛЕКТА...",
  "report_json": {...},
  "is_processed": true,
  "processed_at": "2024-01-01T12:20:00Z"
}
```

### Мои сессии тестирования
**GET** `/tests/sessions/my_sessions/`

**Требует:** Аутентификация

**Ответ:**
```json
[
  {
    "id": "uuid-session-id",
    "test": {...},
    "candidate_email": "candidate@example.com",
    "status": "completed",
    ...
  }
]
```

### Результаты тестов
**GET** `/tests/results/`

**Требует:** Аутентификация

**Ответ:**
```json
[
  {
    "id": 1,
    "session": {...},
    "raw_score": 45,
    "iq_score": 105,
    "report": "...",
    ...
  }
]
```

## Коды ошибок

- `400` - Неверный запрос
- `401` - Не авторизован
- `404` - Не найдено
- `500` - Внутренняя ошибка сервера

## Примеры использования

### Python (requests)
```python
import requests

# Регистрация
response = requests.post('http://localhost:8000/api/accounts/users/register/', json={
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'password123'
})

# Авторизация
session = requests.Session()
response = session.post('http://localhost:8000/api/accounts/users/login/', json={
    'email': 'test@example.com',
    'password': 'password123'
})

# Создание сессии тестирования
response = session.post('http://localhost:8000/api/tests/sessions/create_session/', json={
    'test_id': 1,
    'candidate_email': 'candidate@example.com',
    'candidate_age': 30
})
```

### JavaScript (fetch)
```javascript
// Регистрация
fetch('http://localhost:8000/api/accounts/users/register/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'testuser',
    email: 'test@example.com',
    password: 'password123'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```
