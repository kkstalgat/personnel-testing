#!/bin/bash
# Скрипт для исправления прав на сокет Gunicorn
# Используется в ExecStartPost systemd service

SOCKET_PATH="/var/www/personnel_testing/personnel_testing.sock"
MAX_ATTEMPTS=30  # Максимальное количество попыток (15 секунд)
WAIT_INTERVAL=0.5  # Интервал проверки в секундах

# Ждем создания сокета (используем полные пути)
attempt=0
while [ $attempt -lt $MAX_ATTEMPTS ]; do
    if [ -S "$SOCKET_PATH" ]; then
        break
    fi
    /bin/sleep $WAIT_INTERVAL
    attempt=$((attempt + 1))
done

# Если сокет создан, исправляем права (используем полные пути)
if [ -S "$SOCKET_PATH" ]; then
    /bin/chown ubuntu:www-data "$SOCKET_PATH" 2>/dev/null || true
    /bin/chmod 660 "$SOCKET_PATH" 2>/dev/null || true
    exit 0
else
    # Если сокет не создан, это не критично - возможно Gunicorn еще запускается
    # Не возвращаем ошибку, чтобы не блокировать запуск сервиса
    exit 0
fi
