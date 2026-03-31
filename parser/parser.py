"""
parser.py - Парсер Авито (выдача + страницы объявлений)
"""

import asyncio
import random
import re
from typing import Optional

from loguru import logger
from playwright.async_api import async_playwright, BrowserContext, Page, TimeoutError as PWTimeout

from core.ad import Ad
from core.field_parsers import parse_price, parse_date
from parser.slug_builder import city_to_slug
from parser.parser_config import *

def _parse_id(url: str) -> str:
    m = re.search(r"_(\d+)(?:[/?]|$)", url)
    return m.group(1) if m else ""


def _build_search_url(query: str, city_slug: Optional[str], page: int = 1) -> str:
    base = f"https://www.avito.ru/{city_slug}" if city_slug else "https://www.avito.ru/rossiya"
    encoded = query.replace(" ", "+")
    url = f"{base}?q={encoded}"
    if page > 1:
        url += f"&p={page}"
    return url


async def _random_delay(min_s: float, max_s: float) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


async def _scroll(page: Page) -> None:
    for _ in range(3):
        await page.mouse.wheel(0, random.randint(1500, 3000))
        await asyncio.sleep(random.uniform(1, 2))


async def _collect_ads_from_listing(context: BrowserContext, search_url: str, query: str, city: str) -> list[Ad]:
    """
    Сбор базовых данных (id, url, title) со страницы выдачи
    """
    page = await context.new_page()
    results: list[Ad] = []

    try:
        logger.info("Открываем выдачу: {}", search_url)
        await _random_delay(3.0, 6.0)
        await page.goto(search_url, timeout=60_000)
        await asyncio.sleep(random.uniform(2, 4))
        await _scroll(page)

        cards = page.locator('div.iva-item-body-oMJBI')
        count = await cards.count()
        logger.info("Найдено карточек: {}", count)

        for i in range(count):
            card = cards.nth(i)
            try:
                link_el = card.locator('a').first
                href = await link_el.get_attribute("href")
                title = (await link_el.inner_text()).strip()

                if not href:
                    continue

                full_url = "https://www.avito.ru" + href if href.startswith("/") else href

                results.append(Ad(
                    id=_parse_id(full_url),
                    url=full_url,
                    title=title,
                    query=query,
                    city=city,
                ))
            except Exception:
                continue

    except Exception as e:
        logger.error("Ошибка загрузки выдачи: {}", e)
    finally:
        await page.close()

    return results


async def _enrich_ad(context: BrowserContext, semaphore: asyncio.Semaphore, ad: Ad, index: int, total: int) -> Ad:
    """
    Заполнение недостающих полей со входом в объявление
    """
    async with semaphore:
        page = await context.new_page()
        logger.info("[{}/{}] Открываем объявление: {}", index, total, ad.url)

        try:
            await _random_delay(*DELAY_BETWEEN_ADS)
            await page.goto(ad.url, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(random.uniform(1, 2))
        except PWTimeout:
            logger.warning("Timeout: {}", ad.url)
            await page.close()
            return ad

        html = await page.content()

        if any(m in html for m in [
            "Объявление снято с публикации",
            "item-closed-warning",
            "item-view__block-reason",
            "Объявление недоступно",
        ]):
            ad.status = 0

        el = await page.query_selector('[itemprop="price"]')
        if el:
            content = await el.get_attribute("content")
            if content:
                ad.price = parse_price(content.strip())

        el = await page.query_selector('[itemprop="address"]')
        if el:
            ad.address = (await el.inner_text()).strip()

        el = await page.query_selector('[itemprop="description"], [class*="item-description"]')
        if el:
            ad.description = (await el.inner_text()).strip()

        el = await page.query_selector('[data-marker="item-view/item-date"]')
        if el:
            raw = (await el.inner_text()).strip().lstrip("·").strip()
            ad.published_on = parse_date(raw)

        el = await page.query_selector('[class*="views-count"], [data-marker="item-view/total-views"]')
        if el:
            raw = await el.inner_text()
            digits = re.sub(r"\D", "", raw)
            ad.views = int(digits) if digits else 0

        await page.close()

    return ad


async def _parse_async(query: str, city: str, city_slug: Optional[str], max_pages: int, limit: Optional[int]) -> list[Ad]:
    """
    Асинхронный парсинг
    """
    semaphore = asyncio.Semaphore(PARALLEL_TABS)
    results: list[Ad] = []

    async with async_playwright() as pw:
        browser = await pw.firefox.launch(
            headless=False,
        )
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            extra_http_headers=BASE_HEADERS,
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en-US'] });
            window.chrome = { runtime: {} };
        """)
        await context.add_cookies(BASE_COOKIES)

        for page_num in range(1, max_pages + 1):
            search_url = _build_search_url(query, city_slug, page=page_num)
            ads = await _collect_ads_from_listing(context, search_url, query, city)

            if not ads:
                logger.warning("Страница {} пустая - стоп", page_num)
                break

            if limit:
                remaining = limit - len(results)
                ads = ads[:remaining]

            total = len(ads)
            tasks = [
                _enrich_ad(context, semaphore, ad, i, total)
                for i, ad in enumerate(ads, 1)
            ]
            enriched = await asyncio.gather(*tasks)
            results.extend(enriched)

            if limit and len(results) >= limit:
                break

            if page_num < max_pages:
                await _random_delay(*DELAY_BETWEEN_PAGES)

        await browser.close()

    logger.success("Собрано объявлений: {}", len(results))
    return results


def parse(query: str, city: Optional[str] = None, max_pages: int = 1, limit: Optional[int] = None,) -> list[Ad]:
    """
    Парсинг объявлений Авито

    Args:
        query:     Поисковый запрос
        city:      Город на русском, None - по всей России
        max_pages: Количество страниц поиска для обхода
        limit:     Максимальное количество объявлений, None - без ограничений

    Returns:
        Список объектов Ad
    """
    slug = city_to_slug(city) if city else None
    if city:
        logger.info("Город: {} -> {}", city, slug)

    return asyncio.run(_parse_async(query, city or "", slug, max_pages, limit))