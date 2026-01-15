from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """Расширенная модель пользователя"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True)
    company_name = models.CharField(max_length=255, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    phone_verification_code = models.CharField(max_length=6, blank=True, null=True)
    phone_verification_code_expires = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username or self.email


class SubscriptionPlan(models.Model):
    """Тарифный план"""
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    duration_days = models.IntegerField(verbose_name='Длительность в днях')
    tests_count = models.IntegerField(verbose_name='Количество тестов')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Тарифный план'
        verbose_name_plural = 'Тарифные планы'

    def __str__(self):
        return self.name


class Subscription(models.Model):
    """Подписка пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    remaining_tests = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.user.email} - {self.plan.name}'

    def save(self, *args, **kwargs):
        if not self.pk:  # При создании новой подписки
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
            self.remaining_tests = self.plan.tests_count
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """Проверка валидности подписки"""
        return self.is_active and timezone.now() <= self.end_date and self.remaining_tests > 0


class Module(models.Model):
    """Модуль (дополнительный функционал)"""
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Модуль'
        verbose_name_plural = 'Модули'

    def __str__(self):
        return self.name


class UserModule(models.Model):
    """Активные модули пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='modules')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Модуль пользователя'
        verbose_name_plural = 'Модули пользователей'
        unique_together = ['user', 'module']

    def __str__(self):
        return f'{self.user.email} - {self.module.name}'
