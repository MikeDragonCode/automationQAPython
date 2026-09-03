# boilerplate — общий репозиторий курса

Стартовый фреймворк: `pytest` + `requests` + `playwright`. Именно этот репозиторий студенты
форкают начиная с модуля 2 — дальше все домашки оформляются как PR сюда, а не как отдельные проекты.

## Быстрый старт

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Запуск всех тестов:

```bash
pytest
```

Запуск по группам (маркеры из `pytest.ini`):

```bash
pytest -m unit   # чистые функции, без сети и браузера — модуль 1
pytest -m api    # API-тесты на requests — модуль 3
pytest -m ui     # UI-тесты на Playwright — модуль 4
```

С Allure-отчётом:

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

## Структура

```
boilerplate/
├── clients/            # API-клиенты (модуль 3)
│   ├── api_client.py   # базовый APIClient + BaseUrlSession поверх requests.Session
│   └── users/          # UsersClient — https://jsonplaceholder.typicode.com
├── pages/               # Page Object (модуль 4)
│   ├── base_page.py
│   ├── registration_page.py
│   └── dashboard_page.py
├── tests/
│   ├── unit/            # модуль 1 — pytest на чистых функциях
│   ├── api/             # модуль 3
│   └── ui/              # модуль 4
├── utils/               # fakers, string_utils
├── conftest.py          # общие фикстуры + allure-скриншот при падении UI-теста
├── pytest.ini
└── .github/workflows/ci.yml, .gitlab-ci.yml   # модуль 6
```

## На чём построены примеры

- **UI** — публичное учебное приложение из курса Н. Филонова: https://nikita-filonov.github.io/qa-automation-engineer-ui-course/ (страницы регистрации и Dashboard).
- **API** — публичный демо-API https://jsonplaceholder.typicode.com/users (не требует авторизации, всегда доступен, подходит для отработки GET/POST/PUT/DELETE и Pydantic-схем).

## Правила для PR (с модуля 2)

1. Одна задача — одна ветка — один PR.
2. В описании PR — что сделано и как проверить.
3. Перед мёржем — зелёный CI и минимум одно ревью от одногруппника.
4. Новый API-клиент/Page Object добавляется **рядом** с существующими, по тому же паттерну — не переписывает архитектуру заново.
