"""
slug_builder.py - Транслитерация названия города
"""

import re
import httpx
from transliterate import translit

from parser.translit_pack import register_avito_pack

register_avito_pack()

def _transliterate(city: str) -> str:
    """Транслитерация строки и очистка от недопустимых символов"""
    slug = translit(city.strip().lower(), "ru_avito")
    slug = slug.replace(" ", "_")
    slug = re.sub(r"[^a-z_\-]", "", slug)
    slug = re.sub(r"[_\-]{2,}", lambda m: m.group(0)[0], slug)
    return slug


def _slug_exists(slug: str) -> bool:
    """Проверка, существует ли страница города на Авито"""
    url = f"https://www.avito.ru/{slug}"
    try:
        response = httpx.get(url, follow_redirects=True, timeout=10)

        if response.status_code != 200:
            return False

        text = response.text.lower()

        if "такой страницы не существует" in text:
            return False

        if response.url.path != f"/{slug}":
            return False

        return True

    except httpx.RequestError:
        return False


def city_to_slug(city: str) -> str:
    """
    Конвертация названия города/региона на русском в URL-slug для Авито.
    """
    transliterated = _transliterate(city)

    slug_hyphen = transliterated.replace("_", "-")
    if _slug_exists(slug_hyphen):
        return slug_hyphen

    slug_underscore = transliterated
    if slug_underscore != slug_hyphen and _slug_exists(slug_underscore):
        return slug_underscore

    return slug_hyphen