from django.contrib import admin
from .models import Test, TestQuestion, TestSession, TestAnswer, TestResult


class TestQuestionInline(admin.TabularInline):
    model = TestQuestion
    extra = 0
    fields = ('question_number', 'question_text', 'series', 'question_type', 'block_name', 'display_type', 'answer_options', 'correct_answer', 'order')
    ordering = ('order', 'question_number')


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('name', 'test_type', 'duration_minutes', 'questions_count', 'is_active')
    list_filter = ('test_type', 'is_active')
    search_fields = ('name', 'description')
    inlines = [TestQuestionInline]


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ('test', 'question_number', 'series', 'block_name', 'display_type', 'correct_answer', 'order')
    list_filter = ('test', 'series', 'block_name', 'display_type')
    search_fields = ('question_text', 'test__name')
    ordering = ('test', 'order', 'question_number')
    
    def get_fieldsets(self, request, obj=None):
        """Динамически изменяем fieldsets в зависимости от типа теста"""
        fieldsets = (
            ('Основная информация', {
                'fields': ('test', 'question_number', 'question_text', 'question_image', 'order')
            }),
            ('Классификация', {
                'fields': ('series', 'question_type', 'block_name')
            }),
            ('Варианты ответов', {
                'fields': ('display_type', 'answer_options', 'correct_answer'),
                'description': self._get_answer_options_help(obj)
            }),
            ('Даты', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )
        return fieldsets
    
    def _get_answer_options_help(self, obj):
        """Возвращает подсказку для вариантов ответов в зависимости от типа теста"""
        if obj and obj.test:
            if obj.test.test_type == 'iq_test':
                return (
                    '<div style="background: #f0f8ff; padding: 10px; border-left: 4px solid #1976d2; margin: 10px 0;">'
                    '<strong>Для IQ-теста:</strong><br>'
                    '• <strong>Тип отображения:</strong> выберите "Числовой ответ"<br>'
                    '• <strong>Варианты ответов:</strong> введите JSON массив чисел, например: <code>[1, 2, 3, 4, 5, 6]</code><br>'
                    '• <strong>Правильный ответ:</strong> введите число от 1 до 6 (например: <code>4</code>)'
                    '</div>'
                )
            elif obj.test.test_type == 'personal_qualities':
                return (
                    '<div style="background: #fff3e0; padding: 10px; border-left: 4px solid #ff9800; margin: 10px 0;">'
                    '<strong>Для теста личностных качеств:</strong><br>'
                    '• <strong>Тип отображения:</strong> выберите "Одиночный выбор (radio)"<br>'
                    '• <strong>Варианты ответов:</strong> JSON массив объектов, например: <code>[{"value": "yes", "label": "Да"}, {"value": "no", "label": "Нет"}]</code>'
                    '</div>'
                )
        return (
            '<div style="background: #f5f5f5; padding: 10px; margin: 10px 0;">'
            '<strong>Подсказка:</strong><br>'
            '• <strong>answer_options</strong> - JSON массив. Для числовых ответов: <code>[1, 2, 3, 4, 5, 6]</code><br>'
            '• Для текстовых вариантов: <code>[{"value": "option1", "label": "Вариант 1"}, ...]</code>'
            '</div>'
        )
    
    readonly_fields = ('created_at', 'updated_at')
    
    class Media:
        css = {
            'all': ('admin/css/test_question_admin.css',)
        }


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'test', 'candidate_email', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'test', 'created_at')
    search_fields = ('candidate_email', 'candidate_name', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'started_at', 'completed_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'user', 'test', 'candidate_email', 'candidate_name', 'candidate_age')
        }),
        ('Статус', {
            'fields': ('status', 'started_at', 'completed_at', 'expires_at', 'time_limit_minutes')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(TestAnswer)
class TestAnswerAdmin(admin.ModelAdmin):
    list_display = ('session', 'question_number', 'answer_value', 'series', 'created_at')
    list_filter = ('series', 'created_at')
    search_fields = ('session__candidate_email', 'answer_value')
    readonly_fields = ('created_at',)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('session', 'raw_score', 'final_score', 'iq_score', 'is_processed', 'created_at')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('session__candidate_email', 'report')
    readonly_fields = ('created_at', 'updated_at', 'processed_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('session', 'raw_score', 'final_score')
        }),
        ('IQ тест', {
            'fields': ('iq_score', 'iq_level')
        }),
        ('Личностные качества', {
            'fields': ('scores_json',)
        }),
        ('Отчет', {
            'fields': ('report', 'report_json')
        }),
        ('Обработка', {
            'fields': ('is_processed', 'processed_at')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )
