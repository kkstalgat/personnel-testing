"""
Данные для IQ-теста
60 вопросов, 5 серий (A, B, C, D, E), по 12 вопросов в каждой серии
"""

RAVEN_TEST_ANSWER_KEY = {
    # Серия A (1-12)
    'A1': 4, 'A2': 5, 'A3': 1, 'A4': 2, 'A5': 6, 'A6': 3,
    'A7': 6, 'A8': 2, 'A9': 1, 'A10': 3, 'A11': 4, 'A12': 5,
    
    # Серия B (13-24)
    'B1': 2, 'B2': 6, 'B3': 1, 'B4': 2, 'B5': 1, 'B6': 3,
    'B7': 5, 'B8': 6, 'B9': 4, 'B10': 3, 'B11': 4, 'B12': 5,
    
    # Серия C (25-36)
    'C1': 8, 'C2': 2, 'C3': 3, 'C4': 8, 'C5': 7, 'C6': 4,
    'C7': 5, 'C8': 1, 'C9': 7, 'C10': 6, 'C11': 1, 'C12': 2,
    
    # Серия D (37-48)
    'D1': 3, 'D2': 4, 'D3': 3, 'D4': 7, 'D5': 8, 'D6': 6,
    'D7': 5, 'D8': 4, 'D9': 1, 'D10': 2, 'D11': 5, 'D12': 6,
    
    # Серия E (49-60)
    'E1': 7, 'E2': 6, 'E3': 8, 'E4': 2, 'E5': 1, 'E6': 5,
    'E7': 1, 'E8': 6, 'E9': 3, 'E10': 2, 'E11': 4, 'E12': 5,
}

# Функция для получения правильного ответа по номеру вопроса
def get_correct_answer(question_number):
    """Получить правильный ответ на вопрос по номеру (1-60)"""
    series_map = {
        (1, 12): 'A',
        (13, 24): 'B',
        (25, 36): 'C',
        (37, 48): 'D',
        (49, 60): 'E',
    }
    
    for (start, end), series in series_map.items():
        if start <= question_number <= end:
            series_num = question_number - start + 1
            key = f'{series}{series_num}'
            return RAVEN_TEST_ANSWER_KEY.get(key)
    return None


# IQ таблица перевода сырого балла в IQ
IQ_TABLE = {
    (60, 60): (140, 140),
    (55, 59): (122, 130),
    (50, 54): (112, 120),
    (45, 49): (102, 110),
    (40, 44): (95, 100),
    (35, 39): (88, 94),
    (30, 34): (82, 87),
    (25, 29): (75, 80),
    (0, 24): (0, 70),
}


def get_iq_from_raw_score(raw_score):
    """Получить IQ балл из сырого балла"""
    for (min_score, max_score), (min_iq, max_iq) in IQ_TABLE.items():
        if min_score <= raw_score <= max_score:
            if min_iq == max_iq:
                return min_iq
            # Среднее значение для диапазона
            return (min_iq + max_iq) // 2
    return 70  # Минимальный IQ


# Возрастные коэффициенты
AGE_COEFFICIENTS = {
    (14, 30): 1.0,
    35: 0.97,
    40: 0.93,
    45: 0.88,
    50: 0.82,
    55: 0.76,
    60: 0.70,
}


def get_age_coefficient(age):
    """Получить коэффициент корректировки на возраст"""
    if age < 14:
        return 1.0
    if age > 60:
        return 0.70
    
    if isinstance(AGE_COEFFICIENTS.get(age), (int, float)):
        return AGE_COEFFICIENTS[age]
    
    for key, value in AGE_COEFFICIENTS.items():
        if isinstance(key, tuple) and key[0] <= age <= key[1]:
            return value
    
    # Найти ближайшее значение
    ages = [k for k in AGE_COEFFICIENTS.keys() if isinstance(k, int)]
    if ages:
        closest_age = min(ages, key=lambda x: abs(x - age))
        return AGE_COEFFICIENTS[closest_age]
    
    return 1.0


def calculate_final_iq(base_iq, age):
    """Рассчитать итоговый IQ с учетом возраста"""
    coefficient = get_age_coefficient(age)
    if coefficient == 0:
        return base_iq
    final_iq = int((base_iq / coefficient) * 100) / 100
    return round(final_iq)


def get_iq_level(iq_score):
    """Получить уровень IQ"""
    if iq_score > 121:
        return 'Высокий / Незаурядный интеллект'
    elif 111 <= iq_score <= 120:
        return 'Интеллект выше среднего'
    elif 91 <= iq_score <= 110:
        return 'Средний интеллект'
    elif 81 <= iq_score <= 90:
        return 'Интеллект ниже среднего'
    else:
        return 'Низкий уровень'
