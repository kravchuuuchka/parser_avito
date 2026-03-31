"""
slug_tests.py - Тесты для slug_builder.py (только транслитерация, без HTTP)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import re

from helpers import check, summary
from loguru import logger
from transliterate import translit

from parser.translit_pack import register_avito_pack

register_avito_pack()


def _transliterate(city: str) -> str:
    slug = translit(city.strip().lower(), "ru_avito")
    slug = slug.replace(" ", "_")
    slug = re.sub(r"[^a-z_\-]", "", slug)
    slug = re.sub(r"[_\-]{2,}", lambda m: m.group(0)[0], slug)
    return slug


def run():
    logger.info("====slug_builder====")

    cases = [
        ("Саратов", "saratov"),
        ("Москва", "moskva"),
        ("москва", "moskva"),
        ("Новосибирск", "novosibirsk"),
        ("Йошкар-Ола", "yoshkar-ola"),
        ("Нижний Новгород", "nizhniy_novgorod"),
        ("Щёлково", "schelkovo"),
        ("Улан-Удэ", "ulan-ude"),
    ]
    for city, expected in cases:
        result = _transliterate(city)
        check(f"{city} -> {expected}", result, expected)


if __name__ == "__main__":
    run()
    summary()
