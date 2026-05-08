



# Unihra Python SDK

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/unihra.svg?style=flat-square&color=blue)](https://pypi.org/project/unihra/)
[![Python Versions](https://img.shields.io/pypi/pyversions/unihra.svg?style=flat-square)](https://pypi.org/project/unihra/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://github.com/Unihra/unihra_sdk/blob/main/LICENSE)

**SEO и контентный анализ ваших страниц и конкурентов.**  
Сравнивайте контент, находите зонтичные пробелы и получайте практические рекомендации с использованием зонного анализа и графов знаний.

[English](../README.md) · Русский

---

### Ресурсы

| | |
| :---: | :--- |
| **Продукт** | [unihra.ru](https://unihra.ru) — веб-интерфейс |
| **Документация API** | [unihra.ru/docs](https://unihra.ru/docs) |
| **API ключ** | [unihra.ru](https://unihra.ru) |

</div>

---

## Возможности

- **Зонтичный анализ (зоны)** — рассчитывает вес слов в зависимости от того, где они находятся (title, H1–H6, текст) и их близости к целевым запросам. Даёт конкретные рекомендации (например, что добавить в title или заголовки).
- **Структура страницы** — заголовки, мета-теги и метрики контента для вашего URL и каждого конкурента.
- **Сравнение слов (TF‑IDF)** — рекомендуемые действия для каждого термина (добавить, увеличить, уменьшить, ок).
- **Фразы (n‑граммы)** — повторяющиеся фразы на страницах конкурентов.
- **Граф знаний (триплеты)** — расширенный режим: извлечение фактов `subject → predicate → object` из текстов конкурентов и список тематических пробелов (critical / important / unique).
- **Анкоры (тексты ссылок)** — поиск недостающих текстов внутренних и внешних ссылок, которые конкуренты используют для ранжирования.
- **Cookies** — опциональная передача куки для отдельных URL (полезно для страниц с авторизацией или заглушками).
- **Стриминг** — клиент обрабатывает потоковую передачу статуса анализа в реальном времени и дожидается завершения.
- **Повторные попытки (Retries)** — встроенный механизм повторных HTTP-запросов для нестабильных сетей.
- **Отчеты** — экспорт многолистовых отчетов в Excel с готовым форматированием (требуются доп. зависимости).
- **Прогресс** — опциональный прогресс-бар (полезно в Jupyter Notebook), если установлен `tqdm`.

> 💳 **Стоимость запросов.** Стандартный анализ — **1 кредит** за вызов. Расширенный анализ с `triplet_analysis=True` (Граф знаний) — **5 кредитов** за вызов. По умолчанию используется дешёвый режим.

---

## Установка

```bash
pip install unihra
```

**Дополнительные пакеты** (устанавливайте по необходимости):

| Команда | Включает в себя |
|--------|----------|
| `pip install "unihra[report]"` | Экспорт в Excel (`pandas`, `openpyxl`) |
| `pip install "unihra[full]"` | Экспорт отчетов + прогресс-бар (`tqdm`) |
| `pip install "unihra[mcp]"` | MCP-сервер для Cursor / Claude Code (требуется **Python 3.10+**) |

Или установите нужные библиотеки вручную, например: `pip install pandas openpyxl tqdm`.

---

## Быстрый старт

### 1. Запуск анализа

Передайте **`queries`** (целевые поисковые запросы), чтобы рекомендации по зонам и анализ пробелов были максимально точными.

```python
from unihra import UnihraClient

client = UnihraClient(api_key="ВАШ_API_КЛЮЧ", max_retries=3)

result = client.analyze(
    own_page="https://example.com/my-product",
    competitors=[
        "https://competitor.com/top-product",
        "https://market-leader.com/item",
    ],
    queries=["купить виджет", "лучшие виджеты 2026"],
    lang="ru",
    url_cookies={
        "https://example.com/my-product": "session_id=abc123; auth=true",
    },
    triplet_analysis=False,  # включите True, чтобы получить Граф знаний (5 кредитов)
    verbose=True,
)

gaps = result.get("umbrella_analysis", [])
pages = result.get("page_structure", [])

print(f"Строк зонтичного анализа: {len(gaps)}")
for p in pages:
    print(p["url"], "—", p["meta_tags"]["title"])
```

Включить **Граф знаний** (расширенный анализ покрытия фактов):

```python
result = client.analyze(
    own_page="https://example.com/my-product",
    competitors=["https://competitor.com/top-product"],
    queries=["купить виджет"],
    lang="ru",
    triplet_analysis=True,   # 5 кредитов — добавляется граф знаний и тематические пробелы
    verbose=True,
)

triplets = result.get("triplets_analysis", {})
print("Всего фактов:", triplets.get("stats", {}).get("total_triplets"))
print("Критические тематические пробелы:", len(triplets.get("missing_triplets", {}).get("critical", [])))
```

### 2. Сохранение отчета в Excel

Отчет содержит листы: *Page Structure*, *Umbrella Gaps*, *Word Analysis*, *N‑Grams*, *Anchors* и — при `triplet_analysis=True` — *Triplets* и *Triplets Gaps*.

```python
client.save_report(result, "seo_report.xlsx")
```

---

## Структура результата

SDK возвращает **Python словарь (dict)**, полностью соответствующий API. Ключи нормализованы в **snake_case**.

<details>
<summary><b>1. Структура страницы (Page structure)</b></summary>

**Список** страниц (сначала ваша, затем конкуренты). Каждый элемент включает:

- `url`
- `meta_tags` — `title`, `description` и т.д.
- `content` — `h1_heading`, `heading_structure_raw` (дерево заголовков в виде текста)
- `metrics` — например, `char_count_no_spaces`, `uniqueness_percentage`

</details>

<details>
<summary><b>2. Зонтичный анализ (Umbrella Analysis)</b></summary>

Сравнение лемм с учётом зон и таргет-запросов:

- `lemma` — базовая форма слова  
- `competitor_avg_score`, `own_score` — взвешенные оценки (0.0 у вас часто означает отсутствие слова или слабую зону)  
- `gap` — насколько вы отстаете от конкурентов (чем выше, тем выше приоритет)  
- `coverage_percent` — процент конкурентов, использующих термин в сильном контексте  
- `context_snippet` — короткий пример использования у конкурентов  
- `recommendation` — рекомендуемое действие (например, "Добавить в Title/H1")

```json
{
  "lemma": "аккумулятор",
  "competitor_avg_score": 10.5,
  "own_score": 0.0,
  "gap": 10.5,
  "coverage_percent": 80.0,
  "context_snippet": "долгий срок службы аккумулятора",
  "recommendation": "Добавить в Title/H1"
}
```

</details>

<details>
<summary><b>3. Сравнение слов (Block comparison)</b></summary>

Сравнение на основе частотности (TF‑IDF):

- `frequency`, `frequency_own_page`, `pct_target_comp_avg`
- `action_needed` — `add` (добавить), `increase` (увеличить), `decrease` (уменьшить), `ok` (ок).

```json
{
  "word": "цена",
  "frequency": 12.5,
  "pct_target_comp_avg": 2.5,
  "action_needed": "increase",
  "present_on_own_page": true
}
```

</details>

<details>
<summary><b>4. N‑граммы (N-grams)</b></summary>

Фразы (биграммы / триграммы) и количество страниц конкурентов, на которых они встречаются.

- `ngram`, `pages_count` и др.

</details>

<details>
<summary><b>5. Триплеты — Граф знаний (расширенный режим, 5 кредитов)</b></summary>

Доступно только при `triplet_analysis=True`. Извлекает факты `subject → predicate → object` из текстов конкурентов и группирует тематические пробелы по числу источников.

- `entities[]` — для каждого субъекта:
  - `tier` — уровень важности: `core` → `main` → `additional` → `unique`
  - `triplets_count`, `sources_count`
  - `triplets[]` — список фактов вида `{predicate, object, sources[]}`
- `gaps` — субъекты, **отсутствующие на вашей странице**, сгруппированные по покрытию у конкурентов:
  - `critical` — встречается у **3+** конкурентов
  - `important` — встречается у **2** конкурентов
  - `unique` — встречается у **1** конкурента
- `stats` — `total_triplets`, `sources_with_content`, счётчики пробелов по уровням, `gaps_total`, `batches`.

```json
{
  "entities": [
    {
      "subject": "Минеральная вата",
      "tier": "core",
      "triplets_count": 14,
      "sources_count": 7,
      "triplets": [
        {"predicate": "рабочая температура", "object": "до 700°C",
         "sources": ["comp1.com", "comp4.com"]}
      ]
    }
  ],
  "gaps": {"critical": [...], "important": [...], "unique": [...]},
  "stats": {"total_triplets": 412, "gaps_total": 74}
}
```

</details>

<details>
<summary><b>6. Анализ анкоров (Anchors analysis)</b></summary>

Сравнение текстов ссылок (анкоров), используемых на страницах.

- `anchor` — текст ссылки
- `frequency_own` — вхождения на вашей странице
- `frequency_comp_avg` — среднее количество вхождений у конкурентов
- `pages_count` — количество страниц конкурентов, использующих этот анкор
- `links` — список URL-адресов (href), где этот анкорный текст был найден на всех страницах (ваши + конкуренты)

```json
{
  "anchor": "купить онлайн",
  "frequency_own": 0,
  "frequency_comp_avg": 5.0,
  "pages_count": 3,
  "links": [
    "https://competitor.com/products/buy",
    "https://other-competitor.com/shop"
  ]
}
```

</details>

---

## Командная строка (CLI)

```bash
python -m unihra \
  --key "ВАШ_API_КЛЮЧ" \
  --own "https://mysite.com" \
  --comp "https://comp1.com" \
  --comp "https://comp2.com" \
  --query "главный ключ" \
  --cookies "session=secret_123" \
  --triplets \
  --save report.xlsx \
  --verbose
```

| Параметр | Описание |
|--------|---------|
| `--own` | URL вашей страницы (обязательно) |
| `--comp` | URL конкурента (повторите для нескольких; нужен минимум один) |
| `--query` | Целевой запрос (можно повторять; рекомендуется) |
| `--lang` | `ru` или `en` (по умолчанию `ru`) |
| `--cookies` | Строка куки для вашей страницы |
| `--triplets` | Включить извлечение Графа знаний (стоимость: 5 кредитов вместо 1) |
| `--save` | Сохранить отчет в формате `.xlsx` или `.csv` |
| `--retries` | Количество повторных попыток HTTP-запроса |
| `--verbose` | Показывать прогресс |
| `--no-style` | Сохранить Excel без дополнительного форматирования ячеек |

Вы можете не передавать `--key`, если установлена переменная окружения **`UNIHRA_API_KEY`**.  
Если не указаны `--save` и `--verbose`, JSON-результат будет выведен прямо в терминал.

---

## Cursor, Claude и другие MCP-клиенты

Опциональный **MCP-сервер** позволяет совместимым ИИ-ассистентам вызывать инструменты Unihra напрямую, вместо того чтобы пытаться парсить страницы самостоятельно.

1. Установите: `pip install "unihra[mcp]"` (требуется Python **3.10+**).
2. Задайте API ключ: через переменную окружения **`UNIHRA_API_KEY`** или передав `--key` при запуске сервера.
3. Запустите: `python -m unihra.mcp_server` или команду `unihra-mcp`.
4. Укажите путь к этому Python и модулю в настройках MCP вашего клиента (см. ниже).

**Как это работает:** Инструмент `unihra_analyze` запускает полный анализ и сохраняет результат локально, возвращая только `result_id` и краткую сводку. Затем вы используете инструменты `unihra_get_*` вместе с `result_id` для извлечения конкретных разделов по запросу: зонтичные пробелы, анкоры, слова, n‑граммы, триплеты (Граф знаний) или структура страницы. Это позволяет изучить полный отчёт раздел за разделом.

**Выбор режима с учётом стоимости.** В `unihra_analyze` есть булев параметр `triplet_analysis`. По умолчанию модель использует `false` (1 кредит, стандартный анализ) и переключается на `true` (5 кредитов, Граф знаний) только если пользователь явно просит покрытие фактами / тематический бриф / аудит сущностей.

**Доступные инструменты:**

| Инструмент | Назначение |
|------|---------|
| `unihra_health` | Проверка доступности сервиса |
| `unihra_analyze` | Основной инструмент: полный анализ, сохраняет на диск, возвращает `result_id` + сводку. `triplet_analysis=true` включает Граф знаний (5 кредитов) |
| `unihra_list_results` | Выводит список всех сохраненных результатов анализа на диске |
| `unihra_delete_result` | Удаляет сохраненный результат по `result_id` |
| `unihra_get_page_structure` | Получение структуры заголовков/мета-тегов по `result_id` |
| `unihra_get_gaps` | Получение зонтичных пробелов и рекомендаций по зонам из `result_id` |
| `unihra_get_anchors` | Получение анализа анкоров (текстов ссылок) из `result_id` |
| `unihra_get_triplets` | Получение сущностей Графа знаний и тематических пробелов (только для результатов, созданных с `triplet_analysis=true`) |
| `unihra_get_word_actions` | Получение TF‑IDF слов, сгруппированных по действиям |
| `unihra_get_ngrams` | Получение списка фраз из `result_id` |

**Пример конфигурации MCP** (скорректируйте путь к вашему исполняемому файлу Python):

```json
{
  "mcpServers": {
    "unihra": {
      "command": "python",
      "args":["-m", "unihra.mcp_server"],
      "env": {
        "UNIHRA_API_KEY": "ВАШ_КЛЮЧ_ЗДЕСЬ"
      }
    }
  }
}
```

---

<div align="center">

**Команда Unihra**

[unihra.ru](https://unihra.ru) · [Документация API](https://unihra.ru/docs)

</div>