# Руководство по деплою на Ubuntu Server

## 📋 Содержание
1. [Подготовка сервера](#подготовка-сервера)
2. [Настройка проекта](#настройка-проекта)
3. [Настройка Gunicorn](#настройка-gunicorn)
4. [Настройка Nginx](#настройка-nginx)
5. [Настройка CI/CD](#настройка-cicd)
6. [Команды деплоя](#команды-деплоя)

---

## 🚀 Подготовка сервера

### 1. Подключение к серверу
```bash
ssh user@your-server-ip
```

### 2. Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Установка необходимых пакетов
```bash
# Python и инструменты
sudo apt install -y python3.11 python3.11-venv python3-pip python3-dev

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib libpq-dev

# Nginx
sudo apt install -y nginx

# Дополнительные инструменты
sudo apt install -y git curl build-essential
sudo apt install -y supervisor  # Для управления процессами (опционально)
```

### 4. Настройка PostgreSQL
```bash
# Войти в PostgreSQL
sudo -u postgres psql

# Создать базу данных и пользователя
CREATE DATABASE personnel_testing;
CREATE USER your_db_user WITH PASSWORD 'your_secure_password';
ALTER ROLE your_db_user SET client_encoding TO 'utf8';
ALTER ROLE your_db_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE your_db_user SET timezone TO 'Europe/Moscow';
GRANT ALL PRIVILEGES ON DATABASE personnel_testing TO your_db_user;
\q
```

### 5. Создание пользователя для приложения
```bash
# Создать пользователя (если нужно)
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG sudo deploy

# Создать директорию для проекта
sudo mkdir -p /var/www/personnel_testing
sudo chown deploy:deploy /var/www/personnel_testing
```

---

## 📦 Настройка проекта

### 1. Клонирование репозитория
```bash
cd /var/www/personnel_testing
git clone https://github.com/your-username/your-repo.git .
# или
git clone git@github.com:your-username/your-repo.git .
```

### 2. Создание виртуального окружения
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
```bash
# Создать .env файл
nano .env
```

Добавить следующие переменные:
```env
# Django
SECRET_KEY=your-super-secret-key-here-generate-with-openssl-rand-hex-32
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,server-ip
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Database
DB_NAME=personnel_testing
DB_USER=your_db_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# AI Services
OPENAI_API_KEY=your-openai-key
GEMINI_API_KEY=your-gemini-key

# Site
SITE_URL=https://your-domain.com

# CORS (если нужен фронтенд на другом домене)
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### 4. Применение миграций
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py init_tests  # Инициализация тестов
```

### 5. Создание суперпользователя
```bash
python manage.py createsuperuser
```

---

## 🔧 Настройка Gunicorn

### 1. Установка Gunicorn
```bash
pip install gunicorn
```

### 2. Создание systemd service
```bash
sudo nano /etc/systemd/system/personnel_testing.service
```

Содержимое файла:
```ini
[Unit]
Description=Personnel Testing Gunicorn daemon
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/var/www/personnel_testing
Environment="PATH=/var/www/personnel_testing/venv/bin"
ExecStart=/var/www/personnel_testing/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/personnel_testing/personnel_testing.sock \
    --access-logfile /var/www/personnel_testing/logs/access.log \
    --error-logfile /var/www/personnel_testing/logs/error.log \
    personnel_testing.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 3. Создание директории для логов
```bash
mkdir -p /var/www/personnel_testing/logs
chmod 755 /var/www/personnel_testing/logs
```

### 4. Запуск сервиса
```bash
sudo systemctl daemon-reload
sudo systemctl start personnel_testing
sudo systemctl enable personnel_testing
sudo systemctl status personnel_testing
```

---

## 🌐 Настройка Nginx

### 1. Создание конфигурации Nginx
```bash
sudo nano /etc/nginx/sites-available/personnel_testing
```

Содержимое:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Редирект на HTTPS (после настройки SSL)
    # return 301 https://$server_name$request_uri;

    # Для начала можно использовать HTTP
    location / {
        proxy_pass http://unix:/var/www/personnel_testing/personnel_testing.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Статические файлы
    location /static/ {
        alias /var/www/personnel_testing/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Медиа файлы
    location /media/ {
        alias /var/www/personnel_testing/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Максимальный размер загружаемых файлов
    client_max_body_size 10M;
}
```

### 2. Активация конфигурации
```bash
sudo ln -s /etc/nginx/sites-available/personnel_testing /etc/nginx/sites-enabled/
sudo nginx -t  # Проверка конфигурации
sudo systemctl restart nginx
```

### 3. Настройка SSL (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

---

## 🔄 Настройка CI/CD

### Вариант 1: GitHub Actions (рекомендуется)

Создать файл `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main  # или master

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /var/www/personnel_testing
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python manage.py migrate
            python manage.py collectstatic --noinput
            sudo systemctl restart personnel_testing
            sudo systemctl reload nginx
```

Настройка секретов в GitHub:
- Settings → Secrets and variables → Actions
- Добавить: `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY`

### Вариант 2: Локальный деплой скрипт

Создать файл `deploy.sh` на вашей машине:

```bash
#!/bin/bash

# Конфигурация
SERVER="user@your-server-ip"
PROJECT_DIR="/var/www/personnel_testing"
BRANCH="main"

echo "🚀 Начало деплоя..."

# 1. Push изменений в репозиторий
echo "📤 Отправка изменений в Git..."
git push origin $BRANCH

# 2. Подключение к серверу и деплой
echo "🔌 Подключение к серверу..."
ssh $SERVER << 'ENDSSH'
    cd $PROJECT_DIR
    echo "📥 Получение изменений из Git..."
    git pull origin main
    
    echo "🔧 Активация виртуального окружения..."
    source venv/bin/activate
    
    echo "📦 Установка зависимостей..."
    pip install -r requirements.txt --quiet
    
    echo "🗄️ Применение миграций..."
    python manage.py migrate --noinput
    
    echo "📁 Сбор статических файлов..."
    python manage.py collectstatic --noinput
    
    echo "🔄 Перезапуск сервисов..."
    sudo systemctl restart personnel_testing
    sudo systemctl reload nginx
    
    echo "✅ Деплой завершен!"
ENDSSH

echo "🎉 Деплой успешно завершен!"
```

Сделать скрипт исполняемым:
```bash
chmod +x deploy.sh
./deploy.sh
```

### Вариант 3: Использование Fabric (Python)

Установить Fabric:
```bash
pip install fabric
```

Создать файл `fabfile.py`:
```python
from fabric import Connection, task

SERVER = "user@your-server-ip"
PROJECT_DIR = "/var/www/personnel_testing"

@task
def deploy(c):
    """Деплой на сервер"""
    with Connection(SERVER) as conn:
        with conn.cd(PROJECT_DIR):
            print("📥 Получение изменений...")
            conn.run("git pull origin main")
            
            print("🔧 Активация виртуального окружения...")
            with conn.prefix("source venv/bin/activate"):
                print("📦 Установка зависимостей...")
                conn.run("pip install -r requirements.txt --quiet")
                
                print("🗄️ Применение миграций...")
                conn.run("python manage.py migrate --noinput")
                
                print("📁 Сбор статических файлов...")
                conn.run("python manage.py collectstatic --noinput")
        
        print("🔄 Перезапуск сервисов...")
        conn.sudo("systemctl restart personnel_testing")
        conn.sudo("systemctl reload nginx")
        
    print("✅ Деплой завершен!")
```

Использование:
```bash
fab deploy
```

---

## 📝 Полезные команды

### Просмотр логов
```bash
# Логи Gunicorn
sudo journalctl -u personnel_testing -f

# Логи Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Логи приложения
tail -f /var/www/personnel_testing/logs/error.log
```

### Управление сервисом
```bash
# Перезапуск
sudo systemctl restart personnel_testing

# Остановка
sudo systemctl stop personnel_testing

# Статус
sudo systemctl status personnel_testing

# Просмотр логов
sudo journalctl -u personnel_testing -n 50
```

### Обновление проекта вручную
```bash
cd /var/www/personnel_testing
source venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart personnel_testing
```

---

## 🔒 Безопасность

### 1. Настройка файрвола
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Настройка SSH ключей
```bash
# На вашей машине
ssh-keygen -t rsa -b 4096
ssh-copy-id user@your-server-ip

# Отключить парольную аутентификацию (опционально)
# sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
# sudo systemctl restart sshd
```

### 3. Регулярные бэкапы
```bash
# Создать скрипт бэкапа
nano /var/www/personnel_testing/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/personnel_testing"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Бэкап базы данных
pg_dump -U your_db_user personnel_testing > $BACKUP_DIR/db_$DATE.sql

# Бэкап медиа файлов
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/personnel_testing/media/

# Удаление старых бэкапов (старше 7 дней)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Бэкап завершен: $DATE"
```

Добавить в cron:
```bash
crontab -e
# Каждый день в 2:00
0 2 * * * /var/www/personnel_testing/backup.sh
```

---

## 🐛 Решение проблем

### Gunicorn не запускается
```bash
# Проверить логи
sudo journalctl -u personnel_testing -n 50

# Проверить права доступа
ls -la /var/www/personnel_testing/personnel_testing.sock
```

### Nginx 502 Bad Gateway
```bash
# Проверить, что Gunicorn запущен
sudo systemctl status personnel_testing

# Проверить права на socket
sudo chmod 666 /var/www/personnel_testing/personnel_testing.sock
```

### Статические файлы не загружаются
```bash
# Пересобрать статические файлы
python manage.py collectstatic --noinput --clear
```

---

## 📚 Дополнительные ресурсы

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
