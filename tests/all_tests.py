"""
all_tests.py - Запуск всех тестов

Запуск из корня проекта:
    python tests/all_tests.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import cache_tests
import exporter_tests
import fields_tests
import slug_tests
from helpers import summary

fields_tests.run()
slug_tests.run()
cache_tests.run()
exporter_tests.run()

summary()
