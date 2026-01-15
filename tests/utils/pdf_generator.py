"""
Утилита для генерации PDF отчетов с графиками
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, Group, Line, String
from reportlab.graphics import renderPDF
from reportlab.platypus import Image as RLImage
import re
import os

# Регистрируем шрифты с поддержкой кириллицы
def _register_cyrillic_fonts():
    """Регистрирует шрифты с поддержкой кириллицы"""
    try:
        # Пытаемся использовать встроенные шрифты ReportLab для кириллицы
        # Используем стандартные шрифты, которые поддерживают Unicode
        if not hasattr(_register_cyrillic_fonts, '_registered'):
            # Регистрируем шрифт для кириллицы (используем встроенные шрифты)
            try:
                # Пытаемся зарегистрировать DejaVu Sans, если доступен
                font_paths = [
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                    'C:/Windows/Fonts/arial.ttf',
                    'C:/Windows/Fonts/arialuni.ttf',
                ]
                
                font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('CyrillicFont', font_path))
                            pdfmetrics.registerFont(TTFont('CyrillicFontBold', font_path.replace('Regular', 'Bold').replace('arial.ttf', 'arialbd.ttf')))
                            font_registered = True
                            break
                        except:
                            continue
                
                if not font_registered:
                    # Используем встроенные шрифты ReportLab с поддержкой Unicode
                    # ReportLab имеет встроенную поддержку кириллицы через CIDFont
                    pass
                    
            except Exception as e:
                print(f"Ошибка регистрации шрифта: {e}")
            
            _register_cyrillic_fonts._registered = True
    except:
        pass

# Вызываем регистрацию при импорте
_register_cyrillic_fonts()


def generate_pdf_report(result_data):
    """
    Генерирует PDF отчет из данных результата теста
    
    Args:
        result_data: словарь с данными результата теста (сериализованный TestResult)
    
    Returns:
        BytesIO: буфер с PDF файлом
    """
    # Регистрируем шрифты перед созданием документа
    _register_cyrillic_fonts()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=20*mm, bottomMargin=20*mm)
    
    # Контейнер для элементов PDF
    story = []
    
    # Стили
    styles = getSampleStyleSheet()
    
    # Определяем шрифт с поддержкой кириллицы
    # Используем встроенные шрифты ReportLab, которые поддерживают Unicode
    cyrillic_font = 'Helvetica'  # По умолчанию
    cyrillic_font_bold = 'Helvetica-Bold'
    
    # Пытаемся использовать зарегистрированный кириллический шрифт
    if 'CyrillicFont' in pdfmetrics.getRegisteredFontNames():
        cyrillic_font = 'CyrillicFont'
        cyrillic_font_bold = 'CyrillicFontBold'
    else:
        # Используем встроенные шрифты ReportLab с поддержкой Unicode
        # Helvetica в ReportLab поддерживает базовый Unicode, но лучше использовать Times-Roman или Courier
        # Для лучшей поддержки кириллицы используем Times-Roman
        cyrillic_font = 'Times-Roman'
        cyrillic_font_bold = 'Times-Bold'
    
    # Заголовок
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1976D2'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName=cyrillic_font_bold,
        encoding='utf-8'
    )
    
    # Подзаголовок
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12,
        fontName=cyrillic_font_bold,
        encoding='utf-8'
    )
    
    # Обычный текст
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#000000'),
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        fontName=cyrillic_font,
        encoding='utf-8'
    )
    
    # Информация о соискателе
    info_style = ParagraphStyle(
        'CustomInfo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        spaceAfter=6,
        fontName=cyrillic_font,
        encoding='utf-8'
    )
    
    # Заголовок документа
    session = result_data.get('session', {})
    test = session.get('test', {})
    test_type = test.get('test_type', '')  # Определяем test_type сразу, до использования
    title = f"Отчет по тестированию: {test.get('name', 'Тест')}"
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12*mm))
    
    # Информация о соискателе
    story.append(Paragraph("Информация о соискателе", heading_style))
    
    candidate_name = session.get('candidate_name') or session.get('candidate_email', '')
    story.append(Paragraph(f"<b>Соискатель:</b> {candidate_name}", info_style))
    story.append(Paragraph(f"<b>Email:</b> {session.get('candidate_email', '')}", info_style))
    story.append(Paragraph(f"<b>Тест:</b> {test.get('name', '')}", info_style))
    
    # Даты
    if session.get('created_at'):
        from django.utils import timezone
        from datetime import datetime
        created_at = session.get('created_at')
        if isinstance(created_at, str):
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                story.append(Paragraph(f"<b>Дата создания:</b> {created_date.strftime('%d.%m.%Y %H:%M')}", info_style))
            except:
                story.append(Paragraph(f"<b>Дата создания:</b> {created_at}", info_style))
    
    story.append(Spacer(1, 6*mm))
    
    # Результаты (если есть IQ)
    if result_data.get('iq_score'):
        iq_score = result_data.get('iq_score')
        iq_level = result_data.get('iq_level', '')
        raw_score = result_data.get('raw_score')
        
        # Создаем визуальный график IQ в стиле картинки
        if test_type == 'iq_test':
            story.append(Spacer(1, 10*mm))
            # Большой балл
            iq_style = ParagraphStyle(
                'IQScore',
                parent=title_style,
                fontSize=48,
                textColor=colors.HexColor('#333333'),
                spaceAfter=20,
                alignment=TA_LEFT,
                fontName=cyrillic_font_bold
            )
            story.append(Paragraph(f"<b>{iq_score} баллов</b>", iq_style))
            story.append(Spacer(1, 15*mm))
            
            # График IQ
            iq_chart = _create_iq_chart(iq_score, cyrillic_font, cyrillic_font_bold)
            story.append(iq_chart)
            story.append(Spacer(1, 15*mm))
            
            # Описание уровней IQ
            story.append(Paragraph("Интерпретация результатов IQ:", ParagraphStyle(
                'IQLevelsTitle',
                parent=heading_style,
                fontSize=14,
                fontName=cyrillic_font_bold,
                spaceAfter=10,
                spaceBefore=10,
                encoding='utf-8'
            )))
            
            # Описания уровней
            iq_descriptions = [
                (70, 85, "Очень низкий", "Очень низкий уровень интеллекта. Не подходит для руководящих должностей и должностей, требующих применения умственных способностей."),
                (85, 100, "Низкий", "Низкий уровень интеллекта. Человек с таким интеллектом с трудом оценивает ситуацию и принимает разумные решения. Не подходит для руководящих должностей и решения задач, требующих применения аналитических способностей."),
                (100, 120, "Средний", "Средний уровень интеллекта. Человек с таким интеллектом в целом может оценивать ситуации. Этого уровня интеллекта хватит для принятия не очень сложных решений, но такой сотрудник не рекомендован для руководящих должностей."),
                (120, 140, "Высокий", "Высокий уровень интеллекта. Человек с таким интеллектом способен хорошо оценивать ситуации, принимать решения, которые требуют логического и аналитического мышления. Подходит для руководящих и линейных должностей."),
                (140, 200, "Очень высокий", "Очень высокий уровень интеллекта. Человек с таким интеллектом способен оценивать ситуацию, принимать решения, которые требуют логического и аналитического мышления. Рекомендован на руководящие и любые другие должности."),
            ]
            
            for min_iq, max_iq, level_name, description in iq_descriptions:
                if min_iq <= iq_score < max_iq or (max_iq == 200 and iq_score >= min_iq):
                    # Выделяем текущий уровень
                    level_style = ParagraphStyle(
                        'IQCurrentLevel',
                        parent=normal_style,
                        fontSize=12,
                        fontName=cyrillic_font_bold,
                        textColor=colors.HexColor('#1976d2'),
                        spaceAfter=5,
                        spaceBefore=8,
                        leftIndent=5*mm,
                        encoding='utf-8'
                    )
                    story.append(Paragraph(f"<b>{min_iq}-{max_iq if max_iq < 200 else 'макс'} баллов ({level_name}):</b> {description}", level_style))
                else:
                    desc_style = ParagraphStyle(
                        'IQLevel',
                        parent=normal_style,
                        fontSize=10,
                        fontName=cyrillic_font,
                        spaceAfter=5,
                        spaceBefore=5,
                        leftIndent=5*mm,
                        encoding='utf-8'
                    )
                    story.append(Paragraph(f"<b>{min_iq}-{max_iq if max_iq < 200 else 'макс'} баллов ({level_name}):</b> {description}", desc_style))
            
            story.append(Spacer(1, 10*mm))
            
            # Заключение
            conclusion_style = ParagraphStyle(
                'IQConclusion',
                parent=normal_style,
                fontSize=11,
                fontName=cyrillic_font,
                spaceAfter=5,
                spaceBefore=10,
                encoding='utf-8'
            )
            story.append(Paragraph("IQ - только часть пазла.", ParagraphStyle(
                'IQConclusionTitle',
                parent=heading_style,
                fontSize=14,
                fontName=cyrillic_font_bold,
                spaceAfter=8,
                spaceBefore=10,
                encoding='utf-8'
            )))
            story.append(Paragraph(
                "Интеллект показывает способность человека видеть сходства, различия и тождества. "
                "Уровень IQ показывает насколько он способен разумно мыслить, оценивать ситуации и принимать решения. "
                "Этот индикатор особенно важен при выборе руководителя. Но неверно принимать решение о том, "
                "подходит сотрудник или нет, только на основании IQ-теста. Важно оценить его продуктивность "
                "тестом «Оценка продуктивности» и характер тестом «Оценка личностных качеств».",
                conclusion_style
            ))
            story.append(Spacer(1, 10*mm))
        else:
            # Для других тестов - обычное отображение
            story.append(Paragraph("Результаты тестирования", heading_style))
            story.append(Paragraph(f"<b>IQ балл:</b> {iq_score}", normal_style))
            if iq_level:
                story.append(Paragraph(f"<b>Уровень развития:</b> {iq_level}", normal_style))
            if raw_score is not None:
                story.append(Paragraph(f"<b>Сырой балл:</b> {raw_score}", normal_style))
            story.append(Spacer(1, 6*mm))
    
    # Отчет
    report_text = result_data.get('report', '')
    # test_type уже определен выше (строка 155)
    
    if report_text:
        # Для теста личностных качеств - парсим график
        if test_type == 'personal_qualities':
            story.append(Paragraph("Детальный отчет", heading_style))
            story = _add_personal_qualities_chart(story, report_text, heading_style, normal_style, info_style)
        
        # Добавляем остальной текст отчета
        lines = report_text.split('\n')
        skip_chart_section = False
        in_chart_section = False
        
        for line in lines:
            line = line.strip()
            
            # Пропускаем секцию графика (уже обработана)
            if line.startswith('#### ЧАСТЬ 1:') or 'ЦИФРОВОЙ ПРОФИЛЬ' in line:
                in_chart_section = True
                skip_chart_section = True
                continue
            elif in_chart_section and (line.startswith('#### ЧАСТЬ 2:') or line.startswith('#### ЧАСТЬ 3:')):
                in_chart_section = False
                skip_chart_section = False
            
            if skip_chart_section or not line:
                if not line:
                    story.append(Spacer(1, 3*mm))
                continue
            
            # Заголовки (##)
            if line.startswith('##'):
                text = line.replace('##', '').strip()
                story.append(Paragraph(f"<b>{text}</b>", heading_style))
            # Подзаголовки (### или ####)
            elif line.startswith('###'):
                text = re.sub(r'^#+\s*', '', line).strip()
                story.append(Paragraph(f"<b>{text}</b>", ParagraphStyle(
                    'SubHeading',
                    parent=normal_style,
                    fontSize=12,
                    fontName=cyrillic_font_bold,
                    spaceAfter=8,
                    spaceBefore=8,
                    encoding='utf-8'
                )))
            # Жирный текст (**текст**)
            elif '**' in line:
                line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                story.append(Paragraph(line, normal_style))
            # Списки (- или *)
            elif line.startswith('- ') or line.startswith('* ') or line.startswith('1. '):
                text = re.sub(r'^[-\*\d.]+\s+', '', line).strip()
                story.append(Paragraph(f"• {text}", normal_style))
            # Обычный текст
            else:
                # Экранирование HTML символов, но сохраняем разметку
                line = line.replace('&', '&amp;')
                # Не экранируем уже существующие HTML теги
                if '<' in line and '>' in line:
                    # Уже есть HTML, не экранируем
                    pass
                else:
                    line = line.replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(line, normal_style))
    else:
        story.append(Paragraph("Отчет еще не сформирован", normal_style))
    
    # Генерация PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def _add_personal_qualities_chart(story, report_text, heading_style, normal_style, info_style):
    """Добавить график для теста личностных качеств"""
    from reportlab.platypus import Table
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    
    # Определяем шрифты с поддержкой кириллицы
    registered_fonts = pdfmetrics.getRegisteredFontNames()
    if 'CyrillicFont' in registered_fonts:
        cyrillic_font = 'CyrillicFont'
        cyrillic_font_bold = 'CyrillicFontBold' if 'CyrillicFontBold' in registered_fonts else 'CyrillicFont'
    else:
        cyrillic_font = 'Times-Roman'
        cyrillic_font_bold = 'Times-Bold'
    
    # Парсим график из отчета
    quality_scores = {}
    lines = report_text.split('\n')
    in_chart = False
    
    for line in lines:
        line = line.strip()
        if 'ЦИФРОВОЙ ПРОФИЛЬ' in line or 'ЧАСТЬ 1:' in line:
            in_chart = True
            continue
        elif line.startswith('#### ЧАСТЬ 2:') or line.startswith('#### ЧАСТЬ 3:'):
            in_chart = False
            break
        
        if in_chart and line:
            # Парсим строку типа: "Внимательность [████████████░░░░░░░░] 11.5/20 (Средний уровень)"
            match = re.match(r'^(\w+)\s*\[.*?\]\s*(\d+\.?\d*)/20\s*\((.*?)\)', line)
            if match:
                quality_name = match.group(1).strip()
                score = float(match.group(2))
                level = match.group(3).strip()
                quality_scores[quality_name] = {'score': score, 'level': level}
    
    # Если не нашли данные, пытаемся парсить из текста иначе
    if not quality_scores:
        # Ищем все качества из отчета
        qualities_list = ['Внимательность', 'Позитивность', 'Самообладание', 'Ответственность', 
                         'Уверенность', 'Активность', 'Настойчивость', 'Объективность', 
                         'Чуткость', 'Общительность']
        
        for line in lines:
            for quality in qualities_list:
                if quality in line:
                    # Пытаемся извлечь балл
                    score_match = re.search(r'(\d+\.?\d*)\s*/?\s*20', line)
                    level_match = re.search(r'\((.*?)\)', line)
                    if score_match:
                        score = float(score_match.group(1))
                        level = level_match.group(1).strip() if level_match else 'Не определен'
                        quality_scores[quality] = {'score': score, 'level': level}
    
    # Создаем график
    if quality_scores:
        story.append(Paragraph("#### ЧАСТЬ 1: ЦИФРОВОЙ ПРОФИЛЬ", heading_style))
        story.append(Spacer(1, 10*mm))
        
        # Таблица с графиком
        table_data = [['Качество', 'Балл', 'Уровень']]
        
        # Порядок качеств
        quality_order = ['Внимательность', 'Позитивность', 'Самообладание', 'Ответственность',
                        'Уверенность', 'Активность', 'Настойчивость', 'Объективность',
                        'Чуткость', 'Общительность']
        
        for quality in quality_order:
            if quality in quality_scores:
                data = quality_scores[quality]
                table_data.append([
                    quality,
                    f"{data['score']}/20",
                    data['level']
                ])
        
        # Создаем таблицу
        table = Table(table_data, colWidths=[60*mm, 30*mm, 60*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), cyrillic_font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), cyrillic_font),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 10*mm))
        
        # Создаем визуальный график в стиле второй картинки
        story.append(Paragraph("Визуализация результатов:", ParagraphStyle(
            'ChartTitle',
            parent=normal_style,
            fontSize=14,
            fontName=cyrillic_font_bold,
            spaceAfter=12,
            spaceBefore=8,
            encoding='utf-8'
        )))
        
        # Создаем график с горизонтальными полосами
        chart_drawing = _create_bar_chart(quality_scores, quality_order, cyrillic_font, cyrillic_font_bold)
        story.append(chart_drawing)
        story.append(Spacer(1, 10*mm))
    
    return story


def _create_bar_chart(quality_scores, quality_order, cyrillic_font, cyrillic_font_bold):
    """Создает визуальный график с горизонтальными полосами в стиле второй картинки"""
    from reportlab.graphics.shapes import Drawing, Rect, Group, Line, String
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    
    # Размеры графика
    chart_width = 170 * mm
    chart_height = len(quality_order) * 12 * mm + 30 * mm
    bar_width = 120 * mm
    bar_height = 8 * mm
    bar_spacing = 12 * mm
    left_margin = 50 * mm
    
    drawing = Drawing(chart_width, chart_height)
    
    # Цвета для разных уровней
    def get_color(score):
        if score < 7:
            return colors.HexColor('#d32f2f')  # Красный для низкого
        elif score < 15:
            return colors.HexColor('#1976d2')  # Синий для среднего
        else:
            return colors.HexColor('#388e3c')  # Зеленый для высокого
    
    # Рисуем шкалу
    scale_y = chart_height - 20 * mm
    scale_start_x = left_margin
    scale_end_x = left_margin + bar_width
    
    # Линия шкалы
    drawing.add(Line(scale_start_x, scale_y, scale_end_x, scale_y, 
                     strokeColor=colors.grey, strokeWidth=1))
    
    # Метки шкалы
    scale_labels = ['0', '5', '10', '15', '20']
    scale_positions = [0, 25, 50, 75, 100]  # Проценты
    
    for i, (label, pos) in enumerate(zip(scale_labels, scale_positions)):
        x = scale_start_x + (bar_width * pos / 100)
        # Вертикальная метка
        drawing.add(Line(x, scale_y - 2*mm, x, scale_y + 2*mm, 
                         strokeColor=colors.grey, strokeWidth=0.5))
        # Текст метки
        drawing.add(String(x, scale_y - 6*mm, label, 
                          fontName=cyrillic_font, fontSize=8, 
                          textAnchor='middle', fillColor=colors.black))
    
    # Метки уровней
    level_labels = ['Низкий', 'Средний', 'Высокий']
    level_positions = [10, 50, 90]  # Проценты
    
    for label, pos in zip(level_labels, level_positions):
        x = scale_start_x + (bar_width * pos / 100)
        drawing.add(String(x, scale_y + 6*mm, label, 
                          fontName=cyrillic_font, fontSize=7, 
                          textAnchor='middle', fillColor=colors.grey))
    
    # Рисуем полосы для каждого качества
    y_position = scale_y - 15 * mm
    
    for quality in quality_order:
        if quality in quality_scores:
            data = quality_scores[quality]
            score = data['score']
            level = data['level']
            
            # Вычисляем ширину полосы
            bar_length = (score / 20) * bar_width
            
            # Цвет полосы
            bar_color = get_color(score)
            
            # Рисуем полосу
            drawing.add(Rect(left_margin, y_position - bar_height/2, 
                           bar_length, bar_height,
                           fillColor=bar_color, strokeColor=bar_color, strokeWidth=0))
            
            # Рисуем фон (незаполненная часть)
            if bar_length < bar_width:
                drawing.add(Rect(left_margin + bar_length, y_position - bar_height/2,
                               bar_width - bar_length, bar_height,
                               fillColor=colors.HexColor('#e0e0e0'), 
                               strokeColor=colors.HexColor('#bdbdbd'), strokeWidth=0.5))
            
            # Название качества слева
            drawing.add(String(left_margin - 5*mm, y_position, quality,
                             fontName=cyrillic_font_bold, fontSize=9,
                             textAnchor='end', fillColor=colors.black))
            
            # Значение справа от полосы
            value_text = f"{score}/20"
            drawing.add(String(left_margin + bar_width + 5*mm, y_position, value_text,
                             fontName=cyrillic_font, fontSize=9,
                             textAnchor='start', fillColor=colors.black))
            
            # Уровень под значением
            level_y = y_position - 4*mm
            drawing.add(String(left_margin + bar_width + 5*mm, level_y, f"({level})",
                             fontName=cyrillic_font, fontSize=7,
                             textAnchor='start', fillColor=colors.grey))
            
            y_position -= bar_spacing
    
    return drawing


def _create_iq_chart(iq_score, cyrillic_font, cyrillic_font_bold):
    """Создает визуальный график IQ в стиле картинки с цветными сегментами и маркером"""
    from reportlab.graphics.shapes import Drawing, Rect, Line, String, Polygon
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    
    # Размеры графика
    chart_width = 170 * mm
    chart_height = 60 * mm
    bar_width = 150 * mm
    bar_height = 12 * mm
    left_margin = 10 * mm
    top_margin = 40 * mm
    
    drawing = Drawing(chart_width, chart_height)
    
    # Диапазон IQ для шкалы (от 70 до 160)
    iq_min = 70
    iq_max = 160
    
    # Рисуем цветные сегменты шкалы
    segments = [
        (70, 85, "очень низкий", colors.HexColor('#1565c0')),  # Темно-синий
        (85, 100, "низкий", colors.HexColor('#42a5f5')),  # Светло-синий
        (100, 120, "средний", colors.HexColor('#26a69a')),  # Бирюзовый
        (120, 140, "высокий", colors.HexColor('#66bb6a')),  # Зеленый
        (140, 160, "очень высокий", colors.HexColor('#388e3c')),  # Темно-зеленый
    ]
    
    bar_y = top_margin
    
    for min_iq, max_iq, level_name, color in segments:
        # Вычисляем позицию и ширину сегмента
        start_x = left_margin + ((min_iq - iq_min) / (iq_max - iq_min)) * bar_width
        end_x = left_margin + ((max_iq - iq_min) / (iq_max - iq_min)) * bar_width
        segment_width = end_x - start_x
        
        # Рисуем сегмент
        drawing.add(Rect(start_x, bar_y - bar_height/2, segment_width, bar_height,
                        fillColor=color, strokeColor=color, strokeWidth=0))
        
        # Метка уровня (только для ключевых границ)
        if max_iq in [85, 100, 120, 140]:
            label_x = end_x
            # Вертикальная линия метки
            drawing.add(Line(label_x, bar_y - bar_height/2 - 3*mm, label_x, bar_y + bar_height/2 + 3*mm,
                           strokeColor=colors.black, strokeWidth=0.5))
            # Текст метки
            drawing.add(String(label_x, bar_y - bar_height/2 - 6*mm, str(max_iq),
                             fontName=cyrillic_font, fontSize=8,
                             textAnchor='middle', fillColor=colors.black))
    
    # Метки min и max
    drawing.add(String(left_margin, bar_y - bar_height/2 - 6*mm, "min",
                      fontName=cyrillic_font, fontSize=8,
                      textAnchor='start', fillColor=colors.black))
    drawing.add(String(left_margin + bar_width, bar_y - bar_height/2 - 6*mm, "max",
                      fontName=cyrillic_font, fontSize=8,
                      textAnchor='end', fillColor=colors.black))
    
    # Подписи уровней над сегментами
    label_y = bar_y + bar_height/2 + 5*mm
    for min_iq, max_iq, level_name, color in segments:
        start_x = left_margin + ((min_iq - iq_min) / (iq_max - iq_min)) * bar_width
        end_x = left_margin + ((max_iq - iq_min) / (iq_max - iq_min)) * bar_width
        center_x = (start_x + end_x) / 2
        
        # Проверяем, в каком сегменте находится IQ
        if min_iq <= iq_score < max_iq or (max_iq == 160 and iq_score >= min_iq):
            # Выделяем текущий уровень жирным
            drawing.add(String(center_x, label_y, level_name,
                             fontName=cyrillic_font_bold, fontSize=9,
                             textAnchor='middle', fillColor=colors.black))
        else:
            drawing.add(String(center_x, label_y, level_name,
                             fontName=cyrillic_font, fontSize=8,
                             textAnchor='middle', fillColor=colors.grey))
    
    # Рисуем треугольный маркер для значения IQ
    if iq_min <= iq_score <= iq_max:
        marker_x = left_margin + ((iq_score - iq_min) / (iq_max - iq_min)) * bar_width
        marker_y = bar_y + bar_height/2
        
        # Треугольник маркера (перевернутый)
        triangle_size = 4 * mm
        triangle = Polygon(
            points=[
                marker_x, marker_y + triangle_size,
                marker_x - triangle_size, marker_y,
                marker_x + triangle_size, marker_y
            ],
            fillColor=colors.HexColor('#388e3c'),
            strokeColor=colors.HexColor('#388e3c'),
            strokeWidth=1
        )
        drawing.add(triangle)
        
        # Значение IQ под маркером
        drawing.add(String(marker_x, marker_y + triangle_size + 4*mm, str(iq_score),
                          fontName=cyrillic_font_bold, fontSize=10,
                          textAnchor='middle', fillColor=colors.HexColor('#388e3c')))
    
    return drawing
