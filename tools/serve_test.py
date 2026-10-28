#!/usr/bin/env python3
"""Сервер теста визуального языка: показывает макеты, собирает ответы в raw.csv.

Заменяет связку Google Forms + Apps Script. Респондент открывает одну ссылку,
проходит тест и ответ сразу попадает в research/raw.csv в том формате, который
читает tools/gen_visual_report.py — сопоставлять столбцы вручную не нужно.

Код ротации назначается автоматически по счётчику уже пройденных анкет,
поэтому ни ведущий, ни ввод кода респондентом не требуются.

Запуск:  python3 tools/serve_test.py            (порт 8765)
         python3 tools/serve_test.py --port 9000
Открыть: http://127.0.0.1:8765/
Прогресс: http://127.0.0.1:8765/status
"""
from __future__ import annotations

import argparse, csv, html, json, pathlib, sys, threading, datetime, urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = pathlib.Path(__file__).resolve().parent.parent
MOCKUPS = ROOT / "mockups"
RAW = ROOT / "research" / "raw.csv"
PAIRS = list(csv.DictReader((ROOT / "research" / "adjectives.csv").open(encoding="utf-8")))
LOCK = threading.Lock()

ROT = {"ABC": "abc", "BCA": "bca", "CAB": "cab"}
# распределение по методике: 4 / 3 / 3 на десять человек
CYCLE = ["ABC", "BCA", "CAB", "ABC", "BCA", "CAB", "ABC", "BCA", "CAB", "ABC"]

DEMO = [
    ("age", "Ваш возраст", ["18–24", "25–34", "35–44", "45–55", "старше 55"]),
    ("sex", "Пол", ["женский", "мужской", "не хочу указывать"]),
    ("freq", "Как часто покупаете одежду или обувь онлайн?",
     ["чаще раза в месяц", "раз в 1–3 месяца", "реже", "не покупаю"]),
    ("device", "С какого устройства чаще покупаете?", ["смартфон", "компьютер", "планшет"]),
    ("sells", "Продаёте ли вы одежду или обувь онлайн?",
     ["нет", "да, как ИП или небольшой бренд", "да, как сотрудник магазина"]),
]


def header() -> list[str]:
    h = ["Отметка времени", "Код ротации (назовёт ведущий)"] + [d[1] for d in DEMO]
    for _ in range(3):
        h += [f'{p["right_pole_1"]} — {p["left_pole_5"]}' for p in PAIRS]
        h.append("Какое одно слово первым приходит в голову, когда вы смотрите на этот макет?")
    h += ["Если бы вы выбирали приложение для покупки одежды, какой макет выбрали бы?", "Почему?"]
    return h


def done_count() -> int:
    if not RAW.exists():
        return 0
    with RAW.open(encoding="utf-8", newline="") as f:
        return max(0, sum(1 for _ in f) - 1)


def next_code() -> str:
    return CYCLE[done_count() % len(CYCLE)]


def append(row: list[str]) -> int:
    with LOCK:
        new = not RAW.exists()
        RAW.parent.mkdir(parents=True, exist_ok=True)
        with RAW.open("a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(header())
            w.writerow(row)
        return done_count()


PAGE = """<!doctype html><html lang="ru"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Оценка дизайна приложения</title><style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font:16px/1.55 Inter,-apple-system,'Segoe UI',Roboto,sans-serif;background:#eef0f3;color:#1b2432}
.wrap{max-width:820px;margin:0 auto;padding:24px 18px 64px}
.card{background:#fff;border-radius:14px;padding:24px;box-shadow:0 1px 3px #10182814;margin-bottom:18px}
h1{font-size:23px;margin-bottom:12px;letter-spacing:-.01em}
h2{font-size:19px;margin-bottom:6px}
p{margin-bottom:12px}.muted{color:#5f6878;font-size:14px}
.q{padding:14px 0;border-bottom:1px solid #e8eaee}.q:last-child{border-bottom:0}
.q .t{font-size:15px;font-weight:600;margin-bottom:9px}
.sc{display:flex;align-items:center;gap:10px}
.sc .pole{font-size:13px;color:#5f6878;min-width:104px}
.sc .pole.r{text-align:right}
.sc .opts{display:flex;gap:6px;flex:1;justify-content:center}
.sc label{cursor:pointer}
.sc input{position:absolute;opacity:0;width:0;height:0}
.sc b{display:flex;align-items:center;justify-content:center;width:44px;height:44px;
  border:1px solid #c9ced6;border-radius:10px;font-weight:600;font-size:15px;background:#fff}
.sc input:checked + b{background:#22304a;color:#fff;border-color:#22304a}
.sc input:focus-visible + b{outline:2px solid #3a6ea5;outline-offset:2px}
.ch label{display:block;padding:11px 14px;border:1px solid #c9ced6;border-radius:10px;margin-bottom:8px;cursor:pointer}
.ch input{margin-right:9px}
.ch input:checked ~ span{font-weight:600}
input[type=text],textarea{width:100%;font:inherit;padding:11px 13px;border:1px solid #c9ced6;border-radius:10px}
button.go{font:inherit;font-weight:700;font-size:16px;color:#fff;background:#ad5a21;border:0;
  border-radius:11px;padding:15px 28px;cursor:pointer;width:100%}
button.go:disabled{background:#c9ced6;cursor:not-allowed}
.frame{border:0;width:100%;height:70vh;border-radius:12px;background:#fff;border:1px solid #dfe3e8}
.bar{position:sticky;top:0;z-index:5;background:#22304a;color:#fff;padding:11px 18px;
  display:flex;gap:12px;align-items:center;font-size:14px}
.bar .sp{flex:1}.bar b{font-weight:700}
.tmr{background:#ffffff26;border-radius:8px;padding:5px 11px;font-variant-numeric:tabular-nums}
.err{background:#fbe6e3;color:#9e2117;border-radius:10px;padding:11px 14px;margin-bottom:14px;display:none}
@media(max-width:560px){.sc{flex-direction:column;align-items:stretch;gap:7px}
  .sc .pole,.sc .pole.r{text-align:left;min-width:0}.sc b{width:100%;height:46px}
  .sc .opts{gap:7px}}
</style></head><body>
<div class="bar"><b id="step">Оценка оформления</b><span class="sp"></span>
  <span class="tmr" id="tmr" style="display:none"></span></div>
<div class="wrap" id="app"></div>
<script>window.__CFG__ = /*CONFIG*/;</script>
<script src="/test-runner.js"></script>
</body></html>"""


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(MOCKUPS), **k)

    def log_message(self, fmt, *args):
        """Тихий лог: в консоль идут только отправки анкет.

        Базовый log_error передаёт сюда HTTPStatus, а не строку, поэтому
        подстановка выполняется защищённо — иначе падает сам обработчик логов.
        """
        try:
            line = fmt % args
        except Exception:
            line = str(fmt)
        if "POST" in line:
            sys.stderr.write(f"{self.log_date_time_string()}  ОТПРАВЛЕНА АНКЕТА  "
                             f"{self.client_address[0]}\n")
        elif 'GET / ' in line or 'GET /test ' in line:
            sys.stderr.write(f"{self.log_date_time_string()}  открыл(а) тест     "
                             f"{self.client_address[0]}\n")

    def log_error(self, fmt, *args):
        """404 на favicon и прочий шум в консоль не выводим."""
        return

    def _send(self, body: bytes, ctype="text/html; charset=utf-8", code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/favicon.ico":
            return self._send(b"", "image/x-icon", 204)
        if path in ("/", "/test"):
            code = next_code()
            cfg = {"code": code, "order": list(ROT[code]),
                   "pairs": [{"l": p["left_pole_5"], "r": p["right_pole_1"]} for p in PAIRS],
                   "demo": [{"k": k, "q": q, "opts": o} for k, q, o in DEMO]}
            return self._send(PAGE.replace("/*CONFIG*/", json.dumps(cfg, ensure_ascii=False))
                              .encode("utf-8"))
        if path == "/test-runner.js":
            return self._send((MOCKUPS / "test-runner.js").read_bytes(),
                              "application/javascript; charset=utf-8")
        if path == "/status":
            n = done_count()
            rows = ""
            if RAW.exists():
                with RAW.open(encoding="utf-8", newline="") as f:
                    rd = list(csv.DictReader(f))
                for i, r in enumerate(rd, 1):
                    rows += (f"<tr><td>{i}</td><td>{html.escape(r.get(header()[1],''))}</td>"
                             f"<td>{html.escape(r.get(header()[2],''))}</td>"
                             f"<td>{html.escape(r.get(header()[5],''))}</td></tr>")
            body = (f"<!doctype html><meta charset=utf-8><title>Прогресс теста</title>"
                    f"<style>body{{font:16px Inter,sans-serif;padding:30px;max-width:640px;margin:auto}}"
                    f"table{{border-collapse:collapse;width:100%;margin-top:14px}}"
                    f"td,th{{border:1px solid #ddd;padding:7px 10px;text-align:left;font-size:14px}}</style>"
                    f"<h1>Пройдено: {n} из 10</h1>"
                    f"<p>Следующий код ротации: <b>{next_code()}</b></p>"
                    f"<p>Файл: <code>research/raw.csv</code></p>"
                    f"<table><tr><th>№</th><th>Код</th><th>Возраст</th><th>Устройство</th></tr>"
                    f"{rows}</table>")
            return self._send(body.encode("utf-8"))
        return super().do_GET()

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/submit":
            return self._send(b"not found", "text/plain; charset=utf-8", 404)
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n).decode("utf-8"))
        row = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data["code"]]
        row += [data["demo"].get(k, "") for k, _, _ in DEMO]
        for b in range(3):
            row += [str(data["blocks"][b]["scores"].get(p["id"], "")) for p in PAIRS]
            row.append(data["blocks"][b].get("word", ""))
        row += [data.get("pref", ""), data.get("why", "")]
        total = append(row)
        return self._send(json.dumps({"ok": True, "done": total}).encode("utf-8"),
                          "application/json; charset=utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    for p in PAIRS:
        p.setdefault("id", p["id"])
    try:
        srv = ThreadingHTTPServer(("0.0.0.0", a.port), H)
    except OSError as exc:
        if exc.errno != 98:
            raise
        print(f"Порт {a.port} уже занят другой программой.\n")
        print("Освободить его:")
        print(f"  fuser -k {a.port}/tcp\n")
        print("Или запустить тест на другом порту:")
        print(f"  python3 tools/serve_test.py --port {a.port + 1}")
        return 1
    print(f"Тест запущен.  Пройдено анкет: {done_count()} из 10")
    print(f"  ссылка для респондента : http://127.0.0.1:{a.port}/")
    print(f"  прогресс               : http://127.0.0.1:{a.port}/status")
    print(f"  ответы пишутся в       : research/raw.csv")
    print("\nОстановить: Ctrl+C")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print(f"\nОстановлено. Пройдено анкет: {done_count()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
