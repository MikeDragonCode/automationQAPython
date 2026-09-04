# 3.7. Базовый API-клиент: BaseUrlSession и APIClient

## Зачем это нужно

С этого урока начинается главное отличие модуля 3 от предыдущих: ты больше не пишешь код "в вакууме". Ты открываешь уже существующий файл в общем репозитории и построчно разбираешь, как он устроен, — потому что именно на нём тебе предстоит строить домашнее задание. Не разобравшись в этом файле, дальше двигаться некуда: все специализированные клиенты (`UsersClient` и те, что добавишь ты) наследуются именно от него.

## Теория

Открой файл `boilerplate/clients/api_client.py` — он небольшой, разберём его целиком.

### Проблема: у requests.Session нет base_url

В уроке 3.6 мы остановились на том, что `requests.Session` умеет хранить общие заголовки, но не умеет хранить базовый URL — в отличие от `httpx.Client(base_url=...)` из библиотеки, на которой изначально построен курс-источник. Наш курс использует `requests`, а не `httpx`, поэтому в репозитории уже написано небольшое решение для этой конкретной проблемы — класс `BaseUrlSession`.

### Разбор BaseUrlSession

```python
class BaseUrlSession(Session):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, url: str | bytes, *args: Any, **kwargs: Any) -> Response:
        full_url = f"{self.base_url}/{str(url).lstrip('/')}"
        return super().request(method, full_url, *args, **kwargs)
```

Разбираем построчно:

- Класс **наследуется от `requests.Session`** — то есть `BaseUrlSession` это и есть сессия `requests`, просто с добавленным поведением, а не что-то отдельное.
- `__init__` принимает `base_url`, вызывает конструктор родителя (`super().__init__()`, чтобы сессия проинициализировалась как обычно), а затем сохраняет URL, убрав завершающий слэш (`rstrip("/")`) — это защита от двойного слэша при склейке (`https://example.com/` + `/users` не должно превращаться в `.../ /users`).
- Метод `request` — это тот самый метод, который `requests.Session` вызывает внутри себя при **любом** обращении: `session.get(...)` под капотом всё равно приходит к `session.request("GET", ...)`, то же самое для `post`, `put`, `patch`, `delete`. Переопределив именно `request`, мы гарантируем, что подстановка `base_url` сработает **для всех** методов сразу, а не только для, скажем, `get`.
- Внутри `request` мы склеиваем `base_url` и переданный `url`, обрезая лишние слэши с обеих сторон (`str(url).lstrip('/')` — убираем слэш в начале пути, если он там есть), и вызываем оригинальную реализацию через `super().request(...)`, подставляя уже полный URL.

Итог: `BaseUrlSession("https://jsonplaceholder.typicode.com")` ведёт себя как обычная `requests.Session`, но её методы (`.get("/users")`, `.post("/users", json=...)` и т. д.) принимают **относительные** пути, а не полные URL.

### Разбор APIClient

```python
class APIClient:
    def __init__(self, session: Session):
        self.session = session

    def get(self, url: str, params: dict | None = None) -> Response:
        return self.session.get(url, params=params)

    def post(self, url, json=None, data=None, files=None) -> Response:
        return self.session.post(url, json=json, data=data, files=files)

    def put(self, url: str, json: Any | None = None) -> Response:
        return self.session.put(url, json=json)

    def patch(self, url: str, json: Any | None = None) -> Response:
        return self.session.patch(url, json=json)

    def delete(self, url: str) -> Response:
        return self.session.delete(url)
```

`APIClient` — это базовый класс, от которого будут наследоваться **все** специализированные клиенты проекта (`UsersClient` и любые другие, которые появятся позже). Он не знает ничего про конкретный API или конкретные эндпоинты — он просто задаёт единый интерфейс поверх `requests.Session`: `get`, `post`, `put`, `patch`, `delete`. Обрати внимание, что каждый метод — это тонкая обёртка вокруг одноимённого метода сессии, ничего лишнего.

Зачем нужен этот промежуточный слой, если можно вызывать `self.session.get(...)` напрямую? Дело в том, что именно на этом уровне в будущем удобно добавлять сквозную функциональность — например, логирование каждого запроса, единую обработку ошибок или ретраи. Если это добавить в `APIClient.get`, оно автоматически заработает во всех клиентах, которые от него наследуются, — не придётся править каждый специализированный клиент по отдельности.

### build_http_session — фабрика готовой сессии

```python
def build_http_session(base_url: str, timeout: int = 10) -> Session:
    session = BaseUrlSession(base_url=base_url)
    session.request = _with_default_timeout(session.request, timeout)
    return session
```

Эта функция собирает сессию, готовую к использованию: подставляет `base_url` через `BaseUrlSession` и оборачивает метод `request` так, чтобы у всех запросов был таймаут по умолчанию (10 секунд), даже если вызывающий код не укажет его явно:

```python
def _with_default_timeout(request_func, timeout: int):
    def wrapper(method: str, url: str, *args: Any, **kwargs: Any) -> Response:
        kwargs.setdefault("timeout", timeout)
        return request_func(method, url, *args, **kwargs)

    return wrapper
```

`kwargs.setdefault("timeout", timeout)` — ключевой момент: если вызывающий код **уже** передал свой `timeout`, значение не перезаписывается; таймаут по умолчанию подставляется только тогда, когда его никто не указал.

## Пример

Чтобы получить рабочий клиент "с нуля", в терминале (например, в `python -i` или в отдельном скрипте) можно сделать так:

```python
from clients.api_client import APIClient, build_http_session

session = build_http_session(base_url="https://jsonplaceholder.typicode.com")
client = APIClient(session=session)

response = client.get("/users/1")
print(response.status_code, response.json())
```

Обрати внимание: мы передали относительный путь `"/users/1"`, а не полный URL — именно это и обеспечивает `BaseUrlSession`.

## Частые ошибки

- Пытаться переопределить `get`/`post`/... вместо `request` при попытке добавить сквозную логику в `BaseUrlSession` — тогда логика сработает не для всех методов, а только для переопределённых.
- Забывать про `rstrip`/`lstrip` при самостоятельной реализации похожего класса и получать URL вида `https://example.com//users` (двойной слэш) — большинство серверов такое не примут как ожидаемый путь.
- Путать уровень `APIClient` (общие HTTP-методы) и уровень специализированных клиентов вроде `UsersClient` (конкретные эндпоинты) — специфичного для `/users` в `api_client.py` быть не должно.

## Мини-задание

До того как заглянуть в готовый `APIClient`/`BaseUrlSession` из теории выше, — попробуй сам. Напиши в отдельном скрипте маленький класс `SimpleClient`: конструктор принимает `base_url` и сохраняет его, метод `get(path)` делает `requests.get(...)` на `base_url + path`, метод `post(path, json)` — аналогично `requests.post(...)`. Проверь его на `client.get("/users/1")` и `client.post("/posts", json={"title": "x"})` — оба вызова должны реально сходить в сеть и вернуть ответ.

Теперь сравни свой `SimpleClient` с настоящим `APIClient`/`BaseUrlSession`: что он делает так же, а что — иначе (единая точка для всех методов через `request`, таймаут по умолчанию)? Переписывать свой класс под эталон не нужно — важно осознанно увидеть разницу, а не просто прочитать чужой код.
