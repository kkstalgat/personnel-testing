from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import NotFound
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from .models import Test, TestQuestion, TestSession, TestAnswer, TestResult
from .serializers import TestSerializer, TestSessionSerializer, TestAnswerSerializer, TestResultSerializer
from .services.raven_processor import process_raven_test
from .services.personal_qualities_processor import process_personal_qualities_test
from .services.productivity_processor import process_productivity_test
from .utils.pdf_generator import generate_pdf_report


class TestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Test.objects.filter(is_active=True)
    serializer_class = TestSerializer
    permission_classes = [AllowAny]


class TestSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TestSessionSerializer
    permission_classes = [AllowAny]  # Для прохождения теста соискателями
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return TestSession.objects.filter(user=user).order_by('-created_at')
        # Для неавторизованных (соискателей) возвращаем сессии по ID из URL или query params
        # Это позволяет получить сессию через /api/tests/sessions/{id}/start/
        return TestSession.objects.all().order_by('-created_at')
    
    def get_object(self):
        """
        Переопределяем get_object для поддержки доступа неавторизованных пользователей
        к сессиям по ID из URL
        """
        queryset = self.get_queryset()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = queryset.filter(**filter_kwargs).first()
        
        if obj is None:
            from rest_framework.exceptions import NotFound
            raise NotFound('Сессия не найдена')
        
        # Проверка прав доступа
        self.check_object_permissions(self.request, obj)
        return obj
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_session(self, request):
        """Создать сессию тестирования для соискателя (только для авторизованных пользователей)"""
        from django.db import transaction
        from django.utils import timezone
        from datetime import timedelta
        
        user = request.user
        
        # Проверка наличия активной подписки
        from accounts.models import Subscription
        subscription = Subscription.objects.filter(
            user=user,
            is_active=True,
            remaining_tests__gt=0
        ).first()
        
        if not subscription:
            return Response({'error': 'Нет активной подписки или не осталось тестов'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        test_id = request.data.get('test_id')
        candidate_email = request.data.get('candidate_email', '').strip()
        candidate_name = request.data.get('candidate_name', '').strip()
        candidate_age = request.data.get('candidate_age')
        
        if not test_id or not candidate_email:
            return Response({'error': 'test_id и candidate_email обязательны'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            test = Test.objects.get(id=test_id, is_active=True)
        except Test.DoesNotExist:
            return Response({'error': 'Тест не найден'}, status=status.HTTP_404_NOT_FOUND)
        
        # Проверка на дубликаты: не создавать сессию, если недавно создана аналогичная
        # (защита от двойной отправки)
        recent_threshold = timezone.now() - timedelta(seconds=5)
        recent_session = TestSession.objects.filter(
            user=user,
            test=test,
            candidate_email=candidate_email,
            status=TestSession.STATUS_PENDING,
            created_at__gte=recent_threshold
        ).first()
        
        if recent_session:
            # Если недавно создана похожая сессия, вернуть существующую
            serializer = self.get_serializer(recent_session)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Создание сессии в транзакции для предотвращения race condition
        try:
            with transaction.atomic():
                # Повторная проверка подписки внутри транзакции
                subscription.refresh_from_db()
                if subscription.remaining_tests <= 0:
                    return Response({'error': 'Не осталось тестов'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
                
                # Создание сессии
                session = TestSession.objects.create(
                    user=user,
                    test=test,
                    candidate_email=candidate_email,
                    candidate_name=candidate_name or '',
                    candidate_age=candidate_age,
                    time_limit_minutes=test.duration_minutes,
                    status=TestSession.STATUS_PENDING
                )
                
                # Уменьшение количества оставшихся тестов
                subscription.remaining_tests -= 1
                subscription.save(update_fields=['remaining_tests'])
                
                # Отправка email соискателю
                test_link = f"{settings.SITE_URL}/test/{session.id}/"
                email_sent = False
                email_error = None
                
                try:
                    from django.core.mail import EmailMessage
                    from django.template.loader import render_to_string
                    
                    # Проверяем, что email backend настроен правильно
                    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                        # Если используется console backend, выводим предупреждение
                        print(f"\n{'='*60}")
                        print(f"ВНИМАНИЕ: Используется console email backend!")
                        print(f"Письмо не будет отправлено реально.")
                        print(f"Настройте EMAIL_BACKEND в .env для реальной отправки.")
                        print(f"{'='*60}\n")
                    
                    # Создаем HTML письмо
                    subject = 'Приглашение пройти тестирование'
                    message = f'''Здравствуйте{f", {candidate_name}" if candidate_name else ""}!

Вам направлено приглашение пройти тестирование.
Перейдите по ссылке для начала: {test_link}

Тест: {test.name}
Длительность: {test.duration_minutes} минут

С уважением,
Команда системы тестирования персонала
'''
                    
                    # Отправляем письмо
                    result = send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [candidate_email],
                        fail_silently=False,  # Не скрываем ошибки
                    )
                    
                    if result:
                        email_sent = True
                        print(f"✓ Email успешно отправлен на {candidate_email}")
                    else:
                        email_error = "Email backend вернул False"
                        print(f"✗ Ошибка отправки email: {email_error}")
                        
                except Exception as e:
                    email_error = str(e)
                    # Логируем ошибку подробно
                    import traceback
                    print(f"\n{'='*60}")
                    print(f"ОШИБКА ОТПРАВКИ EMAIL:")
                    print(f"Email: {candidate_email}")
                    print(f"Ошибка: {email_error}")
                    print(f"Traceback:")
                    traceback.print_exc()
                    print(f"{'='*60}\n")
                    
                    # Если это не console backend, пробуем отправить через другой способ
                    if settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend':
                        # Пробуем использовать send_mail с fail_silently=True как fallback
                        try:
                            send_mail(
                                subject,
                                message,
                                settings.DEFAULT_FROM_EMAIL,
                                [candidate_email],
                                fail_silently=True,
                            )
                            print(f"Попытка отправки с fail_silently=True выполнена")
                        except:
                            pass
                
                serializer = self.get_serializer(session)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Ошибка создания сессии: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def start(self, request, pk=None):
        """Начать тест"""
        try:
            session = self.get_object()
        except NotFound as e:
            return Response({'error': f'Сессия не найдена: {str(e)}'}, 
                          status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Ошибка получения сессии: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if session.status != TestSession.STATUS_PENDING:
            return Response({'error': 'Тест уже начат или завершен'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            session.start_test()
            serializer = self.get_serializer(session)
            # Добавляем time_limit_minutes в ответ, если его нет
            response_data = serializer.data
            if 'time_limit_minutes' not in response_data or response_data['time_limit_minutes'] is None:
                response_data['time_limit_minutes'] = session.test.duration_minutes
            return Response(response_data)
        except Exception as e:
            return Response({'error': f'Ошибка начала теста: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def questions(self, request, pk=None):
        """Получить вопросы для теста"""
        import random
        session = self.get_object()
        
        # Получить вопросы для теста
        from .serializers import TestQuestionSerializer
        
        questions = TestQuestion.objects.filter(test=session.test)
        
        # Если вопросов нет в базе, создать их из данных теста (кроме IQ теста)
        if not questions.exists() and session.test.test_type != 'iq_test':
            self._create_questions_for_test(session.test)
            questions = TestQuestion.objects.filter(test=session.test)
        
        # Для теста личностных качеств - перемешиваем вопросы случайным образом
        if session.test.test_type == 'personal_qualities':
            questions_list = list(questions)
            # Используем хэш от session.id для детерминированного seed (чтобы порядок был одинаковым при повторных запросах)
            seed_value = hash(str(session.id)) % (2**31)  # Преобразуем в int для seed
            random.seed(seed_value)
            random.shuffle(questions_list)
            questions = questions_list
        else:
            questions = questions.order_by('order', 'question_number')
        
        serializer = TestQuestionSerializer(questions, many=True)
        return Response(serializer.data)
    
    def _create_questions_for_test(self, test):
        """Создать вопросы для теста на основе его типа (кроме IQ теста - вопросы заносятся вручную)"""
        if test.test_type == 'iq_test':
            # Для IQ теста вопросы не создаем автоматически - заносятся вручную
            return
        
        elif test.test_type == 'personal_qualities':
            from .data.personal_qualities_test import PERSONAL_QUALITIES_BLOCKS
            
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
            from .data.productivity_test import PRODUCTIVITY_QUESTIONS
            
            # Для теста продуктивности - открытые вопросы
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
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def submit_answer(self, request, pk=None):
        """Отправить ответ на вопрос"""
        session = self.get_object()
        
        if session.status != TestSession.STATUS_IN_PROGRESS:
            return Response({'error': 'Тест не начат'}, status=status.HTTP_400_BAD_REQUEST)
        
        question_number = request.data.get('question_number')
        answer_value = request.data.get('answer_value')
        series = request.data.get('series', '')
        
        if not question_number or answer_value is None:
            return Response({'error': 'question_number и answer_value обязательны'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Преобразуем question_number в int для правильной работы unique_together
        try:
            question_number = int(question_number)
        except (ValueError, TypeError):
            return Response({'error': 'question_number должен быть числом'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Используем транзакцию для предотвращения race condition
        try:
            with transaction.atomic():
                answer, created = TestAnswer.objects.update_or_create(
                    session=session,
                    question_number=question_number,
                    defaults={
                        'answer_value': str(answer_value),
                        'series': series or ''
                    }
                )
            
            serializer = TestAnswerSerializer(answer)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        except Exception as e:
            # Если возникла ошибка уникальности, пытаемся обновить существующую запись
            try:
                answer = TestAnswer.objects.get(session=session, question_number=question_number)
                answer.answer_value = str(answer_value)
                answer.series = series or ''
                answer.save()
                serializer = TestAnswerSerializer(answer)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except TestAnswer.DoesNotExist:
                return Response({'error': f'Ошибка сохранения ответа: {str(e)}'}, 
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def complete(self, request, pk=None):
        """Завершить тест и обработать результаты"""
        session = self.get_object()
        
        if session.status != TestSession.STATUS_IN_PROGRESS:
            return Response({'error': 'Тест не в процессе выполнения'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        session.complete_test()
        
        # Получение всех ответов
        answers = TestAnswer.objects.filter(session=session).order_by('question_number')
        answers_data = [
            {
                'question_number': answer.question_number,
                'answer': answer.answer_value,
                'series': answer.series
            }
            for answer in answers
        ]
        
        # Обработка результатов в зависимости от типа теста
        result_data = {}
        try:
            if session.test.test_type == 'iq_test':
                # Преобразование ответов для IQ теста
                raven_answers = []
                for a in answers_data:
                    try:
                        answer_value = int(a['answer'])
                        if 1 <= answer_value <= 6:
                            raven_answers.append({
                                'question_number': a['question_number'],
                                'answer': answer_value
                            })
                    except (ValueError, TypeError):
                        continue
                
                if raven_answers:
                    result_data = process_raven_test(session, raven_answers)
                else:
                    return Response({'error': 'Нет валидных ответов для обработки'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
                    
            elif session.test.test_type == 'personal_qualities':
                # Обработка теста личностных качеств
                # Получаем вопросы с их типами и блоками
                from .models import TestQuestion
                questions = TestQuestion.objects.filter(test=session.test).select_related()
                question_map = {q.question_number: q for q in questions}
                
                # Формируем ответы с информацией о блоках и типах
                formatted_answers = []
                for a in answers_data:
                    q_num = a['question_number']
                    question = question_map.get(q_num)
                    if question:
                        formatted_answers.append({
                            'question_number': q_num,
                            'answer': a['answer'],
                            'block_name': question.block_name or '',
                            'question_type': question.question_type or '+',
                        })
                    else:
                        formatted_answers.append({
                            'question_number': q_num,
                            'answer': a['answer'],
                            'block_name': '',
                            'question_type': '+',
                        })
                
                result_data = process_personal_qualities_test(formatted_answers)
                
            elif session.test.test_type == 'productivity':
                # Обработка теста продуктивности
                result_data = process_productivity_test(answers_data)
            else:
                return Response({'error': 'Неизвестный тип теста'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Ошибка обработки результатов: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Создание результата
        if not result_data:
            return Response({'error': 'Не удалось обработать результаты'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        test_result = TestResult.objects.create(
            session=session,
            raw_score=result_data.get('raw_score'),
            final_score=result_data.get('final_score'),
            iq_score=result_data.get('iq_score'),
            iq_level=result_data.get('iq_level', ''),
            scores_json=result_data.get('scores_json', {}),
            report=result_data.get('report', ''),
            report_json=result_data.get('report_json', {}),
            is_processed=True,
            processed_at=timezone.now()
        )
        
        # Отправка email пользователю с результатами
        if session.user:
            try:
                send_mail(
                    f'Результаты тестирования: {session.candidate_email}',
                    f'Результаты тестирования для {session.candidate_email}:\n\n'
                    f'{test_result.report}',
                    settings.DEFAULT_FROM_EMAIL,
                    [session.user.email],
                    fail_silently=True,  # Не прерывать выполнение при ошибке email
                )
            except Exception as e:
                # Логируем ошибку, но не прерываем выполнение
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка отправки email для сессии {session.id}: {str(e)}")
        
        serializer = TestResultSerializer(test_result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_sessions(self, request):
        """Получить все сессии текущего пользователя"""
        sessions = TestSession.objects.filter(user=request.user).order_by('-created_at')
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def get_result(self, request, pk=None):
        """Получить результат теста (только для владельца сессии)"""
        session = self.get_object()
        
        # Проверка, что сессия принадлежит пользователю
        if session.user != request.user:
            return Response({'error': 'Нет доступа к этому тесту'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Проверка, что тест завершен
        if session.status != TestSession.STATUS_COMPLETED:
            return Response({'error': 'Тест еще не завершен'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            test_result = TestResult.objects.get(session=session)
            serializer = TestResultSerializer(test_result)
            return Response(serializer.data)
        except TestResult.DoesNotExist:
            return Response({'error': 'Результаты теста не найдены'}, 
                          status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def download_pdf(self, request, pk=None):
        """Скачать PDF отчет о результатах теста (серверная генерация через ReportLab)"""
        session = self.get_object()
        
        # Проверка, что сессия принадлежит пользователю
        if session.user != request.user:
            return Response({'error': 'Нет доступа к этому тесту'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Проверка, что тест завершен
        if session.status != TestSession.STATUS_COMPLETED:
            return Response({'error': 'Тест еще не завершен'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            test_result = TestResult.objects.get(session=session)
            serializer = TestResultSerializer(test_result)
            result_data = serializer.data
            
            # Генерация PDF на сервере
            pdf_buffer = generate_pdf_report(result_data)
            
            # Формирование имени файла
            candidate_name = session.candidate_name or session.candidate_email
            safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            test_name = session.test.name.replace(' ', '_')
            date_str = timezone.now().strftime('%Y-%m-%d')
            filename = f"Отчет_{safe_name}_{test_name}_{date_str}.pdf"
            
            # Создание HTTP ответа
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'
            return response
            
        except TestResult.DoesNotExist:
            return Response({'error': 'Результаты теста не найдены'}, 
                          status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': f'Ошибка генерации PDF: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TestResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TestResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TestResult.objects.filter(session__user=self.request.user).order_by('-created_at')
