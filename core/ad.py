"""
ad.py - Структура данных объявления Авито
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Ad:
    id: str = ""
    title: str = ""
    price: Optional[float] = None
    address: str = ""
    description: str = ""
    published_on: Optional[date] = None
    views: int = 0
    url: str = ""
    status: int = 1     # 1 - активно, 0 - закрыто
    city: str = ""
    query: str = ""
    cached_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None