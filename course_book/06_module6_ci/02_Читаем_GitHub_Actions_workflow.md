# 6.2. Читаем GitHub Actions workflow

## Зачем это нужно

Если твой репозиторий живёт на GitHub, пайплайн описывается файлом в `.github/workflows/*.yml`. Уметь прочитать такой файл — значит понимать, что именно выполнится при твоём следующем push, ещё до того, как это произойдёт.

## Теория

Ключевые поля YAML-файла GitHub Actions:

- **`on:`** — триггеры запуска (push, pull_request, расписание, ручной запуск).
- **`jobs:`** — словарь job'ов, каждый со своим именем.
- **`runs-on:`** — на какой виртуальной машине выполняется job (например `ubuntu-latest`).
- **`steps:`** — последовательность шагов внутри job'а: либо готовое действие (`uses: actions/checkout@v4`), либо своя команда (`run: pytest ...`).
- **`needs:`** — job зависит от другого job'а и не начнётся, пока тот не завершится успешно.
- **`if: always()`** — шаг выполнится, даже если предыдущие шаги упали (полезно для загрузки артефактов при падении тестов).

## Пример

Разбор `boilerplate/.github/workflows/ci.yml` построчно:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

Пайплайн запускается на push в `main` и на любой PR, целящийся в `main`. Значит, каждый твой PR в общий репозиторий автоматически прогонит этот workflow.

```yaml
jobs:
  unit-and-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit + API tests
        run: pytest -m "unit or api" --alluredir=allure-results
      - name: Upload allure results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: allure-results-api
          path: allure-results
```

Job `unit-and-api`: скачивает код (`checkout`), ставит Python 3.12, ставит зависимости, запускает только unit- и API-тесты (`-m "unit or api"` — тот же синтаксис маркеров из модуля 1!), и в любом случае (`if: always()`, даже если тесты упали) сохраняет папку `allure-results` как артефакт, который потом можно скачать со страницы прогона.

```yaml
  ui:
    runs-on: ubuntu-latest
    needs: unit-and-api
    steps:
      ...
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install --with-deps chromium
      - name: Run UI tests
        run: pytest -m ui --alluredir=allure-results
```

Job `ui` зависит от `unit-and-api` (`needs:`) — то есть UI-тесты (медленные, с браузером) запустятся только если быстрые тесты уже прошли. Дополнительно этот job ставит браузер Chromium (`playwright install`) — шаг, которого нет в первом job'е, потому что там браузер не нужен.

## Частые ошибки

- Не заметить `needs:` и удивляться, почему UI job вообще не запустился — если `unit-and-api` упал, `ui` не стартует.
- Забыть `if: always()` при добавлении своего шага сохранения артефактов — без него шаг выполнится только при успехе предыдущих, и при падении тестов ты не увидишь allure-results вообще.
- Путать `uses:` (готовое переиспользуемое действие из marketplace) и `run:` (произвольная shell-команда) — это разные механизмы описания шага.

## Мини-задание

Найди в `ci.yml` строку, отвечающую за версию Python, и ответь: что произойдёт, если у тебя локально Python 3.11, а в CI указан 3.12 — где тесты выполнятся "по-настоящему", а где — просто для проверки перед мёржем?

## Как посмотреть результат в интерфейсе GitHub

Вкладка **Actions** в репозитории → конкретный workflow run → список jobs слева → клик на job открывает лог каждого шага. Красный крестик у шага — именно там нужно искать причину падения (см. урок 6.4).
