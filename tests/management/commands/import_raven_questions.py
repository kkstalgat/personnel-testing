"""
Скрипт для импорта вопросов IQ-теста из CSV файла

Использование:
    python manage.py import_raven_questions path/to/file.csv

Формат CSV:
    id,question_number,question_text,question_image,series,...,correct_answer,order,...,test_id,answer_options,display_type
"""
import csv
import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from tests.models import Test, TestQuestion
from tests.data.raven_test import RAVEN_TEST_ANSWER_KEY


class Command(BaseCommand):
    help = 'Импортирует вопросы IQ-теста из CSV файла'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Путь к CSV файлу')
        parser.add_argument(
            '--test-id',
            type=int,
            help='ID IQ-теста (если не указан, будет найден автоматически)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Проверить файл без создания записей в БД',
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        test_id = options.get('test_id')
        dry_run = options['dry_run']

        # Проверяем существование файла
        if not os.path.exists(csv_file_path):
            raise CommandError(f'Файл не найден: {csv_file_path}')

        # Находим IQ-тест
        if test_id:
            try:
                test = Test.objects.get(id=test_id, test_type='iq_test')
            except Test.DoesNotExist:
                raise CommandError(f'Тест с ID {test_id} не найден или не является IQ-тестом')
        else:
            test = Test.objects.filter(test_type='iq_test').first()
            if not test:
                raise CommandError('IQ-тест не найден. Создайте тест через админку или команду init_tests.')

        self.stdout.write(f'Используется тест: {test.name} (ID: {test.id})')

        # Читаем CSV файл
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                # Пытаемся определить разделитель
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter

                reader = csv.reader(f, delimiter=delimiter)
                
                # Пропускаем заголовок, если есть
                first_row = next(reader, None)
                row_counter = 1
                
                if first_row:
                    # Проверяем, является ли первая строка заголовком
                    # Заголовок обычно содержит слова типа "id", "question_number" и т.д.
                    is_header = False
                    if len(first_row) > 0:
                        first_col = first_row[0].strip().lower()
                        # Если первая колонка содержит слова-заголовки, это заголовок
                        if first_col in ['id', 'question_number', 'question_text']:
                            is_header = True
                            self.stdout.write('Обнаружен заголовок, пропускаем...')
                    
                    if not is_header:
                        # Это данные, обрабатываем первую строку
                        self._process_row(first_row, test, dry_run, stats, row_counter)
                        row_counter += 1

                # Обрабатываем остальные строки
                for row in reader:
                    if not row or (len(row) > 0 and not row[0].strip() and len([c for c in row if c.strip()]) == 0):
                        continue
                    self._process_row(row, test, dry_run, stats, row_counter)
                    row_counter += 1

        except Exception as e:
            raise CommandError(f'Ошибка при чтении CSV файла: {str(e)}')

        # Выводим результаты
        self.stdout.write(self.style.SUCCESS(f'\nИмпорт завершен:'))
        self.stdout.write(f'  Создано: {stats["created"]}')
        self.stdout.write(f'  Обновлено: {stats["updated"]}')
        self.stdout.write(f'  Пропущено: {stats["skipped"]}')
        
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f'\nОшибки ({len(stats["errors"])}):'))
            for error in stats['errors'][:10]:  # Показываем первые 10 ошибок
                self.stdout.write(self.style.ERROR(f'  {error}'))
            if len(stats['errors']) > 10:
                self.stdout.write(self.style.ERROR(f'  ... и еще {len(stats["errors"]) - 10} ошибок'))

    def _process_row(self, row, test, dry_run, stats, row_num=None):
        """Обрабатывает одну строку CSV"""
        try:
            # Парсим строку CSV
            # Формат: id,question_number,question_text,question_image,series,...,correct_answer,order,...,test_id,answer_options,display_type
            if len(row) < 10:
                stats['errors'].append(f'Строка {row_num or "?"}: недостаточно колонок ({len(row)})')
                stats['skipped'] += 1
                return

            # Извлекаем данные (индексы могут варьироваться, но обычно так)
            csv_id = row[0].strip() if row[0] else None
            question_number_in_series = int(row[1].strip()) if row[1] and row[1].strip().isdigit() else None
            question_text = row[2].strip() if len(row) > 2 and row[2] else ''
            question_image_path = row[3].strip() if len(row) > 3 and row[3] else ''
            series = row[4].strip() if len(row) > 4 and row[4] else ''
            
            # Ищем правильный ответ и другие поля
            # Правильный ответ обычно в колонке 6 (индекс 6)
            correct_answer_from_csv = None
            if len(row) > 6 and row[6] and row[6].strip():
                try:
                    correct_answer_from_csv = int(row[6].strip())
                except ValueError:
                    pass
            
            # Порядок обычно в колонке 7 (индекс 7)
            order = 0
            if len(row) > 7 and row[7] and row[7].strip().isdigit():
                order = int(row[7].strip())
            
            # answer_options обычно в предпоследней колонке
            answer_options_str = None
            if len(row) >= 2:
                # Ищем JSON массив в последних колонках
                for i in range(len(row) - 1, max(0, len(row) - 5), -1):
                    if row[i] and '[' in row[i] and ']' in row[i]:
                        answer_options_str = row[i].strip()
                        break
            
            # display_type обычно в последней колонке
            display_type = 'number'
            if row[-1] and row[-1].strip():
                display_type = row[-1].strip()

            # Определяем серию из имени файла, если не указана
            if not series and question_image_path:
                # Извлекаем серию из имени файла (например, A1.png -> A)
                filename = os.path.basename(question_image_path)
                if filename:
                    series = filename[0].upper()  # Первая буква - серия
            
            # Определяем номер вопроса в серии из имени файла, если не указан
            if question_number_in_series is None and question_image_path:
                filename = os.path.basename(question_image_path)
                # Извлекаем номер из имени файла (например, A1.png -> 1, A12.png -> 12)
                import re
                match = re.search(r'(\d+)', filename)
                if match:
                    question_number_in_series = int(match.group(1))

            if not series or question_number_in_series is None:
                stats['errors'].append(f'Строка {row_num or "?"}: не удалось определить серию или номер вопроса')
                stats['skipped'] += 1
                return

            # Вычисляем общий номер вопроса (1-60)
            series_map = {
                'A': (1, 12),
                'B': (13, 24),
                'C': (25, 36),
                'D': (37, 48),
                'E': (49, 60),
            }
            
            if series not in series_map:
                stats['errors'].append(f'Строка {row_num or "?"}: неизвестная серия "{series}"')
                stats['skipped'] += 1
                return

            start_num, end_num = series_map[series]
            question_number = start_num + question_number_in_series - 1

            # Получаем правильный ответ из ключа
            answer_key = f'{series}{question_number_in_series}'
            correct_answer = RAVEN_TEST_ANSWER_KEY.get(answer_key)
            
            if correct_answer is None:
                stats['errors'].append(f'Строка {row_num or "?"}: правильный ответ не найден для {answer_key}')
                # Используем значение из CSV, если есть
                if correct_answer_from_csv:
                    correct_answer = correct_answer_from_csv
                    self.stdout.write(self.style.WARNING(f'  Использован ответ из CSV для {answer_key}: {correct_answer}'))
                else:
                    stats['skipped'] += 1
                    return

            # Парсим варианты ответов
            answer_options = [1, 2, 3, 4, 5, 6]  # По умолчанию
            if answer_options_str:
                try:
                    import json
                    answer_options = json.loads(answer_options_str)
                except:
                    # Если не JSON, пытаемся извлечь числа
                    import re
                    numbers = re.findall(r'\d+', answer_options_str)
                    if numbers:
                        answer_options = [int(n) for n in numbers]

            # Проверяем, существует ли вопрос
            question, created = TestQuestion.objects.get_or_create(
                test=test,
                question_number=question_number,
                defaults={
                    'question_text': question_text,
                    'series': series,
                    'display_type': display_type,
                    'answer_options': answer_options,
                    'correct_answer': str(correct_answer),
                    'order': order if order > 0 else question_number,
                }
            )

            if not created:
                # Обновляем существующий вопрос
                question.question_text = question_text
                question.series = series
                question.display_type = display_type
                question.answer_options = answer_options
                question.correct_answer = str(correct_answer)
                question.order = order if order > 0 else question_number

            # Обрабатываем изображение
            if question_image_path and not dry_run:
                # Проверяем, существует ли файл
                if os.path.exists(question_image_path):
                    # Открываем файл и сохраняем
                    with open(question_image_path, 'rb') as img_file:
                        question.question_image.save(
                            os.path.basename(question_image_path),
                            File(img_file),
                            save=False
                        )
                elif question_image_path.startswith('test_questions/'):
                    # Файл может быть в media директории
                    media_path = os.path.join('media', question_image_path)
                    if os.path.exists(media_path):
                        with open(media_path, 'rb') as img_file:
                            question.question_image.save(
                                os.path.basename(question_image_path),
                                File(img_file),
                                save=False
                            )

            if not dry_run:
                question.save()
                if created:
                    stats['created'] += 1
                    self.stdout.write(f'  Создан вопрос {question_number} (серия {series}, номер в серии {question_number_in_series})')
                else:
                    stats['updated'] += 1
                    self.stdout.write(f'  Обновлен вопрос {question_number} (серия {series}, номер в серии {question_number_in_series})')
            else:
                self.stdout.write(f'  [DRY RUN] Будет создан/обновлен вопрос {question_number} (серия {series}, номер в серии {question_number_in_series})')

        except Exception as e:
            stats['errors'].append(f'Строка {row_num or "?"}: {str(e)}')
            stats['skipped'] += 1
