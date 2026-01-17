#!/bin/bash
# Скрипт для мониторинга здоровья сайта
# Использование: ./monitor_site.sh или добавить в crontab

LOG_FILE="/var/www/personnel_testing/logs/health_check.log"
MAX_LOG_SIZE=10485760  # 10MB

# Очистка лога если он слишком большой
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null) -gt $MAX_LOG_SIZE ]; then
    > "$LOG_FILE"
fi

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_service() {
    if systemctl is-active --quiet personnel_testing; then
        return 0
    else
        return 1
    fi
}

check_socket() {
    if [ -S /var/www/personnel_testing/personnel_testing.sock ]; then
        return 0
    else
        return 1
    fi
}

check_recent_errors() {
    ERROR_LOG="/var/www/personnel_testing/logs/error.log"
    if [ ! -f "$ERROR_LOG" ]; then
        return 0
    fi
    
    # Проверяем критические ошибки за последние 5 минут
    RECENT_CRITICAL=$(tail -n 200 "$ERROR_LOG" | grep -E "(CRITICAL|WORKER TIMEOUT|SIGKILL)" | tail -1)
    if [ -n "$RECENT_CRITICAL" ]; then
        log_message "⚠️  WARNING: Critical error found: $RECENT_CRITICAL"
        return 1
    fi
    return 0
}

check_memory() {
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    MEM_INT=${MEM_USAGE%.*}
    
    if [ "$MEM_INT" -gt 90 ]; then
        log_message "⚠️  WARNING: High memory usage: ${MEM_USAGE}%"
        return 1
    fi
    return 0
}

check_disk_space() {
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        log_message "⚠️  WARNING: High disk usage: ${DISK_USAGE}%"
        return 1
    fi
    return 0
}

# Основная проверка
log_message "=== Health Check Started ==="

ALL_OK=true

# Проверка сервиса
if check_service; then
    log_message "✅ Gunicorn service: RUNNING"
else
    log_message "❌ Gunicorn service: STOPPED"
    ALL_OK=false
fi

# Проверка сокета
if check_socket; then
    log_message "✅ Socket file: EXISTS"
else
    log_message "❌ Socket file: MISSING"
    ALL_OK=false
fi

# Проверка памяти
if check_memory; then
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    log_message "✅ Memory usage: ${MEM_USAGE}%"
else
    ALL_OK=false
fi

# Проверка диска
if check_disk_space; then
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}')
    log_message "✅ Disk usage: ${DISK_USAGE}"
else
    ALL_OK=false
fi

# Проверка ошибок
if check_recent_errors; then
    log_message "✅ Recent errors: NONE"
else
    ALL_OK=false
fi

# Проверка процессов Gunicorn
# Используем несколько методов для надежности
GUNICORN_PIDS=$(pgrep -f "gunicorn.*personnel_testing.wsgi" 2>/dev/null | wc -l)

# Альтернативный метод через ps, если pgrep не работает
if [ "$GUNICORN_PIDS" -eq 0 ]; then
    GUNICORN_PIDS=$(ps aux | grep -E "[g]unicorn.*personnel_testing" | wc -l)
fi

if [ "$GUNICORN_PIDS" -gt 1 ]; then
    # Вычитаем master процесс, остальные - воркеры
    WORKER_COUNT=$((GUNICORN_PIDS - 1))
    log_message "✅ Gunicorn workers: $WORKER_COUNT (total processes: $GUNICORN_PIDS)"
elif [ "$GUNICORN_PIDS" -eq 1 ]; then
    log_message "⚠️  WARNING: Only master process found, no workers! (total processes: $GUNICORN_PIDS)"
    ALL_OK=false
else
    # Если процессов нет, но сервис работает - возможно проблема
    if systemctl is-active --quiet personnel_testing; then
        log_message "⚠️  WARNING: Service is active but no gunicorn processes found!"
        ALL_OK=false
    else
        log_message "❌ Gunicorn workers: 0 (no gunicorn processes found)"
        ALL_OK=false
    fi
fi

if [ "$ALL_OK" = true ]; then
    log_message "✅ All checks passed"
    log_message "=== Health Check Completed: OK ==="
    exit 0
else
    log_message "❌ Some checks failed"
    log_message "=== Health Check Completed: FAILED ==="
    exit 1
fi
