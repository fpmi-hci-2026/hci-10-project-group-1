#!/usr/bin/env python3
"""Полная сборка отчёта: Markdown → оглавление с номерами страниц → PDF и DOCX.

Номера страниц заранее неизвестны, поэтому отчёт собирается итеративно:
по готовому PDF определяется, на какой странице начинается каждый раздел,
номера подставляются в оглавление, документ пересобирается. Повторяется,
пока номера не перестанут меняться (обычно два-три прохода).

Запуск: python3 tools/build_report.py
"""
from __future__ import annotations
import pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MD = ROOT / "ОТЧЁТ" / "ЛабРабота5_ПЧМИ.md"
PDF = ROOT / "ОТЧЁТ" / "ЛабРабота5_ПЧМИ.pdf"
MAX_PASSES = 4


def run(script: str, *args) -> None:
    r = subprocess.run([sys.executable, str(ROOT / "tools" / script), *args],
                       capture_output=True, text=True, timeout=600)
    if r.returncode:
        sys.exit(f"{script}: {r.stdout}\n{r.stderr}")


def headings(md: str) -> list[tuple[int, str]]:
    """Разделы верхнего и второго уровня для оглавления."""
    out = []
    for ln in md.splitlines():
        m = re.match(r"^(#{2,3})\s+(.*)$", ln)
        if m:
            out.append((len(m.group(1)), m.group(2).strip()))
    return out


def page_of(hs: list[tuple[int, str]]) -> dict[str, int]:
    """Находит номер страницы начала каждого раздела по тексту PDF."""
    n = int(re.search(r"Pages:\s+(\d+)",
            subprocess.run(["pdfinfo", str(PDF)], capture_output=True,
                           text=True).stdout).group(1))
    pages = []
    for p in range(1, n + 1):
        t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), str(PDF), "-"],
                           capture_output=True, text=True).stdout
        # строки оглавления содержат отточие и тоже совпали бы с заголовками
        t = "\n".join(l for l in t.splitlines() if not re.search(r"\.{4,}", l))
        pages.append(re.sub(r"\s+", " ", t))
    res, start = {}, 0
    for _, title in hs:
        probe = re.sub(r"\s+", " ", title)[:40]
        for p in range(start, n):
            if probe in pages[p]:
                res[title] = p + 1
                start = p          # разделы идут по порядку
                break
    return res


def toc_block(hs: list[tuple[int, str]], pages: dict[str, int]) -> str:
    out = ["<!--raw-->"]
    for lvl, title in hs:
        pg = pages.get(title)
        if pg is None:
            continue
        cls = "toc" if lvl == 2 else "toc-2"
        dots = "." * max(3, 66 - len(title) - (4 if lvl == 3 else 0))
        out.append(f'<p class="{cls}">{title} {dots} {pg}</p>')
    out.append("<!--/raw-->")
    return "\n".join(out)


def main() -> int:
    run("gen_report.py")
    md0 = MD.read_text(encoding="utf-8")
    hs = headings(md0)
    print(f"  разделов в оглавлении: {len(hs)}")

    prev: dict[str, int] = {}
    for p in range(1, MAX_PASSES + 1):
        run("md_to_pdf.py")
        pages = page_of(hs)
        print(f"  проход {p}: страниц {max(pages.values(), default=0)}, "
              f"найдено разделов {len(pages)}"
              + ("" if pages != prev else " — номера совпали"))
        if pages == prev:
            break
        prev = pages
        md = MD.read_text(encoding="utf-8")
        md = re.sub(r"<!--TOC-->(?:\n<!--raw-->.*?<!--/raw-->)?",
                    "<!--TOC-->\n" + toc_block(hs, pages), md, count=1, flags=re.S)
        MD.write_text(md, encoding="utf-8")

    run("md_to_pdf.py")
    run("md_to_docx.py")
    size = PDF.stat().st_size // 1024
    npg = re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(PDF)],
                    capture_output=True, text=True).stdout).group(1)
    print(f"\n  ЛабРабота5_ПЧМИ.pdf  — {npg} страниц, {size} КБ")
    docx = ROOT / "ОТЧЁТ" / "ЛабРабота5_ПЧМИ.docx"
    print(f"  ЛабРабота5_ПЧМИ.docx — {docx.stat().st_size // 1024} КБ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
