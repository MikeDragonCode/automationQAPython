import pytest

from utils.string_utils import chunk_list, count_vowels, is_palindrome, slugify


@pytest.mark.unit
@pytest.mark.parametrize(
    "text, expected",
    [
        ("racecar", True),
        ("A man a plan a canal Panama", True),
        ("hello", False),
        ("", True),
    ],
)
def test_is_palindrome(text, expected):
    assert is_palindrome(text) is expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "text, expected",
    [
        ("Hello World", "hello-world"),
        ("  Python  QA  ", "python-qa"),
        ("already-slug", "already-slug"),
    ],
)
def test_slugify(text, expected):
    assert slugify(text) == expected


@pytest.mark.unit
def test_chunk_list_splits_evenly():
    assert chunk_list([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]


@pytest.mark.unit
def test_chunk_list_last_chunk_may_be_smaller():
    assert chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


@pytest.mark.unit
def test_chunk_list_rejects_non_positive_size():
    with pytest.raises(ValueError):
        chunk_list([1, 2, 3], 0)


@pytest.mark.unit
def test_count_vowels_counts_ru_and_en():
    assert count_vowels("Hello Привет") == 4
