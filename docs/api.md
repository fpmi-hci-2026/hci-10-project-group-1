---
title: "API проекта"
description: "REST API /api/v1 и доменные события Kafka"
---

> **Статус: спроектирован, не реализован.** Контракт выведен из
> [диаграмм последовательности ЛР№3](lab3/README.md#47-диаграммы-последовательности)
> и требований к внешним интерфейсам
> [технического задания](lab3/README.md#5-требования-к-внешним-интерфейсам).
> Разработка не начиналась; форматы ответов уточняются при реализации.

REST API поверх HTTPS, формат обмена — JSON. Базовый путь: `/api/v1`.

---

## Общие соглашения

| Аспект | Решение |
|--------|---------|
| Аутентификация | `Authorization: Bearer <access_token>`; токен выдаёт сервис аутентификации |
| Формат ошибок | `{ "code": "...", "message": "...", "details": { ... } }` |
| Язык сообщений | Русский; сообщения не содержат внутренних кодов статусов и терминов генерации |
| Идемпотентность | Для создающих запросов — заголовок `Idempotency-Key`; повтор с тем же ключом возвращает исходный результат |
| Пагинация | Параметры `page` (с 0) и `size` (по умолчанию 20, максимум 100) |
| Версионирование | Версия в пути: `/api/v1` |
| Ограничение частоты | Заголовки `X-RateLimit-Limit`, `X-RateLimit-Remaining` |

### Коды ответов

| Код | Когда возвращается |
|-----|--------------------|
| `200 OK` | Успешное чтение или изменение |
| `201 Created` | Создан ресурс; `Location` указывает на него |
| `204 No Content` | Изменение без тела ответа |
| `401 Unauthorized` | Токен отсутствует или недействителен |
| `403 Forbidden` | Роль не позволяет выполнить операцию |
| `404 Not Found` | Ресурс не найден или недоступен текущей роли |
| `409 Conflict` | Нехватка остатка; задача модерации уже захвачена |
| `422 Unprocessable Entity` | Неполные атрибуты товара; истёкший срок возврата |
| `429 Too Many Requests` | Превышено ограничение частоты запросов |

---

## 1. Витрина покупателя

### Лента рекомендаций

```http
GET /api/v1/feed?page=0&size=20
Authorization: Bearer <token>        # необязательно
```

```json
{
  "blocks": [
    {
      "kind": "СПЕЦИАЛЬНО_ДЛЯ_ВАС",
      "criteria": "размер S + вискоза + лето",
      "items": [
        {
          "productId": "a3f1…",
          "title": "Платье летнее «Мадрид»",
          "price": 89.00,
          "currency": "BYN",
          "summary": "Лёгкая вискоза, не просвечивает, посадка по фигуре",
          "madeInBelarus": true,
          "photoUrl": "https://cdn…/p/a3f1/main.webp"
        }
      ]
    }
  ],
  "hint": null
}
```

Если персонализирующих данных недостаточно, поле `hint` содержит
`{"type": "ASK_SIZE_PARAMS", "text": "Расскажите о своих размерах"}`, а блоки заполняются
популярными товарами региона (ФТ-1.5).

### Каталог и поиск

```http
GET /api/v1/products?category=platya&size=S&brand=Conte&priceMin=40&priceMax=120
                    &madeInBelarus=true&inStock=true&sort=relevance&page=0&size=20
GET /api/v1/search?q=платье+летнее&page=0&size=20
GET /api/v1/search/suggest?q=плать
POST /api/v1/search/by-photo          # multipart/form-data: image
GET /api/v1/search/by-barcode/{code}
```

### Карточка товара

```http
GET /api/v1/products/{productId}
```

```json
{
  "productId": "a3f1…",
  "title": "Платье летнее «Мадрид»",
  "price": 89.00,
  "brand": { "name": "Conte", "madeInBelarus": true },
  "variants": [ { "variantId": "b7…", "size": "S", "color": "бежевый", "inStock": true } ],
  "description": {
    "composition": "вискоза 95%, эластан 5%",
    "fit": "посадка по фигуре, не просвечивает",
    "care": "ручная стирка при 30 °C",
    "sizeChart": "соответствует размерной сетке бренда"
  },
  "returnPolicy": { "periodDays": 14, "forbidden": false },
  "reviewsSummary": { "count": 42, "rating": 4.6, "fit": "МАЛОМЕРИТ" }
}
```

Отсутствующий подблок описания возвращается значением `null`; интерфейс показывает
«Продавец не указал» (ФТ-3.3).

### Ассистент по размеру

```http
GET /api/v1/products/{productId}/size-advice
PUT /api/v1/profile/size-params
```

```json
// 200 OK — рекомендация сформирована
{
  "recommendedSize": "39",
  "explanation": "эта модель маломерит на полразмера",
  "deviation": -0.5,
  "inStock": false,
  "nearestAvailableSize": "40",
  "note": "Рекомендованного размера 39 нет в наличии"
}

// 200 OK — нужны параметры покупателя
{ "needParams": true, "fields": ["height_cm", "chest_cm", "foot_length_cm"] }

// 200 OK — данных о посадке недостаточно
{ "enoughData": false, "message": "Данных о посадке пока недостаточно" }
```

### Избранное и корзина

```http
GET    /api/v1/favorites
POST   /api/v1/favorites            { "productId": "a3f1…" }
DELETE /api/v1/favorites/{productId}

GET    /api/v1/cart
POST   /api/v1/cart/items           { "variantId": "b7…", "quantity": 1 }
DELETE /api/v1/cart/items/{itemId}
```

### Заказ и оплата

```http
GET  /api/v1/checkout
POST /api/v1/orders
Idempotency-Key: 2f8c…
```

```json
// Запрос
{
  "deliveryMethod": "ПУНКТ_САМОВЫВОЗА",
  "pickupPointId": "c1…",
  "paymentMethod": "КАРТА_ОНЛАЙН"
}

// 201 Created
{
  "orderId": "d4…",
  "number": "10482",
  "status": "СОЗДАН",
  "total": 89.00,
  "returnDueDate": "2026-10-23",
  "paymentUrl": "https://psp…/pay/xyz",
  "trackingCode": null
}

// 409 Conflict — нехватка остатка
{ "code": "OUT_OF_STOCK", "message": "Товар закончился", "details": { "variantId": "b7…" } }
```

```http
GET  /api/v1/orders
GET  /api/v1/orders/{orderId}
POST /api/v1/payments/webhook        # вызывается платёжным шлюзом
```

### Возврат и обмен

```http
GET  /api/v1/orders/{orderId}/return-options
POST /api/v1/returns
GET  /api/v1/returns/{requestId}
```

```json
// GET return-options — 200 OK
{
  "available": true,
  "dueDate": "2026-10-23",
  "reasons": [
    { "code": "НЕ_ПОДОШЁЛ_РАЗМЕР", "photoRequired": false },
    { "code": "НЕ_СООТВЕТСТВУЕТ_ОПИСАНИЮ", "photoRequired": true },
    { "code": "БРАК", "photoRequired": true },
    { "code": "ПЕРЕДУМАЛ", "photoRequired": false }
  ]
}

// GET return-options — 422 Unprocessable Entity (ФТ-6.7)
{
  "code": "RETURN_PERIOD_EXPIRED",
  "message": "Срок возврата истёк 23 октября 2026 года",
  "details": { "dueDate": "2026-10-23", "rulesUrl": "/help/return-policy" }
}
```

```json
// POST /api/v1/returns — 201 Created
{
  "requestId": "e5…",
  "status": "СОЗДАНА",
  "pickupPoint": { "address": "Минск, пр. Независимости, 58" },
  "handOverDue": "2026-10-30"
}
```

### Отзывы

```http
GET  /api/v1/products/{productId}/reviews?page=0&size=20
POST /api/v1/products/{productId}/reviews
```

```json
{ "rating": 5, "body": "Отличное платье", "fitRating": "МАЛОМЕРИТ", "photoUrls": [] }
```

---

## 2. Кабинет продавца

```http
GET    /api/v1/seller/products?status=НА_МОДЕРАЦИИ&page=0&size=20
POST   /api/v1/seller/products
PUT    /api/v1/seller/products/{productId}/attributes
POST   /api/v1/seller/products/batch          # multipart: CSV или XLSX
GET    /api/v1/seller/batches/{batchId}
GET    /api/v1/seller/descriptions/{descriptionId}
PUT    /api/v1/seller/descriptions/{descriptionId}
POST   /api/v1/seller/descriptions/{descriptionId}/submit
GET    /api/v1/seller/analytics?from=2026-09-01&to=2026-09-30
GET    /api/v1/seller/returns
POST   /api/v1/seller/returns/{requestId}/decision
```

```json
// POST /api/v1/seller/products — 422, неполные атрибуты (ФТ-8.6, ФТ-8.7)
{
  "code": "ATTRIBUTES_INCOMPLETE",
  "message": "Заполните обязательные поля",
  "details": {
    "missingFields": [
      { "code": "composition", "displayName": "Состав ткани" },
      { "code": "size_chart", "displayName": "Размерная сетка" }
    ]
  }
}

// GET /api/v1/seller/descriptions/{id} — 200 OK
{
  "descriptionId": "f6…",
  "status": "ЧЕРНОВИК",
  "confidence": "СРЕДНИЙ",
  "versions": [
    { "number": 1, "kind": "ДЛЯ_КАРТОЧКИ", "author": "генератор", "body": "…" },
    { "number": 2, "kind": "ДЛЯ_КАРТОЧКИ", "author": "виктор", "body": "…" },
    { "number": 2, "kind": "ДЛЯ_РЕКОМЕНДАЦИЙ", "author": "генератор", "body": "…" }
  ],
  "blockedPhrases": [],
  "fitHints": { "reviewsCount": 42, "dominant": "МАЛОМЕРИТ" }
}

// PUT /api/v1/seller/descriptions/{id} — 200 OK, найдена запрещённая формулировка (ФТ-8.16)
{
  "status": "ЗАБЛОКИРОВАНО",
  "blockedPhrases": [
    { "phrase": "100% не сядет", "offset": 112, "length": 13,
      "explanation": "Неподтверждаемое заявление о качестве" }
  ]
}
```

---

## 3. Панель администратора

```http
GET  /api/v1/moderation/queue?sort=confidence_asc&page=0&size=50
POST /api/v1/moderation/tasks/{taskId}/claim
POST /api/v1/moderation/tasks/{taskId}/approve
POST /api/v1/moderation/tasks/{taskId}/reject
GET  /api/v1/moderation/comment-templates
GET  /api/v1/admin/generation-rules
POST /api/v1/admin/generation-rules
GET  /api/v1/admin/categories/{categoryId}/required-attributes
PUT  /api/v1/admin/categories/{categoryId}/required-attributes
GET  /api/v1/admin/sellers/quality?period=30d
GET  /api/v1/admin/complaints
```

```json
// GET /api/v1/moderation/queue — 200 OK
{
  "blocked": [
    { "taskId": "g7…", "productTitle": "Куртка зимняя муж.", "sku": "20430",
      "blockedPhrase": "100% не сядет" }
  ],
  "tasks": [
    { "taskId": "h8…", "productTitle": "Платье «Мадрид»", "sku": "20457",
      "confidence": "НИЗКИЙ", "confidenceLabel": "уверенность: низкая",
      "claimedBy": null }
  ],
  "total": 37
}

// POST /api/v1/moderation/tasks/{id}/claim — 409 Conflict (ФТ-9.7)
{ "code": "TASK_ALREADY_CLAIMED", "message": "Задачу уже проверяет другой модератор" }

// POST /api/v1/moderation/tasks/{id}/reject
{ "templateId": "i9…", "comment": "Состав ткани не соответствует фотографии" }
```

---

## 4. Доменные события (Kafka)

Межсервисное взаимодействие между ограниченными контекстами — асинхронное (ОГР-7).

| Топик | Публикует | Подписчики | Назначение |
|-------|-----------|------------|------------|
| `catalog.product.created` | Сервис каталога | Сервис проверки атрибутов | Запуск проверки полноты атрибутов |
| `catalog.attributes.verified` | Сервис проверки атрибутов | Сервис генерации | Запуск генерации черновика |
| `description.draft.created` | Сервис генерации | Сервис модерации | Создание задачи модерации |
| `description.blocked` | Сервис проверки формулировок | Сервис модерации, уведомления | Блокировка публикации |
| `description.published` | Сервис описаний | Рекомендации, поиск, уведомления | Переиндексация и пересборка ленты |
| `moderation.card.returned` | Сервис модерации | Уведомления, рейтинг продавцов | Возврат карточки продавцу |
| `order.created` | Сервис заказов | Уведомления, аналитика | Создание заказа |
| `order.delivered` | Сервис заказов | Сервис возвратов | Запуск отсчёта срока возврата |
| `returns.request.created` | Сервис возвратов | Уведомления | Информирование продавца |
| `reviews.fit.updated` | Сервис отзывов | Ассистент по размеру | Пересчёт статистики посадки |

Формат события — CloudEvents:

```json
{
  "specversion": "1.0",
  "type": "by.marketshop.description.published",
  "source": "/services/description",
  "id": "9f2c…",
  "time": "2026-10-05T18:42:11Z",
  "subject": "a3f1…",
  "data": { "productId": "a3f1…", "descriptionId": "f6…", "summary": "Лёгкая вискоза…" }
}
```

---

## 5. Соответствие API и требований

| Группа маршрутов | Функциональные требования | Диаграмма последовательности |
|------------------|---------------------------|------------------------------|
| `/feed` | ФТ-1.1 … ФТ-1.8 | [Лента рекомендаций](lab3/README.md#471-формирование-персонализированной-ленты) |
| `/products/{id}/size-advice` | ФТ-4.1 … ФТ-4.11 | [Ассистент по размеру](lab3/README.md#472-ассистент-по-размеру) |
| `/orders`, `/payments` | ФТ-5.1 … ФТ-5.10 | [Оформление заказа](lab3/README.md#474-оформление-и-оплата-заказа) |
| `/returns` | ФТ-6.1 … ФТ-6.14 | [Оформление возврата](lab3/README.md#475-оформление-возврата-или-обмена) |
| `/seller/*` | ФТ-8.1 … ФТ-8.18 | [Генерация описания](lab3/README.md#32-диаграмма-последовательности-sequence-diagram) |
| `/moderation/*`, `/admin/*` | ФТ-9.1 … ФТ-9.21 | [Модерация карточки](lab3/README.md#473-модерация-карточки) |
