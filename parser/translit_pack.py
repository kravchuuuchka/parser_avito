"""
translit_pack.py - Кастомный языковой пак транслитерации для Авито
"""

from transliterate.base import TranslitLanguagePack, registry

class _AvitoPack(TranslitLanguagePack):
    language_code = "ru_avito"
    language_name = "Russian (Avito)"

    pre_processor_mapping = {
        "щ": "sch",
        "ш": "sh",
        "ж": "zh",
        "ч": "ch",
        "ю": "yu",
        "я": "ya",
        "ц": "ts",
        "й": "y",
        "ё": "e",
        "ы": "y",
        "э": "e",
        "ъ": "",
        "ь": "",
    }

    mapping = (
        "абвгдезиклмнопрстуфх",
        "abvgdeziklmnoprstufh",
    )


def register_avito_pack() -> None:
    """Регистрация пака в реестре transliterate"""
    try:
        registry.register(_AvitoPack)
    except Exception:
        pass