#!/usr/bin/env python3
"""Генерирует Google Apps Script, создающий анкету исследования визуального языка.

45 шкал руками в Google Forms — час работы и высокий риск опечатки в заголовке,
по которому скрипт обработки ищет столбцы. Этот файл создаёт форму целиком.

Запуск: python3 tools/gen_forms_script.py
Дальше: script.google.com → новый проект → вставить research/forms-apps-script.gs → Run
"""
import csv, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAIRS = list(csv.DictReader((ROOT / "research" / "adjectives.csv").open(encoding="utf-8")))
OUT = ROOT / "research" / "forms-apps-script.gs"

DEMO = [
    ("Ваш возраст", ["18–24", "25–34", "35–44", "45–55", "старше 55"]),
    ("Пол", ["женский", "мужской", "не хочу указывать"]),
    ("Как часто покупаете одежду или обувь онлайн?",
     ["чаще раза в месяц", "раз в 1–3 месяца", "реже", "не покупаю"]),
    ("С какого устройства чаще покупаете?", ["смартфон", "компьютер", "планшет"]),
    ("Продаёте ли вы одежду или обувь онлайн?",
     ["нет", "да, как ИП или небольшой бренд", "да, как сотрудник магазина"]),
]

INTRO = (
    "Мы проектируем приложение для покупки одежды и обуви и хотим понять, "
    "какое впечатление производит его оформление.\n\n"
    "Вам покажут три варианта оформления одного и того же экрана. Нас интересует "
    "только первое впечатление от внешнего вида — не удобство, не функции и не "
    "конкретные товары. Правильных ответов нет.\n\n"
    "Заполнение занимает около 10 минут. Ответы анонимны и используются только "
    "в учебной работе."
)
BLOCK_HELP = ("Посмотрите макет 20–30 секунд, затем оцените его по шкалам ниже. "
              "1 — ближе к левому слову, 5 — ближе к правому. "
              "Оценивайте только оформление.")

scales = [(p["right_pole_1"], p["left_pole_5"]) for p in PAIRS]

js = f"""/**
 * МаркетШоп.by — ЛР№5, задание 1.
 * Создаёт анкету исследования визуального языка: 3 блока по 15 шкал
 * семантического дифференциала + демография + контрольный вопрос.
 *
 * Как запустить:
 *   1. script.google.com → «Новый проект»
 *   2. вставить весь этот файл, заменив содержимое Code.gs
 *   3. Run → разрешить доступ к Google Forms
 *   4. ссылки на форму появятся в «Журнал выполнения» (Ctrl+Enter)
 *
 * Сгенерирован tools/gen_forms_script.py из research/adjectives.csv —
 * заголовки вопросов гарантированно совпадают с тем, что ищет
 * tools/gen_visual_report.py при обработке выгрузки.
 */

var SCALES = {json.dumps(scales, ensure_ascii=False, indent=2)};

var DEMO = {json.dumps(DEMO, ensure_ascii=False, indent=2)};

function createForm() {{
  var form = FormApp.create('Оценка дизайна приложения МаркетШоп.by');
  form.setDescription({json.dumps(INTRO, ensure_ascii=False)});
  form.setCollectEmail(false);
  form.setProgressBar(true);

  // ── код ротации ──
  form.addPageBreakItem()
      .setTitle('Код ротации')
      .setHelpText('Этот код назовёт ведущий. Он задаёт порядок показа макетов.');
  form.addTextItem()
      .setTitle('Код ротации (назовёт ведущий)')
      .setRequired(true)
      .setValidation(FormApp.createTextValidation()
          .requireTextMatchesPattern('^(ABC|BCA|CAB)$')
          .setHelpText('Допустимые значения: ABC, BCA или CAB')
          .build());

  // ── демография ──
  form.addPageBreakItem().setTitle('О вас');
  DEMO.forEach(function (d) {{
    form.addMultipleChoiceItem()
        .setTitle(d[0])
        .setChoiceValues(d[1])
        .setRequired(true);
  }});

  // ── три блока по 15 шкал ──
  for (var b = 1; b <= 3; b++) {{
    form.addPageBreakItem().setTitle('Макет ' + b).setHelpText({json.dumps(BLOCK_HELP, ensure_ascii=False)});
    SCALES.forEach(function (s) {{
      form.addScaleItem()
          .setTitle(s[0] + ' — ' + s[1])
          .setBounds(1, 5)
          .setLabels(s[0], s[1])
          .setRequired(true);
    }});
    form.addTextItem()
        .setTitle('Какое одно слово первым приходит в голову, когда вы смотрите на этот макет?')
        .setRequired(false);
  }}

  // ── контрольный вопрос ──
  form.addPageBreakItem().setTitle('Итог');
  form.addMultipleChoiceItem()
      .setTitle('Если бы вы выбирали приложение для покупки одежды, какой макет выбрали бы?')
      .setChoiceValues(['Макет 1', 'Макет 2', 'Макет 3'])
      .setRequired(true);
  form.addParagraphTextItem().setTitle('Почему?').setRequired(false);

  Logger.log('Ссылка для респондентов: ' + form.getPublishedUrl());
  Logger.log('Ссылка для редактирования: ' + form.getEditUrl());
  Logger.log('Вопросов создано: ' + form.getItems().length);
}}

/**
 * Печатает ссылки с уже подставленным кодом ротации — по одной на каждый порядок.
 * Запускать ПОСЛЕ createForm(). Вставить ID формы из ссылки для редактирования:
 * docs.google.com/forms/d/<ЭТО_ID>/edit
 */
function makePrefilledLinks() {{
  var FORM_ID = 'ВСТАВЬТЕ_ID_ФОРМЫ';
  var form = FormApp.openById(FORM_ID);
  var items = form.getItems(FormApp.ItemType.TEXT);
  var rot = null;
  for (var i = 0; i < items.length; i++) {{
    if (items[i].getTitle().indexOf('ротаци') >= 0) {{ rot = items[i].asTextItem(); break; }}
  }}
  if (!rot) {{ Logger.log('Не найден вопрос с кодом ротации'); return; }}

  Logger.log('Встраиваемая форма: ' + form.getPublishedUrl() + '&embedded=true');
  ['ABC', 'BCA', 'CAB'].forEach(function (code) {{
    var resp = form.createResponse();
    resp.withItemResponse(rot.createResponse(code));
    Logger.log(code + ': ' + resp.toPrefilledUrl());
  }});
  Logger.log('entry id кода ротации: ' + rot.getId());
}}
"""
OUT.write_text(js, encoding="utf-8")
print(f"записано: {OUT.relative_to(ROOT)}")
print(f"шкал: {len(scales)} × 3 блока = {len(scales)*3} + демография {len(DEMO)} "
      f"+ ротация 1 + открытых 3 + итог 2 = {len(scales)*3 + len(DEMO) + 6} вопросов")
