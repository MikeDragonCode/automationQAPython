# 4.14. Разбираем DashboardPage построчно

## Зачем это нужно

`DashboardPage` показывает важную вещь, которую легко упустить: Page Object не обязан быть большим классом со множеством методов. Он должен содержать ровно столько, сколько реально нужно тестам — не больше. Это прямо пригодится в домашнем задании: твой `LoginPage` тоже не должен разрастаться "про запас".

## Теория

Открой `boilerplate/pages/dashboard_page.py` — это всего 19 строк:

```python
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class DashboardPage(BasePage):
    URL = "https://nikita-filonov.github.io/qa-automation-engineer-ui-course/#/dashboard"

    def __init__(self, page: Page):
        super().__init__(page)

        self.toolbar_title = page.locator("[data-testid='dashboard-toolbar-title-text']")

    def check_opened(self) -> None:
        self.check_current_url(self.URL)

    def check_visible_toolbar_title(self) -> None:
        expect(self.toolbar_title).to_be_visible()
        expect(self.toolbar_title).to_have_text("Dashboard")
```

### Наследование и URL

```python
class DashboardPage(BasePage):
    URL = "https://nikita-filonov.github.io/qa-automation-engineer-ui-course/#/dashboard"
```

Так же, как в `RegistrationPage`: наследование от `BasePage` и адрес страницы в виде атрибута класса.

### Конструктор и единственный локатор

```python
def __init__(self, page: Page):
    super().__init__(page)

    self.toolbar_title = page.locator("[data-testid='dashboard-toolbar-title-text']")
```

В отличие от `RegistrationPage`, тут всего один локатор — заголовок страницы. Заметь: у `DashboardPage` нет метода `open_page()`. Это осознанное решение, а не недосмотр — в нашем сценарии пользователь никогда не открывает Dashboard напрямую по URL, он попадает туда только через клик по кнопке Registration. Метод, который никогда не будет вызван, не добавляется просто "для полноты".

### Метод `check_opened`

```python
def check_opened(self) -> None:
    self.check_current_url(self.URL)
```

Это самая показательная строка во всём модуле. `DashboardPage` не проверяет URL заново своими силами — он переиспользует `check_current_url()`, унаследованный от `BasePage` (урок 4.12), просто подставляя туда собственный `self.URL`. Никакого дублирования логики проверки URL между страницами нет — она реализована один раз, в базовом классе.

Название метода — `check_opened`, а не, скажем, `check_url` — читается как законченное утверждение "проверить, что страница открыта". Снаружи тесту не важно, что внутри используется именно проверка URL — он вызывает метод, который отвечает на вопрос по существу.

### Метод `check_visible_toolbar_title`

```python
def check_visible_toolbar_title(self) -> None:
    expect(self.toolbar_title).to_be_visible()
    expect(self.toolbar_title).to_have_text("Dashboard")
```

Две отдельные проверки: сначала — что заголовок вообще виден, затем — что в нём правильный текст. Обрати внимание, что `check_opened()` и `check_visible_toolbar_title()` — это два разных метода, а не один общий `check_dashboard_page()`. Это тоже осознанное разделение: одна проверка отвечает на вопрос "мы на нужной странице?" (по URL), а другая — на вопрос "на странице отображается ожидаемое содержимое?" (по заголовку). Разделение по смыслу делает каждый метод маленьким, понятным и пригодным для переиспользования отдельно от другого — например, где-то в другом сценарии может понадобиться проверить только переход, без проверки заголовка.

## Пример

В тесте эти два метода читаются как два последовательных, но разных по смыслу утверждения:

```python
dashboard_page.check_opened()
dashboard_page.check_visible_toolbar_title()
```

Первая строка: "мы попали туда, куда нужно". Вторая строка: "и там отображается то, что ожидалось". Тест не знает ни про URL, ни про локатор заголовка, ни про то, что `check_opened()` внутри себя вызывает метод из `BasePage`, — вся эта механика скрыта внутри `DashboardPage`.

## Частые ошибки

- Добавлять в `DashboardPage` метод `open_page()` "по аналогии с RegistrationPage" — если в реальных сценариях страница никогда не открывается напрямую, такой метод не нужен: лишний код без применения так же вредит читаемости, как и его нехватка.
- Сливать `check_opened()` и `check_visible_toolbar_title()` в один метод — это будет работать, но лишит тест возможности использовать одну проверку без другой и усложнит диагностику, если тест упадёт (непонятно сразу, что именно не выполнилось: переход или отрисовка).
- Писать `expect(page.locator("[data-testid='dashboard-toolbar-title-text']"))` заново внутри `check_visible_toolbar_title()`, вместо использования готового `self.toolbar_title` из конструктора.

## Мини-задание

Сравни объём кода `RegistrationPage` (урок 4.13) и `DashboardPage` (этот урок). `DashboardPage` заметно меньше — попробуй сформулировать своими словами, почему это нормально и не является признаком "недоделанного" Page Object.
