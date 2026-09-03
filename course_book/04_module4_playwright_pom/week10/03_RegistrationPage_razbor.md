# 4.13. Разбираем RegistrationPage построчно

## Зачем это нужно

`RegistrationPage` — это первый полноценный Page Object в проекте и, что важнее, это тот самый образец, по которому ты будешь строить свой `LoginPage` в домашнем задании. Каждая деталь в этом файле — не случайность, а конкретное архитектурное решение, которое стоит понимать, а не просто копировать.

## Теория

Открой `boilerplate/pages/registration_page.py`:

```python
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class RegistrationPage(BasePage):
    URL = "https://nikita-filonov.github.io/qa-automation-engineer-ui-course/#/auth/registration"

    def __init__(self, page: Page):
        super().__init__(page)

        self.email_input = page.locator("[data-testid='registration-form-email-input'] input")
        self.username_input = page.locator("[data-testid='registration-form-username-input'] input")
        self.password_input = page.locator("[data-testid='registration-form-password-input'] input")
        self.registration_button = page.locator("[data-testid='registration-page-registration-button']")

    def open_page(self) -> None:
        super().open(self.URL)

    def fill_registration_form(self, email: str, username: str, password: str) -> None:
        self.email_input.fill(email)
        self.username_input.fill(username)
        self.password_input.fill(password)

    def click_registration_button(self) -> None:
        self.registration_button.click()

    def check_visible_registration_form(self) -> None:
        expect(self.email_input).to_be_visible()
        expect(self.username_input).to_be_visible()
        expect(self.password_input).to_be_visible()
        expect(self.registration_button).to_be_visible()
```

Разберём построчно.

### Наследование

```python
class RegistrationPage(BasePage):
```

`RegistrationPage(BasePage)` означает "`RegistrationPage` является наследником `BasePage`". Благодаря этому класс автоматически получает `self.page`, `open()` и `check_current_url()`, разобранные в прошлом уроке, — их не нужно писать заново.

### URL как атрибут класса

```python
URL = "https://nikita-filonov.github.io/qa-automation-engineer-ui-course/#/auth/registration"
```

Адрес страницы хранится внутри самого класса, а не передаётся снаружи и не живёт в тесте. Если адрес когда-нибудь изменится, исправлять его нужно будет только в одном месте.

### Конструктор и `super().__init__(page)`

```python
def __init__(self, page: Page):
    super().__init__(page)
```

`super().__init__(page)` вызывает конструктор родительского класса `BasePage`, который мы разобрали в прошлом уроке, — тот самый, что сохраняет `page` в `self.page`. Без этой строки атрибут `self.page` не появится, и все последующие строки конструктора, которые обращаются к `page.locator(...)`, работали бы (потому что `page` доступен как параметр функции), но методы вроде `open_page()`, использующие `self.page` через `BasePage`, — сломались бы.

### Локаторы в конструкторе

```python
self.email_input = page.locator("[data-testid='registration-form-email-input'] input")
self.username_input = page.locator("[data-testid='registration-form-username-input'] input")
self.password_input = page.locator("[data-testid='registration-form-password-input'] input")
self.registration_button = page.locator("[data-testid='registration-page-registration-button']")
```

Это ровно те локаторы, которые мы собрали в таблицу на уроке 4.4. Ключевое архитектурное решение: локаторы создаются один раз, в конструкторе, и сохраняются в атрибуты (`self.email_input` и так далее). Дальше ни один метод класса не пишет CSS-селектор заново — все они используют уже готовые атрибуты. Это даёт три вещи: страницу проще читать, локатор при изменении интерфейса правится только тут, а тесты вообще перестают что-либо знать про CSS-селекторы.

### Метод `open_page`

```python
def open_page(self) -> None:
    super().open(self.URL)
```

Оборачивает метод `open()` из `BasePage`, подставляя в него собственный `self.URL`. Теперь открыть страницу можно одной понятной командой `registration_page.open_page()` — вызывающему коду (тесту) не нужно знать сам адрес.

### Метод `fill_registration_form`

```python
def fill_registration_form(self, email: str, username: str, password: str) -> None:
    self.email_input.fill(email)
    self.username_input.fill(username)
    self.password_input.fill(password)
```

Один метод вместо трёх отдельных вызовов `.fill()`. Это не техническое ограничение Playwright, а осознанное решение: в нашем сценарии пользователь всегда заполняет форму целиком, поэтому один метод, отражающий это целиком, естественнее, чем `fill_email()`, `fill_username()`, `fill_password()` по отдельности. Такой метод лучше отражает реальное действие пользователя, а не техническую последовательность операций.

### Метод `click_registration_button`

```python
def click_registration_button(self) -> None:
    self.registration_button.click()
```

Оборачивает `.click()` над уже готовым локатором кнопки. Тест теперь может вызвать `registration_page.click_registration_button()`, не зная, что за этим скрывается CSS-локатор.

### Метод `check_visible_registration_form`

```python
def check_visible_registration_form(self) -> None:
    expect(self.email_input).to_be_visible()
    expect(self.username_input).to_be_visible()
    expect(self.password_input).to_be_visible()
    expect(self.registration_button).to_be_visible()
```

Проверяет, что все основные элементы формы действительно отображаются. Такую проверку удобно вызывать сразу после открытия страницы — если что-то не загрузилось, тест упадёт здесь с понятной ошибкой, а не позже, при попытке заполнить несуществующее поле.

## Пример

Собранный воедино, класс уже умеет всё, что нужно для сценария регистрации: открыть страницу, убедиться, что форма видна, заполнить её и нажать кнопку — четыре понятных вызова без единого CSS-локатора снаружи класса:

```python
registration_page.open_page()
registration_page.check_visible_registration_form()
registration_page.fill_registration_form(email="a@b.com", username="user", password="pass123")
registration_page.click_registration_button()
```

## Частые ошибки

- Забыть вызвать `super().__init__(page)` в конструкторе новой страницы — тогда `self.page` не появится, и любой метод, который на него опирается (в том числе унаследованные из `BasePage`), выдаст `AttributeError`.
- Создавать локаторы заново внутри каждого метода (`page.locator(...)` прямо в `click_registration_button`), а не один раз в конструкторе — это работает, но нарушает принцип "локаторы в одном месте", ради которого и затевался Page Object.
- Делать один метод, который и заполняет форму, и кликает кнопку, и проверяет результат — такие методы становится сложно переиспользовать по отдельности в разных сценариях (например, для негативного теста нужно заполнить форму, но не проверять успешный переход).

## Мини-задание

Найди в `boilerplate/pages/registration_page.py` строку, отвечающую за проверку видимости кнопки Registration, и объясни (себе или напарнику), почему она использует `expect(self.registration_button)`, а не, например, `expect(page.locator("[data-testid='registration-page-registration-button']"))` заново.
