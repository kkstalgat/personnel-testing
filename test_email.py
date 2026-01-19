#!/usr/bin/env python
"""
Скрипт для тестирования отправки email
Использование: python test_email.py
"""

import os
import sys
import django

# Настройка Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'personnel_testing.settings')
django.setup()

from django.core.mail import send_mail, EmailMessage
from django.conf import settings

def test_email():
    """Тестовая отправка email"""
    
    print("="*60)
    print("ТЕСТИРОВАНИЕ ОТПРАВКИ EMAIL")
    print("="*60)
    print(f"\nТекущие настройки:")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    
    # Предупреждение о console backend
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        print("⚠️  ВНИМАНИЕ: Используется console.EmailBackend!")
        print("   Письма НЕ отправляются реально, а выводятся в консоль/логи.")
        print("   Для реальной отправки настройте SMTP в .env файле.")
    
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER if settings.EMAIL_HOST_USER else '(не задан)'}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"SERVER_EMAIL: {settings.SERVER_EMAIL}")
    print("\n" + "="*60)
    
    # Запрос email для теста
    test_email = input("\nВведите email для тестовой отправки: ").strip()
    
    if not test_email:
        print("❌ Email не указан. Выход.")
        return
    
    print(f"\nОтправка тестового письма на {test_email}...")
    
    try:
        subject = 'Тестовое письмо от IQ System'
        message = '''Здравствуйте!

Это тестовое письмо от системы тестирования персонала.

Если вы получили это письмо, значит настройки email работают правильно.

С уважением,
IQ System
'''
        
        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [test_email],
            fail_silently=False,
        )
        
        if result:
            print(f"\n✅ Письмо успешно отправлено на {test_email}!")
            print("Проверьте почтовый ящик (включая папку 'Спам').")
            
            # Предупреждение о console backend
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                print("\n⚠️  ВНИМАНИЕ: Используется console.EmailBackend!")
                print("Письмо НЕ отправлено реально, а выведено в консоль/логи.")
                print("Для реальной отправки настройте EMAIL_BACKEND в .env:")
                print("EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")
        else:
            print(f"\n⚠️  Письмо не отправлено (результат: {result})")
            
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                print("\n💡 Используется console.EmailBackend - письма не отправляются реально!")
                print("Проверьте логи Gunicorn - там должно быть содержимое письма.")
            
    except Exception as e:
        print(f"\n❌ Ошибка при отправке письма:")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Сообщение: {str(e)}")
        
        # Дополнительная информация для диагностики
        if "550" in str(e) or "permission" in str(e).lower():
            print("\n💡 Возможные причины:")
            print("1. Неправильный EMAIL_HOST_USER или EMAIL_HOST_PASSWORD")
            print("2. Для Gmail нужен App Password, а не обычный пароль")
            print("3. DEFAULT_FROM_EMAIL не совпадает с EMAIL_HOST_USER")
            print("4. Учетная запись не имеет прав на отправку от имени DEFAULT_FROM_EMAIL")
        
        if "authentication" in str(e).lower() or "535" in str(e):
            print("\n💡 Проблема с аутентификацией:")
            print("1. Проверьте правильность EMAIL_HOST_USER и EMAIL_HOST_PASSWORD")
            print("2. Для Gmail используйте App Password (не обычный пароль)")
            print("3. Убедитесь, что включена двухфакторная аутентификация в Gmail")
        
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            print("\n💡 Проблема с подключением:")
            print("1. Проверьте EMAIL_HOST и EMAIL_PORT")
            print("2. Проверьте, не блокирует ли firewall подключение")
            print("3. Проверьте, доступен ли SMTP сервер")

if __name__ == '__main__':
    test_email()
