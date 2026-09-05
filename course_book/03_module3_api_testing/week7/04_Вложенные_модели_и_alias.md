# 3.10. Вложенные модели и Field(alias=...): camelCase vs snake_case

## Зачем это нужно

Реальные API редко возвращают данные в питоновском стиле именования. Рано или поздно тебе встретится поле вроде `firstName` или `createdAt`, и нужно будет решить: либо жить с некрасивым `snake_case`-нарушением в коде, либо настроить Pydantic так, чтобы он сам сопоставлял `camelCase` из JSON с `snake_case` в Python. Разберём оба варианта на реальном примере из репозитория.

## Теория

### Откуда берётся проблема camelCase / snake_case

В Python принят стиль именования `snake_case` (`first_name`, `created_at`). Во многих API (особенно написанных на JavaScript/TypeScript-бэкендах) принят `camelCase` (`firstName`, `createdAt`). Когда мы описываем Pydantic-модель под такой API, у нас есть выбор:

1. Назвать поле модели точно так же, как в JSON (`firstName: str`) — просто, но нарушает питоновский код-стиль внутри проекта.
2. Назвать поле в `snake_case` (`first_name: str`), а связь с JSON-ключом `firstName` настроить через `Field(alias=...)`.

### Field(alias=...)

```python
from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    id: str
    email: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
```

Теперь при создании модели из JSON-словаря `{"id": "1", "email": "a@b.com", "firstName": "Alice", "lastName": "Smith"}` Pydantic сам сопоставит `firstName` → `first_name`. В Python-коде дальше работаем как обычно: `user.first_name`, а не `user.firstName`.

**Важный нюанс:** если задан `alias`, по умолчанию Pydantic ожидает при создании объекта именно алиас (`firstName=...`), а не имя поля (`first_name=...`). Чтобы можно было создавать модель обоими способами (и через алиас, и через имя поля в snake_case — это удобно в тестах, где ты сам формируешь запрос), добавляют:

```python
from pydantic import BaseModel, ConfigDict, Field


class UserSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    first_name: str = Field(alias="firstName")
```

### Обратная сериализация: model_dump(by_alias=True)

Когда модель нужно превратить обратно в словарь для отправки в API, по умолчанию `model_dump()` вернёт ключи в том виде, в котором названы поля модели (`snake_case`). Если API ожидает `camelCase` обратно, нужно явно попросить сериализовать через алиасы:

```python
user.model_dump()               # {"first_name": "Alice", ...} — snake_case
user.model_dump(by_alias=True)  # {"firstName": "Alice", ...} — camelCase, как ждёт API
```

### А что у нас в демо-API?

Открой ещё раз `boilerplate/clients/users/users_schema.py`. Там **нет** ни одного `Field(alias=...)`:

```python
class CompanySchema(BaseModel):
    name: str
    catchPhrase: str  # camelCase-поле оставлено как есть, без alias
    bs: str
```

Это осознанное и вполне рабочее решение: JSONPlaceholder возвращает всего одно по-настоящему "неудобное" поле (`catchPhrase`), и ради него не стали городить `Field(alias=...)` — проще один раз назвать поле модели так же, как в JSON. **Alias нужен не всегда** — он оправдан, когда camelCase-полей в API много и хочется единообразного `snake_case` во всём проекте, либо когда важно строго придерживаться PEP 8 в командном коде. Если поле одно и погоды не делает — это решение архитектурного вкуса команды, а не жёсткое правило Pydantic.

Если бы мы хотели переименовать `catchPhrase` в `catch_phrase`, выглядело бы это так:

```python
class CompanySchema(BaseModel):
    name: str
    catch_phrase: str = Field(alias="catchPhrase")
    bs: str
```

### serialization_alias и validation_alias — когда вход и выход отличаются

Иногда имя поля при чтении из API и при отправке обратно должно различаться, либо алиас нужен только в одну сторону. Для этого у `Field` есть более точечные параметры, чем общий `alias`: `validation_alias` действует только при создании модели (то есть при чтении входящих данных), а `serialization_alias` — только при `model_dump()`/`model_dump_json()` (то есть при отправке):

```python
class UserSchema(BaseModel):
    first_name: str = Field(validation_alias="firstName", serialization_alias="first_name")
```

Здесь модель ожидает на вход `firstName` (как приходит от API), а при сериализации обратно отдаёт `first_name` — например, если твой собственный тестовый код где-то дальше договорился работать со snake_case, а внешний API отдаёт camelCase. `alias` — это просто сокращённая запись для случая, когда `validation_alias` и `serialization_alias` совпадают.

### alias_generator — когда camelCase-полей много

Если бы camelCase был не в одном поле, а во всех, вручную писать `Field(alias=...)` для каждого было бы утомительно. Для этого в Pydantic есть `alias_generator`:

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CourseSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    max_score: int
    min_score: int
```

`to_camel` автоматически превращает имя каждого поля модели (`max_score`) в алиас в camelCase (`maxScore`) — не нужно расставлять `Field(alias=...)` вручную для каждого поля. В нашем демо-API такой необходимости пока нет (camelCase-поле всего одно), но полезно знать про этот механизм — он часто встречается в реальных проектах.

## Пример

Полный пример на модели из репозитория с вложенностью (`UserSchema` → `AddressSchema` → `GeoSchema`):

```python
from pydantic import BaseModel, EmailStr


class GeoSchema(BaseModel):
    lat: str
    lng: str


class AddressSchema(BaseModel):
    street: str
    suite: str
    city: str
    zipcode: str
    geo: GeoSchema


class CompanySchema(BaseModel):
    name: str
    catchPhrase: str
    bs: str


class UserSchema(BaseModel):
    id: int
    name: str
    username: str
    email: EmailStr
    address: AddressSchema
    phone: str
    website: str
    company: CompanySchema
```

Начинать проектирование модели стоит "снизу вверх" — сначала описать самые вложенные структуры (`GeoSchema`), затем те, что их используют (`AddressSchema`), и в конце — главную модель (`UserSchema`). Именно в таком порядке модели и расположены в файле.

## Частые ошибки

- Добавлять `Field(alias=...)` "на всякий случай" ко всем полям, даже если имя в JSON и так уже совпадает со `snake_case` — лишний код без пользы.
- Забыть `populate_by_name=True` (или актуальный аналог в используемой версии Pydantic) и получить ошибку при попытке создать модель через имя поля, а не через алиас.
- Забыть `by_alias=True` при сериализации запроса обратно в JSON — тогда в API уйдёт `snake_case` там, где он ждёт `camelCase`, и запрос будет отклонён или воспринят неправильно.
- Проектировать модели "сверху вниз" и путаться в структуре — начинай с самых глубоко вложенных объектов.

## Мини-задания

1. **Разминка.** Объяви `class Simple(BaseModel): full_name: str = Field(alias="fullName")` без `populate_by_name`. Попробуй создать объект двумя способами: `Simple(fullName="Alice")` и `Simple(full_name="Alice")`. Убедись, что первый вариант работает, а второй падает с `ValidationError` — своими глазами увидь то, о чём написано в теории ("по умолчанию Pydantic ожидает именно alias").

2. **Основное.** В отдельном scratch-скрипте (не в общем репозитории) объяви свою копию модели — только сам класс, не весь файл: `class MyCompanySchema(BaseModel): name: str; catch_phrase: str = Field(alias="catchPhrase"); bs: str`. Получи реального пользователя через `requests.get("https://jsonplaceholder.typicode.com/users/1")`, возьми `response.json()["company"]` и создай из него модель: `MyCompanySchema(**response.json()["company"])`. Убедись, что `company.catch_phrase` работает так же, как в оригинальной схеме работал `company.catchPhrase`. Ничего в общем репозитории менять и откатывать не нужно — весь эксперимент живёт в твоём отдельном файле.

3. **Ближе к практике.** Добавь в свою `MyCompanySchema` из задания 2 `model_config = ConfigDict(populate_by_name=True)`. Убедись, что теперь модель можно создать обоими способами: и через алиас (`MyCompanySchema(name="x", catchPhrase="y", bs="z")`), и через имя поля (`MyCompanySchema(name="x", catch_phrase="y", bs="z")`). Затем вызови `model_dump()` и `model_dump(by_alias=True)` на одном и том же объекте и сравни ключи в обоих словарях — убедись, что только второй вариант вернёт `catchPhrase`, а не `catch_phrase`.

4. **Со звёздочкой.** Перепиши `MyCompanySchema` на использование `alias_generator`: `class MyCompanySchema(BaseModel): model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True); name: str; catch_phrase: str; bs: str` (без ручного `Field(alias=...)`). Проверь на том же `response.json()["company"]`, что `company.catch_phrase` и `model_dump(by_alias=True)["catchPhrase"]` работают так же, как и в задании 3 с ручным `Field(alias=...)`. Объясни себе, в какой момент вручную прописанный `alias` становится неудобным, а `alias_generator` — оправданным (частая ошибка "добавлять alias ко всем полям на всякий случай" — здесь генератор делает это за тебя одной строкой конфига, без ручного повторения для каждого поля).
