# 6.3. Читаем .gitlab-ci.yml

## Зачем это нужно

Многие компании (особенно в РФ и Сербии) держат репозитории на self-hosted GitLab, а не на GitHub. Синтаксис файла другой, но идея та же — важно уметь мысленно "переводить" между ними.

## Теория

Ключевые поля `.gitlab-ci.yml`:

- **`image:`** — Docker-образ, в котором будут выполняться jobs (аналог `runs-on`, но задаётся образом контейнера, а не именем виртуалки).
- **`stages:`** — список этапов пайплайна по порядку. Все jobs одного stage могут выполняться параллельно; следующий stage стартует только после завершения предыдущего.
- **`before_script:`** — команды, которые выполняются перед каждым job'ом (или конкретным job'ом, если указаны внутри него).
- **`script:`** — основные команды job'а (аналог `run:` в GitHub Actions).
- **`needs:`** — как и в GitHub Actions, явная зависимость job'а от другого (без неё порядок определяется только stage).
- **`artifacts:`** — файлы, которые сохраняются после job'а; `when: always` — сохранять даже при падении.

## Пример

Разбор `boilerplate/.gitlab-ci.yml`:

```yaml
image: python:3.12-slim

stages:
  - test-fast
  - test-ui

before_script:
  - pip install -r requirements.txt
```

Все jobs выполняются в контейнере `python:3.12-slim`. Пайплайн состоит из двух последовательных этапов. `before_script` на верхнем уровне — общий для всех jobs, чтобы не дублировать установку зависимостей.

```yaml
unit-and-api:
  stage: test-fast
  script:
    - pytest -m "unit or api" --alluredir=allure-results
  artifacts:
    when: always
    paths:
      - allure-results
```

Job `unit-and-api` относится к первому этапу (`test-fast`), запускает быстрые тесты и сохраняет `allure-results` как артефакт независимо от результата (`when: always`).

```yaml
ui:
  stage: test-ui
  needs: ["unit-and-api"]
  before_script:
    - pip install -r requirements.txt
    - playwright install --with-deps chromium
  script:
    - pytest -m ui --alluredir=allure-results
```

Job `ui` относится ко второму этапу и явно указывает `needs: ["unit-and-api"]` — переопределяет `before_script` (добавляя установку браузера), потому что для UI-тестов нужен ещё и Chromium.

## Сравнение с GitHub Actions

| GitHub Actions | GitLab CI | Смысл |
|---|---|---|
| `runs-on` | `image` | где выполняется job |
| `jobs.<name>` | `<name>:` (в корне файла) | описание job'а |
| `needs:` | `needs:` | явная зависимость между job'ами |
| `if: always()` на шаге | `when: always` на artifacts | сохранять данные при падении |
| `uses: actions/upload-artifact` | `artifacts: paths:` | сохранение файлов после job'а |

Как только видна эта таблица соответствий, читать любой из двух форматов становится вопросом привычки, а не нового знания.

## Частые ошибки

- Думать, что `before_script` выполняется один раз на весь пайплайн — на самом деле он выполняется перед КАЖДЫМ job'ом заново (в своём чистом контейнере), поэтому установка зависимостей повторяется.
- Не заметить переопределение `before_script` внутри job'а `ui` — оно полностью заменяет верхнеуровневый `before_script` для этого job'а, а не дополняет его.
- Путать `stage:` (единственное число, к какому этапу относится job) и `stages:` (список всех этапов пайплайна).

## Мини-задание

Открой пайплайн своего PR (или пример из `.gitlab-ci.yml`) и найди: какой job выполнится, если stage `test-fast` упадёт — выполнится ли `ui`, и почему.
