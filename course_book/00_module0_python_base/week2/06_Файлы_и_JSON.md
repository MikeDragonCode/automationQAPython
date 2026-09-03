# 0.13. Файлы и JSON

## Зачем это нужно

Тестовые данные (логины, ожидаемые ответы) часто хранят в отдельных файлах, а не прямо в коде — так их проще менять, не трогая сам тест. Ответы большинства современных API приходят в формате JSON, и структура JSON почти один в один совпадает со словарями и списками Python, которые ты уже знаешь. Это последний кусочек синтаксиса перед итоговым проектом модуля — скриптом, который реально дёргает публичное API и обрабатывает его JSON-ответ.

## Теория

### Открытие и закрытие файлов

Функция `open(path, mode, encoding=...)` открывает файл. По умолчанию — режим чтения (`"r"`). Другие частые режимы: `"w"` (запись, стирает старое содержимое!), `"a"` (дозапись в конец, не стирая). Всегда указывай `encoding="utf-8"` явно — иначе поведение может зависеть от настроек операционной системы.

Открытый файл обязательно нужно закрывать после использования (`file.close()`), иначе данные могут не сохраниться или файл останется заблокированным. Вместо того чтобы помнить об этом вручную, используют **менеджер контекста** `with` — он гарантированно закроет файл, даже если внутри блока произойдёт ошибка:

```python
with open("data.txt", encoding="utf-8") as file:
    content = file.read()
# файл уже закрыт здесь, даже если что-то пошло не так внутри блока
```

Методы чтения: `.read()` — весь файл одной строкой, `.readline()` — одна строка, `.readlines()` — список всех строк. Чаще всего для построчной обработки используют цикл, потому что файл сам по себе — итерируемый объект:

```python
with open("data.txt", encoding="utf-8") as file:
    for line in file:
        print(line.strip())   # .strip() убирает символ переноса строки '\n'
```

Запись — методом `.write()` (принимает строку, не добавляет перенос строки автоматически) или `.writelines()` (список строк):

```python
with open("out.txt", "w", encoding="utf-8") as file:
    file.write("first line\n")
    file.write("second line\n")
```

### Обработка отсутствующего файла

Если файла не существует, `open()` на чтение вызовет исключение `FileNotFoundError`, и программа аварийно завершится. Чтобы этого не происходило, ошибку оборачивают в `try/except`:

```python
try:
    with open("data.txt", encoding="utf-8") as file:
        content = file.read()
except FileNotFoundError:
    print("Файл не найден, использую значения по умолчанию")
    content = ""
```

Это единственная конструкция обработки исключений, которая нужна на этом этапе курса — подробно `try/except` разберём позже, когда он понадобится для более сложных сценариев (в API-тестах, например).

### Модуль json

JSON (JavaScript Object Notation) — текстовый формат данных, который выглядит почти как словари и списки Python: `{}` — объект (словарь), `[]` — массив (список), строки в двойных кавычках, числа, `true`/`false`/`null` (в Python эквивалентны `True`/`False`/`None`).

Модуль `json` из стандартной библиотеки умеет превращать JSON-текст в Python-объекты и обратно:

| Функция | Что делает |
|---|---|
| `json.loads(text)` | строка JSON → объект Python (словарь/список) |
| `json.dumps(obj)` | объект Python → строка JSON |
| `json.load(file)` | читает JSON прямо из открытого файла → объект Python |
| `json.dump(obj, file)` | записывает объект Python в файл в формате JSON |

```python
import json

data = {"id": 1, "username": "ivan", "is_active": True}

# в строку и обратно
json_text = json.dumps(data)
print(json_text)                    # '{"id": 1, "username": "ivan", "is_active": true}'
restored = json.loads(json_text)
print(restored["username"])         # ivan

# в файл и обратно
with open("user.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

with open("user.json", encoding="utf-8") as file:
    loaded = json.load(file)
    print(loaded)
```

Параметр `indent=2` в `json.dump()` делает файл читаемым для человека (с отступами), а `ensure_ascii=False` — чтобы кириллица сохранялась как есть, а не превращалась в `\uXXXX`-последовательности.

## Пример

```python
import json

test_results = [
    {"test": "test_login", "status": "passed"},
    {"test": "test_registration", "status": "failed"},
]

# сохраняем результаты в файл
with open("results.json", "w", encoding="utf-8") as file:
    json.dump(test_results, file, ensure_ascii=False, indent=2)

# читаем обратно и считаем упавшие тесты
try:
    with open("results.json", encoding="utf-8") as file:
        loaded_results = json.load(file)
except FileNotFoundError:
    loaded_results = []

failed = [r["test"] for r in loaded_results if r["status"] == "failed"]
print(f"Failed tests: {failed}")
# Failed tests: ['test_registration']
```

## Частые ошибки

- Забыть `encoding="utf-8"` — на некоторых системах кириллица и спецсимволы читаются/пишутся некорректно.
- Открыть файл в режиме `"w"`, рассчитывая дозаписать в конец, — режим `"w"` стирает старое содержимое, для дозаписи нужен `"a"`.
- Не обработать `FileNotFoundError` — скрипт падает с трудночитаемым traceback вместо понятного сообщения.
- Перепутать `json.dump`/`json.load` (работают с открытым файлом) и `json.dumps`/`json.loads` (работают со строкой) — буква `s` на конце означает "string".

## Мини-задание

Создай список из 3–4 словарей, описывающих тестовых пользователей (`username`, `email`, `age`). Сохрани его в файл `users.json` с помощью `json.dump` (с отступами и поддержкой кириллицы). Затем открой этот файл заново, прочитай через `json.load`, оберни чтение в `try/except FileNotFoundError` и выведи количество пользователей старше 18 лет.
