# 6.3. Читаем .gitlab-ci.yml

## Зачем это нужно

Многие компании (особенно в РФ и Сербии) держат репозитории на self-hosted GitLab, а не на GitHub. Синтаксис файла другой, но идея та же — важно уметь мысленно "переводить" между ними.

## Теория

### image: — где выполняется job

**`image:`** — Docker-образ, в котором будут выполняться jobs (аналог `runs-on` из GitHub Actions, но задаётся образом контейнера, а не именем виртуалки). В `boilerplate/.gitlab-ci.yml`:

```yaml
image: python:3.12-slim
```

Все jobs пайплайна по умолчанию выполняются в этом контейнере.

### stages и stage — этапы пайплайна

**`stages:`** — список этапов пайплайна по порядку, объявляется один раз на верхнем уровне файла. Все jobs одного stage могут выполняться параллельно; следующий stage стартует только после завершения предыдущего. У каждого job'а есть своё поле **`stage:`** (в единственном числе) — к какому из объявленных этапов он относится:

```yaml
stages:
  - test-fast
  - test-ui
```

```yaml
unit-and-api:
  stage: test-fast
```

Здесь два этапа выполняются строго друг за другом: сначала весь `test-fast`, потом весь `test-ui`.

### before_script и script — общая подготовка и команды job'а

**`before_script:`** — команды, которые выполняются перед каждым job'ом (или конкретным job'ом, если указаны внутри него). **`script:`** — основные команды job'а (аналог `run:` в GitHub Actions).

```yaml
before_script:
  - pip install -r requirements.txt
```

Этот `before_script` объявлен на верхнем уровне файла — значит, он общий для всех jobs, чтобы не дублировать установку зависимостей в каждом. Но job `ui` переопределяет его собственным:

```yaml
ui:
  stage: test-ui
  before_script:
    - pip install -r requirements.txt
    - playwright install --with-deps chromium
  script:
    - pytest -m ui --alluredir=allure-results
```

Важно: `before_script` внутри job'а **полностью заменяет** верхнеуровневый, а не дополняет его — поэтому здесь `pip install -r requirements.txt` пришлось повторить явно, иначе для `ui` зависимости вообще не установились бы.

### needs и artifacts — зависимости и сохранение файлов

**`needs:`** — как и в GitHub Actions, явная зависимость job'а от другого (без неё порядок определяется только принадлежностью к stage). **`artifacts:`** — файлы, которые сохраняются после job'а; `when: always` — сохранять даже при падении:

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

```yaml
ui:
  stage: test-ui
  needs: ["unit-and-api"]
```

Job `ui` относится ко второму этапу и явно указывает `needs: ["unit-and-api"]`.

### Таблица соответствий: GitHub Actions ↔ GitLab CI

| GitHub Actions | GitLab CI | Смысл |
|---|---|---|
| `runs-on` | `image` | где выполняется job |
| `jobs.<name>` | `<name>:` (в корне файла) | описание job'а |
| `needs:` | `needs:` | явная зависимость между job'ами |
| `if: always()` на шаге | `when: always` на artifacts | сохранять данные при падении |
| `uses: actions/upload-artifact` | `artifacts: paths:` | сохранение файлов после job'а |

Как только видна эта таблица соответствий, читать любой из двух форматов становится вопросом привычки, а не нового знания.

## Пример

Разбор `boilerplate/.gitlab-ci.yml` целиком:

```yaml
image: python:3.12-slim

stages:
  - test-fast
  - test-ui

before_script:
  - pip install -r requirements.txt

unit-and-api:
  stage: test-fast
  script:
    - pytest -m "unit or api" --alluredir=allure-results
  artifacts:
    when: always
    paths:
      - allure-results

ui:
  stage: test-ui
  needs: ["unit-and-api"]
  before_script:
    - pip install -r requirements.txt
    - playwright install --with-deps chromium
  script:
    - pytest -m ui --alluredir=allure-results
```

Все jobs выполняются в контейнере `python:3.12-slim`. Пайплайн состоит из двух последовательных этапов: сначала быстрые unit+API тесты, сохраняющие `allure-results` при любом исходе, затем — UI-тесты с браузером, которые явно зависят от успеха первого этапа.

## Частые ошибки

- Думать, что `before_script` выполняется один раз на весь пайплайн — на самом деле он выполняется перед КАЖДЫМ job'ом заново (в своём чистом контейнере), поэтому установка зависимостей повторяется.
- Не заметить переопределение `before_script` внутри job'а `ui` — оно полностью заменяет верхнеуровневый `before_script` для этого job'а, а не дополняет его.
- Путать `stage:` (единственное число, к какому этапу относится job) и `stages:` (список всех этапов пайплайна).

## Мини-задания

1. **Разминка.** Открой `boilerplate/.gitlab-ci.yml`, найди значение `image:` и список `stages:`. Сколько этапов в пайплайне и в каком порядке они идут?
2. **Основное.** Открой пайплайн своего PR (или пример из `.gitlab-ci.yml`) и найди: какой job выполнится, если stage `test-fast` упадёт — выполнится ли `ui`, и почему.
3. **Ближе к практике.** Открой одновременно `boilerplate/.github/workflows/ci.yml` и `boilerplate/.gitlab-ci.yml` и найди в них (без подглядывания в таблицу соответствий из теории) четыре пары эквивалентных полей: где задаётся окружение выполнения, где — зависимость между job'ами, где — сохранение данных при падении, где — сохранение файлов после job'а.
4. **Со звёздочкой.** Представь, что в job'е `ui` убрали собственный `before_script`, но команду `playwright install --with-deps chromium` перенесли в `script` (после `pytest`). Сработает ли UI-тестирование в этом случае так же, как раньше? А если наоборот — оставить только общий верхнеуровневый `before_script` (без переопределения внутри `ui`) и просто запустить job — что пойдёт не так при попытке запустить браузерные тесты?
