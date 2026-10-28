#!/usr/bin/env python3
"""Конвертация отчёта из Markdown в DOCX через LibreOffice.

Промежуточный формат — HTML с оформлением под требования к учебным работам:
Times New Roman 14 пт, полуторный интервал, таблицы 11 пт с границами.

Запуск: python3 tools/md_to_docx.py [--src путь.md] [--out каталог]
"""
from __future__ import annotations
import argparse, html, pathlib, re, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

CSS = """
@page { size: A4; margin: 2cm 1.5cm 2cm 3cm; }
body { font-family: "Times New Roman"; font-size: 14pt; line-height: 1.5;
       text-align: justify; }
h1 { font-size: 18pt; font-weight: bold; text-align: center; margin: 24pt 0 12pt; }
h2 { font-size: 16pt; font-weight: bold; text-align: left; margin: 20pt 0 10pt;
     page-break-before: always; page-break-after: avoid; }
h2.first { page-break-before: auto; }
h3, h4 { page-break-after: avoid; }
table { page-break-inside: avoid; }
h3 { font-size: 14pt; font-weight: bold; text-align: left; margin: 16pt 0 8pt; }
h4 { font-size: 14pt; font-weight: bold; font-style: italic; margin: 12pt 0 6pt; }
p  { margin: 0 0 8pt; text-indent: 1.25cm; }
p.nb { text-indent: 0; }
p.cap { text-indent: 0; font-weight: bold; margin: 12pt 0 4pt; }
table { border-collapse: collapse; table-layout: fixed;
        margin: 4pt 0 12pt; font-size: 10pt; line-height: 1.15; }
th, td { border: 1px solid #000; padding: 2pt 4pt; text-align: left;
         vertical-align: top; word-wrap: break-word;
         overflow-wrap: break-word; hyphens: auto; }
td p, th p { text-indent: 0; text-align: left; margin: 0; }
th { font-weight: bold; background: #efefef; }
ul, ol { margin: 0 0 8pt 1.25cm; }
li { margin-bottom: 3pt; text-align: justify; }
code { font-family: "Courier New"; font-size: 11pt; }
blockquote { margin: 8pt 0 8pt 1.25cm; font-style: italic; }
hr { border: 0; border-top: 1px solid #999; margin: 14pt 0; }
p.tc { text-indent: 0; text-align: center; margin: 0 0 4pt; }
p.tc-top { text-indent: 0; text-align: center; margin: 0 0 2pt;
           text-transform: uppercase; font-size: 13pt; }
p.tc-title { text-indent: 0; text-align: center; font-size: 18pt;
             font-weight: bold; margin: 0 0 6pt; }
p.tc-sub { text-indent: 0; text-align: center; font-size: 15pt; margin: 0 0 6pt; }
p.tc-right { text-indent: 0; text-align: right; margin: 0 0 2pt; }
p.tc-gap { margin: 0; font-size: 14pt; line-height: 1.5; }
p.toc { text-indent: 0; margin: 0 0 3pt; text-align: left; font-size: 13pt; }
p.toc-2 { text-indent: 0; margin: 0 0 3pt 0.8cm; text-align: left; font-size: 13pt; }
p.fig { text-indent: 0; text-align: center; margin: 10pt 0 4pt; }
p.figcap { text-indent: 0; text-align: center; font-size: 12pt;
           margin: 0 0 14pt; page-break-before: avoid; }
"""


BASE_DIR = pathlib.Path(".")


def embed_img(src: str) -> str:
    """Встраивает картинку в разметку: LibreOffice иначе только ссылается на файл,
    и при пересылке DOCX изображения теряются."""
    import base64, mimetypes
    p = BASE_DIR / src
    if not p.exists():
        return src
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def inline(t: str) -> str:
    t = html.escape(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", t)   # ссылки — текстом
    return t


def convert(md: str) -> str:
    out: list[str] = []
    lines = md.splitlines()
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i]

        if not ln.strip():
            i += 1
            continue

        if ln.strip() == "<!--raw-->":          # блок HTML без обработки
            i += 1
            buf = []
            while i < n and lines[i].strip() != "<!--/raw-->":
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("\n".join(buf))
            continue

        if ln.strip() == "<!--TOC-->":          # место под оглавление
            i += 1
            continue

        if ln.strip() == "<!--pagebreak-->":
            out.append('<p style="page-break-after:always; margin:0; font-size:1pt">&nbsp;</p>')
            i += 1
            continue

        if ln.startswith("---") and set(ln.strip()) == {"-"}:
            out.append("<hr/>")
            i += 1
            continue

        mi = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"?(\d+)\"?)?\)\s*$", ln)
        if mi:
            cap, srcimg, w = mi.group(1), mi.group(2), mi.group(3)
            width = f"{int(w)/10:.1f}cm" if w else "15.8cm"
            out.append(f'<p class="fig"><img src="{embed_img(srcimg)}" '
                       f'style="width:{width}"/></p>')
            if cap:
                out.append(f'<p class="figcap">{inline(cap)}</p>')
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lvl = len(m.group(1))
            cls = ""
            if lvl == 2 and not any(x.startswith("<h2") for x in out):
                cls = ' class="first"'
            out.append(f"<h{lvl}{cls}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        # таблица
        if ln.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            # LibreOffice считает ширину колонок по содержимому и выносит
            # широкие таблицы за поле страницы, поэтому задаём доли явно
            ncol = len(head)
            avg = []
            for k in range(ncol):
                vals = [len(head[k])] + [len(r[k]) for r in rows if k < len(r)]
                avg.append(max(4, sum(vals) / len(vals)))
            lo, hi = 7.0, 42.0
            share = [v / sum(avg) * 100 for v in avg]
            share = [min(hi, max(lo, x)) for x in share]
            share = [x / sum(share) * 100 for x in share]
            # ширина в пикселях: HTML-фильтр LibreOffice не принимает проценты
            TOTAL = 605            # 16 см при 96 dpi
            px = [max(34, round(TOTAL * x / 100)) for x in share]
            px[-1] += TOTAL - sum(px)
            cols = "".join(f'<col width="{v}"/>' for v in px)
            t = [f'<table width="{TOTAL}"><colgroup>{cols}</colgroup><tr>']
            t += [f"<th>{inline(c)}</th>" for c in head] + ["</tr>"]
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</table>")
            out.append("".join(t))
            continue

        if ln.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].strip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>")
            continue

        if re.match(r"^\s*[*-]\s+", ln):
            items = []
            while i < n and re.match(r"^\s*[*-]\s+", lines[i]):
                items.append(inline(re.sub(r"^\s*[*-]\s+", "", lines[i])))
                i += 1
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>")
            continue

        if re.match(r"^\s*\d+\.\s+", ln):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(inline(re.sub(r"^\s*\d+\.\s+", "", lines[i])))
                i += 1
            out.append("<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>")
            continue

        # абзац
        buf = []
        while i < n and lines[i].strip() and not re.match(r"^(#{1,4}\s|!\[|<!--|\s*[|>*-]|\s*\d+\.\s)", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        if not buf:
            i += 1
            continue
        text = " ".join(buf)
        cls = ' class="cap"' if re.match(r"^\*\*Таблица \d+", text) else ""
        if not cls and len(text) < 90 and text.startswith("**") and text.endswith("**"):
            cls = ' class="nb"'
        out.append(f"<p{cls}>{inline(text)}</p>")

    return (f'<!doctype html><html lang="ru"><head><meta charset="utf-8"/>'
            f"<style>{CSS}</style></head><body>" + "\n".join(out) + "</body></html>")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "ОТЧЁТ" / "ЛабРабота5_ПЧМИ.md"))
    ap.add_argument("--out", default=str(ROOT / "ОТЧЁТ"))
    a = ap.parse_args()
    src, out = pathlib.Path(a.src), pathlib.Path(a.out)
    if not src.exists():
        sys.exit(f"нет файла {src}")

    globals()["BASE_DIR"] = src.parent
    tmp = out / (src.stem + ".html")
    tmp.write_text(convert(src.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"  промежуточный HTML: {tmp.name} ({tmp.stat().st_size // 1024} КБ)")

    # snap-версия LibreOffice не принимает профиль вне своего каталога,
    # поэтому используем профиль по умолчанию
    r = subprocess.run(
        ["libreoffice", "--headless", "--infilter=HTML (StarWriter)",
         "--convert-to", "docx:MS Word 2007 XML",
         "--outdir", str(out), str(tmp)],
        capture_output=True, text=True, timeout=300)
    docx = out / (src.stem + ".docx")
    if not docx.exists():
        print(r.stdout, r.stderr)
        sys.exit("конвертация не удалась")
    tmp.unlink()
    print(f"  готово: {docx.name} ({docx.stat().st_size // 1024} КБ)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
