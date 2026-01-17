#!/bin/bash
# Скрипт для исправления прав на сокет Gunicorn
# Используется в ExecStartPost systemd service

SOCKET_PATH="/var/www/personnel_testing/personnel_testing.sock"
MAX_ATTEMPTS=20  # Максимальное количество попыток
WAIT_INTERVAL=0.5  # Интервал проверки в секундах

# Ждем создания сокета
attempt=0
while [ ! -S "$SOCKET_PATH" ] && [ $attempt -lt $MAX_ATTEMPTS ]; do
    sleep $WAIT_INTERVAL
    attempt=$((attempt + 1))
done

# Если сокет создан, исправляем права
if [ -S "$SOCKET_PATH" ]; then
    chown ubuntu:www-data "$SOCKET_PATH"
    chmod 660 "$SOCKET_PATH"
    exit 0
else
    echo "Warning: Socket not created within timeout"
    exit 1
fi
