"""
helpers.py - Общие функции для тестов
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from loguru import logger

_total = 0
_passed = 0

TEST_DIR = r"C:\test"


def check(name: str, result, expected):
    global _total, _passed
    _total += 1
    ok = result == expected
    if ok:
        _passed += 1
        logger.success("{}", name)
    else:
        logger.error(
            "{}\n      ожидалось: {!r}\n      получено:  {!r}", name, expected, result
        )


def summary():
    logger.info("-" * 55)
    logger.info("Результат: {}/{}", _passed, _total)
    if _passed == _total:
        logger.success("Все тесты прошли успешно!")
    else:
        logger.error("Есть провалившиеся тесты")


def ensure_test_dir() -> str:
    """Создаёт папку C:\\test если не существует и возвращает путь."""
    os.makedirs(TEST_DIR, exist_ok=True)
    return TEST_DIR
