# 🚀 Быстрый старт деплоя

## Шаг 1: Подготовка сервера

На Ubuntu Server выполните:
```bash
bash setup_server.sh
```

Или вручную:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip python3-dev postgresql postgresql-contrib libpq-dev nginx git
```

## Шаг 2: Настройка базы данных

```bash
sudo -u postgres psql
CREATE DATABASE personnel_testing;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE personnel_testing TO your_user;
\q
```

## Шаг 3: Клонирование проекта

```bash
cd /var/www
sudo mkdir -p personnel_testing
sudo chown $USER:$USER personnel_testing
cd personnel_testing
git clone <your-repo-url> .
```

## Шаг 4: Настройка окружения

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Шаг 5: Создание .env файла

```bash
nano .env
```

Добавьте все необходимые переменные (см. DEPLOYMENT.md)

## Шаг 6: Настройка Gunicorn

```bash
# Скопируйте systemd_service.example
sudo cp systemd_service.example /etc/systemd/system/personnel_testing.service
# Отредактируйте под ваши нужды
sudo nano /etc/systemd/system/personnel_testing.service
sudo systemctl daemon-reload
sudo systemctl enable personnel_testing
sudo systemctl start personnel_testing
```

## Шаг 7: Настройка Nginx

```bash
sudo cp nginx.conf.example /etc/nginx/sites-available/personnel_testing
sudo nano /etc/nginx/sites-available/personnel_testing
# Измените your-domain.com на ваш домен
sudo ln -s /etc/nginx/sites-available/personnel_testing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Шаг 8: Инициализация проекта

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py init_tests
```

## Шаг 9: Настройка SSL (опционально)

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Деплой с вашей машины

### Вариант 1: Использование deploy.sh

1. Отредактируйте `deploy.sh` - укажите ваш сервер
2. На Windows используйте Git Bash или WSL
3. Запустите: `bash deploy.sh`

### Вариант 2: GitHub Actions

1. Добавьте секреты в GitHub:
   - Settings → Secrets → Actions
   - `SERVER_HOST` - IP или домен сервера
   - `SERVER_USER` - пользователь для SSH
   - `SERVER_SSH_KEY` - приватный SSH ключ

2. При каждом push в main ветку будет автоматический деплой

### Вариант 3: Ручной деплой

```bash
# На сервере
cd /var/www/personnel_testing
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart personnel_testing
sudo systemctl reload nginx
```

## Полезные команды

```bash
# Статус сервиса
sudo systemctl status personnel_testing

# Логи
sudo journalctl -u personnel_testing -f

# Перезапуск
sudo systemctl restart personnel_testing

# Проверка Nginx
sudo nginx -t
sudo systemctl status nginx
```

## Решение проблем

- **502 Bad Gateway**: Проверьте, что Gunicorn запущен
- **Статические файлы не загружаются**: `python manage.py collectstatic --noinput`
- **Ошибки миграций**: Проверьте подключение к БД в .env

Подробная документация в `DEPLOYMENT.md`
