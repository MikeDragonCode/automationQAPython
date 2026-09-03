#!/usr/bin/env python3
"""Собирает reader/index.html из course_book/*, jobsearch_track/* и корневых .md.
Ничего не меняет в исходных материалах курса — только читает."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURSE_BOOK = ROOT / "course_book"
JOBSEARCH = ROOT / "jobsearch_track"
TEMPLATE = Path(__file__).with_name("template.html")
OUTPUT = Path(__file__).with_name("index.html")

MODULES = [
    ("00_module0_python_base", "Модуль 0 · Python-база"),
    ("01_module1_pytest_env", "Модуль 1 · pytest как среда"),
    ("02_module2_git_teamwork", "Модуль 2 · Git и командная работа"),
    ("03_module3_api_testing", "Модуль 3 · API-тестирование"),
    ("04_module4_playwright_pom", "Модуль 4 · Playwright + POM"),
    ("05_module5_allure", "Модуль 5 · Allure и отчётность"),
    ("06_module6_ci", "Модуль 6 · CI на уровне пользователя"),
    ("07_module7_final_sprint", "Модуль 7 · Финальный спринт"),
]

NUM_RE = re.compile(r"^(\d+(?:\.\d+)?)\.?\s+(.*)$")

pages = []          # flat ordered list of page dicts
relpath_to_id = {}  # "course_book/05_.../03_....md" -> page id
_counter = 0


def next_id():
    global _counter
    _counter += 1
    return f"p{_counter}"


def parse_title(markdown_text: str):
    for line in markdown_text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            m = NUM_RE.match(heading)
            if m:
                return m.group(1), m.group(2).strip(" .")
            return None, heading
    return None, "Без названия"


HAS_PRACTICE_RE = re.compile(r"^#+\s*Мини-задание", re.MULTILINE)


def add_page(path: Path, section: str, subgroup: str | None, is_overview: bool = False, gateable: bool = True):
    text = path.read_text(encoding="utf-8")
    num, title = parse_title(text)
    pid = next_id()
    relpath = str(path.relative_to(ROOT))
    relpath_to_id[relpath] = pid

    page = {
        "id": pid,
        "section": section,
        "subgroup": subgroup,
        "isOverview": is_overview,
        "num": num,
        "title": title,
        "content": text,
        "hasPractice": gateable and bool(HAS_PRACTICE_RE.search(text)),
        "dir": str(path.parent.relative_to(ROOT)),
    }

    quiz_path = path.parent / (path.stem + ".quiz.json")
    if gateable and quiz_path.exists():
        try:
            data = json.loads(quiz_path.read_text(encoding="utf-8"))
            questions = data.get("questions")
            assert isinstance(questions, list) and 3 <= len(questions) <= 6
            for q in questions:
                assert isinstance(q.get("options"), list) and len(q["options"]) == 4
                assert isinstance(q.get("correct"), int) and 0 <= q["correct"] < 4
                assert q.get("question") and q.get("explain")
            page["quiz"] = questions
        except Exception as e:
            print(f"WARN: bad quiz json at {quiz_path.relative_to(ROOT)}: {e}")

    pages.append(page)


def week_label(dirname: str) -> str:
    m = re.match(r"week(\d+)", dirname)
    return f"Неделя {m.group(1)}" if m else dirname


# --- "О курсе" (справочные страницы, без гейта) ---
add_page(ROOT / "README.md", "О курсе", None, is_overview=True, gateable=False)
add_page(ROOT / "ROADMAP.md", "О курсе", None, gateable=False)
add_page(ROOT / "STYLE_GUIDE.md", "О курсе", None, gateable=False)
add_page(ROOT / "boilerplate" / "README.md", "О курсе", None, gateable=False)

# --- Модули 0-7 ---
for dirname, section_title in MODULES:
    module_dir = COURSE_BOOK / dirname
    entries = sorted(module_dir.iterdir(), key=lambda p: p.name)
    overview = module_dir / "00_overview.md"
    if overview.exists():
        add_page(overview, section_title, None, is_overview=True)
    for entry in entries:
        if entry.name == "00_overview.md":
            continue
        if entry.is_dir():
            label = week_label(entry.name)
            for f in sorted(entry.iterdir(), key=lambda p: p.name):
                if f.suffix == ".md":
                    add_page(f, section_title, label)
        elif entry.suffix == ".md":
            add_page(entry, section_title, None)

# --- Job-search track ---
js_readme = JOBSEARCH / "README.md"
if js_readme.exists():
    add_page(js_readme, "Job-search", None, is_overview=True)
for track_dir, label in [(JOBSEARCH / "ru", "RU"), (JOBSEARCH / "rs", "RS")]:
    if track_dir.exists():
        for f in sorted(track_dir.iterdir(), key=lambda p: p.name):
            if f.suffix == ".md":
                add_page(f, "Job-search", label)

print(f"Собрано страниц: {len(pages)}")

# --- Резолвим относительные .md-ссылки внутри контента в id страниц ---
LINK_RE = re.compile(r"\]\(<?([^()<>\s]+\.md)>?\)")
link_stats = {"resolved": 0, "unresolved": []}


def resolve_links(md_text: str, current_dir: str, source_relpath: str) -> str:
    def repl(m):
        target = m.group(1)
        try:
            resolved = str((ROOT / current_dir / target).resolve().relative_to(ROOT.resolve()))
        except ValueError:
            resolved = str(Path(current_dir) / target)
        resolved = resolved.replace("\\", "/")
        pid = relpath_to_id.get(resolved)
        if pid:
            link_stats["resolved"] += 1
            return f"](#{pid})"
        link_stats["unresolved"].append(f"{source_relpath} -> {target} (looked for {resolved})")
        return m.group(0)
    return LINK_RE.sub(repl, md_text)


for page in pages:
    src_relpath = None
    for rp, pid in relpath_to_id.items():
        if pid == page["id"]:
            src_relpath = rp
            break
    page["content"] = resolve_links(page["content"], page["dir"], src_relpath or "?")
    del page["dir"]

print(f"Внутренних .md-ссылок разрешено: {link_stats['resolved']}")
if link_stats["unresolved"]:
    print(f"НЕ разрешено ({len(link_stats['unresolved'])}):")
    for line in link_stats["unresolved"]:
        print("  -", line)

data_json = json.dumps(pages, ensure_ascii=False)
data_json = data_json.replace("</", "<\\/")  # защита от преждевременного закрытия <script>

template = TEMPLATE.read_text(encoding="utf-8")
if "__COURSE_DATA_JSON__" not in template:
    raise SystemExit("Placeholder __COURSE_DATA_JSON__ не найден в template.html")
output = template.replace("__COURSE_DATA_JSON__", data_json)
OUTPUT.write_text(output, encoding="utf-8")
print(f"Записано: {OUTPUT} ({OUTPUT.stat().st_size / 1024:.0f} KB)")
