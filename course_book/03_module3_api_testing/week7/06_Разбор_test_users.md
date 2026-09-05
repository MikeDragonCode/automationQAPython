# 3.12. Разбор test_users.py: всё вместе

## Зачем это нужно

Ты по отдельности разобрал `APIClient`, `UsersClient`, Pydantic-модели и разницу между `_api`- и обычными методами. Пора увидеть, как всё это работает вместе в настоящем, зелёном тестовом файле — это и есть эталон, на который нужно ориентироваться при написании своих тестов в домашнем задании.

## Теория

Открой `boilerplate/tests/api/test_users.py` целиком:

```python
import allure
import pytest

from clients.users.users_client import UsersClient
from clients.users.users_schema import CreateUserRequestSchema
from utils.fakers import get_random_email, get_random_username


@allure.epic("API")
@allure.feature("Users")
@pytest.mark.api
class TestUsers:

    @allure.title("Получение пользователя по id")
    def test_get_user(self, users_client: UsersClient):
        with allure.step("Запрашиваем пользователя с id=1"):
            user = users_client.get_user(user_id=1)

        with allure.step("Проверяем, что данные пользователя корректны"):
            assert user.id == 1
            assert "@" in user.email

    @allure.title("Получение несуществующего пользователя возвращает 404")
    def test_get_user_not_found(self, users_client: UsersClient):
        with allure.step("Запрашиваем заведомо несуществующего пользователя"):
            response = users_client.get_user_api(user_id=999)

        with allure.step("Проверяем статус-код ответа"):
            assert response.status_code == 404

    @allure.title("Создание пользователя")
    def test_create_user(self, users_client: UsersClient):
        request = CreateUserRequestSchema(
            name="QA Student",
            username=get_random_username(),
            email=get_random_email(),
        )

        with allure.step("Отправляем запрос на создание пользователя"):
            created_user = users_client.create_user(request)

        with allure.step("Проверяем, что вернулись переданные данные"):
            assert created_user.name == request.name
            assert created_user.username == request.username
            assert created_user.email == request.email
```

Разберём по частям, связывая с уроками, которые ты уже прошёл.

### Маркеры и Allure-метаданные (`@pytest.mark.api`, `@allure.epic`, `@allure.feature`)

`@pytest.mark.api` — маркер из `pytest.ini` (модуль 1), который позволяет запускать только API-тесты командой `pytest -m api`. `@allure.epic("API")` и `@allure.feature("Users")` — метаданные для группировки в отчёте Allure; подробно про Allure будет модуль 5, сейчас достаточно знать, что эти декораторы не влияют на логику теста.

### Фикстура users_client (урок 3.8)

Каждый тестовый метод принимает `users_client: UsersClient` как параметр — pytest подставляет туда объект, который вернёт фикстура `users_client` из `conftest.py`. Клиент создаётся один раз на сессию и переиспользуется всеми тремя тестами.

### test_get_user — happy path с высокоуровневым методом

```python
user = users_client.get_user(user_id=1)
assert user.id == 1
assert "@" in user.email
```

Используется `get_user` (не `get_user_api`) — потому что тест хочет удобно проверить конкретные поля через атрибуты (`user.id`, `user.email`), а не копаться в сыром `response.json()`. Под капотом `get_user` уже сходил в API и провалидировал ответ через `UserSchema.model_validate_json(...)` (урок 3.11) — если бы сервер вернул что-то не соответствующее `UserSchema`, тест упал бы ещё на этапе вызова `get_user`, с понятной ошибкой валидации, а не на строке `assert`.

### test_get_user_not_found — негативный сценарий с низкоуровневым методом

```python
response = users_client.get_user_api(user_id=999)
assert response.status_code == 404
```

Здесь используется `get_user_api`, а не `get_user` — намеренно (урок 3.8, 3.11). Тело ответа на несуществующего пользователя не соответствует `UserSchema`, и валидировать его Pydantic-схемой не нужно — единственное, что важно проверить в этом сценарии, это статус-код (урок 3.3).

### test_create_user — работа с фейкерами и Pydantic-моделью запроса

```python
request = CreateUserRequestSchema(
    name="QA Student",
    username=get_random_username(),
    email=get_random_email(),
)
created_user = users_client.create_user(request)
```

Сначала собирается Pydantic-модель запроса `CreateUserRequestSchema` — обрати внимание, что `username` и `email` берутся из `utils/fakers.py` (модуль использует `Faker` под капотом), чтобы каждый прогон теста создавал разные данные и тесты не мешали друг другу при повторных запусках. Затем эта модель целиком передаётся в `create_user(request)` — методу не нужен `dict`, только готовый объект схемы. Внутри `create_user_api` сам вызовет `request.model_dump()` перед отправкой (см. `users_client.py`, урок 3.8).

Проверка `created_user.name == request.name` сравнивает поле ответа с полем исходного запроса напрямую через атрибуты — ещё один пример того, зачем нужны типизированные Pydantic-объекты вместо словарей.

### Импорты в начале файла — тоже часть архитектуры

```python
from clients.users.users_client import UsersClient
from clients.users.users_schema import CreateUserRequestSchema
from utils.fakers import get_random_email, get_random_username
```

Обрати внимание, что тестовый файл не импортирует `APIClient` или `requests` напрямую — тесту вообще не нужно знать, что где-то внутри работает `requests.Session`. Это и есть смысл всей архитектуры клиента (уроки 3.7–3.8): тест общается только с `UsersClient` и Pydantic-схемами, а транспортный уровень от него полностью скрыт. `UsersClient` импортируется только ради подсказки типа в аннотации параметра (`users_client: UsersClient`) — сам объект тест получает через фикстуру, а не создаёт напрямую.

## Пример

Чтобы убедиться, что всё это действительно работает, запусти только API-тесты (маркер из `pytest.ini`, модуль 1):

```bash
pytest -m api -v
```

Ты должен увидеть три зелёных теста: `test_get_user`, `test_get_user_not_found`, `test_create_user`.

## Частые ошибки

- Писать в новом тесте `assert response.json()["email"] == ...` вместо того, чтобы использовать уже готовый высокоуровневый метод клиента и работать через атрибуты — это дублирование логики парсинга, которая уже есть в клиенте.
- Использовать одинаковые (захардкоженные) `username`/`email` в тесте создания пользователя вместо генерации через `utils/fakers.py` — при повторном запуске это может привести к конфликтам данных на реальном (не фейковом) API.
- Не разделять позитивные и негативные тесты по методам клиента (`_api` vs без суффикса) — пытаться валидировать ошибочный ответ Pydantic-схемой успешного сценария.

## Мини-задания

1. **Разминка.** Запусти `pytest -m api -v` локально в форкнутом `boilerplate/`, убедись, что все три теста зелёные. Затем запусти `pytest tests/api/test_users.py::TestUsers::test_create_user -v` — обрати внимание на синтаксис выбора одного конкретного теста внутри класса через `::`.

2. **Основное.** Временно измени `user_id=999` на `user_id=1` в `test_get_user_not_found` и запусти тест снова — убедись, что он падает, и разберись, на какой именно строке (`assert`) это происходит и что именно показывает pytest в выводе (какое значение `status_code` пришло вместо ожидаемого `404`). Верни файл в исходное состояние.

3. **Ближе к практике.** Временно измени `test_create_user` так, чтобы `username=get_random_username()` был заменён на постоянную строку, например `username="fixed_test_user"`. Запусти тест дважды подряд — убедись, что оба раза он всё равно зелёный (JSONPlaceholder не хранит созданных пользователей по-настоящему, поэтому конфликта не будет). Теперь объясни своими словами (без запуска кода), почему на реальном, не фейковом API повторный запуск с захардкоженным `username` мог бы упасть — свяжи это с частой ошибкой из раздела выше про захардкоженные данные. Верни файл в исходное состояние.

4. **Со звёздочкой.** В `UsersClient` уже есть метод `get_users_api()` (список всех пользователей), но в `test_users.py` для него пока нет ни одного теста. Допиши в `TestUsers` новый тест `test_get_users`, который вызывает `users_client.get_users_api()` и по аналогии с `test_get_user_not_found` проверяет только сырой `Response` (без Pydantic-валидации всего списка) — `assert response.status_code == 200` и `assert len(response.json()) > 0`. Запусти `pytest -m api -v` и убедись, что новый тест зелёный вместе с остальными тремя. Это тот же принцип, который урок 3.13 применит к `delete_user_api` в рамках домашнего задания: у метода в клиенте есть код, но нет теста — значит, дописать тест на уже существующий метод тоже часть работы, а не только добавление нового.
