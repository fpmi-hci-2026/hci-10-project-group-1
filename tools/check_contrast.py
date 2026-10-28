#!/usr/bin/env python3
"""Проверка контраста токенов по WCAG 2.1 (ЛР№5, задание 1 и 3).

Читает design/tokens.json и для каждой палитры в светлой и тёмной теме
считает коэффициент контраста обязательных пар. Печатает таблицу и
завершается с кодом 1, если хотя бы одна обязательная пара не проходит.

Уровни: AA обычный текст — 4.5:1, AA крупный текст (>=18.66px bold или >=24px)
и графические элементы — 3:1, AAA — 7:1.
Запуск: python3 tools/check_contrast.py [--md]
"""
import json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENS = ROOT / "design" / "tokens.json"

AA, AA_LARGE, AAA = 4.5, 3.0, 7.0

# (токен переднего плана, токен фона, что это, порог, обязательна ли)
# required=False — пара проверяется справочно и не влияет на итог: WCAG 1.4.11
# не предъявляет требований к чисто декоративным заливкам, под которыми текст
# имеет собственный проверяемый контраст (пара on-accent-soft / accent-soft).
PAIRS = [
    ("text",            "bg",           "основной текст на фоне страницы",      AA, True),
    ("text",            "surface",      "основной текст на карточке",           AA, True),
    ("text-muted",      "surface",      "второстепенный текст на карточке",     AA, True),
    ("text-muted",      "bg",           "второстепенный текст на фоне",         AA, True),
    ("on-brand",        "brand",        "текст в шапке и глобальной навигации", AA, True),
    ("on-accent",       "accent",       "текст на кнопке ключевого действия",   AA, True),
    ("on-accent",       "accent-hover", "текст на кнопке в состоянии hover",    AA, True),
    ("on-accent-soft",  "accent-soft",  "текст на акцентной плашке",            AA, True),
    ("on-success",      "success",      "текст на кнопке/плашке успеха",        AA, True),
    ("on-warning",      "warning",      "текст на плашке предупреждения",       AA, True),
    ("on-error",        "error",        "текст на плашке ошибки",               AA, True),
    ("on-info",         "info",         "текст на информационной плашке",       AA, True),
    ("success",         "success-soft", "бейдж «Опубликовано»",                 AA, True),
    ("warning",         "warning-soft", "бейдж «Не хватает атрибутов»",         AA, True),
    ("error",           "error-soft",   "бейдж «Заблокировано»",                AA, True),
    ("info",            "info-soft",    "бейдж «На модерации»",                 AA, True),
    ("text-muted",      "surface-alt",  "бейдж «Черновик»",                     AA, True),
    ("border-strong",   "surface",      "граница поля ввода",                   AA_LARGE, True),
    ("focus",           "surface",      "кольцо фокуса на карточке",            AA_LARGE, True),
    ("focus",           "bg",           "кольцо фокуса на фоне",                AA_LARGE, True),
    ("decor",           "surface",      "декоративная заливка (справочно)",     AA_LARGE, False),
]


def srgb_to_lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * srgb_to_lin(r) + 0.7152 * srgb_to_lin(g) + 0.0722 * srgb_to_lin(b)


def ratio(fg: str, bg: str) -> float:
    l1, l2 = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def check(tokens: dict) -> tuple[list, int]:
    rows, failures = [], 0
    for pid, pal in tokens["palettes"].items():
        for mode in ("light", "dark"):
            vals = pal[mode]
            for fg, bg, what, need, required in PAIRS:
                r = ratio(vals[fg], vals[bg])
                ok = r >= need
                if not ok and required:
                    failures += 1
                rows.append({
                    "palette": pid, "name": pal["name"], "mode": mode,
                    "fg": fg, "bg": bg, "fg_hex": vals[fg], "bg_hex": vals[bg],
                    "what": what, "ratio": round(r, 2), "need": need,
                    "ok": ok, "aaa": r >= AAA, "required": required,
                })
    return rows, failures


def main() -> int:
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    rows, failures = check(tokens)

    if "--md" in sys.argv:
        out = ["# Отчёт о проверке контраста\n",
               "Сгенерирован `tools/check_contrast.py` из `design/tokens.json` по WCAG 2.1.",
               "Порог AA — 4,5:1 для текста и 3:1 для графических элементов и границ.\n"]
        for pid in tokens["palettes"]:
            out.append(f"\n## {tokens['palettes'][pid]['name']}\n")
            for mode, title in (("light", "Светлая тема"), ("dark", "Тёмная тема")):
                out.append(f"\n### {title}\n")
                out.append("| Пара токенов | Что это | Цвета | Контраст | Порог | Итог |")
                out.append("|---|---|---|---|---|---|")
                for r in rows:
                    if r["palette"] == pid and r["mode"] == mode:
                        if r["aaa"]:
                            mark = "AAA"
                        elif r["ok"]:
                            mark = "AA"
                        elif not r["required"]:
                            mark = "справочно"
                        else:
                            mark = "**не проходит**"
                        out.append(f"| `{r['fg']}` / `{r['bg']}` | {r['what']} | "
                                   f"{r['fg_hex']} / {r['bg_hex']} | {r['ratio']:.2f}:1 | "
                                   f"{r['need']}:1 | {mark} |")
        total = len(rows)
        req = sum(1 for r in rows if r["required"])
        out.append(f"\n---\n\n**Итого:** {total} пар проверено, из них обязательных {req}. "
                   f"Не проходит обязательных: {failures}. "
                   f"Соответствие AAA: {sum(1 for r in rows if r['aaa'])}.")
        (ROOT / "design" / "contrast-report.md").write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"design/contrast-report.md записан: {total} пар, не проходит {failures}")
    else:
        w = max(len(f"{r['fg']}/{r['bg']}") for r in rows)
        cur = None
        for r in rows:
            key = (r["palette"], r["mode"])
            if key != cur:
                cur = key
                print(f"\n=== {r['name']} — {'светлая' if r['mode']=='light' else 'тёмная'} тема")
            if r["aaa"]:
                flag = "AAA "
            elif r["ok"]:
                flag = "AA  "
            elif not r["required"]:
                flag = "спрв"
            else:
                flag = "ПРОВАЛ"
            print(f"  {flag} {r['ratio']:5.2f}:1  (нужно {r['need']}) "
                  f"{r['fg']+'/'+r['bg']:<{w}}  {r['what']}")
        print(f"\nВсего пар: {len(rows)} | не проходит: {failures} | AAA: {sum(1 for r in rows if r['aaa'])}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
