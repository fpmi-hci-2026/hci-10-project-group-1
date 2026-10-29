# Обработка результатов сессий: data/*.csv → таблицы Markdown.
# Запуск: python3 metrics.py > results.md
import csv, math, statistics as st, sys, os
from collections import defaultdict

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
def rows(name): return list(csv.DictReader(open(os.path.join(D, name), encoding='utf-8')))

def wald(x, n, z=1.96):
    """Скорректированный интервал Вальда (Agresti–Coull) для доли успеха."""
    p = (x + z * z / 2) / (n + z * z); h = z * math.sqrt(p * (1 - p) / (n + z * z))
    return max(0, p - h), min(1, p + h)

def sus(r):
    q = [int(r[f'q{i}']) for i in range(1, 11)]
    return 2.5 * sum((v - 1) if i % 2 == 0 else (5 - v) for i, v in enumerate(q))

out = []
S = rows('sessions.csv')
if S:
    out.append('| Платформа | Задание | Успех | 95% ДИ | Время, с (медиана) | Ошибки (среднее) |\n|---|---|---|---|---|---|')
    g = defaultdict(list)
    for r in S: g[(r['platform'], r['task'])].append(r)
    for (pl, t), rs in sorted(g.items()):
        x, n = sum(int(r['success']) for r in rs), len(rs); lo, hi = wald(x, n)
        tm = [float(r['time_s']) for r in rs if r['success'] == '1']
        out.append(f"| {pl} | {t} | {x}/{n} ({x/n:.0%}) | {lo:.0%}–{hi:.0%} | {st.median(tm):.0f} | {st.mean(int(r['errors']) for r in rs):.1f} |" if tm else
                   f"| {pl} | {t} | {x}/{n} | {lo:.0%}–{hi:.0%} | — | {st.mean(int(r['errors']) for r in rs):.1f} |")
    # критерий: контрольное прохождение T2→T5 (строки CTRL) за 180 с не менее чем у 75% участников
    for pl in sorted({r['platform'] for r in S}):
        c = [r for r in S if r['platform'] == pl and r['task'] == 'CTRL']
        if c:
            ok = sum(1 for r in c if r['success'] == '1' and float(r['time_s']) <= 180)
            out.append(f"\nКонтрольное задание, {pl}: {ok} из {len(c)} ({ok/len(c):.0%}) за 180 с — критерий {'выполнен' if ok/len(c) >= .75 else 'не выполнен'}.")
U = rows('sus.csv')
if U:
    out.append('\n| Платформа | Участников | SUS, среднее | Мин. | Макс. |\n|---|---|---|---|---|')
    for pl in sorted({r['platform'] for r in U}):
        s = [sus(r) for r in U if r['platform'] == pl]
        out.append(f'| {pl} | {len(s)} | {st.mean(s):.1f} | {min(s):.1f} | {max(s):.1f} |')
for name, col, title in (('cardsort.csv', 'question', 'Вопрос'), ('expectations.csv', 'element', 'Элемент')):
    R = rows(name)
    if not R: continue
    key = 'hit' if name == 'cardsort.csv' else 'matches'
    out.append(f'\n| Платформа | {title} | Совпадений |\n|---|---|---|')
    g = defaultdict(list)
    for r in R: g[(r['platform'], r[col])].append(r[key] == '1')
    for (pl, k), v in sorted(g.items()):
        out.append(f'| {pl} | {k} | {sum(v)}/{len(v)} ({sum(v)/len(v):.0%}) |')
J = rows('treejack_raw.csv')
if J:
    out.append('\n| Платформа | Задание | Участников | Успех | Прямота | Время, с (медиана) |\n|---|---|---|---|---|---|')
    g = defaultdict(list)
    for r in J: g[(r['platform'], r['task'])].append(r)
    for (pl, t), rs in sorted(g.items()):
        n = len(rs); s_ = sum(int(r['success']) for r in rs); d = sum(int(r['direct']) for r in rs)
        out.append(f"| {pl} | {t} | {n} | {s_/n:.0%} | {d/n:.0%} | {st.median(float(r['time_s']) for r in rs):.0f} |")
print('\n'.join(out) if out else 'Данных пока нет: заполните файлы в data/.')
