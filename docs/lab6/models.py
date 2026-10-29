# Расчёт моделей GOMS (KLM) для веб-форм и TLM для мобильных форм.
# Запуск: python3 models.py > models.md
import re

# KLM: Card, Moran, Newell (1980); K — средний непрофессиональный наборщик
KLM = {'K': 0.28, 'P': 1.10, 'B': 0.10, 'H': 0.40, 'M': 1.35}
# TLM: T — касание цели из исходного положения (El Batran, Dunlop, 2014),
# S — короткий свайп (там же); K — касание клавиши экранной клавиатуры, M — как в KLM
TLM = {'T': 0.08, 'S': 0.07, 'K': 0.28, 'M': 1.35}

def total(seq, ops):
    """seq — строка вида 'M P B B H 21K R0.3'"""
    t, counts = 0.0, {}
    for tok in seq.split():
        m = re.fullmatch(r'(\d*)([A-Z])([\d.]*)', tok)
        n, op, val = int(m.group(1) or 1), m.group(2), m.group(3)
        dt = float(val) if op == 'R' else ops[op]
        t += n * dt; counts[op] = counts.get(op, 0) + n
    return t, counts

def fmt(counts):
    return ' + '.join(f'{n}{op}' if n > 1 else op for op, n in counts.items())

WEB = [  # форма, вариант, способ ввода, последовательность
 ('Вход', 'A: почта и пароль', 'мышь', 'M P B B H 21K H  M P B B H 10K H  M P B B'),
 ('Вход', 'A: почта и пароль', 'клавиатура и мышь', 'M P B B H 21K  M K 10K  M K'),
 ('Вход', 'B: телефон и код из SMS', 'мышь', 'M P B B H 9K H  M P B B  R5  M P B B H 4K'),
 ('Вход', 'B: телефон и код из SMS', 'клавиатура и мышь', 'M P B B H 9K  M K  R5  M 4K'),
 ('Ассистент по размеру', 'A: ввод роста и обхвата', 'мышь', 'M P B B  M P B B H 3K H  M P B B H 2K H  M P B B  M P B B'),
 ('Ассистент по размеру', 'A: ввод роста и обхвата', 'клавиатура и мышь', 'M P B B  H 3K K 2K  M K K  M K'),
 ('Ассистент по размеру', 'B: выбор из списков', 'мышь', 'M P B B  M P B B M P B B  M P B B M P B B  M P B B'),
 ('Ассистент по размеру', 'B: выбор из списков', 'клавиатура и мышь', 'M P B B  M 4K K  M 5K K K  M K'),
 ('Оформление заказа', 'A: одна страница', 'мышь', 'M P B B M P B B  M P B B  M P B B'),
 ('Оформление заказа', 'A: одна страница', 'клавиатура и мышь', 'M P B B  M 2K  M K 2K  M K K'),
 ('Оформление заказа', 'B: мастер из трёх шагов', 'мышь', 'M P B B M P B B  M P B B R0.3  M P B B  M P B B R0.3  M P B B'),
 ('Оформление заказа', 'B: мастер из трёх шагов', 'клавиатура и мышь', 'M P B B  M 2K  K K R0.3  M 2K  K K R0.3  M K'),
]
MOB = [
 ('Вход', 'A: почта и пароль', 'M T 21K  T 10K  M T R0.5'),
 ('Вход', 'B: отпечаток пальца', 'M T R1'),
 ('Ассистент по размеру', 'нижняя панель', 'M T R0.3  M T 3K  T 2K  T  M T'),
 ('Оформление заказа', 'корзина и оплата', 'M S  M T  M T R0.5'),
]

print('| Форма | Вариант | Ввод | Операторы | Время, с |\n|---|---|---|---|---|')
for f, v, i, s in WEB:
    t, c = total(s, KLM); print(f'| {f} | {v} | {i} | {fmt(c)} | {t:.2f} |')
print('\n| Форма | Вариант | Операторы | Время, с |\n|---|---|---|---|')
for f, v, s in MOB:
    t, c = total(s, TLM); print(f'| {f} | {v} | {fmt(c)} | {t:.2f} |')
