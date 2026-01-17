# 🔍 Диагностика падений сайта

## 📋 Быстрая диагностика

### 1. Проверка статуса сервисов

```bash
# Статус Gunicorn
sudo systemctl status personnel_testing

# Статус Nginx
sudo systemctl status nginx

# Статус PostgreSQL
sudo systemctl status postgresql
```

### 2. Основные логи для проверки

#### Логи Gunicorn (самое важное!)
```bash
# Последние ошибки Gunicorn
sudo tail -n 100 /var/www/personnel_testing/logs/error.log

# Мониторинг в реальном времени
sudo tail -f /var/www/personnel_testing/logs/error.log

# Логи доступа Gunicorn
sudo tail -n 100 /var/www/personnel_testing/logs/access.log
```

#### Логи systemd (детальная информация о перезапусках)
```bash
# Последние записи
sudo journalctl -u personnel_testing -n 100

# С последнего перезапуска
sudo journalctl -u personnel_testing -b

# В реальном времени
sudo journalctl -u personnel_testing -f

# С временными метками
sudo journalctl -u personnel_testing --since "1 hour ago"
```

#### Логи Nginx
```bash
# Ошибки Nginx
sudo tail -n 100 /var/log/nginx/error.log

# Доступ к Nginx
sudo tail -n 100 /var/log/nginx/access.log

# Мониторинг в реальном времени
sudo tail -f /var/log/nginx/error.log
```

### 3. Проверка использования ресурсов

```bash
# Использование памяти и CPU
free -h
top
htop  # если установлен

# Использование диска
df -h

# Процессы Gunicorn
ps aux | grep gunicorn

# Использование памяти процессами
ps aux --sort=-%mem | head -20
```

### 4. Проверка сетевых соединений

```bash
# Активные соединения
netstat -tulpn | grep gunicorn
ss -tulpn | grep gunicorn

# Проверка сокета
ls -la /var/www/personnel_testing/personnel_testing.sock
```

---

## 🔴 Типичные причины падений

### 1. **WORKER TIMEOUT** (таймаут воркеров)

**Симптомы:**
- В логах: `[CRITICAL] WORKER TIMEOUT (pid:XXXX)`
- Воркеры перезапускаются
- Долгие запросы к Gemini API

**Решение:**
- Увеличить `timeout` в `gunicorn_config.py` (сейчас 300 секунд)
- Увеличить таймауты в Nginx
- Оптимизировать запросы к Gemini API

### 2. **Out of Memory (OOM)** (нехватка памяти)

**Симптомы:**
- В логах: `Worker (pid:XXXX) was sent SIGKILL! Perhaps out of memory?`
- Система убивает процессы
- Высокое использование памяти

**Решение:**
```bash
# Проверить использование памяти
free -h
ps aux --sort=-%mem | head -10

# Уменьшить количество воркеров в gunicorn_config.py
workers = 2  # вместо 4
```

### 3. **Проблемы с базой данных**

**Симптомы:**
- Ошибки подключения к PostgreSQL
- Медленные запросы
- Блокировки в БД

**Решение:**
```bash
# Проверить статус PostgreSQL
sudo systemctl status postgresql

# Проверить логи PostgreSQL
sudo tail -n 100 /var/log/postgresql/postgresql-*.log

# Проверить активные соединения
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

### 4. **Проблемы с правами доступа**

**Симптомы:**
- `Permission denied` в логах
- Не может записать в файлы логов
- Проблемы с сокетом

**Решение:**
```bash
# Проверить права на директории
ls -la /var/www/personnel_testing/
ls -la /var/www/personnel_testing/logs/

# Исправить права (замените deploy на вашего пользователя)
sudo chown -R deploy:deploy /var/www/personnel_testing/logs
sudo chmod -R 755 /var/www/personnel_testing/logs
```

### 5. **Проблемы с перезапуском воркеров**

**Симптомы:**
- Воркеры перезапускаются слишком часто
- Ошибки при перезапуске

**Решение:**
- Проверить `max_requests` в `gunicorn_config.py`
- Увеличить значение или отключить автоматический перезапуск

---

## 🛠️ Команды для быстрой диагностики

### Полная диагностика одной командой

```bash
echo "=== Статус сервисов ===" && \
sudo systemctl status personnel_testing --no-pager -l && \
echo -e "\n=== Последние ошибки Gunicorn ===" && \
sudo tail -n 50 /var/www/personnel_testing/logs/error.log && \
echo -e "\n=== Использование памяти ===" && \
free -h && \
echo -e "\n=== Процессы Gunicorn ===" && \
ps aux | grep gunicorn | grep -v grep
```

### Мониторинг в реальном времени

```bash
# В одном терминале - логи Gunicorn
sudo tail -f /var/www/personnel_testing/logs/error.log

# В другом терминале - логи systemd
sudo journalctl -u personnel_testing -f

# В третьем терминале - использование ресурсов
watch -n 2 'free -h && echo && ps aux --sort=-%mem | head -10'
```

---

## 📊 Анализ логов

### Поиск критических ошибок

```bash
# Все WORKER TIMEOUT
sudo grep "WORKER TIMEOUT" /var/www/personnel_testing/logs/error.log

# Все SIGKILL (убийство процессов)
sudo grep "SIGKILL" /var/www/personnel_testing/logs/error.log

# Все ошибки за последний час
sudo grep "$(date +%Y-%m-%d)" /var/www/personnel_testing/logs/error.log | grep ERROR

# Подсчет ошибок по типам
sudo grep ERROR /var/www/personnel_testing/logs/error.log | awk '{print $NF}' | sort | uniq -c | sort -rn
```

### Анализ частоты перезапусков

```bash
# Количество перезапусков воркеров за сегодня
sudo grep "Booting worker" /var/www/personnel_testing/logs/error.log | grep "$(date +%Y-%m-%d)" | wc -l

# Время между перезапусками
sudo grep "Booting worker" /var/www/personnel_testing/logs/error.log | tail -20
```

---

## 🔧 Автоматический мониторинг

### Использование скрипта мониторинга

Скрипт `monitor_site.sh` уже создан в корне проекта. Для настройки автоматического мониторинга:

```bash
# 1. Убедитесь, что скрипт исполняемый
chmod +x /var/www/personnel_testing/monitor_site.sh

# 2. Протестируйте вручную
/var/www/personnel_testing/monitor_site.sh

# 3. Добавьте в crontab для проверки каждые 5 минут
crontab -e
# Добавьте строку:
*/5 * * * * /var/www/personnel_testing/monitor_site.sh > /dev/null 2>&1

# 4. Или для более детального логирования (опционально)
*/5 * * * * /var/www/personnel_testing/monitor_site.sh >> /var/www/personnel_testing/logs/health_check.log 2>&1
```

### Просмотр логов мониторинга

```bash
# Последние записи
tail -n 50 /var/www/personnel_testing/logs/health_check.log

# Мониторинг в реальном времени
tail -f /var/www/personnel_testing/logs/health_check.log
```

### Старый скрипт (для справки)

Если нужен другой скрипт, создайте файл `/var/www/personnel_testing/health_check.sh`:

```bash
#!/bin/bash

# Проверка здоровья приложения
echo "=== Health Check $(date) ==="

# Проверка статуса сервиса
if systemctl is-active --quiet personnel_testing; then
    echo "✅ Gunicorn service: RUNNING"
else
    echo "❌ Gunicorn service: STOPPED"
    exit 1
fi

# Проверка сокета
if [ -S /var/www/personnel_testing/personnel_testing.sock ]; then
    echo "✅ Socket file: EXISTS"
else
    echo "❌ Socket file: MISSING"
    exit 1
fi

# Проверка последних ошибок (за последние 5 минут)
RECENT_ERRORS=$(sudo tail -n 100 /var/www/personnel_testing/logs/error.log | \
    grep "$(date +%Y-%m-%d)" | \
    grep -E "(ERROR|CRITICAL|TIMEOUT)" | \
    tail -5)

if [ -z "$RECENT_ERRORS" ]; then
    echo "✅ Recent errors: NONE"
else
    echo "⚠️  Recent errors found:"
    echo "$RECENT_ERRORS"
fi

# Проверка использования памяти
MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
echo "📊 Memory usage: ${MEM_USAGE}%"

if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
    echo "⚠️  WARNING: High memory usage!"
fi

echo "=== End Health Check ==="
```

Сделайте скрипт исполняемым:
```bash
chmod +x /var/www/personnel_testing/health_check.sh
```

---

## 📝 Что проверить при падении

1. ✅ **Статус сервиса** - `sudo systemctl status personnel_testing`
2. ✅ **Последние ошибки** - `sudo tail -n 100 /var/www/personnel_testing/logs/error.log`
3. ✅ **Логи systemd** - `sudo journalctl -u personnel_testing -n 50`
4. ✅ **Использование памяти** - `free -h`
5. ✅ **Активные процессы** - `ps aux | grep gunicorn`
6. ✅ **Права доступа** - `ls -la /var/www/personnel_testing/logs/`
7. ✅ **Сокет файл** - `ls -la /var/www/personnel_testing/personnel_testing.sock`
8. ✅ **Логи Nginx** - `sudo tail -n 50 /var/log/nginx/error.log`

---

## 🚨 Экстренное восстановление

Если сайт упал:

```bash
# 1. Перезапустить сервис
sudo systemctl restart personnel_testing

# 2. Проверить статус
sudo systemctl status personnel_testing

# 3. Если не запускается, проверить логи
sudo journalctl -u personnel_testing -n 50

# 4. Проверить конфигурацию
sudo /var/www/personnel_testing/venv/bin/gunicorn --check-config --config /var/www/personnel_testing/gunicorn_config.py personnel_testing.wsgi:application

# 5. Перезапустить Nginx
sudo systemctl restart nginx
```

---

## 📞 Полезные команды для отладки

```bash
# Проверить, какой пользователь запускает Gunicorn
ps aux | grep gunicorn | head -1

# Проверить переменные окружения процесса
sudo cat /proc/$(pgrep -f gunicorn | head -1)/environ | tr '\0' '\n'

# Проверить открытые файлы процесса
sudo lsof -p $(pgrep -f gunicorn | head -1) | head -20

# Проверить использование памяти процессом
sudo pmap -x $(pgrep -f gunicorn | head -1) | tail -1
```
