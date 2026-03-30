"""
main.py - Точка входа парсера Авито

Использование:
    python main.py --query "котик" --city "Саратов" --pages 1 --limit 10
    python main.py --query "велосипед"
"""

import argparse
from loguru import logger

import core.cache as cache
import parser.parser as parser
import exporter.exporter as exporter


def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Парсер объявлений Авито")
    arg_parser.add_argument("--query", required=True, help="Поисковый запрос, например 'котик'")
    arg_parser.add_argument("--city",  default=None,  help="Город на русском, например 'Саратов'")
    arg_parser.add_argument("--pages", type=int, default=1, help="Количество страниц поиска (по умолчанию 1)")
    arg_parser.add_argument("--limit", type=int, default=None)
    args = arg_parser.parse_args()

    cache.init()

    logger.info("Запрос: «{}»  |  Город: {}", args.query, args.city or "Россия")
    ads = parser.parse(query=args.query, city=args.city, max_pages=args.pages, limit=args.limit)

    cache.save(ads)

    cached_ads = cache.get_by_query(query=args.query, city=args.city)
    filename = _build_filename(args.query, args.city)
    exporter.export(ads=cached_ads, filepath=filename)

    logger.info("Готово. Файл: {}", filename)


def _build_filename(query: str, city: str | None) -> str:
    """Формирует имя файла из запроса и города"""
    safe_query = query.replace(" ", "_")
    if city:
        safe_city = city.replace(" ", "_")
        return f"{safe_query}_{safe_city}.xlsx"
    return f"{safe_query}.xlsx"


if __name__ == "__main__":
    main()