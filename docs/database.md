---
title: "Схема базы данных"
description: "PostgreSQL 16: 40 таблиц, ERD и ключевые решения"
---

СУБД: **PostgreSQL 16**. Схема получена из
[диаграмм классов предметной области](lab3/README.md#45-диаграммы-классов-и-объектов)
и содержит **40 таблиц** и **13 перечисляемых типов**.

- **SQL-файл:** `database/schema.sql`
- **Изображение ERD:** [`04-erd.png`](lab3/diagrams/img/04-erd.png)
- **Исходник PlantUML:** [`04-erd.puml`](lab3/diagrams/04-erd.puml)

Схема проверена применением к чистому экземпляру PostgreSQL 16: все таблицы, типы,
ограничения и индексы создаются без ошибок.

---

## Диаграмма «сущность-связь»

```mermaid
erDiagram
    SELLER ||--o{ PRODUCT : "публикует"
    BRAND ||--o{ PRODUCT : "выпускает"
    BRAND ||--o{ SIZE_CHART : "задаёт"
    CATEGORY ||--o{ PRODUCT : "содержит"
    CATEGORY ||--o| RETURN_POLICY : "имеет правила"
    CATEGORY |o--o{ CATEGORY : "родитель"
    SIZE_CHART |o--o{ PRODUCT : "используется"
    PRODUCT ||--|{ PRODUCT_VARIANT : "имеет"
    PRODUCT_VARIANT ||--|{ STOCK : "хранится"
    WAREHOUSE ||--o{ STOCK : "содержит"
    PRODUCT ||--|{ PRODUCT_ATTRIBUTE : "описывается"
    ATTRIBUTE_DICT ||--o{ PRODUCT_ATTRIBUTE : "типизирует"
    PRODUCT ||--o{ PRODUCT_PHOTO : "иллюстрируется"
    PRODUCT ||--o| DESCRIPTION : "имеет"
    DESCRIPTION ||--|{ DESCRIPTION_VERSION : "содержит"
    DESCRIPTION ||--o{ DESCRIPTION_CLAIM : "обосновывается"
    DESCRIPTION ||--o{ MODERATION_TASK : "проверяется"
    MODERATION_TASK ||--o| MODERATION_DECISION : "завершается"
    ADMINISTRATOR ||--o{ MODERATION_TASK : "обрабатывает"
    COMMENT_TEMPLATE ||--o{ MODERATION_DECISION : "используется"
    SELLER ||--o{ SELLER_VIOLATION : "накапливает"
    CUSTOMER ||--o| SIZE_PARAMS : "имеет"
    CUSTOMER ||--o| CUSTOMER_PREFERENCES : "имеет"
    CUSTOMER ||--o{ VIEW_EVENT : "порождает"
    CUSTOMER ||--o{ FAVORITE : "ведёт"
    CUSTOMER ||--o{ ORDERS : "оформляет"
    CUSTOMER ||--o{ REVIEW : "оставляет"
    PRODUCT ||--o{ REVIEW : "получает"
    REVIEW ||--o{ REVIEW_PHOTO : "содержит"
    ORDERS ||--|{ ORDER_ITEM : "состоит из"
    ORDERS ||--o| PAYMENT : "оплачивается"
    ORDERS ||--o| DELIVERY : "доставляется"
    PICKUP_POINT ||--o{ ORDERS : "выдаёт"
    ORDERS ||--o{ RETURN_REQUEST : "порождает"
    ORDER_ITEM ||--o{ RETURN_REQUEST : "возвращается"
    RETURN_REQUEST ||--o{ RETURN_PHOTO : "подтверждается"
    PRODUCT_VARIANT ||--o{ ORDER_ITEM : "заказывается"
    CITY ||--o{ CUSTOMER : "проживание"
    CITY ||--o{ PICKUP_POINT : "расположение"

    PRODUCT {
        uuid id PK
        uuid seller_id FK
        uuid category_id FK
        uuid brand_id FK
        uuid size_chart_id FK
        varchar sku
        varchar title
        numeric price
        season_enum season
    }
    DESCRIPTION {
        uuid id PK
        uuid product_id FK "UNIQUE"
        moderation_status_enum status
        confidence_enum confidence
        text block_reason
    }
    DESCRIPTION_VERSION {
        uuid id PK
        uuid description_id FK
        smallint number
        version_kind_enum kind
        text body
        varchar author
    }
    DESCRIPTION_CLAIM {
        uuid id PK
        uuid description_id FK
        text statement
        varchar source_attribute FK
        boolean verified
    }
    STOCK {
        uuid variant_id PK
        uuid warehouse_id PK
        integer quantity
        integer reserved
    }
    MODERATION_TASK {
        uuid id PK
        uuid description_id FK
        uuid moderator_id FK
        timestamptz claimed_at
        timestamptz locked_until
    }
    ORDERS {
        uuid id PK
        uuid customer_id FK
        varchar number "UNIQUE"
        order_status_enum status
        payment_method_enum payment_method
        delivery_method_enum delivery_method
        numeric total
        date return_due_date
        varchar idempotency_key "UNIQUE"
    }
    RETURN_REQUEST {
        uuid id PK
        uuid order_id FK
        uuid order_item_id FK
        return_reason_enum reason
        return_status_enum status
        boolean is_exchange
        date hand_over_due
    }
    REVIEW {
        uuid id PK
        uuid product_id FK
        uuid customer_id FK
        smallint rating
        fit_enum fit_rating
    }
```

На диаграмме показаны ключевые таблицы со столбцами; полный перечень из 40 таблиц — в
SQL-файле `database/schema.sql`.

---

## Группы таблиц

| Группа | Таблицы | Назначение |
|--------|---------|------------|
| Справочники | `city`, `brand`, `category`, `attribute_dict`, `category_required_attribute` | Иерархия категорий, бренды, состав обязательных атрибутов |
| Каталог | `seller`, `product`, `product_variant`, `warehouse`, `stock`, `product_attribute`, `product_photo`, `size_chart` | Товары, варианты по размеру и цвету, остатки, атрибуты |
| Описания | `description`, `description_version`, `description_claim`, `prompt_template`, `generation_rule` | Описания, версии, обоснование утверждений, шаблоны промптов, правила |
| Модерация | `administrator`, `moderation_task`, `moderation_decision`, `comment_template`, `seller_violation`, `complaint` | Очередь, решения, нарушения, жалобы |
| Покупатели | `customer`, `size_params`, `customer_preferences`, `view_event`, `favorite`, `recommendation_block` | Профиль, параметры размера, поведение, персонализация |
| Заказы | `orders`, `order_item`, `payment`, `delivery`, `pickup_point` | Заказ, позиции, оплата, доставка |
| Возвраты | `return_request`, `return_photo`, `return_policy` | Заявки, фотографии, правила возврата |
| Отзывы | `review`, `review_photo` | Отзывы с оценкой посадки |

---

## Ключевые решения по схеме

| № | Решение | Обоснование |
|---|---------|-------------|
| 1 | `description.product_id` имеет ограничение уникальности | У товара не более одного описания; версии вынесены в отдельную таблицу |
| 2 | Версии и обоснования удаляются каскадно вместе с описанием | Композиция доменной модели переходит в `ON DELETE CASCADE` |
| 3 | Перечисления домена отображены в `ENUM`-типы, а не `varchar` | Проверка допустимых значений переносится на уровень БД |
| 4 | `stock` имеет составной первичный ключ «вариант + склад» | Один вариант хранится на нескольких складах с разными остатками |
| 5 | `stock.reserved` отделён от `quantity`, добавлено ограничение `reserved <= quantity` | Резерв при оформлении заказа не искажает фактический остаток |
| 6 | `order_item.price_at_order` хранит цену на момент заказа | Цена товара меняется, сумма оформленного заказа — нет |
| 7 | `orders.return_due_date` фиксируется при создании заказа | Изменение правил возврата не ухудшает условия уже оформленных заказов |
| 8 | `orders.idempotency_key` уникален | Повторная отправка запроса не создаёт второй заказ |
| 9 | `return_request` ссылается и на заказ, и на позицию | Поддержка частичного возврата |
| 10 | `generation_rule` не связана внешним ключом с описаниями | Правила применяются алгоритмом при проверке текста |
| 11 | Таблица называется `orders`, а не `order` | `order` — зарезервированное слово SQL |
| 12 | Пароли и секреты в схеме отсутствуют | Аутентификация вынесена в отдельный сервис |

---

## Индексы

Созданы только индексы, необходимые для выполнения требований к производительности:

| Индекс | Требование |
|--------|------------|
| `idx_task_open` (частичный, по незахваченным задачам) | ФТ-9.1 — сортировка очереди модерации |
| `idx_review_product_fit` | ФТ-4.4 — агрегация оценок посадки для ассистента по размеру |
| `idx_view_event_customer` | ФТ-1.1 — формирование персонализированной ленты |
| `idx_orders_customer` | ФТ-6.1 — список «Мои заказы» с признаком возврата |
| `idx_description_status`, `idx_version_description` | ФТ-1.2 — отбор опубликованных описаний |

Партиционирование и дополнительные индексы относятся к физической модели и будут определены
по результатам нагрузочного тестирования.
