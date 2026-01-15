# Конфигурация Gunicorn для продакшн
import multiprocessing

# Базовые настройки
bind = "unix:/var/www/personnel_testing/personnel_testing.sock"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Логирование
accesslog = "/var/www/personnel_testing/logs/access.log"
errorlog = "/var/www/personnel_testing/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Безопасность
user = "deploy"
group = "deploy"
umask = 0o007

# Перезапуск при изменении кода (для разработки)
# reload = True

# Предзагрузка приложения для экономии памяти
preload_app = True

# Максимальное количество запросов перед перезапуском воркера
max_requests = 1000
max_requests_jitter = 50
