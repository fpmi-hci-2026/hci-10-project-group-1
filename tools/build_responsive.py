#!/usr/bin/env python3
"""Адаптивные макеты каталога и экрана мобильного приложения (ЛР№5, задание 2).

Собирает:
  mockups/catalog.html             отзывчивая страница каталога (одна разметка)
  mockups/responsive-catalog.html  витрина: та же страница в шести ширинах
  mockups/mobile-home.html         главная после авторизации (лента рекомендаций)
  mockups/devices.html             витрина: тот же экран на пяти устройствах
  mockups/BREAKPOINTS.md           таблица «что меняется на каждом брейкпоинте»

Сетка, палитра и товары берутся из design/tokens.json и research/products.csv,
поэтому макеты не расходятся с руководством по стилям.

Запуск: python3 tools/build_responsive.py --palette c
"""
from __future__ import annotations
import argparse, csv, html, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
PRODUCTS = list(csv.DictReader((ROOT / "research" / "products.csv").open(encoding="utf-8")))
FONTS = ROOT / "mockups" / "fonts" / "fonts.css"
OUT = ROOT / "mockups"

CHANGES = [
    ("1440+", 1440, "Сайдбар фильтров 3 колонки слева, сетка 4 карточки в ряд. "
                    "Поиск развёрнут в шапке, вся глобальная навигация видна."),
    ("992–1199", 1024, "Сайдбар сохраняется, сетка сокращается до 3 карточек. "
                       "Названия категорий в шапке без изменений."),
    ("768–991", 768, "Сайдбар сворачивается в кнопку «Фильтры» и выдвижную панель. "
                     "Сетка 3 карточки. Поиск сжимается, утилиты шапки — только иконки."),
    ("576–767", 600, "Сетка 2 карточки. Сортировка переезжает в нижнюю всплывающую панель. "
                     "Хлебные крошки сокращаются до последнего уровня."),
    ("400–575", 414, "Категории — горизонтальная лента с прокруткой. "
                     "Внизу закрепляется панель «Фильтры · Сортировка». Поиск — по иконке."),
    ("320–399", 360, "Сетка 2 карточки с уплотнённой типографикой: название в две строки, "
                     "цена и рейтинг в одну. Отступы 16 px, кнопка «В корзину» на всю ширину."),
]


def e(s): return html.escape(str(s))
def money(v): return f"{float(v):,.2f}".replace(",", " ").replace(".", ",") if v else ""
def fonts_css():
    return FONTS.read_text(encoding="utf-8") if FONTS.exists() else ""


def vars_css(pal: str) -> str:
    out = []
    for mode in ("light", "dark"):
        decls = " ".join(f"--{k}:{v};" for k, v in T["palettes"][pal][mode].items())
        out.append(f'html[data-mode="{mode}"]{{{decls}}}')
    return "\n".join(out)


THEME_JS = ("<script>(function(){var m=new URLSearchParams(location.search)"
            ".get('mode');document.documentElement.dataset.mode="
            "m===\'dark\'?\'dark\':\'light\';})();</script>")

BASE = r"""
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{-webkit-font-smoothing:antialiased}
body{font-family:Inter,-apple-system,'Segoe UI',Roboto,sans-serif;background:var(--bg);
     color:var(--text);font-size:16px;line-height:1.5}
img{display:block;max-width:100%}
.logo{font-family:Manrope,Inter,sans-serif;font-weight:800;letter-spacing:-.02em}
a{color:inherit;text-decoration:none}
"""

CATALOG_CSS = r"""
/* ── шапка ── */
.top{background:var(--brand);color:var(--on-brand)}
.wrap{max-width:1440px;margin:0 auto;padding:0 60px}
.top .wrap{display:flex;align-items:center;gap:32px;height:72px}
.logo{font-size:22px;color:var(--on-brand)}
.logo i{font-style:normal;color:var(--accent-soft)}
.search{flex:1;display:flex;align-items:center;gap:10px;background:var(--surface);
        border-radius:10px;height:44px;padding:0 14px;color:var(--text-muted);font-size:15px}
.search .sb{margin-left:auto;background:var(--accent);color:var(--on-accent);
        border-radius:7px;padding:7px 16px;font-size:14px;font-weight:600}
.util{display:flex;gap:24px;font-size:13px}
.util div{display:flex;flex-direction:column;align-items:center;gap:3px}
.util b{font-size:17px;font-weight:400;line-height:1}
.nav{background:var(--surface);border-bottom:1px solid var(--border)}
.nav .wrap{display:flex;align-items:center;gap:26px;height:52px;font-size:15px;overflow:auto}
.nav .g{font-weight:600}
.nav .sep{width:1px;height:20px;background:var(--border);flex:none}
.nav .bel{margin-left:auto;background:var(--accent-soft);color:var(--on-accent-soft);
        font-size:13px;font-weight:600;border-radius:999px;padding:6px 14px;white-space:nowrap}

/* ── каркас страницы ── */
.page{max-width:1440px;margin:0 auto;padding:24px 60px 56px}
.crumbs{font-size:13px;color:var(--text-muted);margin-bottom:10px}
.crumbs .last{color:var(--text)}
h1{font-size:30px;font-weight:700;letter-spacing:-.01em}
.cnt{color:var(--text-muted);font-size:14px;margin-top:4px}
.cols{display:grid;grid-template-columns:312px 1fr;gap:24px;margin-top:22px;align-items:start}

/* ── фильтры ── */
.side{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px}
.fgroup{padding:14px 0;border-bottom:1px solid var(--border)}
.fgroup:first-child{padding-top:0}
.fgroup:last-child{border-bottom:0;padding-bottom:0}
.fgroup h3{font-size:13px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;
        color:var(--text-muted);margin-bottom:10px}
.fgroup label{display:flex;align-items:center;gap:9px;font-size:14px;padding:5px 0}
.fgroup label i{width:17px;height:17px;border:1.5px solid var(--border-strong);border-radius:5px;
        flex:none;background:var(--surface)}
.fgroup label.on i{background:var(--accent);border-color:var(--accent)}
.fgroup label span.n{margin-left:auto;color:var(--text-muted);font-size:13px}
.szgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px}
.szgrid b{font-size:13px;font-weight:600;text-align:center;padding:8px 0;
        border:1px solid var(--border-strong);border-radius:8px}
.szgrid b.on{background:var(--brand);color:var(--on-brand);border-color:var(--brand)}
.price-row{display:flex;gap:8px}
.price-row span{flex:1;border:1px solid var(--border-strong);border-radius:8px;padding:8px 10px;
        font-size:13px;color:var(--text-muted)}
.hint{margin-top:14px;background:var(--accent-soft);color:var(--on-accent-soft);
      border-radius:10px;padding:11px 12px;font-size:13px;line-height:1.4}

/* ── панель сортировки ── */
.bar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.chip{display:inline-flex;align-items:center;gap:7px;background:var(--surface);
      border:1px solid var(--border);border-radius:999px;padding:7px 13px;font-size:13px}
.chip.sel{background:var(--accent-soft);color:var(--on-accent-soft);border-color:transparent;font-weight:600}
.sort{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:14px;color:var(--text-muted)}
.sort b{color:var(--text);font-weight:600}
.fbtn{display:none;align-items:center;gap:8px;background:var(--surface);
      border:1px solid var(--border-strong);border-radius:10px;padding:10px 15px;font-size:14px;font-weight:600}
.fbtn em{font-style:normal;background:var(--accent);color:var(--on-accent);
      border-radius:999px;padding:1px 7px;font-size:12px}

/* ── сетка товаров ── */
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:24px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;
      overflow:hidden;display:flex;flex-direction:column}
.ph{position:relative;aspect-ratio:3/4;background:var(--surface-alt)}
.ph img{width:100%;height:100%;object-fit:cover}
.bdg{position:absolute;left:10px;top:10px;font-size:11px;font-weight:600;border-radius:999px;
     padding:4px 9px;background:var(--accent-soft);color:var(--on-accent-soft)}
.bdg.fit{background:var(--warning-soft);color:var(--warning)}
.fav{position:absolute;right:10px;top:10px;width:30px;height:30px;border-radius:50%;
     background:var(--surface);display:flex;align-items:center;justify-content:center;
     font-size:14px;color:var(--text-muted)}
.cb{padding:12px 13px 14px;display:flex;flex-direction:column;gap:6px;flex:1}
.br{font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--text-muted)}
.ti{font-size:15px;font-weight:600;line-height:1.3}
.sm{font-size:12.5px;line-height:1.4;color:var(--text-muted)}
.rt{font-size:12.5px;color:var(--text-muted)}
.rt b{color:var(--text)}
.pr{margin-top:auto;padding-top:6px;display:flex;align-items:baseline;gap:8px}
.pr .now{font-size:18px;font-weight:700}
.pr .old{font-size:13px;color:var(--text-muted);text-decoration:line-through}
.cart{margin-top:9px;background:var(--accent);color:var(--on-accent);border-radius:9px;
      min-height:44px;display:flex;align-items:center;justify-content:center;
      font-size:13.5px;font-weight:600}
.pager{display:flex;justify-content:center;gap:7px;margin-top:32px}
.pager b{min-width:38px;height:38px;display:flex;align-items:center;justify-content:center;
      border:1px solid var(--border);border-radius:9px;font-size:14px;font-weight:600;background:var(--surface)}
.pager b.on{background:var(--brand);color:var(--on-brand);border-color:var(--brand)}
.sticky{display:none;position:sticky;bottom:0;background:var(--surface);
      border-top:1px solid var(--border);padding:10px 16px;gap:10px}
.sticky div{flex:1;text-align:center;font-size:14px;font-weight:600;padding:11px 0;
      border:1px solid var(--border-strong);border-radius:10px}

/* ══ 992–1199: сайдбар сохраняется, сетка 3 карточки ══ */
@media (max-width:1199px){
  .wrap,.page{max-width:1024px;padding-left:20px;padding-right:20px}
  .cols{grid-template-columns:228px 1fr}
  .grid{grid-template-columns:repeat(3,1fr)}
}
/* ══ 768–991: фильтры в выдвижную панель ══ */
@media (max-width:991px){
  .wrap,.page{max-width:768px;padding-left:24px;padding-right:24px}
  .cols{grid-template-columns:1fr}
  .side{display:none}
  .fbtn{display:inline-flex}
  .search .sb{display:none}
  .util div span{display:none}
  h1{font-size:26px}
}
/* ══ 576–767: сетка 2 карточки ══ */
@media (max-width:767px){
  .wrap,.page{max-width:600px}
  .grid{grid-template-columns:repeat(2,1fr);gap:16px}
  .crumbs span:not(.last){display:none}
  .sort{margin-left:0;width:100%}
  h1{font-size:23px}
}
/* ══ 400–575: категории прокруткой, липкая панель снизу ══ */
@media (max-width:575px){
  .cart{min-height:48px}
  .fav{width:44px;height:44px;font-size:17px}
  .szgrid b{padding:13px 0}
  .fgroup label{padding:9px 0}
  .wrap,.page{max-width:none;padding-left:16px;padding-right:16px}
  .top .wrap{height:60px;gap:14px}
  .search{height:40px;font-size:0;gap:0;justify-content:center;flex:none;width:40px;padding:0}
  .util{gap:16px}
  .nav .wrap{gap:18px;height:46px}
  .nav .bel{margin-left:0}
  .bar .chip:nth-child(n+3){display:none}
  .fbtn,.sort{display:none}
  .sticky{display:flex}
  .page{padding-bottom:16px}
}
/* ══ 320–399: уплотнение ══ */
@media (max-width:399px){
  .grid{gap:12px}
  .logo{font-size:19px}
  h1{font-size:20px}
  .cb{padding:10px 11px 12px;gap:5px}
  .ti{font-size:14px}
  .sm{display:none}
  .pr .now{font-size:16px}
  .cart{font-size:13px}
}
"""


def card(p, compact=False):
    badge = ""
    if p["badge"]:
        cls = "bdg fit" if "Маломерит" in p["badge"] else "bdg"
        badge = f'<span class="{cls}">{e(p["badge"])}</span>'
    old = f'<span class="old">{money(p["price_old"])} р.</span>' if p["price_old"] else ""
    return f"""<article class="card">
  <div class="ph"><img src="img/{p['id']}.jpg" alt=""/>{badge}<span class="fav">♡</span></div>
  <div class="cb"><div class="br">{e(p['brand'])}</div><div class="ti">{e(p['title'])}</div>
    <div class="sm">{e(p['summary'])}</div>
    <div class="rt">★ <b>{e(p['rating'])}</b> · {e(p['reviews'])}</div>
    <div class="pr"><span class="now">{money(p['price'])} р.</span>{old}</div>
    <div class="cart">В корзину</div></div></article>"""


def catalog_html(pal: str) -> str:
    cards = "\n".join(card(p) for p in PRODUCTS)
    sizes = "".join(f'<b class="{"on" if s=="46" else ""}">{s}</b>' for s in
                    ["40","42","44","46","48","50","52","54"])
    return f"""<!doctype html><html lang="ru" data-mode="light"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Каталог — МаркетШоп.by</title>
<style>{fonts_css()}
{vars_css(pal)}
{BASE}{CATALOG_CSS}</style></head><body>
<header class="top"><div class="wrap">
  <div class="logo">МаркетШоп<i>.by</i></div>
  <div class="search">⌕ <span>Платье, кроссовки, бренд…</span><span class="sb">Найти</span></div>
  <nav class="util"><div><b>♡</b><span>Избранное</span></div>
    <div><b>▤</b><span>Корзина</span></div><div><b>☺</b><span>Профиль</span></div></nav>
</div></header>
<nav class="nav"><div class="wrap">
  <a class="g">Каталог</a><a class="g">Рекомендации</a><span class="sep"></span>
  <a>Женщинам</a><a>Мужчинам</a><a>Детям</a><a>Обувь</a><a>Распродажа</a>
  <span class="bel">Сделано в Беларуси</span>
</div></nav>
<main class="page">
  <div class="crumbs"><span>Главная · </span><span>Женщинам · </span><span class="last">Одежда</span></div>
  <h1>Женская одежда</h1>
  <div class="cnt">1 248 товаров · описания проверены продавцом и модератором</div>
  <div class="cols">
    <aside class="side">
      <div class="fgroup"><h3>Категория</h3>
        <label class="on"><i></i>Платья<span class="n">312</span></label>
        <label><i></i>Блузы и рубашки<span class="n">208</span></label>
        <label><i></i>Джинсы<span class="n">164</span></label>
        <label><i></i>Верхняя одежда<span class="n">97</span></label>
        <label><i></i>Трикотаж<span class="n">143</span></label></div>
      <div class="fgroup"><h3>Цена, BYN</h3>
        <div class="price-row"><span>от 49</span><span>до 389</span></div></div>
      <div class="fgroup"><h3>Размер</h3><div class="szgrid">{sizes}</div></div>
      <div class="fgroup"><h3>Особенности</h3>
        <label class="on"><i></i>Сделано в Беларуси<span class="n">486</span></label>
        <label><i></i>Есть в наличии<span class="n">1 102</span></label>
        <label><i></i>Со скидкой<span class="n">217</span></label></div>
      <div class="fgroup"><h3>Бренд</h3>
        <label><i></i>Conte<span class="n">88</span></label>
        <label><i></i>Mark Formelle<span class="n">124</span></label>
        <label><i></i>Elema<span class="n">61</span></label></div>
      <div class="hint">Не уверены в размере? Ассистент подскажет, маломерит ли бренд,
        по вашим меркам — прямо в карточке товара.</div>
    </aside>
    <section>
      <div class="bar">
        <span class="fbtn">⚙ Фильтры <em>2</em></span>
        <span class="chip sel">Платья ✕</span>
        <span class="chip sel">Сделано в Беларуси ✕</span>
        <span class="chip">Размер 46 ✕</span>
        <div class="sort">Сортировка: <b>по популярности</b> ⌄</div>
      </div>
      <div class="grid">{cards}</div>
      <div class="pager"><b class="on">1</b><b>2</b><b>3</b><b>…</b><b>52</b></div>
    </section>
  </div>
</main>
<div class="sticky"><div>⚙ Фильтры · 2</div><div>⇅ Сортировка</div></div>
{THEME_JS}
</body></html>"""


MOBILE_CSS = r"""
.mtop{background:var(--brand);color:var(--on-brand);padding:10px 16px 12px}
.mtop .r1{display:flex;align-items:center;justify-content:space-between}
.mtop .logo{font-size:19px;color:var(--on-brand)}
.mtop .logo i{font-style:normal;color:var(--accent-soft)}
.mtop .ic{font-size:17px;opacity:.9}
.msearch{margin-top:10px;background:var(--surface);border-radius:10px;height:40px;
         display:flex;align-items:center;gap:9px;padding:0 13px;color:var(--text-muted);font-size:14px}
.cats{display:flex;gap:8px;overflow:auto;padding:12px 16px 0}
.cats b{flex:none;font-size:13px;font-weight:600;background:var(--surface);
        border:1px solid var(--border);border-radius:999px;padding:7px 14px}
.cats b.on{background:var(--accent-soft);color:var(--on-accent-soft);border-color:transparent}
.greet{padding:16px 16px 0}
.greet h2{font-size:20px;font-weight:700;letter-spacing:-.01em}
.greet p{font-size:13.5px;color:var(--text-muted);margin-top:3px}
.mgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;padding:12px 16px 16px}
.mbar{position:sticky;bottom:0;background:var(--surface);border-top:1px solid var(--border);
      display:flex;padding:8px 0 12px}
.mbar div{flex:1;min-height:48px;display:flex;flex-direction:column;align-items:center;
      justify-content:center;font-size:10px;color:var(--text-muted)}
.mbar div b{font-size:17px;font-weight:400;margin-bottom:2px}
.mbar div.on{color:var(--accent)}
/* планшеты: три и четыре колонки, навигация сбоку */
@media (min-width:700px){
  .mgrid{grid-template-columns:repeat(3,1fr);gap:16px;padding:16px 24px 24px}
  .cats{padding:16px 24px 0}.greet{padding:20px 24px 0}.greet h2{font-size:24px}
  .mtop{padding:14px 24px 16px}
}
@media (min-width:820px){
  .mgrid{grid-template-columns:repeat(4,1fr);gap:20px;padding:20px 32px 32px}
  .cats{padding:20px 32px 0}.greet{padding:24px 32px 0}
  .mtop{padding:16px 32px 18px}
}
"""


def mobile_home(pal: str) -> str:
    cards = "\n".join(card(p) for p in PRODUCTS)
    return f"""<!doctype html><html lang="ru" data-mode="light"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Главная — МаркетШоп.by</title>
<style>{fonts_css()}
{vars_css(pal)}
{BASE}{CATALOG_CSS}{MOBILE_CSS}</style></head><body>
<header class="mtop">
  <div class="r1"><div class="logo">МаркетШоп<i>.by</i></div>
    <div><span class="ic">♡</span> &nbsp; <span class="ic">▤</span></div></div>
  <div class="msearch">⌕ Платье, кроссовки, бренд…</div>
</header>
<div class="cats"><b class="on">Для вас</b><b>Новинки</b><b>Платья</b><b>Обувь</b>
  <b>Сделано в Беларуси</b><b>Распродажа</b></div>
<div class="greet"><h2>Специально для вас</h2>
  <p>Подобрано по размеру 46, любимым категориям и сезону</p></div>
<div class="mgrid">{cards}</div>
<nav class="mbar"><div class="on"><b>⌂</b>Главная</div><div><b>⌕</b>Поиск</div>
  <div><b>♡</b>Избранное</div><div><b>▤</b>Корзина</div><div><b>☺</b>Профиль</div></nav>
{THEME_JS}
</body></html>"""


SHOW_CSS = r"""
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,-apple-system,sans-serif;background:#2b2f36;color:#eceef1;padding:28px}
h1{font-size:21px;font-weight:700;margin-bottom:6px}
.lead{font-size:14px;color:#a9b0ba;margin-bottom:22px;max-width:860px;line-height:1.55}
.row{display:flex;gap:22px;align-items:flex-start;overflow-x:auto;padding-bottom:14px}
.item{flex:none}
.cap{font-size:13px;margin-bottom:7px;display:flex;gap:8px;align-items:baseline}
.cap b{font-weight:700}.cap span{color:#a9b0ba;font-size:12px}
iframe{border:0;background:#fff;border-radius:10px;box-shadow:0 10px 28px #0006;display:block}
.note{margin-top:18px;font-size:13px;color:#a9b0ba;line-height:1.6;max-width:860px}
.note code{background:#3a3f48;padding:1px 6px;border-radius:5px}
"""


def showcase(title, lead, frames, note) -> str:
    items = "\n".join(
        f'<div class="item"><div class="cap"><b>{e(c)}</b><span>{e(s)}</span></div>'
        f'<iframe src="{src}" width="{w}" height="{h}" loading="lazy"></iframe></div>'
        for c, s, src, w, h in frames)
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{e(title)}</title><style>{SHOW_CSS}</style></head><body>
<h1>{e(title)}</h1><div class="lead">{lead}</div>
<div class="row">{items}</div><div class="note">{note}</div></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--palette", default="c", choices=["a", "b", "c"])
    a = ap.parse_args()

    (OUT / "catalog.html").write_text(catalog_html(a.palette), encoding="utf-8")
    (OUT / "mobile-home.html").write_text(mobile_home(a.palette), encoding="utf-8")

    frames = [(f"{w} px", rng, "catalog.html", w, 1200) for rng, w, _ in CHANGES]
    (OUT / "responsive-catalog.html").write_text(showcase(
        "Каталог с фильтрами — шесть разрешений",
        "Одна и та же страница <code>catalog.html</code> в шести ширинах монтажной области. "
        "Это не шесть отдельных макетов, а одна разметка с медиазапросами: перетаскивая край окна "
        "браузера, можно увидеть переходы между состояниями.",
        frames,
        "Расчёт сетки и перечень изменений — в <code>BREAKPOINTS.md</code>. "
        "Палитра переключается режимом переменных, тёмная тема — атрибутом "
        "<code>data-mode=\"dark\"</code> на корневом элементе."), encoding="utf-8")

    dev_frames = [(d["name"], f'{d["w"]}×{d["h"]} · {d["platform"]}',
                   "mobile-home.html", d["w"], d["h"]) for d in T["grid"]["devices"]]
    (OUT / "devices.html").write_text(showcase(
        "Главная после авторизации — пять устройств",
        "Экран ленты «Специально для вас» на трёх смартфонах и двух планшетах. "
        "Сетка карточек меняется с 2 колонок на смартфоне до 3 на iPad mini и 4 на iPad Pro; "
        "нижняя панель навигации сохраняется в зоне досягаемости большого пальца.",
        dev_frames,
        "Размеры устройств заданы в <code>design/tokens.json</code> → <code>grid.devices</code>. "
        "Тач-зоны не меньше 44 pt на iOS и 48 dp на Android."), encoding="utf-8")

    g = T["grid"]["breakpoints"]
    L = ["# Адаптивные макеты каталога — брейкпоинты", "",
         "Страница для адаптации — **каталог с фильтрами**: у неё самая богатая структура "
         "(боковая панель фильтров и сетка карточек), поэтому перестроение видно на каждом шаге.", "",
         "## Расчёт модульной сетки", "",
         "Ширина контейнера = колонка × N + гаттер × (N − 1).", "",
         "| Диапазон | Артборд | Контейнер | Колонок | Гаттер | Колонка | Поля | Проверка |",
         "|---|---|---|---|---|---|---|---|"]
    for b in g:
        if isinstance(b["container"], int):
            calc = b["column"] * b["columns"] + b["gutter"] * (b["columns"] - 1)
            chk = f"{b['columns']}×{b['column']} + {b['columns']-1}×{b['gutter']} = {calc}"
        else:
            chk = "резиновая (Stretch)"
        L.append(f"| {b['range']} | {b['artboard']} | {b['container']} | {b['columns']} | "
                 f"{b['gutter']} | {b['column']} | {b['margin']} | {chk} |")
    L += ["", "## Что меняется на каждом брейкпоинте", "",
          "| Диапазон | Артборд | Изменения |", "|---|---|---|"]
    L += [f"| {rng} | {w} | {ch} |" for rng, w, ch in CHANGES]
    L += ["", "## Файлы", "",
          "| Файл | Назначение |", "|---|---|",
          "| `catalog.html` | отзывчивая страница каталога — одна разметка на все разрешения |",
          "| `responsive-catalog.html` | витрина: та же страница в шести ширинах |",
          "| `mobile-home.html` | главная после авторизации, лента рекомендаций |",
          "| `devices.html` | витрина: тот же экран на пяти устройствах |", "",
          "Макеты не рисовались по отдельности: при изменении токенов или списка товаров "
          "достаточно перезапустить `tools/build_responsive.py`.", ""]
    (OUT / "BREAKPOINTS.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"Палитра: {T['palettes'][a.palette]['name']}\n")
    for f in ("catalog.html", "mobile-home.html", "responsive-catalog.html",
              "devices.html", "BREAKPOINTS.md"):
        print(f"  mockups/{f:<26} {(OUT/f).stat().st_size//1024} КБ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
