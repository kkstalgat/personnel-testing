#!/bin/bash
# Скрипт для проверки логов email
# Использование: ./check_email_logs.sh

echo "=== Проверка логов email ==="
echo ""

# Логи Gunicorn
LOG_FILE="/var/www/personnel_testing/logs/error.log"

if [ -f "$LOG_FILE" ]; then
    echo "📋 Последние ошибки email в логах Gunicorn:"
    echo "---"
    sudo grep -i "email\|mail\|smtp\|550\|535\|permission" "$LOG_FILE" | tail -30
    echo ""
    
    echo "📋 Последние 50 строк логов (для контекста):"
    echo "---"
    sudo tail -n 50 "$LOG_FILE"
else
    echo "⚠️  Файл логов не найден: $LOG_FILE"
fi

echo ""
echo "=== Проверка systemd логов ==="
echo "---"
sudo journalctl -u personnel_testing -n 100 | grep -i "email\|mail\|smtp" || echo "Нет записей об email в systemd логах"

echo ""
echo "=== Проверка настроек email ==="
echo "---"
cd /var/www/personnel_testing 2>/dev/null || echo "Не удалось перейти в директорию проекта"
if [ -f ".env" ]; then
    echo "Настройки email в .env:"
    grep -E "EMAIL|SMTP" .env | sed 's/PASSWORD=.*/PASSWORD=***/' || echo "Настройки email не найдены в .env"
else
    echo "⚠️  Файл .env не найден"
fi
