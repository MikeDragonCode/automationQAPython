# 6.2. Читаем GitHub Actions workflow

## Зачем это нужно

Если твой репозиторий живёт на GitHub, пайплайн описывается файлом в `.github/workflows/*.yml`. Уметь прочитать такой файл — значит понимать, что именно выполнится при твоём следующем push, ещё до того, как это произойдёт.

## Теория

### on: — что запускает workflow

**`on:`** описывает триггеры запуска. В `boilerplate/.github/workflows/ci.yml`:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

Пайплайн запускается на push в `main` и на любой PR, целящийся в `main`. Значит, каждый твой PR в общий репозиторий автоматически прогонит этот workflow. Обрати внимание: push в любую другую ветку (например, твою рабочую `feature/...`) сам по себе этот workflow не запустит — сработает именно момент, когда из неё открыт PR в `main`.

### jobs, runs-on и steps — из чего состоит job

- **`jobs:`** — словарь job'ов, каждый со своим именем.
- **`runs-on:`** — на какой виртуальной машине выполняется job (например `ubuntu-latest`).
- **`steps:`** — последовательность шагов внутри job'а.

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

### uses: vs run: — готовое действие или своя команда

Шаг описывается одним из двух способов: `uses:` подключает готовое переиспользуемое действие из GitHub Actions Marketplace (например `actions/checkout@v4` — стандартный шаг клонирования репозитория), а `run:` выполняет произвольную shell-команду (например `pip install -r requirements.txt`). Оба варианта видно прямо в шагах `unit-and-api`: `uses: actions/checkout@v4` — готовое действие, `run: pip install -r requirements.txt` — своя команда.

### needs: — зависимость между jobs

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

### if: always() — сохранение данных даже при падении

По умолчанию шаг в GitHub Actions выполняется, только если все предыдущие шаги job'а прошли успешно. `if: always()` отменяет это правило для конкретного шага — он выполнится в любом случае, даже если тесты выше упали:

```yaml
- name: Upload allure results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: allure-results-api
    path: allure-results
```

Без этой строчки при падении тестов шаг загрузки артефакта просто не выполнился бы, и результаты прогона (нужные для диагностики через Allure, модуль 5) потерялись бы — а они особенно нужны именно тогда, когда что-то упало.

## Пример

Собранные вместе, оба job'а из `boilerplate/.github/workflows/ci.yml` описывают последовательный пайплайн: сначала `unit-and-api` (быстро, без браузера), и только при его успехе — `ui` (медленнее, с Chromium), причём оба job'а в любом случае сохраняют `allure-results` как артефакт, даже если тесты внутри упали.

## Частые ошибки

- Не заметить `needs:` и удивляться, почему UI job вообще не запустился — если `unit-and-api` упал, `ui` не стартует.
- Забыть `if: always()` при добавлении своего шага сохранения артефактов — без него шаг выполнится только при успехе предыдущих, и при падении тестов ты не увидишь allure-results вообще.
- Путать `uses:` (готовое переиспользуемое действие из marketplace) и `run:` (произвольная shell-команда) — это разные механизмы описания шага.

## Мини-задания

1. **Разминка.** Найди в `ci.yml` секцию `on:` и перечисли оба триггера, которые запускают workflow. Запустится ли этот workflow сам по себе на push в ветку `feature/my-branch`, если из неё ещё не открыт PR в `main`?
2. **Основное.** Найди в `ci.yml` строку, отвечающую за версию Python, и ответь: что произойдёт, если у тебя локально Python 3.11, а в CI указан 3.12 — где тесты выполнятся "по-настоящему", а где — просто для проверки перед мёржем?
3. **Ближе к практике.** Представь, что в логе job'а `ui` ты видишь строку `Executable doesn't exist at .../chromium-.../chrome-linux/headless_shell`. Найди в `ci.yml`, в каком именно шаге устанавливается браузер для UI-тестов, и объясни своими словами, что скорее всего пошло не так и на каком этапе (до запуска `pytest` или уже во время него) это произошло.
4. **Со звёздочкой.** Если убрать `needs: unit-and-api` из job'а `ui`, что изменится в поведении пайплайна — когда теперь стартует `ui`? И если после этого `unit-and-api` упадёт, выполнится ли `ui`, и почему это может быть нежелательным поведением для реального проекта?

## Как посмотреть результат в интерфейсе GitHub

Вкладка **Actions** в репозитории → конкретный workflow run → список jobs слева → клик на job открывает лог каждого шага. Красный крестик у шага — именно там нужно искать причину падения (см. урок 6.4).
