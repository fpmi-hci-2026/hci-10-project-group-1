-- =====================================================================
-- МаркетШоп.by — схема базы данных (PostgreSQL 16)
-- Версия: 1.0 от 05.10.2026
-- =====================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------
-- Перечисляемые типы
-- ---------------------------------------------------------------------
CREATE TYPE season_enum            AS ENUM ('ЗИМА', 'ВЕСНА_ОСЕНЬ', 'ЛЕТО', 'ВСЕСЕЗОННЫЙ');
CREATE TYPE moderation_status_enum AS ENUM ('ЧЕРНОВИК', 'НА_МОДЕРАЦИИ', 'ОПУБЛИКОВАНО',
                                            'ВОЗВРАЩЕНО_ПРОДАВЦУ', 'ЗАБЛОКИРОВАНО');
CREATE TYPE confidence_enum        AS ENUM ('НИЗКИЙ', 'СРЕДНИЙ', 'ВЫСОКИЙ');
CREATE TYPE version_kind_enum      AS ENUM ('ДЛЯ_КАРТОЧКИ', 'ДЛЯ_РЕКОМЕНДАЦИЙ');
CREATE TYPE verdict_enum           AS ENUM ('ОДОБРЕНО', 'ВОЗВРАЩЕНО', 'ЗАБЛОКИРОВАНО');
CREATE TYPE violation_enum         AS ENUM ('ЗАПРЕЩЁННАЯ_ФОРМУЛИРОВКА', 'НЕСООТВЕТСТВИЕ_ФОТО',
                                            'НЕПОЛНЫЕ_АТРИБУТЫ', 'ПОВТОРНОЕ_НАРУШЕНИЕ');
CREATE TYPE order_status_enum      AS ENUM ('СОЗДАН', 'ОПЛАЧЕН', 'ПЕРЕДАН_В_ДОСТАВКУ',
                                            'ГОТОВ_К_ВЫДАЧЕ', 'ВЫДАН', 'ОТМЕНЁН');
CREATE TYPE payment_method_enum    AS ENUM ('КАРТА_ОНЛАЙН', 'ПРИ_ПОЛУЧЕНИИ', 'ЕРИП');
CREATE TYPE delivery_method_enum   AS ENUM ('ПУНКТ_САМОВЫВОЗА', 'КУРЬЕР', 'БЕЛПОЧТА');
CREATE TYPE return_reason_enum     AS ENUM ('НЕ_ПОДОШЁЛ_РАЗМЕР', 'НЕ_СООТВЕТСТВУЕТ_ОПИСАНИЮ',
                                            'БРАК', 'ПЕРЕДУМАЛ');
CREATE TYPE return_status_enum     AS ENUM ('СОЗДАНА', 'ТОВАР_СДАН', 'НА_РАССМОТРЕНИИ',
                                            'ОДОБРЕНА', 'ОТКЛОНЕНА', 'СРЕДСТВА_ВОЗВРАЩЕНЫ');
CREATE TYPE fit_enum               AS ENUM ('МАЛОМЕРИТ', 'СООТВЕТСТВУЕТ', 'БОЛЬШЕМЕРИТ');
CREATE TYPE block_kind_enum        AS ENUM ('СПЕЦИАЛЬНО_ДЛЯ_ВАС', 'ПОХОЖИЕ_ТОВАРЫ',
                                            'С_ЭТИМ_ПОКУПАЮТ');

-- ---------------------------------------------------------------------
-- Справочники
-- ---------------------------------------------------------------------
CREATE TABLE city (
    id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name    varchar(120) NOT NULL UNIQUE,
    region  varchar(120) NOT NULL
);

CREATE TABLE brand (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name             varchar(120) NOT NULL UNIQUE,
    made_in_belarus  boolean      NOT NULL DEFAULT false
);

CREATE TABLE category (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id uuid REFERENCES category (id) ON DELETE RESTRICT,
    name      varchar(120) NOT NULL,
    level     smallint     NOT NULL CHECK (level BETWEEN 1 AND 4),
    slug      varchar(160) NOT NULL UNIQUE
);

-- Состав обязательных атрибутов настраивается администратором (US-18, AC-06.4)
CREATE TABLE attribute_dict (
    code         varchar(64) PRIMARY KEY,
    display_name varchar(120) NOT NULL,
    value_type   varchar(16)  NOT NULL CHECK (value_type IN ('text','number','enum','boolean')),
    required     boolean      NOT NULL DEFAULT false
);

CREATE TABLE category_required_attribute (
    category_id uuid        NOT NULL REFERENCES category (id)       ON DELETE CASCADE,
    code        varchar(64) NOT NULL REFERENCES attribute_dict (code) ON DELETE RESTRICT,
    PRIMARY KEY (category_id, code)
);

-- ---------------------------------------------------------------------
-- Продавцы и каталог
-- ---------------------------------------------------------------------
CREATE TABLE seller (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_name varchar(120) NOT NULL,
    unp        char(9)      NOT NULL UNIQUE,
    city_id    uuid         REFERENCES city (id),
    rating     numeric(2,1) CHECK (rating BETWEEN 0 AND 5),
    created_at timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE size_chart (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id      uuid         NOT NULL REFERENCES brand (id) ON DELETE CASCADE,
    item_type     varchar(64)  NOT NULL,
    fit_deviation numeric(3,2) NOT NULL DEFAULT 0,
    UNIQUE (brand_id, item_type)
);

CREATE TABLE product (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id         uuid          NOT NULL REFERENCES seller (id)     ON DELETE RESTRICT,
    category_id       uuid          NOT NULL REFERENCES category (id)   ON DELETE RESTRICT,
    brand_id          uuid          REFERENCES brand (id)               ON DELETE RESTRICT,
    size_chart_id     uuid          REFERENCES size_chart (id)          ON DELETE SET NULL,
    sku               varchar(64)   NOT NULL,
    title             varchar(200)  NOT NULL,
    price             numeric(10,2) NOT NULL CHECK (price > 0),
    season            season_enum   NOT NULL,
    country_of_origin varchar(80),
    created_at        timestamptz   NOT NULL DEFAULT now(),
    UNIQUE (seller_id, sku)
);

CREATE TABLE product_variant (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id uuid        NOT NULL REFERENCES product (id) ON DELETE CASCADE,
    size       varchar(16) NOT NULL,
    color      varchar(40),
    barcode    varchar(32) UNIQUE,
    UNIQUE (product_id, size, color)
);

CREATE TABLE warehouse (
    id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name    varchar(120) NOT NULL,
    city_id uuid REFERENCES city (id)
);

-- Составной первичный ключ: один вариант хранится на нескольких складах
CREATE TABLE stock (
    variant_id   uuid    NOT NULL REFERENCES product_variant (id) ON DELETE CASCADE,
    warehouse_id uuid    NOT NULL REFERENCES warehouse (id)       ON DELETE RESTRICT,
    quantity     integer NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    reserved     integer NOT NULL DEFAULT 0 CHECK (reserved >= 0),
    PRIMARY KEY (variant_id, warehouse_id),
    CONSTRAINT stock_reserved_le_quantity CHECK (reserved <= quantity)
);

CREATE TABLE product_attribute (
    product_id uuid        NOT NULL REFERENCES product (id)         ON DELETE CASCADE,
    code       varchar(64) NOT NULL REFERENCES attribute_dict (code) ON DELETE RESTRICT,
    value      text,
    PRIMARY KEY (product_id, code)
);

CREATE TABLE product_photo (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id uuid         NOT NULL REFERENCES product (id) ON DELETE CASCADE,
    url        varchar(400) NOT NULL,
    sort_order smallint     NOT NULL DEFAULT 0,
    is_primary boolean      NOT NULL DEFAULT false
);

-- ---------------------------------------------------------------------
-- Описания товаров и правила генерации
-- ---------------------------------------------------------------------
-- UQ на product_id: у товара не более одного описания (ФТ-11.3)
CREATE TABLE description (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id   uuid                   NOT NULL UNIQUE REFERENCES product (id) ON DELETE CASCADE,
    status       moderation_status_enum NOT NULL DEFAULT 'ЧЕРНОВИК',
    confidence   confidence_enum        NOT NULL DEFAULT 'НИЗКИЙ',
    block_reason text,
    created_at   timestamptz            NOT NULL DEFAULT now()
);

-- Композиция доменной модели → FK с ON DELETE CASCADE (ФТ-11.4)
CREATE TABLE description_version (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    description_id uuid              NOT NULL REFERENCES description (id) ON DELETE CASCADE,
    number         smallint          NOT NULL,
    kind           version_kind_enum NOT NULL,
    body           text              NOT NULL,
    author         varchar(64)       NOT NULL,
    created_at     timestamptz       NOT NULL DEFAULT now(),
    UNIQUE (description_id, number, kind)
);

-- Сопоставление утверждений описания с атрибутами-источниками (AC-02.3, ФТ-3.4)
CREATE TABLE description_claim (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    description_id   uuid        NOT NULL REFERENCES description (id) ON DELETE CASCADE,
    statement        text        NOT NULL,
    source_attribute varchar(64) REFERENCES attribute_dict (code) ON DELETE SET NULL,
    verified         boolean     NOT NULL DEFAULT false
);

CREATE TABLE prompt_template (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id uuid        REFERENCES category (id) ON DELETE CASCADE,
    tone        varchar(32) NOT NULL,
    body        text        NOT NULL,
    version     smallint    NOT NULL DEFAULT 1,
    active      boolean     NOT NULL DEFAULT true
);

-- Правила не связаны FK с описаниями: применяются алгоритмом при проверке текста
CREATE TABLE generation_rule (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    phrase      varchar(200) NOT NULL UNIQUE,
    explanation text,
    active      boolean      NOT NULL DEFAULT true
);

-- ---------------------------------------------------------------------
-- Модерация
-- ---------------------------------------------------------------------
CREATE TABLE administrator (
    id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    login varchar(64) NOT NULL UNIQUE,
    role  varchar(32) NOT NULL
);

CREATE TABLE comment_template (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    body           text           NOT NULL,
    violation_kind violation_enum NOT NULL,
    active         boolean        NOT NULL DEFAULT true
);

-- claimed_at / locked_until обеспечивают захват задачи одним модератором (AC-08.7, ФТ-9.7)
CREATE TABLE moderation_task (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    description_id uuid        NOT NULL REFERENCES description (id)   ON DELETE CASCADE,
    moderator_id   uuid        REFERENCES administrator (id)          ON DELETE SET NULL,
    claimed_at     timestamptz,
    locked_until   timestamptz,
    created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE moderation_decision (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id      uuid         NOT NULL UNIQUE REFERENCES moderation_task (id)  ON DELETE CASCADE,
    verdict      verdict_enum NOT NULL,
    comment      text,
    template_id  uuid         REFERENCES comment_template (id) ON DELETE SET NULL,
    decided_at   timestamptz  NOT NULL DEFAULT now(),
    duration_sec integer      CHECK (duration_sec >= 0)
);

CREATE TABLE seller_violation (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id    uuid           NOT NULL REFERENCES seller (id) ON DELETE CASCADE,
    kind         violation_enum NOT NULL,
    description_id uuid         REFERENCES description (id) ON DELETE SET NULL,
    recorded_at  timestamptz    NOT NULL DEFAULT now()
);

CREATE TABLE complaint (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source         varchar(32) NOT NULL,
    description_id uuid        REFERENCES description (id) ON DELETE CASCADE,
    body           text        NOT NULL,
    resolved       boolean     NOT NULL DEFAULT false,
    created_at     timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Покупатели и персонализация
-- ---------------------------------------------------------------------
CREATE TABLE customer (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    phone      varchar(20) NOT NULL UNIQUE,
    name       varchar(120),
    city_id    uuid        REFERENCES city (id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE size_params (
    customer_id    uuid PRIMARY KEY REFERENCES customer (id) ON DELETE CASCADE,
    height_cm      smallint     CHECK (height_cm BETWEEN 100 AND 230),
    chest_cm       smallint     CHECK (chest_cm BETWEEN 50 AND 200),
    foot_length_cm numeric(3,1) CHECK (foot_length_cm BETWEEN 15 AND 40),
    usual_top_size varchar(8)
);

CREATE TABLE customer_preferences (
    customer_id      uuid PRIMARY KEY REFERENCES customer (id) ON DELETE CASCADE,
    categories       uuid[]        NOT NULL DEFAULT '{}',
    materials        varchar(64)[] NOT NULL DEFAULT '{}',
    price_min        numeric(10,2),
    price_max        numeric(10,2),
    updated_at       timestamptz   NOT NULL DEFAULT now(),
    CONSTRAINT price_range_valid CHECK (price_min IS NULL OR price_max IS NULL OR price_min <= price_max)
);

CREATE TABLE view_event (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid        REFERENCES customer (id) ON DELETE CASCADE,
    device_id   varchar(64),
    product_id  uuid        NOT NULL REFERENCES product (id) ON DELETE CASCADE,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    duration_sec integer    CHECK (duration_sec >= 0)
);

CREATE TABLE favorite (
    customer_id uuid        NOT NULL REFERENCES customer (id) ON DELETE CASCADE,
    product_id  uuid        NOT NULL REFERENCES product (id)  ON DELETE CASCADE,
    added_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (customer_id, product_id)
);

CREATE TABLE recommendation_block (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid            REFERENCES customer (id) ON DELETE CASCADE,
    kind        block_kind_enum NOT NULL,
    criteria    varchar(200)    NOT NULL,
    updated_at  timestamptz     NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Заказы, оплата и доставка
-- ---------------------------------------------------------------------
CREATE TABLE pickup_point (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    address           varchar(240) NOT NULL,
    city_id           uuid         NOT NULL REFERENCES city (id),
    accepts_returns   boolean      NOT NULL DEFAULT true
);

CREATE TABLE return_policy (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id      uuid     NOT NULL UNIQUE REFERENCES category (id) ON DELETE CASCADE,
    period_days      smallint NOT NULL CHECK (period_days >= 0),
    return_forbidden boolean  NOT NULL DEFAULT false
);

-- Таблица названа orders: order — зарезервированное слово SQL
CREATE TABLE orders (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id     uuid                 NOT NULL REFERENCES customer (id) ON DELETE RESTRICT,
    number          varchar(16)          NOT NULL UNIQUE,
    status          order_status_enum    NOT NULL DEFAULT 'СОЗДАН',
    payment_method  payment_method_enum  NOT NULL,
    delivery_method delivery_method_enum NOT NULL,
    pickup_point_id uuid                 REFERENCES pickup_point (id) ON DELETE SET NULL,
    total           numeric(10,2)        NOT NULL CHECK (total >= 0),
    -- Срок возврата фиксируется при создании заказа и далее не пересчитывается (ФТ-5.6)
    return_due_date date,
    idempotency_key varchar(64)          UNIQUE,
    created_at      timestamptz          NOT NULL DEFAULT now()
);

CREATE TABLE order_item (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id       uuid          NOT NULL REFERENCES orders (id)          ON DELETE CASCADE,
    variant_id     uuid          NOT NULL REFERENCES product_variant (id) ON DELETE RESTRICT,
    quantity       integer       NOT NULL CHECK (quantity > 0),
    price_at_order numeric(10,2) NOT NULL CHECK (price_at_order >= 0)
);

CREATE TABLE payment (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id    uuid          NOT NULL UNIQUE REFERENCES orders (id) ON DELETE CASCADE,
    amount      numeric(10,2) NOT NULL CHECK (amount >= 0),
    external_id varchar(64),
    status      varchar(24)   NOT NULL,
    paid_at     timestamptz
);

CREATE TABLE delivery (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id      uuid        NOT NULL UNIQUE REFERENCES orders (id) ON DELETE CASCADE,
    tracking_code varchar(64),
    expected_date date,
    status        varchar(32) NOT NULL DEFAULT 'СОЗДАНА'
);

-- ---------------------------------------------------------------------
-- Возвраты и обмены
-- ---------------------------------------------------------------------
-- Ссылка и на заказ, и на позицию — поддержка частичного возврата (ФТ-6.10)
CREATE TABLE return_request (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        uuid               NOT NULL REFERENCES orders (id)     ON DELETE CASCADE,
    order_item_id   uuid               NOT NULL REFERENCES order_item (id) ON DELETE CASCADE,
    reason          return_reason_enum NOT NULL,
    status          return_status_enum NOT NULL DEFAULT 'СОЗДАНА',
    is_exchange     boolean            NOT NULL DEFAULT false,
    pickup_point_id uuid               REFERENCES pickup_point (id) ON DELETE SET NULL,
    hand_over_due   date,
    created_at      timestamptz        NOT NULL DEFAULT now()
);

CREATE TABLE return_photo (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    return_request_id uuid         NOT NULL REFERENCES return_request (id) ON DELETE CASCADE,
    url               varchar(400) NOT NULL,
    uploaded_at       timestamptz  NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Отзывы
-- ---------------------------------------------------------------------
CREATE TABLE review (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id  uuid        NOT NULL REFERENCES product (id)  ON DELETE CASCADE,
    customer_id uuid        NOT NULL REFERENCES customer (id) ON DELETE CASCADE,
    order_id    uuid        REFERENCES orders (id) ON DELETE SET NULL,
    rating      smallint    NOT NULL CHECK (rating BETWEEN 1 AND 5),
    body        text,
    fit_rating  fit_enum    NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (product_id, customer_id, order_id)
);

CREATE TABLE review_photo (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id uuid         NOT NULL REFERENCES review (id) ON DELETE CASCADE,
    url       varchar(400) NOT NULL
);

-- ---------------------------------------------------------------------
-- Индексы, необходимые для требований к производительности
-- ---------------------------------------------------------------------
CREATE INDEX idx_product_category        ON product (category_id);
CREATE INDEX idx_product_seller          ON product (seller_id);
CREATE INDEX idx_variant_product         ON product_variant (product_id);
CREATE INDEX idx_description_status      ON description (status);
CREATE INDEX idx_version_description     ON description_version (description_id, kind);
-- Сортировка очереди модерации по уверенности (ФТ-9.1)
CREATE INDEX idx_task_open               ON moderation_task (created_at)
                                         WHERE claimed_at IS NULL;
CREATE INDEX idx_orders_customer         ON orders (customer_id, created_at DESC);
CREATE INDEX idx_return_order            ON return_request (order_id);
-- Агрегация оценок посадки для ассистента по размеру (ФТ-4.4)
CREATE INDEX idx_review_product_fit      ON review (product_id, fit_rating);
CREATE INDEX idx_view_event_customer     ON view_event (customer_id, occurred_at DESC);

COMMIT;
