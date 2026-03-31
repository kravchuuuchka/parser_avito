"""
cache.py - SQLite-кэш объявлений Авито
"""

import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional

from loguru import logger

from core.ad import Ad
from core.cache_config import CACHE_TTL_HOURS, DB_PATH
from core.field_parsers import parse_date, parse_price


def init(db_path: str = DB_PATH) -> None:
    """Создание БД и таблицы, если они ещё не существуют"""
    with _connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ads (
                id              TEXT PRIMARY KEY,
                title           TEXT,
                price           REAL,
                address         TEXT,
                description     TEXT,
                published_on    TEXT,
                views           INTEGER,
                url             TEXT,
                status          INTEGER,
                city            TEXT,
                query           TEXT,
                cached_at       TEXT,
                updated_at      TEXT
            )
        """)
    logger.info("Кэш инициализирован: {}", db_path)


def _connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> datetime:
    return datetime.now().replace(tzinfo=None)


def _dt_to_str(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


def _str_to_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _date_to_str(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


def _str_to_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        return None


def _row_to_ad(row: sqlite3.Row) -> Ad:
    return Ad(
        id=row["id"],
        title=row["title"],
        price=row["price"],
        address=row["address"],
        description=row["description"],
        published_on=_str_to_date(row["published_on"]),
        views=int(row["views"]),
        url=row["url"],
        status=int(row["status"]),
        city=row["city"],
        query=row["query"],
        cached_at=_str_to_dt(row["cached_at"]),
        updated_at=_str_to_dt(row["updated_at"]),
    )


def _prepare(ad: Ad) -> tuple[Optional[float], Optional[str]]:
    """Конвертация сырых полей Ad перед записью в БД"""
    price = parse_price(str(ad.price)) if isinstance(ad.price, str) else ad.price
    published_on = _date_to_str(
        parse_date(ad.published_on)
        if isinstance(ad.published_on, str)
        else ad.published_on
    )
    return price, published_on


def save(ads: list[Ad], db_path: str = DB_PATH) -> None:
    """
    Сохранение списка объявлений в кэш
    """
    if not ads:
        return

    with _connect(db_path) as conn:
        ids = [ad.id for ad in ads]
        placeholders = ",".join("?" * len(ids))
        existing_rows = conn.execute(
            f"""SELECT id, title, price, description, status, cached_at
                FROM ads WHERE id IN ({placeholders})""",
            ids,
        ).fetchall()
        existing = {row["id"]: row for row in existing_rows}

        now = _now()
        ttl = timedelta(hours=CACHE_TTL_HOURS)

        for ad in ads:
            price, published_on = _prepare(ad)

            if ad.id not in existing:
                if ad.status == 0:
                    logger.debug("Пропускаем закрытое новое объявление: {}", ad.id)
                    continue
                conn.execute(
                    """
                    INSERT INTO ads (
                        id, title, price, address, description,
                        published_on, views, url, status,
                        city, query, cached_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        ad.id,
                        ad.title,
                        price,
                        ad.address,
                        ad.description,
                        published_on,
                        ad.views,
                        ad.url,
                        ad.status,
                        ad.city,
                        ad.query,
                        _dt_to_str(now),
                        _dt_to_str(now),
                    ),
                )
                logger.debug("Добавлено: {}", ad.id)

            else:
                row = existing[ad.id]
                cached_at = _str_to_dt(row["cached_at"])

                if cached_at and (now - cached_at) < ttl:
                    logger.debug("Свежий кэш, пропускаем: {}", ad.id)
                    continue

                changed = (
                    int(row["status"]) != ad.status
                    or row["price"] != price
                    or row["title"] != ad.title
                    or row["description"] != ad.description
                )
                if changed:
                    conn.execute(
                        """
                        UPDATE ads SET
                            title       = ?,
                            price       = ?,
                            description = ?,
                            status      = ?,
                            views       = ?,
                            updated_at  = ?
                        WHERE id = ?
                    """,
                        (
                            ad.title,
                            price,
                            ad.description,
                            ad.status,
                            ad.views,
                            _dt_to_str(now),
                            ad.id,
                        ),
                    )
                    logger.debug("Обновлено: {}", ad.id)
                else:
                    logger.debug("Без изменений: {}", ad.id)


def get_by_query(
    query: str, city: Optional[str] = None, db_path: str = DB_PATH
) -> list[Ad]:
    """
    Отображение объявлений из кэша по поисковому запросу и городу

    Args:
        query: Поисковый запрос
        city:  Город. None - без фильтра по городу
    """
    with _connect(db_path) as conn:
        if city:
            rows = conn.execute(
                "SELECT * FROM ads WHERE query = ? AND city = ?",
                (query, city),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM ads WHERE query = ?",
                (query,),
            ).fetchall()

    ads = [_row_to_ad(row) for row in rows]
    logger.info(
        "Из кэша получено {} объявлений (запрос: «{}», город: {})",
        len(ads),
        query,
        city or "все",
    )
    return ads
