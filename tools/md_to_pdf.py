#!/usr/bin/env python3
"""Сборка отчёта в PDF с нумерацией страниц.

Markdown → HTML → ODT → правка колонтитула → PDF.
Промежуточный ODT нужен потому, что импорт HTML в LibreOffice не создаёт
колонтитулов, а номера страниц в учебном отчёте обязательны.

Запуск: python3 tools/md_to_pdf.py
"""
from __future__ import annotations
import argparse, pathlib, re, shutil, subprocess, sys, zipfile
from importlib.machinery import SourceFileLoader

ROOT = pathlib.Path(__file__).resolve().parent.parent
M = SourceFileLoader("m", str(ROOT / "tools" / "md_to_docx.py")).load_module()

FOOT_STYLE = ('<style:footer-style>'
              '<style:header-footer-properties svg:height="0.7cm" '
              'fo:margin-top="0.5cm" fo:min-height="0.7cm" '
              'style:dynamic-spacing="false"/>'
              '</style:footer-style>')
FOOTER = ('<style:footer><text:p text:style-name="MP_Footer">'
          '<text:page-number text:select-page="current">1</text:page-number>'
          '</text:p></style:footer>')
PSTYLE = ('<style:style style:name="MP_Footer" style:family="paragraph">'
          '<style:paragraph-properties fo:text-align="center" '
          'fo:margin-top="0cm" fo:margin-bottom="0cm"/>'
          '<style:text-properties style:font-name="Times New Roman" '
          'fo:font-size="12pt"/></style:style>')


def soffice(*args, cwd: pathlib.Path):
    subprocess.run(["libreoffice", "--headless", *args], capture_output=True,
                   timeout=300, cwd=str(cwd))


def add_page_numbers(odt: pathlib.Path, out: pathlib.Path) -> bool:
    zin = zipfile.ZipFile(odt)
    st = zin.read("styles.xml").decode("utf-8")
    content = zin.read("content.xml").decode("utf-8")

    used = set(re.findall(r'style:master-page-name="([^"]+)"', content + st)) or {"Standard"}
    changed = False

    for mp in used:
        m = re.search(rf'<style:master-page style:name="{re.escape(mp)}"'
                      rf'[^>]*style:page-layout-name="([^"]+)"[^>]*?(/?)>', st)
        if not m:
            continue
        layout, selfclose = m.group(1), m.group(2)

        # 1. включить колонтитул в макете страницы
        blk = re.search(rf'<style:page-layout style:name="{re.escape(layout)}">.*?'
                        rf'</style:page-layout>', st, re.S)
        if blk:
            b = blk.group(0)
            nb = (re.sub(r'<style:footer-style>.*?</style:footer-style>', FOOT_STYLE, b, flags=re.S)
                  if "<style:footer-style>" in b
                  else b.replace("</style:page-layout>", FOOT_STYLE + "</style:page-layout>"))
            st = st.replace(b, nb)

        # 2. вставить колонтитул ВНУТРЬ master-page; тег бывает самозакрывающимся
        if selfclose:
            st = st.replace(m.group(0), m.group(0)[:-2] + ">" + FOOTER + "</style:master-page>")
        else:
            st = st.replace(m.group(0), m.group(0) + FOOTER)
        changed = True

    if not changed:
        return False
    st = st.replace("</office:styles>", PSTYLE + "</office:styles>")

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zin.infolist():
            zo.writestr(it, st.encode("utf-8") if it.filename == "styles.xml"
                        else zin.read(it.filename))
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "ОТЧЁТ" / "ЛабРабота5_ПЧМИ.md"))
    a = ap.parse_args()
    src = pathlib.Path(a.src).resolve()
    work = src.parent

    M.BASE_DIR = src.parent
    html = work / "_build.html"
    html.write_text(M.convert(src.read_text(encoding="utf-8")), encoding="utf-8")
    soffice("--infilter=HTML (StarWriter)", "--convert-to", "odt:writer8",
            "--outdir", str(work), str(html), cwd=work)

    odt = work / "_build.odt"
    if not odt.exists():
        sys.exit("не удалось получить ODT")

    numbered = work / "_numbered.odt"
    if not add_page_numbers(odt, numbered):
        sys.exit("не удалось вставить нумерацию")

    soffice("--convert-to", "pdf", "--outdir", str(work), str(numbered), cwd=work)
    pdf = work / "_numbered.pdf"
    if not pdf.exists():
        sys.exit("не удалось получить PDF")

    final = work / (src.stem + ".pdf")
    shutil.move(str(pdf), str(final))
    for f in (html, odt, numbered):
        f.unlink(missing_ok=True)
    print(f"  готово: {final.name} ({final.stat().st_size // 1024} КБ)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
