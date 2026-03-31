"""
field_parsers.py — Парсинг сырых строк полей объявлений Авито в типизированные значения
"""

import re
from datetime import date, timedelta
from typing import Optional


def parse_price(raw: str) -> Optional[float]:
    """
    Преобразование строки цены в число с плавающей точкой (рубли.копейки)
    """
    if not raw:
        return None

    normalized = raw.strip().lower()

    if normalized in ("бесплатно", "даром"):
        return 0.00

    if any(w in normalized for w in ("не указан", "договор", "обмен")):
        return None

    m = re.search(r"[\d\s]+(?:[.,]\d+)?", normalized)
    if not m:
        return None

    number_str = m.group(0).replace(" ", "").replace(",", ".")
    try:
        return round(float(number_str), 2)
    except ValueError:
        return None


_MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def parse_date(raw: str) -> Optional[date]:
    """
    Преобразование строки даты Авито в объект date без временной зоны

    Возвращает None если формат не распознан
    """
    if not raw:
        return None

    normalized = raw.strip().lower()
    today = date.today()

    if normalized.startswith("сегодня"):
        return today

    if normalized.startswith("вчера"):
        return today - timedelta(days=1)

    m = re.match(r"(\d+)\s+д", normalized)
    if m:
        return today - timedelta(days=int(m.group(1)))

    m = re.match(r"(\d{1,2})\s+([а-яё]+)(?:\s+(\d{4}))?", normalized)
    if m:
        day = int(m.group(1))
        month = _MONTHS.get(m.group(2))
        year = int(m.group(3)) if m.group(3) else today.year
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                return None

    return None
