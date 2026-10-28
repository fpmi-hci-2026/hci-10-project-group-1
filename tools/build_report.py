#!/usr/bin/env python3
"""Полная сборка отчёта: Markdown → PDF и DOCX.

PDF верстается WeasyPrint (постраничный CSS: поля, колонтитулы, нумерация,
повтор шапки таблиц, переносы), DOCX собирается напрямую через python-docx.
LibreOffice не используется — его импорт HTML давал негодную типографику.

Запуск: .venv/bin/python tools/build_report.py
"""
import pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "bin" / "python"


def run(script: str) -> None:
    exe = str(PY) if PY.exists() and script != "gen_report.py" else sys.executable
    r = subprocess.run([exe, str(ROOT / "tools" / script)],
                       capture_output=True, text=True, timeout=900)
    if r.returncode:
        sys.exit(f"{script}:\n{r.stdout}\n{r.stderr}")
    print(r.stdout.rstrip())


for s in ("gen_report.py", "render_pdf.py", "render_docx.py"):
    print(f"— {s}")
    run(s)
