# 4.16. Добавляем новый Page Object: шаблон на примере LoginPage

## Зачем это нужно

Это последний теоретический урок модуля — и он же самый практический. Дальше домашнее задание попросит тебя сделать ровно то, что мы сейчас разберём: добавить в `boilerplate/pages/` новый Page Object по образцу уже существующих. Здесь мы соберём этот процесс в пошаговый чек-лист на примере `LoginPage` для страницы логина учебного приложения.

## Теория

У учебного приложения есть страница логина по адресу `.../#/auth/login`. Через DevTools на ней найдены такие `data-testid`:

| Элемент | `data-testid` | Особенность |
|---|---|---|
| Поле Email | `login-form-email-input` | на внешнем `div`, `input` вложен внутрь — как в `RegistrationPage` |
| Поле Password | `login-form-password-input` | так же, `input` вложен внутрь |
| Кнопка LOGIN | `login-page-login-button` | стоит прямо на `<button>` |
| Ссылка "Registration" | `login-page-registration-link` | стоит прямо на `<a>` |

Структура полностью повторяет то, что мы разбирали в уроках 4.3–4.4 для формы регистрации: и `login-form-email-input`, и `login-form-password-input` — это контейнеры, а не сами поля ввода, поэтому в локаторе нужно добавлять `input`. У кнопки и ссылки `data-testid` стоит прямо на элементе, поэтому без уточнения.

### Шаг 1. Создать файл рядом с существующими

```
boilerplate/pages/login_page.py
```

Не в отдельной папке, не с другим именованием — рядом с `base_page.py`, `registration_page.py`, `dashboard_page.py`, в том же стиле именования (`snake_case`, суффикс `_page`).

### Шаг 2. Импорты и наследование

```python
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    URL = "https://nikita-filonov.github.io/qa-automation-engineer-ui-course/#/auth/login"
```

Тот же набор импортов, что у `RegistrationPage` и `DashboardPage`: `Page` для аннотации типа, `expect` для проверок, `BasePage` для наследования. `URL` — атрибут класса, как и в остальных страницах.

### Шаг 3. Конструктор с `super().__init__` и локаторами

```python
    def __init__(self, page: Page):
        super().__init__(page)

        self.email_input = page.locator("[data-testid='login-form-email-input'] input")
        self.password_input = page.locator("[data-testid='login-form-password-input'] input")
        self.login_button = page.locator("[data-testid='login-page-login-button']")
```

Обязательный первый вызов — `super().__init__(page)`, иначе `self.page` не появится (урок 4.12). Дальше — локаторы, по одному на каждый нужный элемент, сохранённые в атрибуты, а не пересоздаваемые внутри методов (урок 4.13).

### Шаг 4. Метод открытия страницы

```python
    def open_page(self) -> None:
        super().open(self.URL)
```

В отличие от `DashboardPage`, здесь метод открытия нужен: пользователь может зайти на страницу логина напрямую.

### Шаг 5. Действия пользователя

```python
    def fill_login_form(self, email: str, password: str) -> None:
        self.email_input.fill(email)
        self.password_input.fill(password)

    def click_login_button(self) -> None:
        self.login_button.click()
```

Один метод на осмысленное действие пользователя — заполнение формы целиком, отдельно клик по кнопке. Так же, как в `RegistrationPage.fill_registration_form()`.

### Шаг 6. Проверки

```python
    def check_visible_login_form(self) -> None:
        expect(self.email_input).to_be_visible()
        expect(self.password_input).to_be_visible()
        expect(self.login_button).to_be_visible()
```

Проверка отображения формы — по тому же шаблону, что `check_visible_registration_form()`.

### Итоговый файл

```python
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    URL = "https://nikita-filonov.github.io/qa-automation-engineer-ui-course/#/auth/login"

    def __init__(self, page: Page):
        super().__init__(page)

        self.email_input = page.locator("[data-testid='login-form-email-input'] input")
        self.password_input = page.locator("[data-testid='login-form-password-input'] input")
        self.login_button = page.locator("[data-testid='login-page-login-button']")

    def open_page(self) -> None:
        super().open(self.URL)

    def fill_login_form(self, email: str, password: str) -> None:
        self.email_input.fill(email)
        self.password_input.fill(password)

    def click_login_button(self) -> None:
        self.login_button.click()

    def check_visible_login_form(self) -> None:
        expect(self.email_input).to_be_visible()
        expect(self.password_input).to_be_visible()
        expect(self.login_button).to_be_visible()
```

### Проверки — это не только `to_be_visible`

Все проверки, что мы разбирали в уроках 4.12–4.14, использовали `to_be_visible()`, `to_have_url()` и `to_have_text()`. Это далеко не полный список: у `expect()` в Playwright есть и другие проверки состояния элемента — например, `to_be_disabled()` (элемент неактивен) или `to_be_enabled()` (элемент активен). Для новой страницы метод-проверка не обязан ограничиваться видимостью — если по сценарию важно, что кнопка заблокирована, пока форма не заполнена, это тоже законный `check_...`-метод, устроенный по тому же принципу: один `expect(...)` внутри понятно названного метода.

### Как убедиться, что локатор смотрит на тот элемент, что нужно

Таблица `data-testid` в начале урока — не выдумка, а результат осмотра реальной страницы через DevTools (урок 4.2): для каждого элемента нужно было открыть инспектор, найти узел с атрибутом `data-testid` и проверить, стоит ли он прямо на нужном элементе (`<button>`, `<a>`) или на обёртке, внутри которой лежит настоящий `<input>`. Это ровно та же процедура, что мы проделывали для формы регистрации на уроке 4.4. Пропустить этот шаг и написать локатор "по аналогии", не открыв DevTools на реальной странице логина, — самый частый источник локатора, который в тесте просто ничего не находит.

### Шаг 7. Фикстура в conftest.py

По образцу урока 4.15, в `boilerplate/conftest.py` добавляется фикстура рядом с уже существующими — не вместо них:

```python
from pages.login_page import LoginPage


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    return LoginPage(page)
```

### Шаг 8. Использование в тесте

```python
@pytest.mark.ui
def test_login_with_valid_credentials(login_page: LoginPage, dashboard_page: DashboardPage):
    login_page.open_page()
    login_page.check_visible_login_form()
    login_page.fill_login_form(email="user@example.com", password="password123")
    login_page.click_login_button()

    dashboard_page.check_opened()
```

Тест снова не содержит ни одного `page.locator(...)` и ни одного URL — вся техническая часть спрятана внутри `LoginPage` и `DashboardPage`.

## Пример

Полный чек-лист, по которому добавляется любой новый Page Object в этом проекте:

1. Новый файл в `pages/`, имя в `snake_case` с суффиксом `_page`.
2. Класс наследуется от `BasePage`.
3. `URL` как атрибут класса (если у страницы есть собственный адрес).
4. Конструктор начинается с `super().__init__(page)`.
5. Локаторы создаются один раз в конструкторе и сохраняются в `self.*`.
6. Один метод — одно осмысленное действие пользователя.
7. Проверки — отдельными методами, разделёнными по смыслу (переход vs содержимое, как в `DashboardPage`).
8. Фикстура в `conftest.py`, добавленная рядом с существующими.
9. Тест использует только методы Page Object, ни одного `page.locator(...)` напрямую.

## Частые ошибки

- Копировать `RegistrationPage` целиком и просто менять названия переменных, не проверив реальные `data-testid` новой страницы через DevTools — на других страницах приложения атрибуты могут называться иначе.
- Забыть добавить фикстуру в `conftest.py` и создавать `LoginPage(page)` прямо в тесте — это откат к проблеме, которую мы решали в уроке 4.15.
- Помещать новый файл не в `pages/`, а рядом с тестами или в корень проекта — ломает структуру, которую видят и используют все остальные участники общего репозитория.

## Мини-задания

1. **Разминка.** По памяти, не подглядывая в "Итоговый файл" выше, напиши только конструктор `LoginPage` (импорты, наследование, `super().__init__`, три локатора). Затем сверь построчно с версией из урока — какие расхождения нашёл?
2. **Основное.** Прежде чем переходить к домашнему заданию, самостоятельно (без копирования из этого урока) допиши в свой черновик `LoginPage` метод `check_opened`, аналогичный `DashboardPage.check_opened()` из урока 4.14 — с использованием `check_current_url()` из `BasePage`.
3. **Ближе к практике.** В таблице `data-testid` в начале урока есть четвёртый элемент, который не попал в итоговый класс, — ссылка "Registration" (`login-page-registration-link`). Добавь в свой черновик `LoginPage`: локатор `self.registration_link` в конструкторе и метод `click_registration_link()`, построенный по тому же шаблону, что и `click_login_button()`.
4. **Со звёздочкой.** Частые ошибки предупреждают: копировать `RegistrationPage`, не проверив реальные `data-testid` новой страницы. По таблице из урока кнопка LOGIN имеет `data-testid="login-page-login-button"`, стоящий прямо на `<button>` — без вложенного `input`. Напиши, каким локатором её бы описал человек, слепо скопировавший привычку "всегда добавлять `input`" из полей email/password (`page.locator("[data-testid='login-page-login-button'] input")`), и объясни одним предложением, почему такой локатор ничего не найдёт на реальной странице.
