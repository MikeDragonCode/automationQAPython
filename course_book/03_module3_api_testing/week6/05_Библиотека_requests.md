# 3.5. Библиотека requests: первые запросы

## Зачем это нужно

`requests` — стандартная библиотека Python для HTTP-запросов, на которой построен весь API-слой нашего общего репозитория. Прежде чем разбирать готовый `APIClient` (модуль недели 7), нужно уверенно понимать, что делает сама библиотека без всяких обёрток — иначе абстракции сверху будут выглядеть как магия.

## Теория

`requests` устанавливается через `pip install requests` (в `boilerplate/requirements.txt` она уже зафиксирована) и предоставляет функции по каждому HTTP-методу: `requests.get()`, `requests.post()`, `requests.put()`, `requests.patch()`, `requests.delete()`.

### Базовый запрос и объект Response

```python
import requests

response = requests.get("https://jsonplaceholder.typicode.com/users/1")
```

Результат вызова — объект `Response`. У него есть несколько ключевых атрибутов и методов, которые ты будешь использовать в каждом тесте:

- `response.status_code` — числовой статус-код ответа (`int`), например `200`.
- `response.json()` — парсит тело ответа как JSON и возвращает Python-объект (обычно `dict` или `list`). Бросит исключение, если тело не является валидным JSON.
- `response.text` — тело ответа как есть, в виде строки, без парсинга.
- `response.headers` — заголовки ответа (похоже на словарь).

### Query-параметры

Передаются через именованный аргумент `params` — `requests` сам соберёт из словаря строку запроса:

```python
response = requests.get(
    "https://jsonplaceholder.typicode.com/comments",
    params={"postId": 1},
)
print(response.url)  # https://jsonplaceholder.typicode.com/comments?postId=1
```

### Тело запроса (JSON)

Для методов, поддерживающих тело (`POST`, `PUT`, `PATCH`), данные передаются через `json=` — `requests` сам сериализует словарь в JSON-строку и выставит заголовок `Content-Type: application/json`:

```python
response = requests.post(
    "https://jsonplaceholder.typicode.com/users",
    json={"name": "QA Student", "username": "qa_student"},
)
print(response.status_code)  # 201
print(response.json())       # созданный (не сохранённый по-настоящему) объект с id
```

Если нужно отправить данные в формате `application/x-www-form-urlencoded` (это встречается реже, но иногда требуется, например, для некоторых форм логина), используется аргумент `data=` вместо `json=`.

### Заголовки и таймаут

```python
response = requests.get(
    "https://jsonplaceholder.typicode.com/users/1",
    headers={"Authorization": "Bearer <token>"},
    timeout=10,
)
```

`timeout` — не мелочь ради галочки. Без него тест может зависнуть на неопределённое время, если сервер не отвечает. Хорошая практика — всегда задавать таймаут явно.

### requests.get(...) в каждом тесте — рабочий, но не масштабируемый вариант

На этом этапе у тебя уже достаточно знаний, чтобы написать первый настоящий API-тест:

```python
import requests


def test_get_user():
    response = requests.get("https://jsonplaceholder.typicode.com/users/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
```

Это рабочий тест. Но если таких тестов станет двадцать, а базовый URL API вдруг изменится (например, добавится версия `/api/v2/...`) — тебе придётся редактировать URL в каждом тесте. Это и есть повод для следующего урока: как убрать повторяющиеся детали (`base_url`, заголовки, таймаут) в одно место.

## Пример

Полный пример работы с `requests`, включающий GET, POST и обработку ошибки:

```python
import requests

# Успешный GET
response = requests.get("https://jsonplaceholder.typicode.com/users/1")
print(response.status_code, response.json())

# POST с телом
response = requests.post(
    "https://jsonplaceholder.typicode.com/users",
    json={"name": "QA Student", "username": "qa_student", "email": "qa@example.com"},
)
print(response.status_code, response.json())

# Запрос к несуществующему ресурсу
response = requests.get("https://jsonplaceholder.typicode.com/users/9999")
print(response.status_code)  # 404
```

## Частые ошибки

- Забыть таймаут и получить тест, который зависает на минуты при проблемах с сетью.
- Вызвать `response.json()` на ответе, у которого тело — не JSON (например, HTML-страница ошибки 502 от прокси-сервера) — упадёт с исключением, а не даст полезное сообщение "нет JSON".
- Перепутать `params` и `json` — например, попытаться передать тело GET-запроса через `json=` (у большинства серверов GET с телом либо игнорируется, либо приводит к ошибке).
- Не проверять `response.status_code` перед тем, как парсить `response.json()` — если сервер вернул ошибку с пустым телом, `.json()` упадёт раньше, чем ты увидишь осмысленное сообщение об ошибке.

## Мини-задание

Напиши три отдельных вызова `requests` без обёрток: GET на `/users/1`, POST на `/posts` с телом `{"title": "test", "body": "text", "userId": 1}`, DELETE на `/posts/1`. Для каждого вывода в консоль и `response.status_code`, и `response.json()`. Убедись, что коды ответа соответствуют тому, что ты изучил в уроках 3.2–3.3.
