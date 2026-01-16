# 🏃 Настройка Self-hosted GitHub Actions Runner

## Преимущества Self-hosted Runner

- ✅ Не нужен внешний SSH доступ
- ✅ Работает напрямую на сервере
- ✅ Быстрее, чем через SSH
- ✅ Полный контроль над окружением

---

## Шаг 1: Получить токен регистрации

1. Откройте репозиторий: https://github.com/kkstalgat/personnel-testing
2. Перейдите: **Settings** → **Actions** → **Runners**
3. Нажмите **"New self-hosted runner"**
4. Выберите:
   - **Operating system**: Linux
   - **Architecture**: X64
5. Скопируйте команды, которые покажет GitHub (они будут использованы ниже)

---

## Шаг 2: Установка Runner на сервере

Выполните на сервере (Ubuntu):

```bash
# 1. Создать директорию для runner
mkdir -p ~/actions-runner && cd ~/actions-runner

# 2. Скачать последнюю версию runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# 3. Распаковать
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# 4. Настроить runner (используйте токен из GitHub)
./config.sh --url https://github.com/kkstalgat/personnel-testing --token YOUR_TOKEN_HERE
```

При настройке:
- **Enter the name of the runner**: `production-server` (или любое имя)
- **Enter the name of the work folder**: нажмите Enter (по умолчанию `_work`)
- **Enter additional labels**: нажмите Enter (или добавьте `self-hosted,linux,x64`)

---

## Шаг 3: Установить Runner как service

```bash
# Установить как systemd service
sudo ./svc.sh install

# Запустить service
sudo ./svc.sh start

# Проверить статус
sudo ./svc.sh status
```

---

## Шаг 4: Проверка работы

1. Откройте: https://github.com/kkstalgat/personnel-testing/settings/actions/runners
2. Должен появиться runner со статусом "Idle" (зеленый)

---

## Шаг 5: Обновить workflow

Workflow файл уже обновлен для использования self-hosted runner.

---

## Полезные команды

```bash
# Остановить runner
sudo ./svc.sh stop

# Запустить runner
sudo ./svc.sh start

# Перезапустить runner
sudo ./svc.sh restart

# Проверить статус
sudo ./svc.sh status

# Посмотреть логи
sudo journalctl -u actions.runner.* -f

# Удалить runner (если нужно)
sudo ./svc.sh stop
sudo ./svc.sh uninstall
./config.sh remove --token YOUR_TOKEN
```

---

## Обновление Runner

```bash
cd ~/actions-runner

# Остановить
sudo ./svc.sh stop

# Скачать новую версию
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Распаковать (перезапишет старые файлы)
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Запустить
sudo ./svc.sh start
```

---

## Решение проблем

### Runner не появляется в GitHub

- Проверьте, что токен правильный
- Проверьте интернет-соединение на сервере
- Проверьте логи: `sudo journalctl -u actions.runner.* -n 50`

### Runner не запускается

```bash
# Проверить статус
sudo systemctl status actions.runner.*.service

# Посмотреть логи
sudo journalctl -u actions.runner.* -f
```

### Workflow не запускается на runner

- Убедитесь, что в workflow указано `runs-on: self-hosted`
- Проверьте, что runner имеет правильные labels
