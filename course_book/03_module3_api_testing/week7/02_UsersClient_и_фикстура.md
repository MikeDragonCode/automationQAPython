# 3.8. UsersClient и фикстура users_client

## Зачем это нужно

`APIClient` из прошлого урока ничего не знает про `/users` — и это правильно, он универсальный. Конкретную логику под конкретный ресурс добавляют специализированные клиенты. `UsersClient` — первый такой клиент в репозитории, и он же — прямой образец для твоего домашнего задания: новые методы ты будешь добавлять именно в него, по тому же паттерну.

## Теория

Открой `boilerplate/clients/users/users_client.py`:

```python
from requests import Response

from clients.api_client import APIClient, build_http_session
from clients.users.users_schema import (
    CreateUserRequestSchema,
    CreateUserResponseSchema,
    UserSchema,
)

BASE_URL = "https://jsonplaceholder.typicode.com"


class UsersClient(APIClient):
    def get_users_api(self) -> Response:
        return self.get("/users")

    def get_user_api(self, user_id: int) -> Response:
        return self.get(f"/users/{user_id}")

    def create_user_api(self, request: CreateUserRequestSchema) -> Response:
        return self.post("/users", json=request.model_dump())

    def delete_user_api(self, user_id: int) -> Response:
        return self.delete(f"/users/{user_id}")

    def get_user(self, user_id: int) -> UserSchema:
        response = self.get_user_api(user_id)
        return UserSchema.model_validate_json(response.text)

    def create_user(self, request: CreateUserRequestSchema) -> CreateUserResponseSchema:
        response = self.create_user_api(request)
        return CreateUserResponseSchema.model_validate_json(response.text)


def get_users_client() -> UsersClient:
    return UsersClient(session=build_http_session(base_url=BASE_URL))
```

### Наследование от APIClient

`class UsersClient(APIClient):` — `UsersClient` получает все методы `get/post/put/patch/delete` бесплатно, просто по факту наследования. Ему остаётся только описать, **какие именно** запросы имеют смысл для ресурса `/users`, и под какими именами их удобно вызывать из тестов.

### Два уровня методов: `_api` и обычные

Обрати внимание на закономерность в названиях:

- `get_users_api`, `get_user_api`, `create_user_api`, `delete_user_api` — методы с суффиксом `_api`. Они возвращают **сырой** `requests.Response`, ничего не валидируя и не преобразуя. Это низкоуровневый слой — нужен, например, когда в тесте важно проверить именно статус-код или сырое тело ответа (в том числе для негативных сценариев, где сервер возвращает не то, что ожидалось).
- `get_user`, `create_user` — методы **без** суффикса `_api`. Они вызывают соответствующий `_api`-метод и сразу возвращают уже провалидированный Pydantic-объект (`UserSchema`, `CreateUserResponseSchema`) вместо сырого `Response`. Это высокоуровневый слой — удобен, когда тест хочет сразу работать с типизированными полями (`user.email`, `user.id`), а не лезть в `response.json()["email"]`.

Такое разделение — не случайность и не лишняя сложность: оно даёт тесту выбор. Если тест проверяет happy path и хочет удобный доступ к полям — он берёт `get_user()`. Если тест целенаправленно проверяет ошибку (несуществующий пользователь, `404`) — валидировать тело ответа Pydantic-схемой бессмысленно (там и не будет корректного пользователя), поэтому тест берёт `get_user_api()` и проверяет только `response.status_code`.

### get_users_client — фабрика клиента

```python
def get_users_client() -> UsersClient:
    return UsersClient(session=build_http_session(base_url=BASE_URL))
```

Это обычная функция (не метод класса), которая скрывает детали сборки: откуда взять `base_url`, как собрать сессию (`build_http_session` из урока 3.7). Тестам и фикстурам не нужно знать эти детали — они просто вызывают `get_users_client()` и получают готовый к работе объект.

### Фикстура users_client в conftest.py

В `boilerplate/conftest.py` есть:

```python
@pytest.fixture(scope="session")
def users_client() -> UsersClient:
    return get_users_client()
```

`scope="session"` означает, что клиент создаётся **один раз** за весь прогон тестов, а не заново для каждого теста — так как `UsersClient` не хранит состояние конкретного теста (никаких "текущих данных пользователя" внутри клиента нет), пересоздавать его каждый раз бессмысленно и просто тратит время.

Любой тест, которому нужен доступ к API `/users`, просто объявляет параметр `users_client: UsersClient` в сигнатуре теста — pytest сам подставит туда готовый объект благодаря механизму фикстур (это ты уже проходил в модуле 1).

## Пример

Использование клиента в тесте выглядит так (полный разбор `test_users.py` будет в уроке 3.12):

```python
def test_get_user(users_client: UsersClient):
    user = users_client.get_user(user_id=1)
    assert user.id == 1
```

А вот негативный сценарий, где нужен именно `_api`-метод:

```python
def test_get_user_not_found(users_client: UsersClient):
    response = users_client.get_user_api(user_id=999)
    assert response.status_code == 404
```

## Частые ошибки

- Добавлять в `UsersClient` метод, который не относится к `/users` (например, работу с постами) — специализированный клиент должен отвечать только за свой ресурс. Для другого ресурса — новый клиент рядом, по тому же паттерну.
- Реализовывать только высокоуровневый метод (`get_user`) без низкоуровневого (`get_user_api`) — тогда написать негативный тест на ошибку станет неудобно или невозможно, ведь Pydantic-валидация ответа с ошибкой просто упадёт с исключением вместо понятного `assert`.
- Создавать `UsersClient` вручную в каждом тесте вместо использования фикстуры `users_client` — дублирование той же природы, что и с голым `requests.get(...)` в модуле недели 6.

## Мини-задание

Добавь в свой форк новый метод `find_user_by_username(self, username: str) -> UserSchema | None` в `UsersClient` — по тому же паттерну, что и остальные методы класса. Он должен вызвать уже существующий `get_users_api()`, пройтись по списку пользователей из `response.json()` и вернуть того, чей `username` совпадает с переданным (`UserSchema(**matching_dict)`), либо `None`, если такого нет. Проверь его в отдельном скрипте на реальном username с `https://jsonplaceholder.typicode.com/users` (например, `"Bret"`).
