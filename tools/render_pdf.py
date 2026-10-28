#!/usr/bin/env python3
"""Вёрстка отчёта в PDF средствами WeasyPrint.

LibreOffice импортирует HTML как веб-страницу и даёт плохую типографику:
таблицы выходят за поле, иллюстрации не выравниваются, переносов нет.
WeasyPrint — движок постраничной вёрстки CSS: поля, колонтитулы, нумерация,
повтор шапки таблицы при переносе, висячие строки — всё описывается правилами.

Оглавление собирается за два прохода: первый рендер даёт номера страниц
разделов через дерево закладок документа, они подставляются, рендер повторяется.

Запуск: python3 tools/render_pdf.py   (из виртуального окружения .venv)
"""
from __future__ import annotations
import html as H
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MD = ROOT / "ОТЧЁТ" / "ЛабРабота5_ПЧМИ.md"
PDF = ROOT / "ОТЧЁТ" / "ЛабРабота5_ПЧМИ.pdf"

CSS = """
@page {
  size: A4;
  margin: 20mm 15mm 20mm 30mm;
  @bottom-center { content: counter(page); font-family: "Liberation Serif";
                   font-size: 11pt; color: #000; }
}
@page :first { @bottom-center { content: none; } }

html { font-family: "Liberation Serif", "Times New Roman", serif; font-size: 14pt; }
body { margin: 0; line-height: 1.5; text-align: justify;
       hyphens: auto; -weasy-hyphens: auto; orphans: 2; widows: 2; }

h1, h2, h3, h4 { font-weight: bold; text-align: left; page-break-after: avoid;
                 break-after: avoid; hyphens: none; }
h2 { font-size: 16pt; margin: 0 0 12pt; page-break-before: always; break-before: page; }
h2.nobreak { page-break-before: auto; break-before: auto; }
h3 { font-size: 14pt; margin: 16pt 0 8pt; }
h4 { font-size: 14pt; font-style: italic; margin: 12pt 0 6pt; }

p { margin: 0 0 6pt; text-indent: 12.5mm; }
p.nb, blockquote p { text-indent: 0; }

/* таблицы */
table { width: 100%; border-collapse: collapse; margin: 4pt 0 12pt;
        font-size: 10.5pt; line-height: 1.25; page-break-inside: auto; }
thead { display: table-header-group; }
tr { page-break-inside: avoid; break-inside: avoid; }
th, td { border: 0.5pt solid #000; padding: 2.5pt 4pt; text-align: left;
         vertical-align: top; hyphens: auto; }
th { font-weight: bold; background: #ececec; }
p.cap { text-indent: 0; font-weight: bold; margin: 12pt 0 3pt;
        page-break-after: avoid; break-after: avoid; }

/* иллюстрации */
figure { margin: 10pt 0 14pt; text-align: center; page-break-inside: avoid;
         break-inside: avoid; }
figure img { max-width: 100%; max-height: 190mm; }
figcaption { font-size: 12pt; text-indent: 0; text-align: center;
             margin-top: 5pt; line-height: 1.3; }

ul, ol { margin: 0 0 8pt 12.5mm; padding-left: 5mm; }
li { margin-bottom: 3pt; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 10.5pt; }
blockquote { margin: 8pt 0 8pt 12.5mm; padding-left: 4mm;
             border-left: 2pt solid #bbb; font-style: italic; }
hr { border: 0; border-top: 0.5pt solid #999; margin: 12pt 0; }

/* титульный лист */
.title-page { page-break-after: always; break-after: page; text-align: center;
              hyphens: none; }
.title-page p { text-indent: 0; margin: 0 0 3pt; }
.tp-org { text-transform: uppercase; font-size: 13pt; }
.tp-h { font-size: 19pt; font-weight: bold; margin: 8pt 0; }
.tp-sub { font-size: 14pt; }
.tp-right { text-align: right; }
.sp-l { height: 30mm; } .sp-m { height: 18mm; } .sp-s { height: 9mm; }

/* содержание */
.toc-h { font-size: 16pt; font-weight: bold; text-align: center;
         margin: 0 0 14pt; hyphens: none; }
.toc-item { text-indent: 0; margin: 0 0 4pt; text-align: left; hyphens: none;
            font-size: 13pt; display: flex; }
.toc-item.l2 { padding-left: 8mm; font-size: 12.5pt; }
.toc-item .t { white-space: nowrap; overflow: hidden; }
.toc-item .d { flex: 1; border-bottom: 1pt dotted #666; margin: 0 3pt 3pt; }
.toc-item .p { white-space: nowrap; }
.toc-page { page-break-after: always; break-after: page; }
"""


def inline(t: str) -> str:
    t = H.escape(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", t)
    return t


def md_to_html(md: str) -> str:
    out: list[str] = []
    lines = md.splitlines()
    i, n = 0, len(lines)
    seen_h2 = False
    while i < n:
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue

        if ln.strip() == "<!--raw-->":
            i += 1
            buf = []
            while i < n and lines[i].strip() != "<!--/raw-->":
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("\n".join(buf))
            continue
        if ln.strip() in ("<!--TOC-->", "<!--pagebreak-->"):
            if ln.strip() == "<!--pagebreak-->":
                out.append('<div style="break-after:page"></div>')
            i += 1
            continue

        if ln.startswith("---") and set(ln.strip()) == {"-"}:
            out.append("<hr/>")
            i += 1
            continue

        mi = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$", ln)
        if mi:
            cap = inline(mi.group(1))
            out.append(f'<figure><img src="{mi.group(2)}"/>'
                       + (f"<figcaption>{cap}</figcaption>" if cap else "") + "</figure>")
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lvl, txt = len(m.group(1)), m.group(2)
            cls = ""
            if lvl == 2 and not seen_h2:
                cls, seen_h2 = ' class="nobreak"', True
            out.append(f"<h{lvl}{cls}>{inline(txt)}</h{lvl}>")
            i += 1
            continue

        if ln.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = ["<table><thead><tr>"] + [f"<th>{inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue

        if ln.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].strip())
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(buf))}</p></blockquote>")
            continue

        for pat, tag in ((r"^\s*[*-]\s+", "ul"), (r"^\s*\d+\.\s+", "ol")):
            if re.match(pat, ln):
                items = []
                while i < n and re.match(pat, lines[i]):
                    items.append(inline(re.sub(pat, "", lines[i])))
                    i += 1
                out.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>")
                break
        else:
            buf = []
            while i < n and lines[i].strip() and not re.match(
                    r"^(#{1,4}\s|!\[|<!--|\s*[|>*-]|\s*\d+\.\s)", lines[i]):
                buf.append(lines[i].strip())
                i += 1
            if not buf:
                i += 1
                continue
            text = " ".join(buf)
            cls = ' class="nb"' if re.match(r"^\*\*Таблица \d+", text) else ""
            if cls:
                cls = ' class="cap"'
            out.append(f"<p{cls}>{inline(text)}</p>")
    return "\n".join(out)


def document(md: str, toc_html: str):
    from weasyprint import HTML, CSS as WCSS
    body = md_to_html(md).replace("<!--TOCSLOT-->", toc_html)
    doc = (f'<!doctype html><html lang="ru"><head><meta charset="utf-8"/>'
           f"<title>Отчёт ЛР№5</title></head><body>{body}</body></html>")
    return HTML(string=doc, base_url=str(MD.parent)).render(
        stylesheets=[WCSS(string=CSS)])


def toc_from(rendered, headings) -> str:
    """Собирает содержание по дереву закладок готового документа."""
    flat = []

    def walk(items):
        for label, (page, _x, _y), children, *_ in items:
            flat.append((label.strip(), page + 1))
            walk(children)
    walk(rendered.make_bookmark_tree())
    pages = {}
    for label, pg in flat:
        pages.setdefault(label, pg)

    out = ['<p class="toc-h">Содержание</p>']
    for lvl, title in headings:
        pg = pages.get(title)
        if pg is None:
            continue
        cls = "toc-item" + (" l2" if lvl == 3 else "")
        out.append(f'<p class="{cls}"><span class="t">{H.escape(title)}</span>'
                   f'<span class="d"></span><span class="p">{pg}</span></p>')
    return f'<div class="toc-page">{"".join(out)}</div>'


def main() -> int:
    md = MD.read_text(encoding="utf-8")
    md = re.sub(r"<!--TOC-->(?:\n<!--raw-->.*?<!--/raw-->)?",
                "<!--raw-->\n<!--TOCSLOT-->\n<!--/raw-->", md, count=1, flags=re.S)
    headings = [(len(m.group(1)), m.group(2).strip())
                for m in re.finditer(r"^(#{2,3})\s+(.*)$", md, re.M)]

    first = document(md, "")
    toc = toc_from(first, headings)
    final = document(md, toc)
    final.write_pdf(str(PDF))
    print(f"  разделов в содержании: {toc.count('toc-item')}")
    print(f"  готово: {PDF.name} — {len(final.pages)} страниц, "
          f"{PDF.stat().st_size // 1024} КБ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
