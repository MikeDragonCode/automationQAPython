# 4.15. Фикстуры для Page Object в conftest.py

## Зачем это нужно

У нас уже есть `RegistrationPage` и `DashboardPage`, но если создавать их прямо внутри теста, в тест вернётся техническая подготовка, от которой мы как раз пытались избавиться в уроке 4.11. Фикстуры pytest (модуль 1) и Page Object (уроки 4.12–4.14) вместе закрывают эту проблему — и именно так организован `boilerplate/conftest.py`.

## Теория

### Проблема: создание объектов страниц внутри теста

Если бы мы использовали `RegistrationPage` и `DashboardPage` "в лоб", тест выглядел бы так:

```python
@pytest.mark.ui
def test_successful_registration(page: Page, user_data: dict[str, str]):
    registration_page = RegistrationPage(page)
    dashboard_page = DashboardPage(page)

    registration_page.open_page()
    ...
```

Код рабочий, но первые две строки — не действие пользователя и не проверка, а чисто техническая подготовка объектов. Чем больше таких строк накапливается в начале каждого теста, тем сильнее тест отвлекается от описания сценария.

### Решение: фикстуры возвращают готовые объекты страниц

В модуле 1 мы уже создавали фикстуры, возвращающие данные:

```python
@pytest.fixture
def user_data() -> dict[str, str]:
    return {...}
```

Точно так же фикстура может возвращать не данные, а готовый объект класса. В `boilerplate/conftest.py` это выглядит так:

```python
@pytest.fixture
def registration_page(page: Page) -> RegistrationPage:
    return RegistrationPage(page)


@pytest.fixture
def dashboard_page(page: Page) -> DashboardPage:
    return DashboardPage(page)
```

Разберём сигнатуру `def registration_page(page: Page) -> RegistrationPage`. Параметр `page` — это не наш объект, а встроенная фикстура из плагина `pytest-playwright` (мы пользовались ей ещё в уроке 4.6, просто не через фикстуру, а через ручной запуск `sync_playwright()`). Когда pytest видит, что тесту нужна фикстура `registration_page`, он сначала подготавливает фикстуру `page`, от которой она зависит, и только потом передаёт результат внутрь. Это одна из сильных сторон pytest — **фикстуры могут зависеть друг от друга**, образуя цепочку:

```
pytest-playwright → page → registration_page → RegistrationPage(page)
```

### Как эти фикстуры используются в тесте

Тест из `boilerplate/tests/ui/test_registration.py` получает готовые объекты страниц прямо через параметры функции:

```python
def test_successful_registration(
        self,
        user_data: dict[str, str],
        registration_page: RegistrationPage,
        dashboard_page: DashboardPage,
):
```

Обрати внимание: в параметрах теста нет `page` — тест вообще не запрашивает "сырой" объект Playwright, потому что вся работа с ним уже упакована внутрь `RegistrationPage` и `DashboardPage`.

### Зачем нужны аннотации типов

```python
registration_page: RegistrationPage
```

На поиск фикстуры pytest это не влияет — фикстуры ищутся по имени (`registration_page`), а не по типу. Аннотация нужна для IDE: автодополнение методов, подсказки параметров, переход к определению класса. На небольшом проекте это не критично, но при росте кодовой базы такие подсказки экономят много времени — особенно когда Page Object'ов становится десяток и больше.

### Почему фикстура лучше создания объекта в тесте

Сравним ещё раз. Было:

```python
registration_page = RegistrationPage(page)
dashboard_page = DashboardPage(page)
```

Стало:

```python
def test_successful_registration(
        registration_page: RegistrationPage,
        dashboard_page: DashboardPage,
):
```

Во втором варианте тест описывает только сценарий — подготовка объектов спрятана в `conftest.py`, где ей и место. Это тот же принцип, что мы применили к локаторам в уроках 4.12–4.14: техническая деталь вынесена туда, где она нужна один раз, а не туда, где её приходится видеть постоянно.

## Пример

Открой `boilerplate/conftest.py` целиком — там всего три фикстуры, относящиеся к модулю 4 (плюс отдельно фикстуры для модуля 3 и allure-хук для модуля 5, их пока игнорируй):

```python
@pytest.fixture
def user_data() -> dict[str, str]:
    return {
        "email": get_random_email(),
        "username": get_random_username(),
        "password": get_random_password(),
    }


@pytest.fixture
def registration_page(page: Page) -> RegistrationPage:
    return RegistrationPage(page)


@pytest.fixture
def dashboard_page(page: Page) -> DashboardPage:
    return DashboardPage(page)
```

Именно к этому файлу ты будешь добавлять фикстуру для своего `LoginPage` в домашнем задании — рядом с уже существующими, а не вместо них.

## Частые ошибки

- Создавать объект страницы внутри тестовой функции "для простоты", вместо того чтобы вынести это в фикстуру — работать будет, но это возвращает проблему, которую мы решали в этом уроке.
- Добавлять фикстуре побочные действия сверх создания объекта (например, сразу вызывать `open_page()` внутри фикстуры) — фикстура `registration_page` в `boilerplate/` только создаёт объект, а открытие страницы остаётся явным действием внутри теста, потому что это часть сценария, а не подготовки.
- Забывать аннотацию возвращаемого типа у фикстуры — код будет работать и без неё, но IDE перестанет подсказывать методы объекта там, где фикстура используется.

## Мини-задание

Открой `boilerplate/conftest.py` и найди фикстуру `user_data`. Определи, зависит ли она от фикстуры `page` так же, как `registration_page` и `dashboard_page`, или устроена независимо. Обоснуй разницу тем, что именно возвращает каждая из фикстур.
