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

### Почему это отдельный класс, а не просто функция

Может показаться, что то же самое можно было решить проще: завести функцию `build_url(base_url, path)` и звать её перед каждым запросом. Разница в том, что тогда **каждый** вызывающий код был бы обязан не забыть вызвать эту функцию — а забыть легко, особенно через полгода работы над проектом, когда пишешь двадцатый метод в клиенте по образцу предыдущих девятнадцати. `BaseUrlSession` устраняет этот риск полностью: подстановка `base_url` происходит **внутри** транспортного слоя, один раз, и дальше про неё просто не нужно помнить, к какому бы клиенту или методу ты ни писал код.

```python
session = BaseUrlSession(base_url="https://jsonplaceholder.typicode.com")
session.get("/users/1")   # относительный путь, base_url подставится сам
```

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

### setdefault на практике: когда таймаут можно переопределить

`dict.setdefault(key, value)` — метод обычных словарей Python: если ключ уже есть, ничего не меняет и возвращает существующее значение; если ключа нет — добавляет его с переданным значением. Именно поэтому вызывающий код всегда может явно передать свой `timeout`, и обёртка не станет его перезаписывать:

```python
session = build_http_session(base_url="https://jsonplaceholder.typicode.com", timeout=10)

session.get("/users")                 # уйдёт с timeout=10 (значение по умолчанию)
session.get("/users", timeout=30)     # уйдёт с timeout=30 — kwargs уже содержит "timeout", setdefault его не трогает
```

Это удобно для медленных эндпоинтов (например, генерация отчёта на сервере) — не обязательно поднимать таймаут по умолчанию для вообще всех запросов клиента, достаточно указать его точечно, в конкретном вызове.

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

## Мини-задания

1. **Разминка.** В отдельном скрипте создай `session = build_http_session(base_url="https://jsonplaceholder.typicode.com")` и `client = APIClient(session=session)`. Сделай `client.get("/users/1")` и `client.get("/posts/1")`, распечатай `response.status_code` для каждого. Затем попробуй `client.get("users/1")` (без ведущего слэша) — убедись, что результат тот же самый, и объясни себе, почему `lstrip("/")` внутри `BaseUrlSession` делает разницу между `"users/1"` и `"/users/1"` несущественной.

2. **Основное.** До того как заглянуть в готовый `APIClient`/`BaseUrlSession` из теории выше, — попробуй сам, "с нуля". Напиши в отдельном скрипте маленький класс `SimpleClient`: конструктор принимает `base_url` и сохраняет его, метод `get(path)` делает `requests.get(...)` на `base_url + path`, метод `post(path, json)` — аналогично `requests.post(...)`. Проверь его на `client.get("/users/1")` и `client.post("/posts", json={"title": "x"})` — оба вызова должны реально сходить в сеть и вернуть ответ. Теперь сравни свой `SimpleClient` с настоящим `APIClient`/`BaseUrlSession`: что он делает так же, а что — иначе (единая точка для всех методов через `request`, таймаут по умолчанию)? Переписывать свой класс под эталон не нужно — важно осознанно увидеть разницу, а не просто прочитать чужой код.

3. **Ближе к практике.** Замерь на практике, что даёт таймаут по умолчанию. В отдельном скрипте создай сессию через `build_http_session(base_url="https://jsonplaceholder.typicode.com")` и вызови `session.get("/users/1", timeout=0.001)` — заведомо нереалистично маленький таймаут; убедись, что `requests` бросает исключение (`requests.exceptions.ConnectTimeout` или `ReadTimeout`), и `kwargs.setdefault` тут не спас, потому что таймаут был передан явно. Затем вызови `session.get("/users/1")` без явного таймаута и убедись, что запрос успевает выполниться за таймаут по умолчанию (10 секунд), который подставился сам.

4. **Со звёздочкой.** Собери у себя мини-версию `BaseUrlSession`, но переопредели в ней не `request`, а `get`. Позови `session.post("/users", json={"name": "x"})` и убедись, что подстановки `base_url` не произошло (упадёт с ошибкой невалидного URL для `post`, хотя для `get` всё будет работать) — это и есть частая ошибка из раздела выше, только теперь ты увидишь её на собственном коде, а не прочитаешь как утверждение.
