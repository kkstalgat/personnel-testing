# Конфигурация Gunicorn для продакшн
import multiprocessing

# Базовые настройки
bind = "unix:/var/www/personnel_testing/personnel_testing.sock"
# Уменьшить количество воркеров для экономии памяти
cpu_count = multiprocessing.cpu_count()
workers = min(cpu_count * 2 + 1, 4)  # Максимум 4 воркера

worker_class = "sync"
worker_connections = 1000
timeout = 300  # Увеличить таймаут до 5 минут для длинных запросов к Gemini API
keepalive = 2

# Логирование
accesslog = "/var/www/personnel_testing/logs/access.log"
errorlog = "/var/www/personnel_testing/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Безопасность
# user и group управляются через systemd service
# user = "ubuntu"  # Раскомментируйте и укажите нужного пользователя, если нужно
# group = "ubuntu"
umask = 0o022  # Более мягкие права для создания файлов

# Перезапуск при изменении кода (для разработки)
# reload = True

# Предзагрузка приложения для экономии памяти
preload_app = True

# Максимальное количество запросов перед перезапуском воркера
max_requests = 1000
max_requests_jitter = 50
