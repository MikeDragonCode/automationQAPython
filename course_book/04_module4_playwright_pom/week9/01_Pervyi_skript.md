# 4.6. Первый Playwright-скрипт: goto, locator, fill, click

## Зачем это нужно

Это первый урок, где ты напишешь реально работающий код на Playwright. Дальше в модуле мы будем постоянно опираться на эти четыре операции — `goto`, `locator`, `fill`, `click` — они встречаются в любом UI-автотесте, независимо от того, что он проверяет.

## Теория

Важное уточнение сразу: то, что мы напишем в этом уроке — ещё не тест. Тест не просто выполняет действия, а ещё и проверяет результат через `assert` или `expect()`. Пока проверок не будет, поэтому правильнее называть файл скриптом. Про `expect()` поговорим в следующем уроке (4.7), а полноценные `pytest`-тесты у нас уже есть в `boilerplate/tests/ui/test_registration.py` — на неделе 10 разберём его архитектуру.

### Запуск браузера и создание страницы

Любой Playwright-скрипт в синхронном режиме начинается с одной и той же конструкции:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    browser.close()
```

Разберём по частям:

- `from playwright.sync_api import sync_playwright` — импортирует точку входа в Playwright.
- `with sync_playwright() as p:` — запускает Playwright и создаёт объект `p`, через который дальше запускается браузер.
- `browser = p.chromium.launch(headless=False)` — запускает браузер Chromium в видимом режиме.
- `page = browser.new_page()` — создаёт новую вкладку. `page` — один из главных объектов Playwright: через него выполняется открытие страниц, поиск элементов, ввод текста, клики, проверки.
- `browser.close()` — закрывает браузер после завершения работы.

Если запустить такой скрипт, браузер откроется, создаст пустую вкладку и почти сразу же закроется — между действиями нет пауз, и Python выполняет их за доли секунды.

### `page.goto()` — открываем страницу

```python
page.goto("https://nikita-filonov.github.io/qa-automation-engineer-ui-course/#/auth/registration")
```

Метод `page.goto(url)` открывает страницу по указанному адресу. `page` — это объект, через который Playwright управляет открытой вкладкой браузера, и почти вся дальнейшая работа идёт именно через него: `page.goto(...)`, `page.locator(...)`, `page.url`.

### `page.locator()` и `.fill()` — находим поле и вводим текст

```python
page.locator("[data-testid='registration-form-email-input'] input").fill("user@example.com")
```

`page.locator(...)` находит элемент на странице по локатору (мы разобрали эти локаторы на неделе 8). `.fill(...)` вводит текст в найденное поле. Важно: `fill` не дописывает текст в конец поля, а сначала очищает его и затем устанавливает новое значение — это то, что обычно и нужно при заполнении формы.

### `.click()` — нажимаем кнопку

```python
page.locator("[data-testid='registration-page-registration-button']").click()
```

`.click()` выполняет клик по найденному элементу.

## Пример

Полный сценарий — от открытия страницы до нажатия кнопки Registration:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(
        "https://nikita-filonov.github.io/qa-automation-engineer-ui-course/#/auth/registration"
    )

    page.locator("[data-testid='registration-form-email-input'] input").fill("user@example.com")
    page.locator("[data-testid='registration-form-username-input'] input").fill("testuser")
    page.locator("[data-testid='registration-form-password-input'] input").fill("password123")
    page.locator("[data-testid='registration-page-registration-button']").click()

    browser.close()
```

Порядок действий важен: Playwright выполняет команды сверху вниз, и нельзя заполнить поле до того, как открылась страница, или нажать кнопку раньше, чем заполнены обязательные поля.

Чтобы увидеть результат своими глазами (иначе браузер закроется слишком быстро), временно добавь перед `browser.close()`:

```python
input("Нажмите Enter для завершения...")
```

После проверки эту строку нужно убрать — это временный инструмент отладки, а не часть сценария.

Сохрани скрипт как `registration_script.py` в корне своего форка `boilerplate/` (это отдельный экспериментальный файл, не путай с тестами в `tests/ui/`) и запусти:

```bash
python -m registration_script
```

## Частые ошибки

- Забыть, что `fill()` требует, чтобы элемент уже был на странице — если локатор написан с ошибкой, Playwright будет ждать появления элемента и в итоге упадёт с таймаутом.
- Перепутать порядок действий: попытаться нажать кнопку до заполнения полей.
- Не активировать виртуальное окружение перед запуском — тогда Python не найдёт установленный `playwright`.
- Забыть выполнить `playwright install chromium` — без этого браузер не запустится, и Playwright сам подскажет нужную команду в тексте ошибки.

## Мини-задание

Возьми скрипт из примера и измени значения email, username и password на свои собственные. Добавь `input("Нажмите Enter для завершения...")` перед `browser.close()` и убедись, что все три поля действительно заполнились правильными значениями — глазами, в открывшемся окне браузера.
