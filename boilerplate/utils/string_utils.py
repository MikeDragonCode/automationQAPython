"""
Небольшой набор чистых функций без внешних зависимостей.
Используется в модуле 1 как материал для первых pytest-тестов —
фикстур, параметризации и маркеров, без API и без браузера.
"""


def is_palindrome(text: str) -> bool:
    normalized = "".join(ch.lower() for ch in text if ch.isalnum())
    return normalized == normalized[::-1]


def slugify(text: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in text.strip())
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-")


def chunk_list(items: list, size: int) -> list[list]:
    if size <= 0:
        raise ValueError("size must be a positive integer")
    return [items[i:i + size] for i in range(0, len(items), size)]


def count_vowels(text: str) -> int:
    vowels = set("aeiouAEIOUаеёиоуыэюяАЕЁИОУЫЭЮЯ")
    return sum(1 for ch in text if ch in vowels)
