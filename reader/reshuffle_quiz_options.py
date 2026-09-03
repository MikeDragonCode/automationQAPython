#!/usr/bin/env python3
"""Одноразовый скрипт: перемешивает варианты ответов в каждом вопросе так,
чтобы позиция правильного ответа была равномерно распределена по всем 4
слотам (round-robin по всем вопросам курса), а не сосредоточена в одном
месте. Порядок неверных вариантов внутри вопроса тоже рандомизируется.
Текст question/options/explain не меняется — меняется только порядок
элементов в options и, соответственно, индекс correct."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
random.seed(20260903)

files = sorted(ROOT.glob("course_book/**/*.quiz.json"))

# собираем все вопросы по порядку файлов, чтобы назначить целевые позиции round-robin
all_refs = []  # (file_path, data, question_index)
file_data = {}
for f in files:
    data = json.loads(f.read_text(encoding="utf-8"))
    file_data[f] = data
    for qi in range(len(data["questions"])):
        all_refs.append((f, qi))

target_positions = [i % 4 for i in range(len(all_refs))]
random.shuffle(target_positions)  # чтобы порядок целевых позиций не был предсказуемым 0,1,2,3,0,1,2,3...

before_counts = [0, 0, 0, 0]
after_counts = [0, 0, 0, 0]

for (f, qi), target in zip(all_refs, target_positions):
    q = file_data[f]["questions"][qi]
    before_counts[q["correct"]] += 1

    correct_text = q["options"][q["correct"]]
    distractors = [opt for i, opt in enumerate(q["options"]) if i != q["correct"]]
    random.shuffle(distractors)

    new_options = distractors[:]
    new_options.insert(target, correct_text)

    q["options"] = new_options
    q["correct"] = target
    after_counts[target] += 1

for f, data in file_data.items():
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

total = len(all_refs)
print(f"Обработано вопросов: {total}")
print("До:  ", [f"{c} ({c/total*100:.1f}%)" for c in before_counts])
print("После:", [f"{c} ({c/total*100:.1f}%)" for c in after_counts])
