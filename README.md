# Сервис тестирования персонала

Веб-приложение для тестирования персонала на основе Django и PostgreSQL.

## Описание

Сервис предоставляет возможность:
- Регистрации и авторизации пользователей (HR-специалистов)
- Покупки подписок и тарифных планов
- Создания сессий тестирования для соискателей
- Прохождения трех типов тестов:
  - Тест Равена (IQ-тест) - 60 вопросов, 20 минут
  - Оценка личностных качеств - 200 вопросов, 35 минут
  - Оценка продуктивности - 20 вопросов, 10 минут
- Автоматической обработки результатов тестов
- Отправки результатов на email

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd testing
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

5. Настройте базу данных PostgreSQL и обновите настройки в `.env`.

6. Выполните миграции:
```bash
python manage.py makemigrations
python manage.py migrate
```

7. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

8. Инициализируйте тесты:
```bash
python manage.py init_tests
```

9. Запустите сервер разработки:
```bash
python manage.py runserver
```

## API Endpoints

### Accounts

- `POST /api/accounts/users/register/` - Регистрация пользователя
- `POST /api/accounts/users/verify_email/` - Подтверждение email
- `POST /api/accounts/users/login/` - Авторизация
- `GET /api/accounts/users/profile/` - Профиль пользователя (требует авторизации)
- `GET /api/accounts/subscription-plans/` - Список тарифных планов
- `GET /api/accounts/subscriptions/current/` - Текущая подписка

### Tests

- `GET /api/tests/tests/` - Список доступных тестов
- `POST /api/tests/sessions/create_session/` - Создать сессию тестирования (требует авторизации)
- `GET /api/tests/sessions/{id}/` - Получить сессию тестирования
- `POST /api/tests/sessions/{id}/start/` - Начать тест
- `POST /api/tests/sessions/{id}/submit_answer/` - Отправить ответ на вопрос
- `POST /api/tests/sessions/{id}/complete/` - Завершить тест и получить результаты
- `GET /api/tests/sessions/my_sessions/` - Мои сессии (требует авторизации)
- `GET /api/tests/results/` - Результаты тестов (требует авторизации)

## Структура проекта

```
personnel_testing/
├── accounts/          # Приложение для работы с пользователями и подписками
├── tests/            # Приложение для тестирования
│   ├── data/         # Данные для тестов
│   └── services/     # Сервисы обработки результатов
├── personnel_testing/ # Основные настройки проекта
└── templates/        # HTML шаблоны
```

## Тесты

### Тест Равена (IQ-тест)
- 60 вопросов в 5 сериях (A, B, C, D, E)
- Длительность: 20 минут
- Ответы: числа от 1 до 6
- Автоматический расчет IQ с учетом возраста

### Оценка личностных качеств
- 200 вопросов в 10 блоках
- Длительность: 35 минут
- Ответы: Да/Нет/Иногда
- Оценка 10 качеств: внимательность, позитивность, самообладание и др.

### Оценка продуктивности
- 20 вопросов
- Длительность: 10 минут
- Открытые ответы
- Анализ ориентации на результат vs процесс

## Админ-панель

Доступна по адресу `/admin/` после создания суперпользователя.

## Лицензия

MIT
