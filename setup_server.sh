#!/bin/bash

# Скрипт для первоначальной настройки Ubuntu Server
# Запускать на сервере: bash setup_server.sh

set -e

echo "🚀 Настройка Ubuntu Server для Django проекта..."

# Обновление системы
echo "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка базовых пакетов
echo "📦 Установка базовых пакетов..."
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    python3-dev \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    nginx \
    git \
    curl \
    build-essential \
    supervisor \
    certbot \
    python3-certbot-nginx

# Настройка PostgreSQL
echo "🗄️ Настройка PostgreSQL..."
echo "Введите имя пользователя базы данных:"
read DB_USER
echo "Введите пароль для базы данных:"
read -s DB_PASSWORD

sudo -u postgres psql << EOF
CREATE DATABASE personnel_testing;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET timezone TO 'Europe/Moscow';
GRANT ALL PRIVILEGES ON DATABASE personnel_testing TO $DB_USER;
\q
EOF

echo "✅ База данных создана"

# Создание директории проекта
echo "📁 Создание директории проекта..."
sudo mkdir -p /var/www/personnel_testing
sudo mkdir -p /var/www/personnel_testing/logs
sudo mkdir -p /var/backups/personnel_testing

# Определение пользователя
if [ -z "$SUDO_USER" ]; then
    DEPLOY_USER=$(whoami)
else
    DEPLOY_USER=$SUDO_USER
fi

sudo chown -R $DEPLOY_USER:$DEPLOY_USER /var/www/personnel_testing
sudo chmod -R 755 /var/www/personnel_testing

echo "✅ Директории созданы"

# Настройка файрвола
echo "🔥 Настройка файрвола..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo "✅ Файрвол настроен"

echo ""
echo "✅ Настройка сервера завершена!"
echo ""
echo "Следующие шаги:"
echo "1. Клонируйте репозиторий: cd /var/www/personnel_testing && git clone <your-repo> ."
echo "2. Создайте виртуальное окружение: python3.11 -m venv venv"
echo "3. Активируйте окружение: source venv/bin/activate"
echo "4. Установите зависимости: pip install -r requirements.txt"
echo "5. Создайте .env файл с настройками"
echo "6. Примените миграции: python manage.py migrate"
echo "7. Соберите статические файлы: python manage.py collectstatic"
echo "8. Настройте Gunicorn и Nginx (см. DEPLOYMENT.md)"
