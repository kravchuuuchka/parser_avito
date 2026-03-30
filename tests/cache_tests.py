"""
cache_tests.py - Тесты для cache.py
БД сохраняется в C:\\test\\cache_test.db
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import sqlite3
from datetime import date, datetime, timedelta

from loguru import logger
from core.ad import Ad
import core.cache as cache
from helpers import check, ensure_test_dir, summary


def run():
    logger.info("====cache====")

    test_dir = ensure_test_dir()
    db = os.path.join(test_dir, "cache_test.db")

    if os.path.exists(db):
        os.unlink(db)

    _run(db)
    logger.info("БД сохранена в {}", db)


def _run(db: str) -> None:
    cache.init(db)

    ad1 = Ad(
        id="111", title="Котик рыжий", price=500.0,
        address="Новосибирск", description="Милый",
        published_on=date(2026, 3, 1), views=10,
        url="https://avito.ru/item_111", status=1,
        city="новосибирск", query="котик",
    )
    ad2 = Ad(
        id="222", title="Котик серый", price=0.0,
        address="Новосибирск", description="Ищет дом",
        published_on=date(2026, 3, 2), views=5,
        url="https://avito.ru/item_222", status=1,
        city="новосибирск", query="котик",
    )
    ad_closed = Ad(
        id="333", title="Котик закрытый", price=100.0,
        address="Новосибирск", description="Уже продан",
        published_on=date(2026, 3, 1), views=1,
        url="https://avito.ru/item_333", status=0,
        city="новосибирск", query="котик",
    )

    cache.save([ad1, ad2, ad_closed], db)

    ads = cache.get_by_query("котик", "новосибирск", db)
    check("добавлено 2 активных объявления",   len(ads), 2)
    check("закрытое не добавилось",            all(a.id != "333" for a in ads), True)

    found = next((a for a in ads if a.id == "222"), None)
    check("бесплатно = 0.0",                  found.price if found else None, 0.0)

    old_time = (datetime.now() - timedelta(hours=2)).isoformat(timespec="seconds")
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE ads SET cached_at = ? WHERE id = '111'", (old_time,))

    ad1_updated = Ad(
        id="111", title="Котик рыжий", price=700.0,
        address="Новосибирск", description="Милый",
        published_on=date(2026, 3, 1), views=15,
        url="https://avito.ru/item_111", status=1,
        city="новосибирск", query="котик",
    )
    cache.save([ad1_updated], db)
    ads = cache.get_by_query("котик", "новосибирск", db)
    updated = next((a for a in ads if a.id == "111"), None)
    check("цена обновилась 500.0 -> 700.0",    updated.price if updated else None, 700.0)

    ad_spb = Ad(
        id="444", title="Котик петербургский", price=200.0,
        address="СПб", description="Пушистый",
        published_on=date(2026, 3, 3), views=3,
        url="https://avito.ru/item_444", status=1,
        city="санкт-петербург", query="котик",
    )
    cache.save([ad_spb], db)
    ads_nsk = cache.get_by_query("котик", "новосибирск", db)
    ads_spb = cache.get_by_query("котик", "санкт-петербург", db)
    check("фильтр по городу новосибирск",   len(ads_nsk), 2)
    check("фильтр по городу санкт-петербург",           len(ads_spb), 1)

    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE ads SET cached_at = ? WHERE id = '222'", (old_time,))

    ad2_closed = Ad(
        id="222", title="Котик серый", price=0.0,
        address="Новосибирск", description="Ищет дом",
        published_on=date(2026, 3, 2), views=5,
        url="https://avito.ru/item_222", status=0,
        city="новосибирск", query="котик",
    )
    cache.save([ad2_closed], db)
    ads = cache.get_by_query("котик", "новосибирск", db)
    closed = next((a for a in ads if a.id == "222"), None)
    check("статус изменился на 0 (закрыто)",  closed.status if closed else None, 0)

    ad = ads[0]
    check("published_on имеет тип date",      type(ad.published_on), date)
    check("cached_at имеет тип datetime",     type(ad.cached_at),    datetime)
    check("updated_at имеет тип datetime",    type(ad.updated_at),   datetime)


if __name__ == "__main__":
    run()
    summary()