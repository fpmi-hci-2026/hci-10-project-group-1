#!/usr/bin/env python3
"""Интерактивный прототип покупательского сценария (ЛР№5, задание 2, п. 4).

Собирает связанные экраны: вход, лента рекомендаций, карточка товара,
ассистент по размеру, корзина, подтверждение заказа. Переходы — настоящие
ссылки, прототип открывается в браузере и работает без Figma.

Сценарии соответствуют вариантам использования ЛР№4:
UC-20/21 авторизация, UC-01 лента, UC-03 карточка, UC-04 подбор размера,
UC-05/06 оформление и оплата заказа.

Запуск: python3 tools/build_prototype.py --palette c
"""
from __future__ import annotations
import argparse, csv, html, json, pathlib, re
from importlib.machinery import SourceFileLoader

ROOT = pathlib.Path(__file__).resolve().parent.parent
R = SourceFileLoader("r", str(ROOT / "tools" / "build_responsive.py")).load_module()
T = R.T
PRODUCTS = R.PRODUCTS
OUT = ROOT / "mockups"
HERO_MD = (ROOT / "research" / "product-hero.md").read_text(encoding="utf-8")


def hero(field, default=""):
    m = re.search(rf"^-\s*{re.escape(field)}\s*:\s*(.*)$", HERO_MD, re.M)
    v = m.group(1).strip() if m else default
    return "" if v.lower() == "нет" else v


e, money = R.e, R.money
HP = next(p for p in PRODUCTS if p["id"] == "feed-4")

PROTO_CSS = r"""
.scr{max-width:520px;margin:0 auto;background:var(--bg);min-height:100vh;
     display:flex;flex-direction:column}
.sbar{height:26px;background:var(--surface);display:flex;align-items:center;
      justify-content:space-between;padding:0 16px;font-size:11px;font-weight:600}
.hd{height:52px;background:var(--surface);border-bottom:1px solid var(--border);
    display:flex;align-items:center;gap:12px;padding:0 14px;font-size:16px;font-weight:600}
.hd a.ic,.hd span.ic{color:var(--text-muted);font-size:19px;font-weight:400;
    min-width:44px;min-height:44px;display:flex;align-items:center;justify-content:center}
.hd .sp{flex:1}
.body{flex:1;padding:18px 16px 24px}
.btn{display:flex;align-items:center;justify-content:center;min-height:52px;
     background:var(--accent);color:var(--on-accent);border-radius:12px;
     font-size:16px;font-weight:700;width:100%;margin-top:16px}
.btn.sec{background:var(--surface);color:var(--text);border:1px solid var(--border-strong)}
.fld{margin-top:14px}
.fld label{display:block;font-size:13px;font-weight:600;color:var(--text-muted);margin-bottom:6px}
.fld .inp{min-height:52px;display:flex;align-items:center;padding:0 14px;background:var(--surface);
     border:1px solid var(--border-strong);border-radius:11px;font-size:16px}
.fld .inp.ph{color:var(--text-muted)}
.lnk{display:block;text-align:center;margin-top:16px;font-size:14px;color:var(--text-muted)}
.lnk b{color:var(--accent);font-weight:600}
.h1{font-size:26px;font-weight:700;letter-spacing:-.01em}
.sub{color:var(--text-muted);font-size:14px;margin-top:6px}
.or{display:flex;align-items:center;gap:12px;margin:18px 0 0;color:var(--text-muted);font-size:13px}
.or::before,.or::after{content:"";flex:1;height:1px;background:var(--border)}
.bn{position:sticky;bottom:0;background:var(--surface);border-top:1px solid var(--border);
    display:flex;padding:8px 0 12px}
.bn a{flex:1;min-height:48px;display:flex;flex-direction:column;align-items:center;
      justify-content:center;font-size:10px;color:var(--text-muted)}
.bn a b{font-size:17px;font-weight:400;margin-bottom:2px}
.bn a.on{color:var(--accent)}

/* карточка товара */
.gal{position:relative;aspect-ratio:3/4;background:var(--surface-alt)}
.gal img{width:100%;height:100%;object-fit:cover}
.dots{position:absolute;left:0;right:0;bottom:12px;display:flex;justify-content:center;gap:6px}
.dots i{width:6px;height:6px;border-radius:50%;background:var(--surface);opacity:.55}
.dots i.on{opacity:1;width:18px;border-radius:3px}
.pbr{font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--text-muted)}
.pti{font-size:21px;font-weight:700;line-height:1.25;margin-top:3px;letter-spacing:-.01em}
.ppr{display:flex;align-items:baseline;gap:10px;margin-top:10px}
.ppr .now{font-size:25px;font-weight:700}
.prt{display:flex;align-items:center;gap:8px;margin-top:10px;font-size:13px;color:var(--text-muted)}
.prt b{color:var(--text)}
.fitchip{background:var(--warning-soft);color:var(--warning);font-size:12px;font-weight:600;
      border-radius:999px;padding:4px 10px}
.asis{margin-top:14px;background:var(--accent-soft);border-radius:12px;padding:14px;display:block}
.asis .h{font-size:14px;font-weight:700;color:var(--on-accent-soft);display:flex;gap:7px;align-items:center}
.asis p{font-size:13px;line-height:1.45;color:var(--on-accent-soft);margin-top:5px;opacity:.92}
.asis .b{margin-top:11px;display:inline-flex;align-items:center;min-height:44px;padding:0 18px;
      background:var(--accent);color:var(--on-accent);border-radius:9px;font-size:14px;font-weight:600}
.dsc{margin-top:18px}
.dsc h4{font-size:17px;font-weight:700}
.dl{margin-top:10px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:4px 14px}
.dl .it{padding:11px 0;border-bottom:1px solid var(--border)}
.dl .it:last-child{border-bottom:0}
.dl .k{font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--text-muted)}
.dl .v{font-size:14px;line-height:1.45;margin-top:3px}
.dl .v.na{color:var(--text-muted);font-style:italic}
.szs{margin-top:18px}
.szs .h{font-size:14px;font-weight:600;display:flex;justify-content:space-between}
.szs .h span{color:var(--text-muted);font-weight:400}
.szl{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
.szl b{font-size:14px;font-weight:600;min-width:52px;min-height:48px;display:flex;
     align-items:center;justify-content:center;border:1px solid var(--border-strong);
     border-radius:10px;background:var(--surface)}
.szl b.on{background:var(--brand);color:var(--on-brand);border-color:var(--brand)}
.szl b.off{color:var(--text-muted);opacity:.45;text-decoration:line-through;border-style:dashed}

/* всплывающая панель ассистента */
.ov{position:fixed;inset:0;background:#0007;display:none;align-items:flex-end;z-index:20}
.ov:target{display:flex}
.ov .sheet{width:100%;max-width:520px;margin:0 auto;background:var(--surface);
     border-radius:18px 18px 0 0;padding:20px 18px 24px}
.ov h3{font-size:19px;font-weight:700}
.ov .close{position:absolute;top:0;right:0;min-width:48px;min-height:48px;
     display:flex;align-items:center;justify-content:center;color:var(--text-muted);font-size:22px}
.ov .wrap{position:relative}
.res{margin-top:16px;background:var(--success-soft);color:var(--success);
     border-radius:11px;padding:14px;font-size:14px;line-height:1.45;font-weight:600}

/* корзина */
.ci{display:flex;gap:12px;background:var(--surface);border:1px solid var(--border);
    border-radius:12px;padding:12px;margin-bottom:12px}
.ci img{width:76px;height:101px;object-fit:cover;border-radius:8px;flex:none}
.ci .m{flex:1;display:flex;flex-direction:column;gap:3px}
.ci .m .t{font-size:14px;font-weight:600;line-height:1.3}
.ci .m .s{font-size:12.5px;color:var(--text-muted)}
.ci .m .p{font-size:16px;font-weight:700;margin-top:auto}
.sum{background:var(--surface);border:1px solid var(--border);border-radius:12px;
     padding:14px;margin-top:4px}
.sum div{display:flex;justify-content:space-between;font-size:14px;padding:5px 0}
.sum div.tot{border-top:1px solid var(--border);margin-top:7px;padding-top:11px;
     font-size:18px;font-weight:700}
.sum .free{color:var(--success);font-weight:600}
.pay{margin-top:18px}
.pay h4{font-size:15px;font-weight:700;margin-bottom:10px}
.pay label{display:flex;align-items:center;gap:11px;min-height:52px;background:var(--surface);
     border:1px solid var(--border);border-radius:11px;padding:0 14px;margin-bottom:9px;font-size:14px}
.pay label.on{border-color:var(--accent);background:var(--accent-soft);color:var(--on-accent-soft);font-weight:600}
.pay label i{width:19px;height:19px;border-radius:50%;border:2px solid var(--border-strong);flex:none}
.pay label.on i{border-color:var(--accent);background:var(--accent);box-shadow:inset 0 0 0 3px var(--surface)}
.done{text-align:center;padding:48px 20px}
.done .ok{width:76px;height:76px;border-radius:50%;background:var(--success-soft);color:var(--success);
     display:flex;align-items:center;justify-content:center;font-size:38px;margin:0 auto 20px}
.done h2{font-size:24px;font-weight:700}
.done p{color:var(--text-muted);margin-top:9px;font-size:15px;line-height:1.5}
.done .num{margin-top:16px;font-family:ui-monospace,monospace;font-size:15px;font-weight:600}
"""


def page(title, inner, extra=""):
    return f"""<!doctype html><html lang="ru" data-mode="light"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{e(title)} — МаркетШоп.by</title>
<style>{R.fonts_css()}
{R.vars_css(PAL)}
{R.BASE}{R.CATALOG_CSS}{R.MOBILE_CSS}{PROTO_CSS}</style></head><body>
{inner}
{extra}
{R.THEME_JS}
</body></html>"""


def bottom_nav(active="home"):
    items = [("home", "⌂", "Главная", "prototype-home.html"),
             ("search", "⌕", "Поиск", "catalog.html"),
             ("fav", "♡", "Избранное", "#"),
             ("cart", "▤", "Корзина", "prototype-cart.html"),
             ("me", "☺", "Профиль", "#")]
    return '<nav class="bn">' + "".join(
        f'<a class="{"on" if k == active else ""}" href="{h}"><b>{i}</b>{t}</a>'
        for k, i, t, h in items) + "</nav>"


def login():
    inner = f"""<div class="scr">
 <div class="sbar"><span>19:42</span><span>⌁ ▮▮▮ ▰</span></div>
 <div class="body">
  <div class="logo" style="font-size:26px;color:var(--brand)">МаркетШоп<i style="font-style:normal;color:var(--accent)">.by</i></div>
  <div style="margin-top:28px"><div class="h1">Вход</div>
   <div class="sub">Войдите, чтобы видеть подборку под ваш размер и стиль</div></div>
  <div class="fld"><label>Электронная почта</label>
   <div class="inp">anastasiya@example.by</div></div>
  <div class="fld"><label>Пароль</label>
   <div class="inp">••••••••••</div></div>
  <a class="btn" href="prototype-home.html">Войти</a>
  <a class="lnk" href="#">Забыли пароль?</a>
  <div class="or">или</div>
  <a class="btn sec" href="prototype-home.html">⬤ &nbsp;Войти по отпечатку</a>
  <a class="lnk" href="#">Нет аккаунта? <b>Зарегистрироваться</b></a>
 </div></div>"""
    return page("Вход", inner)


def product():
    sizes_in = [s.strip() for s in hero("Размеры в наличии").split(";") if s.strip()]
    sizes_out = [s.strip() for s in hero("Размеры закончились").split(";") if s.strip()]
    sz = "".join(f'<b class="{"on" if i == 1 else ""}">{e(s)}</b>'
                 for i, s in enumerate(sizes_in))
    sz += "".join(f'<b class="off">{e(s)}</b>' for s in sizes_out)
    blocks = [("Состав", hero("Состав")), ("Посадка", hero("Посадка")),
              ("Уход", hero("Уход")), ("Размерная сетка бренда", hero("Размерная сетка бренда"))]
    items = "".join(
        f'<div class="it"><div class="k">{e(k)}</div>'
        f'<div class="v{"" if v else " na"}">{e(v) if v else "Продавец не указал"}</div></div>'
        for k, v in blocks)
    inner = f"""<div class="scr">
 <div class="sbar"><span>19:44</span><span>⌁ ▮▮▮ ▰</span></div>
 <div class="hd"><a class="ic" href="prototype-home.html">‹</a><span>Карточка товара</span>
   <span class="sp"></span><span class="ic">♡</span><span class="ic">⇪</span></div>
 <div class="gal"><img src="img/hero-1.jpg" alt=""/>
   <div class="dots"><i class="on"></i><i></i><i></i><i></i><i></i></div></div>
 <div class="body">
  <div class="pbr">{e(hero('Бренд'))}</div>
  <div class="pti">{e(hero('Название'))}</div>
  <div class="ppr"><span class="now">{money(HP['price'])} р.</span></div>
  <div class="prt">★ <b>{e(hero('Оценка'))}</b> · {e(hero('Число отзывов'))} отзывов
    <span class="fitchip">Маломерит · {e(hero('Маломерит'))}</span></div>
  <a class="asis" href="#assistant">
    <div class="h">⇲ Ассистент по размеру</div>
    <p>{e(hero('Размерная сетка бренда'))}</p>
    <span class="b">Подобрать размер</span></a>
  <div class="dsc"><h4>Описание</h4><div class="dl">{items}</div></div>
  <div class="szs"><div class="h">Размер <span>Таблица размеров</span></div>
    <div class="szl">{sz}</div></div>
  <a class="btn" href="prototype-cart.html">В корзину · {money(HP['price'])} р.</a>
 </div>
 {bottom_nav('home')}</div>"""
    overlay = f"""<div class="ov" id="assistant"><div class="sheet"><div class="wrap">
  <a class="close" href="#">✕</a>
  <h3>Ассистент по размеру</h3>
  <div class="sub">Укажите параметры — подберём размер и не придётся оформлять возврат</div>
  <div class="fld"><label>Рост, см</label><div class="inp">168</div></div>
  <div class="fld"><label>Обхват бёдер, см</label><div class="inp">96</div></div>
  <div class="res">Вам подойдёт размер 46.<br/>{e(hero('Размерная сетка бренда'))}</div>
  <a class="btn" href="#">Выбрать 46</a>
 </div></div></div>"""
    return page("Карточка товара", inner, overlay)


def cart():
    p2 = next(p for p in PRODUCTS if p["id"] == "feed-1")
    total = float(HP["price"]) + float(p2["price"])
    inner = f"""<div class="scr">
 <div class="sbar"><span>19:46</span><span>⌁ ▮▮▮ ▰</span></div>
 <div class="hd"><a class="ic" href="prototype-product.html">‹</a><span>Корзина</span></div>
 <div class="body">
  <div class="ci"><img src="img/hero-1.jpg" alt=""/><div class="m">
    <div class="t">{e(hero('Название'))}</div>
    <div class="s">{e(hero('Бренд'))} · размер 46</div>
    <div class="p">{money(HP['price'])} р.</div></div></div>
  <div class="ci"><img src="img/feed-1.jpg" alt=""/><div class="m">
    <div class="t">{e(p2['title'])}</div>
    <div class="s">{e(p2['brand'])} · размер 46</div>
    <div class="p">{money(p2['price'])} р.</div></div></div>
  <div class="sum">
    <div><span>Товары, 2 шт.</span><span>{money(total)} р.</span></div>
    <div><span>Доставка в пункт самовывоза</span><span class="free">бесплатно</span></div>
    <div><span>Срок возврата</span><span>14 дней</span></div>
    <div class="tot"><span>К оплате</span><span>{money(total)} р.</span></div>
  </div>
  <div class="pay"><h4>Способ оплаты</h4>
    <label class="on"><i></i>Банковская карта онлайн</label>
    <label><i></i>Наличными при получении</label>
    <label><i></i>ЕРИП</label>
  </div>
  <a class="btn" href="prototype-done.html">Оформить заказ</a>
 </div>
 {bottom_nav('cart')}</div>"""
    return page("Корзина", inner)


def done():
    inner = f"""<div class="scr">
 <div class="sbar"><span>19:47</span><span>⌁ ▮▮▮ ▰</span></div>
 <div class="hd"><span>Заказ оформлен</span></div>
 <div class="body"><div class="done">
   <div class="ok">✓</div>
   <h2>Заказ оформлен</h2>
   <p>Придёт в пункт самовывоза на ул. Немига, 5<br/>ориентировочно 30 октября</p>
   <div class="num">{T['constraints']['order_number_example']}</div>
   <a class="btn" href="prototype-home.html">Вернуться на главную</a>
   <a class="lnk" href="#">Условия возврата и обмена</a>
 </div></div>
 {bottom_nav('cart')}</div>"""
    return page("Заказ оформлен", inner)


def home():
    """Лента с рабочими ссылками на карточку товара."""
    src = (OUT / "mobile-home.html").read_text(encoding="utf-8")
    src = src.replace("<article class=\"card\">", "<a class=\"card\" href=\"prototype-product.html\">")
    src = src.replace("</div></article>", "</div></a>")
    nav = bottom_nav("home")
    src = re.sub(r'<nav class="mbar">.*?</nav>', nav, src, flags=re.S)
    src = src.replace("</style>", PROTO_CSS + "\n</style>")
    return src


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--palette", default="c", choices=["a", "b", "c"])
    PAL = ap.parse_args().palette
    files = {"prototype-login.html": login(), "prototype-home.html": home(),
             "prototype-product.html": product(), "prototype-cart.html": cart(),
             "prototype-done.html": done()}
    for n, c in files.items():
        (OUT / n).write_text(c, encoding="utf-8")
        print(f"  mockups/{n:<28} {len(c)//1024:>3} КБ")
    print(f"\nТочка входа: mockups/prototype-login.html")
