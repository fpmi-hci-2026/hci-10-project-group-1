#!/usr/bin/env python3
"""Скачивает Inter и Manrope в mockups/fonts/, чтобы макеты не зависели от интернета.

Во время теста с респондентами макеты должны выглядеть одинаково независимо от сети:
если шрифт не загрузится, браузер подставит системный и дизайн изменится.

Запуск: python3 tools/fetch_fonts.py
"""
import pathlib, re, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "mockups" / "fonts"
URL = ("https://fonts.googleapis.com/css2?"
       "family=Inter:wght@400;600;700&family=Manrope:wght@800&display=swap")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/131.0.0.0 Safari/537.36")
# оставляем только нужные подмножества: латиница и кириллица
KEEP = ("latin", "latin-ext", "cyrillic", "cyrillic-ext")


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main() -> int:
    FONTS.mkdir(parents=True, exist_ok=True)
    css = get(URL).decode("utf-8")
    blocks = re.findall(r"(/\*\s*([\w-]+)\s*\*/\s*)?(@font-face\s*\{.*?\})", css, re.S)
    out, saved, skipped = [], 0, 0
    for _, subset, block in blocks:
        if subset and subset not in KEEP:
            skipped += 1
            continue
        m = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        if not m:
            skipped += 1
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        wt = re.search(r"font-weight:\s*(\d+)", block).group(1)
        name = f"{fam.lower()}-{wt}-{subset or 'all'}.woff2"
        path = FONTS / name
        if not path.exists():
            path.write_bytes(get(m.group(1)))
        saved += 1
        out.append(f"/* {subset} */\n" + block.replace(m.group(1), f"fonts/{name}"))
    (FONTS / "fonts.css").write_text("\n".join(out) + "\n", encoding="utf-8")
    total = sum(p.stat().st_size for p in FONTS.glob("*.woff2"))
    print(f"скачано начертаний-подмножеств: {saved} (пропущено {skipped})")
    print(f"файлов woff2: {len(list(FONTS.glob('*.woff2')))}, всего {total/1024:.0f} КБ")
    print(f"описание: {(FONTS/'fonts.css').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
