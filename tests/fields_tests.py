"""
fields_tests.py - Тесты для field_parsers.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, timedelta

from helpers import check, summary
from loguru import logger

from core.field_parsers import parse_date, parse_price


def run():
    logger.info("====field_parsers====")

    logger.info("Тест parse_price:")
    check("1 500 ₽ -> 1500.0", parse_price("1 500 ₽"), 1500.0)
    check("100 000 руб. -> 100000.0", parse_price("100 000 руб."), 100000.0)
    check("99.50 ₽ -> 99.5", parse_price("99.50 ₽"), 99.5)
    check("Бесплатно -> 0.0", parse_price("Бесплатно"), 0.0)
    check("даром -> 0.0", parse_price("даром"), 0.0)
    check("Цена не указана -> None", parse_price("Цена не указана"), None)
    check("Договорная -> None", parse_price("Договорная"), None)
    check("пустая строка -> None", parse_price(""), None)

    logger.info("Тест parse_date:")
    today = date.today()
    check(f"сегодня в 14:32 -> {today}", parse_date("сегодня в 14:32"), today)
    check(
        f"вчера в 09:00 -> {today - timedelta(days=1)}",
        parse_date("вчера в 09:00"),
        today - timedelta(days=1),
    )
    check(
        f"2 дня назад -> {today - timedelta(days=2)}",
        parse_date("2 дня назад"),
        today - timedelta(days=2),
    )
    check("15 марта 2024 -> 2024-03-15", parse_date("15 марта 2024"), date(2024, 3, 15))
    check(
        f"15 марта -> {date(today.year, 3, 15)}",
        parse_date("15 марта"),
        date(today.year, 3, 15),
    )
    check("пустая строка -> None", parse_date(""), None)
    check("только что -> None", parse_date("только что"), None)


if __name__ == "__main__":
    run()
    summary()
