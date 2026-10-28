#!/usr/bin/env python3
"""Снимает скриншоты макетов для переноса в Figma (ЛР№5, задание 2).

Использует headless-режим Firefox с отдельным профилем. Результат —
prototype/screenshots/, готовые к перетаскиванию во фреймы Figma.

Требуется запущенный сервер макетов:
    cd mockups && python3 -m http.server 8765

Запуск: python3 tools/make_screenshots.py
"""
from __future__ import annotations
import json, os, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
OUT = ROOT / "prototype" / "screenshots"
SNAP = pathlib.Path.home() / "snap" / "firefox" / "common"
PROFILE = SNAP / "ff-shot"
STAGE = SNAP / "shots"
BASE = "http://127.0.0.1:8765"

JOBS = [(f'cat-{b["artboard"]}.png', f'{BASE}/catalog.html',
         b["artboard"], 2600, f'Каталог, {b["range"]}')
        for b in T["grid"]["breakpoints"]]
JOBS += [(f'dev-{d["name"].lower().replace(" ", "-").replace("(", "").replace(")", "").replace('"', "")}.png',
          f'{BASE}/mobile-home.html', d["w"], d["h"], f'{d["name"]}, {d["w"]}×{d["h"]}')
         for d in T["grid"]["devices"]]
JOBS += [
    ("dark-catalog-1440.png", f"{BASE}/catalog.html?mode=dark", 1440, 2600,
     "Каталог, тёмная тема"),
    ("dark-feed-375.png", f"{BASE}/mobile-home.html?mode=dark", 375, 1600,
     "Мобильная главная, тёмная тема"),
]


JOBS += [
    ("proto-1-вход.png", f"{BASE}/prototype-login.html", 393, 852, "Прототип: вход"),
    ("proto-2-лента.png", f"{BASE}/prototype-home.html", 393, 1500, "Прототип: лента"),
    ("proto-3-карточка.png", f"{BASE}/prototype-product.html", 393, 2100, "Прототип: карточка товара"),
    ("proto-4-ассистент.png", f"{BASE}/prototype-product.html#assistant", 393, 852, "Прототип: ассистент по размеру"),
    ("proto-5-корзина.png", f"{BASE}/prototype-cart.html", 393, 1300, "Прототип: корзина"),
    ("proto-6-заказ.png", f"{BASE}/prototype-done.html", 393, 852, "Прототип: заказ оформлен"),
]

def shot(name: str, url: str, w: int, h: int) -> bool:
    dst = STAGE / name
    dst.unlink(missing_ok=True)
    env = {**os.environ, "MOZ_NO_REMOTE": "1"}
    r = subprocess.run(
        ["firefox", "--headless", "--no-remote", "--profile", str(PROFILE),
         "--screenshot", str(dst), "--window-size", f"{w},{h}", url],
        capture_output=True, text=True, timeout=180, env=env)
    if not dst.exists():
        print(f"    ошибка: {r.stderr.strip()[:120]}")
        return False
    shutil.move(str(dst), OUT / name)
    return True


def main() -> int:
    try:
        import urllib.request
        urllib.request.urlopen(BASE, timeout=3)
    except Exception:
        sys.exit(f"ОШИБКА: сервер макетов не отвечает на {BASE}\n"
                 f"Запустите:  cd mockups && python3 -m http.server 8765")

    PROFILE.mkdir(parents=True, exist_ok=True)
    STAGE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    ok = 0
    for name, url, w, h, title in JOBS:
        print(f"  {title:<42} {w}×{h}", end=" ", flush=True)
        if shot(name, url, w, h):
            from PIL import Image
            size = Image.open(OUT / name).size
            kb = (OUT / name).stat().st_size // 1024
            print(f"→ {name}  {size[0]}×{size[1]}, {kb} КБ")
            ok += 1
        else:
            print("→ НЕ СНЯТО")
    print(f"\nГотово: {ok} из {len(JOBS)} → prototype/screenshots/")
    return 0 if ok == len(JOBS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
