from django.db import models
from django.utils import timezone
from accounts.models import User
import uuid


class TestType(models.TextChoices):
    IQ_TEST = 'iq_test', 'IQ-тест'
    PERSONAL_QUALITIES = 'personal_qualities', 'Оценка личностных качеств'
    PRODUCTIVITY = 'productivity', 'Оценка продуктивности'


class Test(models.Model):
    """Модель теста"""
    test_type = models.CharField(max_length=50, choices=TestType.choices, verbose_name='Тип теста')
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    duration_minutes = models.IntegerField(verbose_name='Длительность в минутах')
    questions_count = models.IntegerField(verbose_name='Количество вопросов')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return self.name


class TestQuestion(models.Model):
    """Вопрос теста"""
    # Типы отображения вопроса
    DISPLAY_CHOICES = [
        ('radio', 'Одиночный выбор (radio)'),
        ('checkbox', 'Множественный выбор (checkbox)'),
        ('textarea', 'Открытый текст (textarea)'),
        ('number', 'Числовой ответ'),
        ('select', 'Выпадающий список'),
    ]
    
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions', verbose_name='Тест')
    question_number = models.IntegerField(verbose_name='Номер вопроса')
    question_text = models.TextField(blank=True, verbose_name='Текст вопроса')
    question_image = models.ImageField(upload_to='test_questions/', blank=True, null=True, verbose_name='Изображение вопроса')
    series = models.CharField(max_length=10, blank=True, verbose_name='Серия (для IQ теста: A, B, C, D, E)')
    question_type = models.CharField(max_length=50, blank=True, verbose_name='Тип вопроса')  # Для личностных качеств: + или -
    block_name = models.CharField(max_length=100, blank=True, verbose_name='Название блока (для личностных качеств)')
    
    # Варианты ответов (JSON массив: [{"value": "yes", "label": "Да"}, ...])
    answer_options = models.JSONField(default=list, blank=True, verbose_name='Варианты ответов')
    
    # Тип отображения вопроса
    display_type = models.CharField(max_length=20, choices=DISPLAY_CHOICES, default='radio', verbose_name='Тип отображения')
    
    # Правильный ответ (для IQ теста)
    correct_answer = models.CharField(max_length=10, blank=True, verbose_name='Правильный ответ')
    
    order = models.IntegerField(default=0, verbose_name='Порядок отображения')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Вопрос теста'
        verbose_name_plural = 'Вопросы тестов'
        unique_together = ['test', 'question_number']
        ordering = ['order', 'question_number']

    def __str__(self):
        return f'{self.test.name} - Вопрос {self.question_number}'


class TestSession(models.Model):
    """Сессия прохождения теста"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_sessions', verbose_name='Пользователь')
    test = models.ForeignKey(Test, on_delete=models.PROTECT, verbose_name='Тест')
    candidate_email = models.EmailField(verbose_name='Email соискателя')
    candidate_name = models.CharField(max_length=255, blank=True, verbose_name='Имя соискателя')
    candidate_age = models.IntegerField(null=True, blank=True, verbose_name='Возраст соискателя')
    
    # Статус прохождения
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_EXPIRED = 'expired'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Ожидает прохождения'),
        (STATUS_IN_PROGRESS, 'В процессе'),
        (STATUS_COMPLETED, 'Завершен'),
        (STATUS_EXPIRED, 'Истек'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='Статус')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Начало прохождения')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Завершение прохождения')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Истекает')
    
    # Время ограничения
    time_limit_minutes = models.IntegerField(null=True, blank=True, verbose_name='Лимит времени (минуты)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Сессия тестирования'
        verbose_name_plural = 'Сессии тестирования'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.test.name} - {self.candidate_email}'

    def start_test(self):
        """Начать тест"""
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_IN_PROGRESS
            self.started_at = timezone.now()
            if self.time_limit_minutes:
                self.expires_at = self.started_at + timezone.timedelta(minutes=self.time_limit_minutes)
            self.save()

    def complete_test(self):
        """Завершить тест"""
        if self.status == self.STATUS_IN_PROGRESS:
            self.status = self.STATUS_COMPLETED
            self.completed_at = timezone.now()
            self.save()


class TestAnswer(models.Model):
    """Ответ на вопрос теста"""
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='answers', verbose_name='Сессия')
    question_number = models.IntegerField(verbose_name='Номер вопроса')
    answer_value = models.TextField(verbose_name='Значение ответа')  # Может быть число (1-6) или текст
    series = models.CharField(max_length=10, blank=True, verbose_name='Серия (для IQ теста)')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ответ на вопрос'
        verbose_name_plural = 'Ответы на вопросы'
        unique_together = ['session', 'question_number']

    def __str__(self):
        return f'Session {self.session.id} - Q{self.question_number}'


class TestResult(models.Model):
    """Результат прохождения теста"""
    session = models.OneToOneField(TestSession, on_delete=models.CASCADE, related_name='result', verbose_name='Сессия')
    
    # Общие данные
    raw_score = models.IntegerField(null=True, blank=True, verbose_name='Сырой балл')
    final_score = models.FloatField(null=True, blank=True, verbose_name='Итоговый балл')
    
    # Данные для IQ теста
    iq_score = models.IntegerField(null=True, blank=True, verbose_name='IQ балл')
    iq_level = models.CharField(max_length=100, blank=True, verbose_name='Уровень IQ')
    
    # Данные для теста личностных качеств
    scores_json = models.JSONField(default=dict, blank=True, verbose_name='Баллы по шкалам (JSON)')
    
    # Отчет
    report = models.TextField(blank=True, verbose_name='Текстовый отчет')
    report_json = models.JSONField(default=dict, blank=True, verbose_name='Отчет (JSON)')
    
    # Обработка
    is_processed = models.BooleanField(default=False, verbose_name='Обработан')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата обработки')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'

    def __str__(self):
        return f'Result for {self.session}'
