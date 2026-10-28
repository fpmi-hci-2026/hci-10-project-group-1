#!/usr/bin/env python3
"""Обработка результатов исследования визуального языка (ЛР№5, задание 1, п. 11).

Читает выгрузку Google Forms и файл пар прилагательных, считает средние по каждой
паре для каждого варианта дизайна, строит диаграммы-профили с наложенным целевым
профилем и выбирает вариант по минимуму взвешенной суммы отклонений от цели.

Зависимостей нет — только стандартная библиотека, графики в SVG.

Запуск:
    python3 tools/gen_visual_report.py                      # research/raw.csv
    python3 tools/gen_visual_report.py --raw путь/к.csv      # другой файл
    python3 tools/gen_visual_report.py --out каталог         # другой каталог вывода
"""
from __future__ import annotations

import argparse
import csv
import math
import pathlib
import re
import statistics
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
ADJ = ROOT / "research" / "adjectives.csv"
ROTATIONS = {"ABC": "abc", "BCA": "bca", "CAB": "cab"}
PALETTE_NAMES = {"a": "Вариант A «Доверие»", "b": "Вариант B «Технологичный»",
                 "c": "Вариант C «Тёплый локальный»"}
CHART_COLORS = {"a": "#2B6CB0", "b": "#B7791F", "c": "#2F7A5A"}
CHART_MARKERS = {"a": "circle", "b": "square", "c": "triangle"}
TARGET_COLOR = "#6B7280"


# ──────────────────────────────── чтение данных ────────────────────────────────

def rel(path: pathlib.Path) -> str:
    """Путь относительно каталога работы, если он внутри него, иначе как есть."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def norm(s: str) -> str:
    """Нормализует строку для сопоставления: NFC, ё→е, схлопывание пробелов, lower."""
    s = unicodedata.normalize("NFC", s).replace("ё", "е").replace("Ё", "Е")
    return re.sub(r"\s+", " ", s).strip().lower()


def load_pairs() -> list[dict]:
    rows = list(csv.DictReader(ADJ.open(encoding="utf-8")))
    for r in rows:
        r["target"] = float(r["target"])
        r["weight"] = int(r["weight"])
    if len(rows) != 15:
        sys.exit(f"ОШИБКА: в adjectives.csv {len(rows)} пар, методичка требует 15")
    return rows


def find_scale_columns(header: list[str], pairs: list[dict]) -> dict[str, list[int]]:
    """Для каждой пары ищет все столбцы-шкалы по обоим полюсам в заголовке.

    Порядок появления = номер блока (Макет 1, 2, 3).
    """
    found: dict[str, list[int]] = {}
    problems = []
    for p in pairs:
        left, right = norm(p["right_pole_1"]), norm(p["left_pole_5"])  # «1» — правый полюс
        idx = [i for i, h in enumerate(header)
               if left in norm(h) and right in norm(h)]
        found[p["id"]] = idx
        if len(idx) != 3:
            problems.append(f"  {p['id']} «{p['right_pole_1']} — {p['left_pole_5']}»: "
                            f"найдено столбцов {len(idx)}, ожидается 3")
    if problems:
        sys.exit("ОШИБКА: не удалось сопоставить шкалы со столбцами выгрузки.\n"
                 + "\n".join(problems)
                 + "\n\nПроверьте, что заголовок каждого вопроса в Google Forms имеет вид\n"
                   "«Злой — Добрый» и совпадает во всех трёх блоках (см. research/questionnaire.md).")
    return found


def find_column(header: list[str], *keywords: str) -> int | None:
    for i, h in enumerate(header):
        if all(k in norm(h) for k in keywords):
            return i
    return None


def load_responses(raw: pathlib.Path, pairs: list[dict]) -> tuple[list[dict], dict]:
    with raw.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        sys.exit(f"ОШИБКА: в {raw.name} нет ответов")
    header, body = rows[0], [r for r in rows[1:] if any(c.strip() for c in r)]

    cols = find_scale_columns(header, pairs)
    i_rot = find_column(header, "ротаци")
    if i_rot is None:
        sys.exit("ОШИБКА: не найден столбец с кодом ротации. Добавьте в форму вопрос "
                 "«Код ротации (назовёт ведущий)» — см. research/questionnaire.md")
    i_age = find_column(header, "возраст")
    i_dev = find_column(header, "устройств")
    i_freq = find_column(header, "часто")
    i_pref = find_column(header, "выбрали")

    responses, skipped = [], []
    for n, row in enumerate(body, start=1):
        def cell(i): return row[i].strip() if i is not None and i < len(row) else ""
        code = cell(i_rot).upper().replace(" ", "")
        if code not in ROTATIONS:
            skipped.append(f"респондент {n}: код ротации «{cell(i_rot)}» не распознан "
                           f"(ожидается ABC, BCA или CAB)")
            continue
        order = ROTATIONS[code]            # order[k] = палитра в блоке k+1
        scores: dict[tuple[str, str], int] = {}
        bad = []
        for p in pairs:
            for block, col in enumerate(cols[p["id"]]):
                v = cell(col)
                if not v:
                    bad.append(f"{p['id']}/макет{block+1}")
                    continue
                try:
                    iv = int(float(v.replace(",", ".")))
                except ValueError:
                    bad.append(f"{p['id']}/макет{block+1}='{v}'")
                    continue
                if not 1 <= iv <= 5:
                    bad.append(f"{p['id']}/макет{block+1}={iv}")
                    continue
                scores[(order[block], p["id"])] = iv
        if bad:
            skipped.append(f"респондент {n} (код {code}): пропущено или неверно "
                           f"{len(bad)} оценок — {', '.join(bad[:5])}"
                           + (" …" if len(bad) > 5 else ""))
            if len(bad) > 15:
                continue
        pref_block = None
        m = re.search(r"[123]", cell(i_pref))
        if m:
            pref_block = order[int(m.group()) - 1]
        responses.append({
            "n": n, "code": code, "scores": scores, "pref": pref_block,
            "age": cell(i_age), "device": cell(i_dev), "freq": cell(i_freq),
        })

    meta = {"skipped": skipped, "total_rows": len(body),
            "has_pref": i_pref is not None,
            "has_demo": any(x is not None for x in (i_age, i_dev, i_freq))}
    if not responses:
        sys.exit("ОШИБКА: ни один ответ не удалось разобрать.\n" + "\n".join(skipped))
    return responses, meta


# ──────────────────────────────── расчёты ────────────────────────────────

def aggregate(responses: list[dict], pairs: list[dict]) -> dict:
    stats: dict[str, dict[str, dict]] = {}
    for pal in "abc":
        stats[pal] = {}
        for p in pairs:
            vals = [r["scores"][(pal, p["id"])] for r in responses
                    if (pal, p["id"]) in r["scores"]]
            if not vals:
                continue
            stats[pal][p["id"]] = {
                "n": len(vals),
                "mean": statistics.fmean(vals),
                "median": statistics.median(vals),
                "sd": statistics.stdev(vals) if len(vals) > 1 else 0.0,
                "sum": sum(vals),
            }
    for pal in "abc":
        dev = wdev = 0.0
        for p in pairs:
            st = stats[pal].get(p["id"])
            if not st:
                continue
            d = abs(st["mean"] - p["target"])
            dev += d
            wdev += d * p["weight"]
        stats[pal]["_total"] = {"dev": dev, "wdev": wdev}
    return stats


def pick_winner(stats: dict) -> tuple[str, list[tuple[str, float]]]:
    ranking = sorted(((pal, stats[pal]["_total"]["wdev"]) for pal in "abc"),
                     key=lambda t: t[1])
    return ranking[0][0], ranking


# ──────────────────────────────── диаграмма-профиль ────────────────────────────────

def marker(kind: str, x: float, y: float, color: str, r: float = 4.0) -> str:
    if kind == "circle":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}"/>'
    if kind == "square":
        return (f'<rect x="{x-r:.1f}" y="{y-r:.1f}" width="{2*r}" height="{2*r}" '
                f'fill="{color}"/>')
    return (f'<polygon points="{x:.1f},{y-r-0.5:.1f} {x+r+0.5:.1f},{y+r:.1f} '
            f'{x-r-0.5:.1f},{y+r:.1f}" fill="{color}"/>')


def profile_svg(pairs: list[dict], stats: dict, shown: tuple[str, ...]) -> str:
    row_h, top, bottom = 34, 72, 86
    left, right = 196, 150
    plot_w = 420
    height = top + row_h * len(pairs) + bottom
    width = left + plot_w + right

    def x_of(v: float) -> float:
        return left + (v - 1) / 4 * plot_w

    def y_of(i: int) -> float:
        return top + row_h * i + row_h / 2

    o: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Inter, Arial, sans-serif">',
        '<style>'
        '.bg{fill:#FFFFFF}.ax{stroke:#D9DDE3;stroke-width:1}.axm{stroke:#AEB4BD;stroke-width:1}'
        '.lbl{font-size:13px;fill:#2A2F38}.lblr{font-size:13px;fill:#6B7280}'
        '.tick{font-size:12px;fill:#6B7280}.ttl{font-size:16px;font-weight:700;fill:#1B2432}'
        '.lg{font-size:12.5px;fill:#2A2F38}.band{fill:#F6F7F9}'
        '@media (prefers-color-scheme: dark){'
        '.bg{fill:#151A21}.band{fill:#1C222B}.ax{stroke:#2E3744}.axm{stroke:#46525F}'
        '.lbl{fill:#E6EAF0}.lblr{fill:#99A2AE}.tick{fill:#99A2AE}.ttl{fill:#F2F5F9}.lg{fill:#E6EAF0}}'
        '</style>',
        f'<rect class="bg" width="{width}" height="{height}"/>',
        f'<text class="ttl" x="20" y="30">Диаграмма-профиль вариантов дизайна</text>',
        f'<text class="tick" x="20" y="50">Семантический дифференциал, шкала 1–5; '
        f'пунктир — целевой профиль</text>',
    ]
    for i in range(len(pairs)):
        if i % 2 == 0:
            o.append(f'<rect class="band" x="{left}" y="{top+row_h*i}" '
                     f'width="{plot_w}" height="{row_h}"/>')
    for v in range(1, 6):
        cls = "axm" if v == 3 else "ax"
        o.append(f'<line class="{cls}" x1="{x_of(v):.1f}" y1="{top}" '
                 f'x2="{x_of(v):.1f}" y2="{top+row_h*len(pairs)}"/>')
        o.append(f'<text class="tick" x="{x_of(v):.1f}" y="{top-8}" '
                 f'text-anchor="middle">{v}</text>')
    for i, p in enumerate(pairs):
        y = y_of(i)
        w = " ×2" if p["weight"] > 1 else ""
        o.append(f'<text class="lbl" x="{left-12}" y="{y+4:.1f}" text-anchor="end">'
                 f'{p["right_pole_1"]}{w}</text>')
        o.append(f'<text class="lblr" x="{left+plot_w+12}" y="{y+4:.1f}">'
                 f'{p["left_pole_5"]}</text>')
    # целевой профиль
    pts = " ".join(f"{x_of(p['target']):.1f},{y_of(i):.1f}" for i, p in enumerate(pairs))
    o.append(f'<polyline points="{pts}" fill="none" stroke="{TARGET_COLOR}" '
             f'stroke-width="2" stroke-dasharray="6 4"/>')
    for i, p in enumerate(pairs):
        o.append(f'<circle cx="{x_of(p["target"]):.1f}" cy="{y_of(i):.1f}" r="2.6" '
                 f'fill="{TARGET_COLOR}"/>')
    # профили вариантов
    for pal in shown:
        color = CHART_COLORS[pal]
        xs = [(i, stats[pal][p["id"]]["mean"]) for i, p in enumerate(pairs)
              if p["id"] in stats[pal]]
        pts = " ".join(f"{x_of(v):.1f},{y_of(i):.1f}" for i, v in xs)
        o.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.4"/>')
        for i, v in xs:
            o.append(marker(CHART_MARKERS[pal], x_of(v), y_of(i), color))
    # легенда
    ly = top + row_h * len(pairs) + 30
    lx = left
    for pal in shown:
        o.append(marker(CHART_MARKERS[pal], lx, ly - 4, CHART_COLORS[pal]))
        o.append(f'<line x1="{lx-14}" y1="{ly-4}" x2="{lx+14}" y2="{ly-4}" '
                 f'stroke="{CHART_COLORS[pal]}" stroke-width="2.4"/>')
        o.append(f'<text class="lg" x="{lx+22}" y="{ly}">{PALETTE_NAMES[pal]}</text>')
        ly += 22
    o.append(f'<line x1="{lx-14}" y1="{ly-4}" x2="{lx+14}" y2="{ly-4}" '
             f'stroke="{TARGET_COLOR}" stroke-width="2" stroke-dasharray="6 4"/>')
    o.append(f'<text class="lg" x="{lx+22}" y="{ly}">Целевой профиль (задан до теста)</text>')
    o.append("</svg>")
    return "\n".join(o)


# ──────────────────────────────── отчёт ────────────────────────────────

def write_results(out: pathlib.Path, pairs: list[dict], stats: dict, responses: list[dict],
                  meta: dict, winner: str, ranking: list[tuple[str, float]]) -> None:
    n = len(responses)
    L: list[str] = [
        "# Результаты исследования визуального языка",
        "",
        f"Сгенерировано `tools/gen_visual_report.py` из `research/raw.csv` "
        f"и `research/adjectives.csv`. Респондентов в обработке: **{n}**.",
        "",
        "Метод — семантический дифференциал: 15 пар прилагательных, шкала 1–5, "
        "где 5 соответствует левому полюсу пары. Целевой профиль задан **до** проведения "
        "теста на основании ЛР№1–ЛР№4 и при обработке не изменялся.",
        "",
    ]
    if meta["skipped"]:
        L += ["> **Исключено из обработки:**", ""]
        L += [f"> * {s}" for s in meta["skipped"]]
        L += [""]

    if meta["has_demo"]:
        L += ["## Состав выборки", "", "| Признак | Распределение |", "|---|---|"]
        for key, title in (("age", "Возраст"), ("freq", "Частота покупок онлайн"),
                           ("device", "Основное устройство")):
            vals = [r[key] for r in responses if r[key]]
            if not vals:
                continue
            dist = {v: vals.count(v) for v in dict.fromkeys(vals)}
            cells = ", ".join(f"{k} — {v}" for k, v in
                              sorted(dist.items(), key=lambda t: -t[1]))
            L += [f"| {title} | {cells} |"]
        L += [""]

    L += ["## Средние оценки по парам прилагательных", "",
          "| Пара (5 ← → 1) | Цель | Вес | A | B | C | Лучший |",
          "|---|---|---|---|---|---|---|"]
    for p in pairs:
        cells, best, bestd = [], None, 99.0
        for pal in "abc":
            st = stats[pal].get(p["id"])
            if not st:
                cells.append("—")
                continue
            d = abs(st["mean"] - p["target"])
            if d < bestd:
                bestd, best = d, pal
            cells.append(f"{st['mean']:.2f} ± {st['sd']:.2f}")
        L += [f"| {p['left_pole_5']} — {p['right_pole_1']} | {p['target']:.1f} | "
              f"{'×2' if p['weight']>1 else '—'} | {cells[0]} | {cells[1]} | {cells[2]} | "
              f"{best.upper() if best else '—'} |"]
    L += ["", "Формат ячейки — среднее ± стандартное отклонение. "
              "Столбец «Лучший» — вариант с минимальным отклонением от цели по этой паре.", ""]

    L += ["## Отклонение от целевого профиля", "",
          "| Вариант | Σ отклонений | Σ взвешенных | Место |", "|---|---|---|---|"]
    for place, (pal, wdev) in enumerate(ranking, start=1):
        L += [f"| {PALETTE_NAMES[pal]} | {stats[pal]['_total']['dev']:.2f} | "
              f"**{wdev:.2f}** | {place} |"]
    gap = ranking[1][1] - ranking[0][1]
    L += ["", f"Взвешенная сумма учитывает двойной вес пар «Честный — Лживый» и "
              f"«Надёжный — Ненадёжный»: они закрывают подтверждённые опросом барьеры "
              f"(60,9% и 39,1%).", ""]

    L += ["## Выбор варианта", "",
          f"**{PALETTE_NAMES[winner]}** — наименьшее взвешенное отклонение от целевого "
          f"профиля ({ranking[0][1]:.2f}), отрыв от второго места {gap:.2f}.", ""]
    if gap < 1.0:
        L += ["> ⚠️ Отрыв менее 1,0 — различие на границе значимости. В отчёте необходимо "
              "оговорить, что варианты по совокупности шкал близки, и опереться "
              "на расхождения по ключевым парам и на контрольный вопрос прямого выбора.", ""]

    L += ["### Где проигравшие варианты отклонились сильнее всего", ""]
    for pal, _ in ranking[1:]:
        worst = sorted((p for p in pairs if p["id"] in stats[pal]),
                       key=lambda p: -abs(stats[pal][p["id"]]["mean"] - p["target"]))[:3]
        items = "; ".join(
            f"«{p['left_pole_5']}» {stats[pal][p['id']]['mean']:.2f} против цели "
            f"{p['target']:.1f}" for p in worst)
        L += [f"* **{PALETTE_NAMES[pal]}**: {items}.", ""]

    if meta["has_pref"]:
        prefs = [r["pref"] for r in responses if r["pref"]]
        if prefs:
            dist = {pal: prefs.count(pal) for pal in "abc"}
            top = max(dist, key=lambda k: dist[k])
            L += ["## Контрольный вопрос: прямой выбор", "",
                  "| Вариант | Выбрали | Доля |", "|---|---|---|"]
            for pal in "abc":
                L += [f"| {PALETTE_NAMES[pal]} | {dist[pal]} | "
                      f"{dist[pal]/len(prefs)*100:.0f}% |"]
            agree = (top == winner)
            L += ["", f"Прямой выбор {'**совпадает**' if agree else '**не совпадает**'} "
                      f"с результатом по шкалам "
                      f"({PALETTE_NAMES[top]} против {PALETTE_NAMES[winner]}).", ""]
            if not agree:
                L += ["> Расхождение прямого выбора и профиля по шкалам — самостоятельный "
                      "вывод: шкалы измеряют соответствие целевым эмоциям, прямой выбор — "
                      "эстетическое предпочтение. Приоритет отдаётся профилю, поскольку "
                      "целевые значения выведены из данных опроса ЛР№1, а не из вкуса "
                      "респондента; расхождение фиксируется в отчёте.", ""]

    L += ["## Диаграммы", "",
          "* `charts/profile-all.svg` — профили всех трёх вариантов с целевым профилем",
          *[f"* `charts/profile-{pal}.svg` — {PALETTE_NAMES[pal]} отдельно"
            for pal in "abc"], ""]
    (out / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "research" / "raw.csv"))
    ap.add_argument("--out", default=str(ROOT / "research"))
    a = ap.parse_args()

    raw, out = pathlib.Path(a.raw), pathlib.Path(a.out)
    if not raw.exists():
        sys.exit(f"ОШИБКА: нет файла {raw}\n"
                 f"Положите выгрузку Google Forms в research/raw.csv "
                 f"(см. research/questionnaire.md).")
    (out / "charts").mkdir(parents=True, exist_ok=True)

    pairs = load_pairs()
    responses, meta = load_responses(raw, pairs)
    stats = aggregate(responses, pairs)
    winner, ranking = pick_winner(stats)

    (out / "charts" / "profile-all.svg").write_text(
        profile_svg(pairs, stats, ("a", "b", "c")), encoding="utf-8")
    for pal in "abc":
        (out / "charts" / f"profile-{pal}.svg").write_text(
            profile_svg(pairs, stats, (pal,)), encoding="utf-8")

    write_results(out, pairs, stats, responses, meta, winner, ranking)

    print(f"Респондентов обработано: {len(responses)} из {meta['total_rows']}")
    if meta["skipped"]:
        print(f"Исключено: {len(meta['skipped'])} — подробности в results.md")
    print("\nВзвешенное отклонение от целевого профиля:")
    for place, (pal, wdev) in enumerate(ranking, 1):
        print(f"  {place}. {PALETTE_NAMES[pal]:32} {wdev:6.2f}")
    print(f"\nПОБЕДИТЕЛЬ: {PALETTE_NAMES[winner]}")
    print(f"\nЗаписано: {rel(out/'results.md')}, "
          f"{rel(out/'charts')}/profile-*.svg (4 файла)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
