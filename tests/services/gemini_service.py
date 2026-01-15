"""
Сервис для работы с Gemini 2.5 Flash API
"""
import os
import json
from django.conf import settings

try:
    # Используем старый пакет google.generativeai (новый google.genai имеет другой API)
    # TODO: Обновить на google.genai после изучения нового API
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    USE_NEW_API = False
except ImportError:
    GEMINI_AVAILABLE = False
    USE_NEW_API = False
    genai = None


def get_gemini_client():
    """Получить клиент Gemini API"""
    if not GEMINI_AVAILABLE:
        raise ImportError("Библиотека google-generativeai не установлена. Установите: pip install google-generativeai")
    
    api_key = getattr(settings, 'GEMINI_API_KEY', os.getenv('GEMINI_API_KEY'))
    if not api_key:
        raise ValueError("GEMINI_API_KEY не установлен в настройках или переменных окружения")
    
    # Используем старый API (google.generativeai)
    # Предупреждение о deprecation можно игнорировать, API все еще работает
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    return model


def call_gemini(prompt, system_instruction=None, max_retries=3, retry_delay=5, timeout=240):
    """
    Вызвать Gemini API с промптом
    
    Args:
        prompt: Текст промпта
        system_instruction: Системная инструкция (опционально)
        max_retries: Максимальное количество попыток при ошибке квоты
        retry_delay: Задержка между попытками в секундах
        timeout: Таймаут запроса в секундах (по умолчанию 240 секунд = 4 минуты)
    
    Returns:
        str: Ответ от Gemini
    """
    import time
    
    model = get_gemini_client()
    
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 32768,  # Увеличено для длинных отчетов (максимум для gemini-2.5-flash)
    }
    
    last_error = None
    for attempt in range(max_retries):
        try:
            # Используем старый API (google.generativeai)
            # Таймаут контролируется на уровне Gunicorn (300 секунд)
            if system_instruction:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    system_instruction=system_instruction
                )
            else:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            return response.text
            
        except Exception as e:
            error_str = str(e)
            last_error = e
            
            # Проверка на таймаут
            if "timeout" in error_str.lower() or "deadline" in error_str.lower() or "timed out" in error_str.lower():
                if attempt < max_retries - 1:
                    print(f"Таймаут при вызове Gemini API. Попытка {attempt + 1}/{max_retries}. Повтор через {retry_delay} секунд...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(f"Таймаут при вызове Gemini API после {max_retries} попыток. Запрос занял слишком много времени.")
            
            # Проверка на ошибку квоты (429)
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                if attempt < max_retries - 1:
                    # Извлекаем время задержки из ошибки, если указано
                    delay = retry_delay
                    if "retry_delay" in error_str.lower():
                        # Пытаемся извлечь секунды из ошибки
                        import re
                        match = re.search(r'seconds[:\s]+(\d+)', error_str, re.IGNORECASE)
                        if match:
                            delay = int(match.group(1)) + 2  # Добавляем 2 секунды для безопасности
                    
                    print(f"Превышена квота Gemini API. Попытка {attempt + 1}/{max_retries}. Повтор через {delay} секунд...")
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(f"Превышена квота Gemini API после {max_retries} попыток. Попробуйте позже или проверьте ваш план подписки.")
            else:
                # Для других ошибок не повторяем
                raise Exception(f"Ошибка при вызове Gemini API: {error_str}")
    
    # Если все попытки исчерпаны
    raise Exception(f"Ошибка при вызове Gemini API после {max_retries} попыток: {str(last_error)}")
