# 📧 Настройка отправки email

## 🔍 Проверка текущих настроек

На сервере выполните:

```bash
cd /var/www/personnel_testing
source venv/bin/activate

# Проверьте текущие настройки email
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'personnel_testing.settings')
import django
django.setup()
from django.conf import settings
print('EMAIL_BACKEND:', settings.EMAIL_BACKEND)
print('EMAIL_HOST:', settings.EMAIL_HOST)
print('EMAIL_PORT:', settings.EMAIL_PORT)
print('EMAIL_HOST_USER:', settings.EMAIL_HOST_USER or '(не задан)')
print('DEFAULT_FROM_EMAIL:', settings.DEFAULT_FROM_EMAIL)
"
```

## 🧪 Тестирование отправки email

### Вариант 1: Использование скрипта test_email.py

```bash
cd /var/www/personnel_testing
source venv/bin/activate
python test_email.py
```

### Вариант 2: Через Django shell

```bash
cd /var/www/personnel_testing
source venv/bin/activate
python manage.py shell
```

В shell выполните:

```python
from django.core.mail import send_mail
from django.conf import settings

# Проверьте настройки
print("EMAIL_BACKEND:", settings.EMAIL_BACKEND)
print("EMAIL_HOST:", settings.EMAIL_HOST)
print("EMAIL_HOST_USER:", settings.EMAIL_HOST_USER)
print("DEFAULT_FROM_EMAIL:", settings.DEFAULT_FROM_EMAIL)

# Тестовая отправка
send_mail(
    'Тестовое письмо',
    'Это тестовое письмо от IQ System.',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@example.com'],  # Замените на ваш email
    fail_silently=False,
)
```

## ⚙️ Настройка email в .env

Откройте файл `.env` на сервере:

```bash
nano /var/www/personnel_testing/.env
```

### Для Gmail

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Важно для Gmail:**
1. Используйте **App Password**, а не обычный пароль
2. Включите двухфакторную аутентификацию
3. Создайте App Password: https://myaccount.google.com/apppasswords
4. `DEFAULT_FROM_EMAIL` должен совпадать с `EMAIL_HOST_USER`

### Для других SMTP серверов

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587  # или 465 для SSL
EMAIL_USE_TLS=True  # True для порта 587
EMAIL_USE_SSL=False  # True для порта 465
EMAIL_HOST_USER=your-email@your-domain.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@your-domain.com
```

## 🔧 Исправление ошибки "Client does not have permissions to send as this sender"

Эта ошибка возникает, когда `DEFAULT_FROM_EMAIL` не совпадает с `EMAIL_HOST_USER` или у учетной записи нет прав.

### Решение:

1. **Убедитесь, что `DEFAULT_FROM_EMAIL` совпадает с `EMAIL_HOST_USER`:**
   ```env
   EMAIL_HOST_USER=your-email@gmail.com
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```

2. **Для Gmail:** Используйте тот же email в обоих полях

3. **Для корпоративной почты:** Убедитесь, что учетная запись имеет права на отправку от имени `DEFAULT_FROM_EMAIL`

## 📝 Проверка после настройки

После изменения `.env` файла:

```bash
# Перезапустите Gunicorn
sudo systemctl restart personnel_testing

# Проверьте настройки
cd /var/www/personnel_testing
source venv/bin/activate
python test_email.py
```

## 🐛 Диагностика проблем

### Ошибка: "535 Authentication failed"

**Причина:** Неправильный пароль или username

**Решение:**
- Для Gmail: используйте App Password
- Проверьте правильность `EMAIL_HOST_USER` и `EMAIL_HOST_PASSWORD`

### Ошибка: "550 Client does not have permissions to send as this sender"

**Причина:** `DEFAULT_FROM_EMAIL` не совпадает с `EMAIL_HOST_USER`

**Решение:**
```env
EMAIL_HOST_USER=your-email@gmail.com
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### Ошибка: "Connection timeout" или "Connection refused"

**Причина:** Проблемы с подключением к SMTP серверу

**Решение:**
- Проверьте `EMAIL_HOST` и `EMAIL_PORT`
- Проверьте firewall на сервере
- Проверьте, доступен ли SMTP сервер из сети

### Email не отправляется, но ошибок нет

**Причина:** Используется `console.EmailBackend`

**Решение:**
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

## 📊 Логирование email

Для отладки можно временно включить логирование всех email в консоль:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Это выведет все письма в логи Gunicorn вместо реальной отправки.

## ✅ Чеклист настройки

- [ ] `EMAIL_BACKEND` установлен в `django.core.mail.backends.smtp.EmailBackend`
- [ ] `EMAIL_HOST` указан правильно
- [ ] `EMAIL_PORT` указан правильно (587 для TLS, 465 для SSL)
- [ ] `EMAIL_USE_TLS` или `EMAIL_USE_SSL` настроены правильно
- [ ] `EMAIL_HOST_USER` указан
- [ ] `EMAIL_HOST_PASSWORD` указан (для Gmail - App Password)
- [ ] `DEFAULT_FROM_EMAIL` совпадает с `EMAIL_HOST_USER`
- [ ] Gunicorn перезапущен после изменений
- [ ] Тестовая отправка прошла успешно
