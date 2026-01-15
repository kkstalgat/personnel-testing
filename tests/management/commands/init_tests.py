"""
Команда для инициализации тестов в базе данных
"""
from django.core.management.base import BaseCommand
from tests.models import Test, TestQuestion


class Command(BaseCommand):
    help = 'Инициализация тестов в базе данных'

    def handle(self, *args, **options):
        tests_data = [
            {
                'test_type': 'iq_test',
                'name': 'IQ-тест',
                'description': 'IQ-тест (прогрессивные матрицы Равена) предназначен для диагностики уровня интеллектуального развития.',
                'duration_minutes': 20,
                'questions_count': 60,
                'is_active': True
            },
            {
                'test_type': 'personal_qualities',
                'name': 'Оценка личностных качеств',
                'description': 'Тест для оценки личностных качеств кандидата: внимательность, позитивность, самообладание, ответственность и др.',
                'duration_minutes': 35,
                'questions_count': 200,
                'is_active': True
            },
            {
                'test_type': 'productivity',
                'name': 'Оценка продуктивности',
                'description': 'Тест для оценки продуктивности кандидата и его ориентации на результат.',
                'duration_minutes': 20,
                'questions_count': 20,
                'is_active': True
            },
        ]
        
        for test_data in tests_data:
            test, created = Test.objects.update_or_create(
                test_type=test_data['test_type'],
                defaults=test_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан тест: {test.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Тест уже существует: {test.name}'))
            
            # Создать вопросы для теста (кроме IQ теста - вопросы заносим вручную)
            if test.test_type != 'iq_test':
                existing_count = TestQuestion.objects.filter(test=test).count()
                expected_count = test_data.get('questions_count', 0)
                
                if existing_count == 0:
                    # Создаем вопросы, если их нет
                    self._create_questions_for_test(test)
                    question_count = TestQuestion.objects.filter(test=test).count()
                    self.stdout.write(self.style.SUCCESS(f'  Создано вопросов: {question_count}'))
                elif existing_count < expected_count:
                    # Удаляем старые вопросы и создаем заново, если их меньше ожидаемого
                    TestQuestion.objects.filter(test=test).delete()
                    self._create_questions_for_test(test)
                    question_count = TestQuestion.objects.filter(test=test).count()
                    self.stdout.write(self.style.SUCCESS(f'  Пересоздано вопросов: {question_count} (было {existing_count}, должно быть {expected_count})'))
                else:
                    question_count = TestQuestion.objects.filter(test=test).count()
                    self.stdout.write(self.style.WARNING(f'  Вопросы уже существуют ({question_count} вопросов)'))
            else:
                question_count = TestQuestion.objects.filter(test=test).count()
                if question_count > 0:
                    self.stdout.write(self.style.WARNING(f'  Вопросы уже существуют ({question_count} вопросов)'))
                else:
                    self.stdout.write(self.style.SUCCESS('  Вопросы для IQ теста нужно занести вручную через админ-панель'))
    
    def _create_questions_for_test(self, test):
        """Создать вопросы для теста на основе его типа (кроме IQ теста)"""
        if test.test_type == 'personal_qualities':
            from tests.data.personal_qualities_test import PERSONAL_QUALITIES_BLOCKS
            
            # Варианты ответов для теста личностных качеств
            answer_options = [
                {"value": "yes", "label": "Да"},
                {"value": "no", "label": "Нет"},
                {"value": "sometimes", "label": "Иногда"}
            ]
            
            q_num = 1
            for block_name, block_data in PERSONAL_QUALITIES_BLOCKS.items():
                if 'questions' in block_data:
                    for question in block_data['questions']:
                        TestQuestion.objects.create(
                            test=test,
                            question_number=q_num,
                            question_text=question.get('text', ''),
                            question_type=question.get('type', '+'),
                            block_name=block_name,
                            answer_options=answer_options,
                            display_type='radio',
                            order=q_num
                        )
                        q_num += 1
        
        elif test.test_type == 'productivity':
            from tests.data.productivity_test import PRODUCTIVITY_QUESTIONS
            
            # Для теста продуктивности - открытые вопросы без вариантов
            for question_data in PRODUCTIVITY_QUESTIONS:
                TestQuestion.objects.create(
                    test=test,
                    question_number=question_data['number'],
                    question_text=question_data['question'],
                    block_name=question_data.get('block', ''),
                    answer_options=[],  # Нет вариантов, открытый текст
                    display_type='textarea',
                    order=question_data['number']
                )
