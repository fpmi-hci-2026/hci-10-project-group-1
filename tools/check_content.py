#!/usr/bin/env python3
"""Проверка контента для макетов ЛР№5.

Проверяет research/products.csv, research/product-hero.md и наличие фото
в mockups/img/ до сборки макетов — чтобы не пересобирать их дважды.
Запуск: python3 tools/check_content.py
"""
import csv, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "research" / "products.csv"
HERO = ROOT / "research" / "product-hero.md"
IMG = ROOT / "mockups" / "img"
SUMMARY_MAX = 90          # CHECK-ограничение БД, ЛР№4 п.2.1 / AC-01.2
TITLE_MAX = 45            # переполнение карточки на 360 px
REVIEW_MAX = 140

HERO_FIELDS = ["Бренд", "Название", "Цена", "Размеры в наличии",
               "Состав", "Посадка", "Уход", "Размерная сетка бренда"]

errors: list[str] = []
warnings: list[str] = []
notes: list[str] = []


def check_products() -> None:
    if not PRODUCTS.exists():
        errors.append(f"нет файла {PRODUCTS.relative_to(ROOT)}")
        return
    rows = list(csv.DictReader(PRODUCTS.open(encoding="utf-8")))
    filled = [r for r in rows if (r.get("brand") or "").strip()]
    if len(filled) < 8:
        errors.append(f"products.csv: заполнено {len(filled)} товаров из 8 "
                      f"(не заполнены: {', '.join(r['id'] for r in rows if r not in filled)})")
    seen_titles: dict[str, str] = {}
    for r in filled:
        pid = r["id"]
        s = (r.get("summary") or "").strip()
        if not s:
            errors.append(f"{pid}: пустой summary — он выводится в карточке ленты (AC-01.2)")
        elif len(s) > SUMMARY_MAX:
            errors.append(f"{pid}: summary {len(s)} символов, максимум {SUMMARY_MAX} "
                          f"(CHECK-ограничение БД из ЛР№4). Сократите на {len(s)-SUMMARY_MAX}")
        elif len(s) > SUMMARY_MAX - 5:
            notes.append(f"{pid}: summary {len(s)}/{SUMMARY_MAX} — у предела, это хорошо "
                         f"для демонстрации ограничения")
        t = (r.get("title") or "").strip()
        if len(t) > TITLE_MAX:
            errors.append(f"{pid}: название {len(t)} символов, максимум {TITLE_MAX} — "
                          f"иначе карточка ломается на 360 px")
        if t in seen_titles:
            warnings.append(f"{pid}: название дублирует {seen_titles[t]}")
        seen_titles[t] = pid
        for fld in ("price", "price_old"):
            v = (r.get(fld) or "").strip()
            if v and not re.fullmatch(r"\d+(\.\d{1,2})?", v):
                errors.append(f"{pid}: {fld}='{v}' — ожидается число вида 149.00")
        if (r.get("price_old") or "").strip() and (r.get("price") or "").strip():
            if float(r["price_old"]) <= float(r["price"]):
                warnings.append(f"{pid}: старая цена не больше текущей")
        sizes = (r.get("sizes") or "").strip()
        if not sizes:
            warnings.append(f"{pid}: не указаны размеры")
        elif not re.fullmatch(r"[\w.]+(;[\w.]+)*", sizes):
            errors.append(f"{pid}: размеры '{sizes}' — ожидается перечисление через ';'")
        rating = (r.get("rating") or "").strip()
        if rating and not (re.fullmatch(r"[0-5](\.\d)?", rating)):
            errors.append(f"{pid}: rating='{rating}' — ожидается 0–5 с одним знаком")


def check_hero() -> None:
    if not HERO.exists():
        errors.append(f"нет файла {HERO.relative_to(ROOT)}")
        return
    text = HERO.read_text(encoding="utf-8")
    for fld in HERO_FIELDS:
        m = re.search(rf"^-\s*{re.escape(fld)}\s*:\s*(.*)$", text, re.M)
        if not m:
            errors.append(f"product-hero.md: нет строки «{fld}»")
        elif not m.group(1).strip():
            errors.append(f"product-hero.md: «{fld}» не заполнено "
                          f"(если подблока нет — напишите «нет»)")
        elif m.group(1).strip().lower() == "нет":
            notes.append(f"product-hero.md: «{fld}» = нет → на макете будет "
                         f"«Продавец не указал» (AC-02.2)")
    for m in re.finditer(r"\|\s*Текст:\s*(.+)$", text, re.M):
        if len(m.group(1).strip()) > REVIEW_MAX:
            warnings.append(f"отзыв длиннее {REVIEW_MAX} символов "
                            f"({len(m.group(1).strip())}) — обрежется на макете")


def check_images() -> None:
    need = [f"feed-{i}.jpg" for i in range(1, 9)] + \
           [f"hero-{i}.jpg" for i in range(1, 6)] + ["banner.jpg"]
    present = {f.name.lower() for f in IMG.glob("*") if f.is_file()}
    missing = [n for n in need
               if n not in present and n.replace(".jpg", ".png") not in present]
    if missing:
        warnings.append(f"нет фото ({len(missing)} из {len(need)}): {', '.join(missing)} "
                        f"— на их месте будет нейтральный плейсхолдер")
    try:
        from PIL import Image
    except ImportError:
        Image = None
    if Image is not None:
        for n in need:
            f = IMG / n
            if not f.exists():
                continue
            w, h = Image.open(f).size
            if n.startswith("banner"):
                continue
            if abs(w / h - 0.75) > 0.01:
                warnings.append(f"{n}: соотношение {w/h:.3f} вместо 0.750 — нужно кадрировать")
            if w < 350:
                errors.append(f"{n}: ширина {w} px — карточка в ленте занимает ~306 px, "
                              f"фото будет размытым. Нужен файл крупнее")
            elif w < 600:
                warnings.append(f"{n}: ширина {w} px — хватит при показе макета в 100%, "
                                f"но будет мягко на retina-скриншоте")
    for f in IMG.glob("*"):
        if f.is_file() and f.suffix.lower() in {".jpg",".jpeg",".png"} \
                and f.stat().st_size > 2 * 1024 * 1024:
            warnings.append(f"{f.name}: {f.stat().st_size/1048576:.1f} МБ — больше 2 МБ, сожмите")


def main() -> int:
    check_products()
    check_hero()
    check_images()

    for title, items, sign in (("ОШИБКИ — без этого макеты не собрать", errors, "✗"),
                               ("ПРЕДУПРЕЖДЕНИЯ — собрать можно, но лучше поправить", warnings, "!"),
                               ("ЗАМЕЧАНИЯ", notes, "i")):
        if items:
            print(f"\n{title}:")
            for it in items:
                print(f"  {sign} {it}")

    print()
    if errors:
        print(f"Готовность: НЕ ГОТОВО — {len(errors)} ошибок, {len(warnings)} предупреждений")
        return 1
    print(f"Готовность: ГОТОВО к сборке макетов ({len(warnings)} предупреждений)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
