#!/bin/bash

# Скрипт для деплоя проекта на сервер
# Использование: ./deploy.sh

# ============================================
# КОНФИГУРАЦИЯ - ИЗМЕНИТЕ ПОД ВАШ СЕРВЕР
# ============================================
SERVER="user@your-server-ip"  # Замените на ваш сервер
PROJECT_DIR="/var/www/personnel_testing"
BRANCH="main"  # или master
USE_SSH_KEY=true  # Использовать SSH ключ (true) или пароль (false)

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
info() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Проверка наличия изменений
if [ -n "$(git status -s)" ]; then
    warning "Есть незакоммиченные изменения!"
    read -p "Продолжить деплой? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🚀 Начало деплоя на сервер..."

# 1. Проверка подключения к серверу
info "Проверка подключения к серверу..."
if ssh -o ConnectTimeout=5 $SERVER "echo 'Connected'" > /dev/null 2>&1; then
    info "Подключение к серверу успешно"
else
    error "Не удалось подключиться к серверу. Проверьте настройки."
    exit 1
fi

# 2. Push изменений в репозиторий (если используется Git)
if git rev-parse --git-dir > /dev/null 2>&1; then
    info "Отправка изменений в Git..."
    CURRENT_BRANCH=$(git branch --show-current)
    
    if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
        warning "Вы находитесь на ветке $CURRENT_BRANCH, а не на $BRANCH"
        read -p "Продолжить? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    git push origin $BRANCH
    if [ $? -ne 0 ]; then
        error "Ошибка при отправке в Git"
        exit 1
    fi
    info "Изменения отправлены в Git"
else
    warning "Не обнаружен Git репозиторий, пропускаем push"
fi

# 3. Деплой на сервер
info "Подключение к серверу и выполнение деплоя..."

ssh $SERVER << 'ENDSSH'
    set -e  # Остановка при ошибке
    
    cd /var/www/personnel_testing || {
        echo "Ошибка: директория проекта не найдена"
        exit 1
    }
    
    echo "📥 Получение изменений из Git..."
    git fetch origin
    git reset --hard origin/main || git reset --hard origin/master
    
    echo "🔧 Активация виртуального окружения..."
    if [ ! -d "venv" ]; then
        echo "Создание виртуального окружения..."
        python3.11 -m venv venv
    fi
    source venv/bin/activate
    
    echo "📦 Обновление зависимостей..."
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    
    echo "🗄️ Применение миграций базы данных..."
    python manage.py migrate --noinput
    
    echo "📁 Сбор статических файлов..."
    python manage.py collectstatic --noinput --clear
    
    echo "🔄 Перезапуск сервисов..."
    sudo systemctl restart personnel_testing
    sudo systemctl reload nginx
    
    echo "✅ Деплой на сервере завершен!"
ENDSSH

if [ $? -eq 0 ]; then
    info "Деплой успешно завершен!"
    echo ""
    echo "Проверьте работу сайта:"
    echo "  - Статус сервиса: ssh $SERVER 'sudo systemctl status personnel_testing'"
    echo "  - Логи: ssh $SERVER 'sudo journalctl -u personnel_testing -n 50'"
else
    error "Ошибка при деплое на сервер"
    exit 1
fi
