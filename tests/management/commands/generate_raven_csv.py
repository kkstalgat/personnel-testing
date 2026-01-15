"""
Скрипт для генерации CSV файла с вопросами IQ-теста

Использование:
    python manage.py generate_raven_csv output.csv
"""
import csv
from django.core.management.base import BaseCommand, CommandError
from tests.data.raven_test import RAVEN_TEST_ANSWER_KEY


class Command(BaseCommand):
    help = 'Генерирует CSV файл с вопросами IQ-теста для импорта'

    def add_arguments(self, parser):
        parser.add_argument('output_file', type=str, help='Путь к выходному CSV файлу')
        parser.add_argument(
            '--template',
            type=str,
            help='Путь к шаблонному CSV файлу для анализа структуры',
        )

    def handle(self, *args, **options):
        output_file = options['output_file']
        template_file = options.get('template')
        
        # Правильные ответы из ключа
        answer_key = RAVEN_TEST_ANSWER_KEY
        
        # Определяем структуру CSV на основе шаблона или используем стандартную
        csv_structure = self._analyze_template(template_file) if template_file else None
        
        # Генерируем все 60 вопросов
        questions = []
        
        # Серия A (вопросы 1-12)
        for i in range(1, 13):
            question_num = i
            series = 'A'
            answer_key_str = f'{series}{i}'
            correct_answer = answer_key.get(answer_key_str, '')
            image_filename = f'{series}{i}.png'
            
            questions.append({
                'id': '',  # Будет заполнено при импорте
                'question_number': i,  # Номер в серии
                'question_text': 'Вашей задачей является найти в ряде фрагментов тот, который точно вписался бы в свободное место и ввести соответствующий номер фрагмента в поле ответа.',
                'question_image': f'test_questions/{image_filename}',
                'series': series,
                'question_type': '',
                'block_name': '',
                'correct_answer': str(correct_answer),
                'order': question_num,  # Общий номер вопроса (1-60)
                'created_at': '',
                'updated_at': '',
                'test_id': '1',  # Будет определен при импорте
                'answer_options': '[1, 2, 3, 4, 5, 6]',
                'display_type': 'number',
            })
        
        # Серия B (вопросы 13-24)
        for i in range(1, 13):
            question_num = 12 + i  # 13-24
            series = 'B'
            answer_key_str = f'{series}{i}'
            correct_answer = answer_key.get(answer_key_str, '')
            image_filename = f'{series}{i}.png'
            
            questions.append({
                'id': '',
                'question_number': i,  # Номер в серии
                'question_text': 'Вашей задачей является найти в ряде фрагментов тот, который точно вписался бы в свободное место и ввести соответствующий номер фрагмента в поле ответа.',
                'question_image': f'test_questions/{image_filename}',
                'series': series,
                'question_type': '',
                'block_name': '',
                'correct_answer': str(correct_answer),
                'order': question_num,
                'created_at': '',
                'updated_at': '',
                'test_id': '1',
                'answer_options': '[1, 2, 3, 4, 5, 6]',
                'display_type': 'number',
            })
        
        # Серия C (вопросы 25-36)
        for i in range(1, 13):
            question_num = 24 + i  # 25-36
            series = 'C'
            answer_key_str = f'{series}{i}'
            correct_answer = answer_key.get(answer_key_str, '')
            image_filename = f'{series}{i}.png'
            
            questions.append({
                'id': '',
                'question_number': i,  # Номер в серии
                'question_text': 'Вашей задачей является найти в ряде фрагментов тот, который точно вписался бы в свободное место и ввести соответствующий номер фрагмента в поле ответа.',
                'question_image': f'test_questions/{image_filename}',
                'series': series,
                'question_type': '',
                'block_name': '',
                'correct_answer': str(correct_answer),
                'order': question_num,
                'created_at': '',
                'updated_at': '',
                'test_id': '1',
                'answer_options': '[1, 2, 3, 4, 5, 6]',
                'display_type': 'number',
            })
        
        # Серия D (вопросы 37-48)
        for i in range(1, 13):
            question_num = 36 + i  # 37-48
            series = 'D'
            answer_key_str = f'{series}{i}'
            correct_answer = answer_key.get(answer_key_str, '')
            image_filename = f'{series}{i}.png'
            
            questions.append({
                'id': '',
                'question_number': i,  # Номер в серии
                'question_text': 'Вашей задачей является найти в ряде фрагментов тот, который точно вписался бы в свободное место и ввести соответствующий номер фрагмента в поле ответа.',
                'question_image': f'test_questions/{image_filename}',
                'series': series,
                'question_type': '',
                'block_name': '',
                'correct_answer': str(correct_answer),
                'order': question_num,
                'created_at': '',
                'updated_at': '',
                'test_id': '1',
                'answer_options': '[1, 2, 3, 4, 5, 6]',
                'display_type': 'number',
            })
        
        # Серия E (вопросы 49-60)
        for i in range(1, 13):
            question_num = 48 + i  # 49-60
            series = 'E'
            answer_key_str = f'{series}{i}'
            correct_answer = answer_key.get(answer_key_str, '')
            image_filename = f'{series}{i}.png'
            
            questions.append({
                'id': '',
                'question_number': i,  # Номер в серии
                'question_text': 'Вашей задачей является найти в ряде фрагментов тот, который точно вписался бы в свободное место и ввести соответствующий номер фрагмента в поле ответа.',
                'question_image': f'test_questions/{image_filename}',
                'series': series,
                'question_type': '',
                'block_name': '',
                'correct_answer': str(correct_answer),
                'order': question_num,
                'created_at': '',
                'updated_at': '',
                'test_id': '1',
                'answer_options': '[1, 2, 3, 4, 5, 6]',
                'display_type': 'number',
            })
        
        # Записываем в CSV
        fieldnames = [
            'id', 'question_number', 'question_text', 'question_image', 
            'series', 'question_type', 'block_name', 'correct_answer', 
            'order', 'created_at', 'updated_at', 'test_id', 
            'answer_options', 'display_type'
        ]
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
                # Не записываем заголовок, так как в исходном файле его нет
                # writer.writeheader()
                
                for question in questions:
                    writer.writerow(question)
            
            self.stdout.write(self.style.SUCCESS(f'CSV файл успешно создан: {output_file}'))
            self.stdout.write(f'Создано {len(questions)} вопросов')
            self.stdout.write(f'Серия A: вопросы 1-12')
            self.stdout.write(f'Серия B: вопросы 13-24')
            self.stdout.write(f'Серия C: вопросы 25-36')
            self.stdout.write(f'Серия D: вопросы 37-48')
            self.stdout.write(f'Серия E: вопросы 49-60')
            
        except Exception as e:
            raise CommandError(f'Ошибка при создании CSV файла: {str(e)}')
    
    def _analyze_template(self, template_file):
        """Анализирует шаблонный CSV файл для определения структуры"""
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                first_row = next(reader, None)
                if first_row:
                    return first_row
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Не удалось проанализировать шаблон: {str(e)}'))
        return None
