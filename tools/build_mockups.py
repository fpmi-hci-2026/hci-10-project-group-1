#!/usr/bin/env python3
"""Сборка макетов для исследования визуального языка (ЛР№5, задание 1, п. 7).

Собирает mockups/visual-language.html — веб-главную 1440 px и мобильную карточку
товара 375 px — в трёх цветовых вариантах из design/tokens.json.

Разметка, типографика, сетка, фотографии и тексты ОДИНАКОВЫ во всех вариантах:
переключается только набор CSS-переменных. Это выполняет требование методички
«макеты должны отличаться друг от друга только цветовой гаммой».

Запуск: python3 tools/build_mockups.py
"""
import csv, json, pathlib, re, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
PRODUCTS = list(csv.DictReader((ROOT / "research" / "products.csv").open(encoding="utf-8")))
HERO_MD = (ROOT / "research" / "product-hero.md").read_text(encoding="utf-8")
OUT = ROOT / "mockups" / "visual-language.html"
FONTS_CSS = ROOT / "mockups" / "fonts" / "fonts.css"

def hero(field, default=""):
    m = re.search(rf"^-\s*{re.escape(field)}\s*:\s*(.*)$", HERO_MD, re.M)
    v = m.group(1).strip() if m else default
    return "" if v.lower() == "нет" else v

def e(s): return html.escape(str(s))
def money(v): return f"{float(v):,.2f}".replace(",", " ").replace(".", ",") if v else ""

def fonts_css():
    """Локальные шрифты; если не скачаны — подключение с Google Fonts (нужен интернет)."""
    if FONTS_CSS.exists():
        return FONTS_CSS.read_text(encoding="utf-8")
    return ("@import url('https://fonts.googleapis.com/css2?"
            "family=Inter:wght@400;600;700&family=Manrope:wght@800&display=swap');")


# ── CSS-переменные всех шести режимов ────────────────────────────────────────
def css_vars():
    out = []
    for pid, pal in T["palettes"].items():
        for mode in ("light", "dark"):
            decls = " ".join(f"--{k}:{v};" for k, v in pal[mode].items())
            st = []
            for sid, s in T["status"].items():
                if sid.startswith("$"): continue
                st.append(f"--st-{sid}-bg:var(--{s['bg']});--st-{sid}-fg:var(--{s['fg']});")
            out.append(f'html[data-palette="{pid}"][data-mode="{mode}"]{{{decls}{"".join(st)}}}')
    return "\n".join(out)

CSS = r"""
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
body{font-family:Inter,-apple-system,'Segoe UI',Roboto,sans-serif;background:#8a8a8a;
     color:var(--text);font-size:16px;line-height:1.5}
img{display:block;max-width:100%}
.logo{font-family:Manrope,Inter,sans-serif;font-weight:800;letter-spacing:-.02em}

/* ── служебная панель: скрыта, когда в адресе есть ?theme= ── */
#bar{position:fixed;inset:0 0 auto 0;z-index:99;display:flex;gap:16px;align-items:center;
     padding:10px 18px;background:#14171c;color:#fff;font-size:13px}
#bar a,#bar button{font:inherit;color:#fff;background:#2a2f38;border:1px solid #3c434e;
     border-radius:7px;padding:6px 12px;cursor:pointer;text-decoration:none}
#bar a.on{background:#fff;color:#14171c;border-color:#fff;font-weight:600}
#bar .sp{flex:1}
body.clean #bar{display:none}
.stage{padding:64px 0 48px}
body.clean .stage{padding:0}
.cap{max-width:1440px;margin:0 auto 10px;padding:0 20px;color:#f2f2f2;font-size:13px;letter-spacing:.02em}
body.clean .cap{display:none}

/* ── рамки макетов ── */
.frame{background:var(--bg);color:var(--text);overflow:hidden}
.webwrap{width:1440px;transform-origin:top left}
.webouter{margin:0 auto 56px;overflow:hidden}
.mobouter{display:flex;justify-content:center;padding-bottom:40px}
.mob{width:375px;border-radius:0;box-shadow:0 18px 50px rgba(0,0,0,.35)}

/* ── ВЕБ-ГЛАВНАЯ ── */
.topbar{background:var(--brand);color:var(--on-brand)}
.row{max-width:1440px;margin:0 auto;padding:0 60px}
.topbar .row{display:flex;align-items:center;gap:32px;height:72px}
.topbar .logo{font-size:23px;color:var(--on-brand)}
.topbar .logo i{font-style:normal;color:var(--accent-soft)}
.search{flex:1;display:flex;align-items:center;gap:10px;background:var(--surface);
        border-radius:10px;height:44px;padding:0 14px;color:var(--text-muted);font-size:15px}
.search .sb{margin-left:auto;background:var(--accent);color:var(--on-accent);
        border-radius:7px;padding:7px 16px;font-size:14px;font-weight:600}
.util{display:flex;gap:26px;font-size:13px;color:var(--on-brand);opacity:.95}
.util div{display:flex;flex-direction:column;align-items:center;gap:3px}
.util b{font-size:17px;font-weight:400;line-height:1}
.util .cnt{position:relative}
.util .cnt em{position:absolute;top:-5px;right:-11px;background:var(--accent);
        color:var(--on-accent);font-style:normal;font-size:10px;font-weight:700;
        border-radius:9px;padding:1px 5px}
.cats{background:var(--surface);border-bottom:1px solid var(--border)}
.cats .row{display:flex;align-items:center;gap:28px;height:52px;font-size:15px}
.cats a{color:var(--text);text-decoration:none}
.cats a.g{font-weight:600}
.cats .sep{width:1px;height:20px;background:var(--border);flex:none}
.cats .bel{margin-left:auto;background:var(--accent-soft);color:var(--on-accent-soft);
        font-size:13px;font-weight:600;border-radius:999px;padding:6px 14px}

.hero{max-width:1440px;margin:32px auto 0;padding:0 60px}
.hero .in{position:relative;border-radius:16px;overflow:hidden;height:273px;background:var(--surface-alt)}
.hero img{width:100%;height:100%;object-fit:cover}
.hero .ov{position:absolute;inset:0;display:flex;align-items:center;
        background:linear-gradient(90deg,var(--brand) 0%,transparent 62%)}
.hero .tx{padding:0 48px;max-width:560px;color:var(--on-brand)}
.hero h2{font-size:30px;line-height:1.2;font-weight:700;letter-spacing:-.01em}
.hero p{margin:10px 0 18px;font-size:15px;opacity:.9}
.btn{display:inline-block;background:var(--accent);color:var(--on-accent);
     border-radius:9px;padding:12px 22px;font-size:15px;font-weight:600}

.sec{max-width:1440px;margin:44px auto 0;padding:0 60px}
.sec h3{font-size:24px;font-weight:700;letter-spacing:-.01em}
.sec .sub{color:var(--text-muted);font-size:15px;margin-top:6px}
.grid{display:grid;grid-template-columns:repeat(4,312px);gap:24px;margin-top:22px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;
      overflow:hidden;display:flex;flex-direction:column}
.ph{position:relative;aspect-ratio:3/4;background:var(--surface-alt)}
.ph img{width:100%;height:100%;object-fit:cover}
.bdg{position:absolute;left:12px;top:12px;font-size:12px;font-weight:600;
     border-radius:999px;padding:5px 11px;background:var(--accent-soft);color:var(--on-accent-soft)}
.bdg.fit{background:var(--warning-soft);color:var(--warning)}
.fav{position:absolute;right:12px;top:12px;width:34px;height:34px;border-radius:50%;
     background:var(--surface);display:flex;align-items:center;justify-content:center;
     font-size:15px;color:var(--text-muted)}
.cb{padding:14px 16px 16px;display:flex;flex-direction:column;gap:7px;flex:1}
.br{font-size:12px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--text-muted)}
.ti{font-size:16px;font-weight:600;line-height:1.3}
.sm{font-size:13px;line-height:1.45;color:var(--text-muted)}
.rt{font-size:13px;color:var(--text-muted);display:flex;align-items:center;gap:5px}
.rt b{color:var(--text);font-weight:600}
.pr{margin-top:auto;padding-top:8px;display:flex;align-items:baseline;gap:9px}
.pr .now{font-size:20px;font-weight:700}
.pr .old{font-size:14px;color:var(--text-muted);text-decoration:line-through}
.cart{margin-top:10px;background:var(--accent);color:var(--on-accent);border-radius:9px;
      padding:11px 0;text-align:center;font-size:14px;font-weight:600}
.foot{margin-top:52px;background:var(--surface-alt);border-top:1px solid var(--border)}
.foot .row{display:flex;gap:40px;padding-top:26px;padding-bottom:26px;
      font-size:13px;color:var(--text-muted)}
.foot .logo{font-size:16px;color:var(--text)}

/* ── МОБИЛЬНАЯ КАРТОЧКА ── */
.sbar{height:26px;background:var(--surface);display:flex;align-items:center;
      justify-content:space-between;padding:0 16px;font-size:11px;font-weight:600;color:var(--text)}
.mhead{height:46px;background:var(--surface);border-bottom:1px solid var(--border);
      display:flex;align-items:center;gap:12px;padding:0 14px;font-size:15px;font-weight:600}
.mhead .ic{color:var(--text-muted);font-size:17px;font-weight:400}
.mhead .sp{flex:1}
.gal{position:relative;height:300px;background:var(--surface-alt)}
.gal img{width:100%;height:100%;object-fit:cover}
.dots{position:absolute;left:0;right:0;bottom:12px;display:flex;justify-content:center;gap:6px}
.dots i{width:6px;height:6px;border-radius:50%;background:var(--surface);opacity:.5}
.dots i.on{opacity:1;width:18px;border-radius:3px}
.mbody{background:var(--bg);padding:14px 16px 0}
.mbr{font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--text-muted)}
.mti{font-size:19px;font-weight:700;line-height:1.25;margin-top:3px;letter-spacing:-.01em}
.mpr{display:flex;align-items:baseline;gap:10px;margin-top:9px}
.mpr .now{font-size:24px;font-weight:700}
.mpr .old{font-size:15px;color:var(--text-muted);text-decoration:line-through}
.mrt{display:flex;align-items:center;gap:8px;margin-top:9px;font-size:13px;color:var(--text-muted)}
.mrt b{color:var(--text)}
.fitchip{background:var(--warning-soft);color:var(--warning);font-size:12px;font-weight:600;
      border-radius:999px;padding:4px 10px}
.asis{margin-top:13px;background:var(--accent-soft);border-radius:12px;padding:13px 14px}
.asis .h{font-size:14px;font-weight:700;color:var(--on-accent-soft);display:flex;gap:7px;align-items:center}
.asis p{font-size:13px;line-height:1.45;color:var(--on-accent-soft);margin-top:5px;opacity:.92}
.asis .b{margin-top:10px;display:inline-block;background:var(--accent);color:var(--on-accent);
      border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600}
.dsc{margin-top:16px}
.dsc h4{font-size:16px;font-weight:700}
.dl{margin-top:9px;background:var(--surface);border:1px solid var(--border);border-radius:12px;
      padding:4px 14px}
.dl .it{padding:10px 0;border-bottom:1px solid var(--border)}
.dl .it:last-child{border-bottom:0}
.dl .k{font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--text-muted)}
.dl .v{font-size:14px;line-height:1.45;margin-top:3px}
.dl .v.na{color:var(--text-muted);font-style:italic}
.szs{margin-top:16px}
.szs .h{font-size:13px;font-weight:600;display:flex;justify-content:space-between;align-items:center}
.szs .h span{color:var(--text-muted);font-weight:400}
.szl{display:flex;gap:8px;margin-top:9px;flex-wrap:wrap}
.szl b{font-size:14px;font-weight:600;min-width:46px;text-align:center;padding:10px 0;
      border:1px solid var(--border-strong);border-radius:9px;background:var(--surface)}
.szl b.on{background:var(--brand);color:var(--on-brand);border-color:var(--brand)}
.szl b.off{color:var(--text-muted);opacity:.45;text-decoration:line-through;border-style:dashed}
.mcta{margin:18px 0 0;display:flex;gap:10px;padding-bottom:16px}
.mcta .a{flex:1;background:var(--accent);color:var(--on-accent);border-radius:11px;
      padding:15px 0;text-align:center;font-size:16px;font-weight:700}
.mcta .f{width:54px;border:1px solid var(--border-strong);border-radius:11px;background:var(--surface);
      display:flex;align-items:center;justify-content:center;font-size:19px;color:var(--text-muted)}
.mnav{background:var(--surface);border-top:1px solid var(--border);display:flex;
      padding:9px 0 14px}
.mnav div{flex:1;text-align:center;font-size:10px;color:var(--text-muted)}
.mnav div b{display:block;font-size:17px;font-weight:400;margin-bottom:3px}
.mnav div.on{color:var(--brand)}
"""

def card(p, idx):
    badge = ""
    if p["badge"]:
        cls = "bdg fit" if "Маломерит" in p["badge"] else "bdg"
        badge = f'<span class="{cls}">{e(p["badge"])}</span>'
    old = f'<span class="old">{money(p["price_old"])} р.</span>' if p["price_old"] else ""
    return f"""<article class="card">
      <div class="ph"><img src="img/{p['id']}.jpg" alt=""/>{badge}<span class="fav">♡</span></div>
      <div class="cb">
        <div class="br">{e(p['brand'])}</div>
        <div class="ti">{e(p['title'])}</div>
        <div class="sm">{e(p['summary'])}</div>
        <div class="rt">★ <b>{e(p['rating'])}</b> · {e(p['reviews'])} отзывов</div>
        <div class="pr"><span class="now">{money(p['price'])} р.</span>{old}</div>
        <div class="cart">В корзину</div>
      </div></article>"""

def web_page():
    cards = "\n".join(card(p, i) for i, p in enumerate(PRODUCTS))
    return f"""<div class="frame">
  <header class="topbar"><div class="row">
    <div class="logo">МаркетШоп<i>.by</i></div>
    <div class="search">⌕ Платье, кроссовки, бренд…<span class="sb">Найти</span></div>
    <nav class="util">
      <div><b>♡</b>Избранное</div>
      <div class="cnt"><b>⌂</b>Корзина<em>3</em></div>
      <div><b>☺</b>Профиль</div>
    </nav>
  </div></header>
  <nav class="cats"><div class="row">
    <a class="g">Каталог</a><a class="g">Рекомендации</a>
    <span class="sep"></span>
    <a>Женщинам</a><a>Мужчинам</a><a>Детям</a><a>Обувь</a><a>Распродажа</a>
    <span class="bel">Сделано в Беларуси</span>
  </div></nav>
  <section class="hero"><div class="in">
    <img src="img/banner.jpg" alt=""/>
    <div class="ov"><div class="tx">
      <h2>Осенние образы<br/>локальных брендов</h2>
      <p>Описания собраны из характеристик товара и проверены продавцом</p>
      <span class="btn">Смотреть подборку</span>
    </div></div>
  </div></section>
  <section class="sec">
    <h3>Специально для вас</h3>
    <div class="sub">Подобрано по вашему размеру, любимым категориям и сезону</div>
    <div class="grid">{cards}</div>
  </section>
  <footer class="foot"><div class="row">
    <div class="logo">МаркетШоп.by</div>
    <span>О сервисе</span><span>Продавцам</span><span>Доставка и оплата</span>
    <span>Возврат и обмен</span><span>Помощь</span>
  </div></footer>
</div>"""

def mobile_page():
    hp = next(p for p in PRODUCTS if p["id"] == "feed-4")
    sizes_in = [s.strip() for s in hero("Размеры в наличии").split(";") if s.strip()]
    sizes_out = [s.strip() for s in hero("Размеры закончились").split(";") if s.strip()]
    sz = "".join(f'<b class="{"on" if i==1 else ""}">{e(s)}</b>' for i, s in enumerate(sizes_in))
    sz += "".join(f'<b class="off">{e(s)}</b>' for s in sizes_out)
    blocks = [("Состав", hero("Состав")), ("Посадка", hero("Посадка")),
              ("Уход", hero("Уход")), ("Размерная сетка бренда", hero("Размерная сетка бренда"))]
    items = "".join(
        f'<div class="it"><div class="k">{e(k)}</div>'
        f'<div class="v{"" if v else " na"}">{e(v) if v else "Продавец не указал"}</div></div>'
        for k, v in blocks)
    small = hero("Маломерит")
    return f"""<div class="frame mob">
  <div class="sbar"><span>19:42</span><span>⌁ ▮▮▮ ▰</span></div>
  <div class="mhead"><span class="ic">‹</span><span>Карточка товара</span>
       <span class="sp"></span><span class="ic">♡</span><span class="ic">⇪</span></div>
  <div class="gal"><img src="img/hero-1.jpg" alt=""/>
       <div class="dots"><i class="on"></i><i></i><i></i><i></i><i></i></div></div>
  <div class="mbody">
    <div class="mbr">{e(hero('Бренд'))}</div>
    <div class="mti">{e(hero('Название'))}</div>
    <div class="mpr"><span class="now">{money(hp['price'])} р.</span></div>
    <div class="mrt">★ <b>{e(hero('Оценка'))}</b> · {e(hero('Число отзывов'))} отзывов
         <span class="fitchip">Маломерит · {e(small)}</span></div>
    <div class="asis">
      <div class="h">⇲ Ассистент по размеру</div>
      <p>{e(hero('Размерная сетка бренда'))}</p>
      <span class="b">Подобрать размер</span>
    </div>
    <div class="dsc"><h4>Описание</h4><div class="dl">{items}</div></div>
    <div class="szs"><div class="h">Размер <span>Таблица размеров</span></div>
         <div class="szl">{sz}</div></div>
    <div class="mcta"><div class="a">В корзину</div><div class="f">♡</div></div>
  </div>
  <nav class="mnav">
    <div class="on"><b>⌂</b>Главная</div><div><b>⌕</b>Поиск</div>
    <div><b>♡</b>Избранное</div><div><b>▤</b>Корзина</div><div><b>☺</b>Профиль</div>
  </nav>
</div>"""

JS = r"""
const q=new URLSearchParams(location.search);
const pal=(q.get('theme')||'a').toLowerCase();
const mode=(q.get('mode')||'light').toLowerCase();
document.documentElement.dataset.palette=['a','b','c'].includes(pal)?pal:'a';
document.documentElement.dataset.mode=mode==='dark'?'dark':'light';
if(q.has('theme'))document.body.classList.add('clean');
document.querySelectorAll('#bar a').forEach(a=>{
  if(a.dataset.t===pal)a.classList.add('on');});
function fit(){
  const o=document.querySelector('.webouter'),w=document.querySelector('.webwrap');
  if(!o||!w)return;
  const s=Math.min(1,(o.clientWidth)/1440);
  w.style.transform='scale('+s+')';
  o.style.height=(w.getBoundingClientRect().height)+'px';
}
addEventListener('resize',fit);addEventListener('load',fit);fit();
"""

HTML = f"""<!doctype html>
<html lang="ru" data-palette="a" data-mode="light">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>МаркетШоп.by — исследование визуального языка</title>
<style>
{fonts_css()}
{css_vars()}
{CSS}
</style>
</head>
<body>
<div id="bar">
  <span>Вариант палитры:</span>
  <a href="?theme=a" data-t="a">A · Доверие</a>
  <a href="?theme=b" data-t="b">B · Технологичный</a>
  <a href="?theme=c" data-t="c">C · Тёплый локальный</a>
  <span class="sp"></span>
  <a href="?theme=a&amp;mode=dark">Тёмная тема</a>
  <span style="opacity:.6">служебная панель — у респондента не показывается</span>
</div>
<div class="stage">
  <div class="cap">Веб-приложение, главная страница, 1440 px</div>
  <div class="webouter"><div class="webwrap">{web_page()}</div></div>
  <div class="cap">Мобильное приложение, карточка товара, 375 px</div>
  <div class="mobouter">{mobile_page()}</div>
</div>
<script>{JS}</script>
</body>
</html>
"""

OUT.write_text(HTML, encoding="utf-8")
print(f"собрано: {OUT.relative_to(ROOT)}  ({len(HTML)//1024} КБ)")
print(f"товаров в ленте: {len(PRODUCTS)} | подблоков описания: 4 | режимов палитры: 6")
print("\nпредъявлять респондентам:")
for p in "abc":
    print(f"  вариант {p.upper()}: visual-language.html?theme={p}")
