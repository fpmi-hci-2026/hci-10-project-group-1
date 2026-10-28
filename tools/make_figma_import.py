#!/usr/bin/env python3
"""Самодостаточные HTML-файлы для импорта в Figma плагином html.to.design.

Плагин принимает вставленный код, но внешние файлы (картинки, шрифты) подтянуть
не может. Скрипт встраивает их прямо в HTML как data-URI и уменьшает фотографии,
чтобы код помещался в поле вставки.

Запуск: python3 tools/make_figma_import.py
"""
from __future__ import annotations
import base64, io, pathlib, re
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
MOCK = ROOT / "mockups"
OUT = ROOT / "prototype" / "figma-import"
MAXW = 420          # ширины достаточно: в Figma фото всё равно масштабируется


def img_data_uri(path: pathlib.Path) -> str:
    im = Image.open(path).convert("RGB")
    if im.width > MAXW:
        im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=78, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def font_data_uri(path: pathlib.Path) -> str:
    return "data:font/woff2;base64," + base64.b64encode(path.read_bytes()).decode()


def inline(src: pathlib.Path, mode: str = "light") -> str:
    html = src.read_text(encoding="utf-8")

    # Шрифты не встраиваем: Inter и Manrope входят в стандартный набор Figma,
    # а base64-шрифты утраивают размер файла и мешают вставке кода в плагин.
    html = re.sub(r"@font-face\s*\{[^}]*\}", "", html)
    html = re.sub(r"/\*\s*[\w-]+\s*\*/", "", html)

    # картинки
    def i_sub(m):
        p = MOCK / m.group(1)
        return f'src="{img_data_uri(p)}"' if p.exists() else m.group(0)
    html = re.sub(r'src="(img/[^"]+)"', i_sub, html)

    # тема фиксируется в атрибуте: скрипты плагин не выполняет
    html = re.sub(r'data-mode="\w+"', f'data-mode="{mode}"', html)
    html = re.sub(r"<script>.*?</script>", "", html, flags=re.S)
    return html


JOBS = [
    ("1-каталог.html", "catalog.html", "light",
     "Каталог с фильтрами. Ширину задаёте в плагине: 1440, 1024, 768, 600, 414 или 360 — "
     "вёрстка сама перестроится под каждую"),
    ("2-главная.html", "mobile-home.html", "light",
     "Главная после авторизации. Ширину задаёте в плагине: 375, 393, 412, 744 или 834"),
    ("3-каталог-тёмная.html", "catalog.html", "dark",
     "Каталог в тёмной теме — для раздела руководства по стилям"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, src, mode, title in JOBS:
        html = inline(MOCK / src, mode)
        (OUT / name).write_text(html, encoding="utf-8")
        kb = (OUT / name).stat().st_size // 1024
        rows.append((name, title, kb))
        print(f"  {name:<24} {kb:>5} КБ   {title}")

    readme = ["# Импорт макетов в Figma кодом", "",
              "Файлы в этой папке самодостаточны: фотографии и шрифты встроены внутрь, "
              "внешних ссылок нет. Их можно вставить в плагин и получить настоящие "
              "слои Figma — рамки, текст, картинки, — а не картинку целиком.", "",
              "## Порядок", "",
              "1. В Figma: **Menu → Plugins → Browse plugins** → найти **html.to.design** → Run.",
              "2. В окне плагина выбрать вкладку **Code** (вставка кода), а не **URL**.",
              "3. Открыть нужный файл из таблицы ниже в текстовом редакторе, "
              "выделить всё (**Ctrl+A**), скопировать (**Ctrl+C**).",
              "4. Вставить в поле плагина, задать **Viewport width** — нужную ширину, "
              "нажать **Import**. Вёрстка отзывчивая, поэтому один и тот же файл "
              "при разной ширине даёт разную компоновку.",
              "5. Через 10–30 секунд на холсте появится фрейм со слоями.", "",
              "## Файлы", "",
              "| Файл | Что получится | Размер |",
              "|---|---|---|"]
    for name, title, kb in rows:
        readme.append(f"| `{name}` | {title} | {kb} КБ |")
    (OUT / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    print(f"\nГотово: {len(rows)} файлов + README.md → prototype/figma-import/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
