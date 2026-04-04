



# Unihra Python SDK

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/unihra.svg?style=flat-square&color=blue)](https://pypi.org/project/unihra/)
[![Python Versions](https://img.shields.io/pypi/pyversions/unihra.svg?style=flat-square)](https://pypi.org/project/unihra/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://github.com/Unihra/unihra_sdk/blob/main/LICENSE)

**SEO и семантический анализ ваших страниц и конкурентов.**  
Сравнивайте контент, находите семантические пробелы и получайте практические рекомендации с использованием зонного анализа и векторной семантики.

[English](../README.md) · Русский

---

### Ресурсы

| | |
| :---: | :--- |
| **Продукт** | [unihra.ru](https://unihra.ru) — веб-интерфейс |
| **Документация API** | [unihra.ru/docs](https://unihra.ru/docs) |
| **API ключ** | Telegram: [@UniHRA_bot](https://t.me/UniHRA_bot) |
| **Обновления** | [@mncosine](https://t.me/mncosine) |

</div>

---

## Возможности

- **Семантический контекст (зоны)** — рассчитывает вес слов в зависимости от того, где они находятся (title, H1–H6, текст) и их близости к целевым запросам. Дает конкретные рекомендации (например, что добавить в title или заголовки).
- **Структура страницы** — заголовки, мета-теги и метрики контента для вашего URL и каждого конкурента.
- **Сравнение слов (TF‑IDF)** — рекомендуемые действия для каждого термина (добавить, увеличить, уменьшить, ок).
- **Фразы (n‑граммы)** — повторяющиеся фразы на страницах конкурентов.
- **Векторные / LSI слова (DrMaxs)** — семантически связанный словарь для заданной тематики.
- **Анкоры (тексты ссылок)** — поиск недостающих текстов внутренних и внешних ссылок, которые конкуренты используют для ранжирования.
- **Cookies** — опциональная передача куки для отдельных URL (полезно для страниц с авторизацией или заглушками).
- **Стриминг** — клиент обрабатывает потоковую передачу статуса анализа в реальном времени и дожидается завершения.
- **Повторные попытки (Retries)** — встроенный механизм повторных HTTP-запросов для нестабильных сетей.
- **Отчеты** — экспорт многолистовых отчетов в Excel с готовым форматированием (требуются доп. зависимости).
- **Прогресс** — опциональный прогресс-бар (полезно в Jupyter Notebook), если установлен `tqdm`.

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
    queries=["купить виджет", "лучшие виджеты 2025"],
    lang="ru",
    url_cookies={
        "https://example.com/my-product": "session_id=abc123; auth=true",
    },
    verbose=True,
)

gaps = result.get("semantic_context_analysis", [])
pages = result.get("page_structure",[])

print(f"Строк семантических пробелов: {len(gaps)}")
for p in pages:
    print(p["url"], "—", p["meta_tags"]["title"])
```

### 2. Сохранение отчета в Excel

Отчет содержит листы: *Page Structure*, *Semantic Gaps*, *Word Analysis*, *N‑Grams*, *Anchors* и векторные разделы.

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
<summary><b>2. Семантический контекст (Semantic context analysis)</b></summary>

Сравнение лемм с учетом зон и запросов:

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
<summary><b>5. DrMaxs (Векторные / LSI слова)</b></summary>

Семантически близкие к топику слова, сгруппированные (например, `by_frequency`, `by_tfidf`), с указанием `similarity_score` и наличия слова на вашей странице.

```json
{
  "word": "логистика",
  "similarity_score": 0.89,
  "present_on_own_page": false
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

**Как это работает:** Инструмент `unihra_analyze` запускает полный анализ и сохраняет результат локально, возвращая только `result_id` и краткую сводку. Затем вы используете инструменты `unihra_get_*` вместе с `result_id` для извлечения конкретных разделов по запросу: семантические пробелы, анкоры, слова, n-граммы, векторные слова или структура страницы. Это позволяет изучить полный отчёт раздел за разделом.

**Доступные инструменты:**

| Инструмент | Назначение |
|------|---------|
| `unihra_health` | Проверка доступности сервиса |
| `unihra_analyze` | Основной инструмент: полный анализ, сохраняет на диск, возвращает `result_id` + сводку |
| `unihra_list_results` | Выводит список всех сохраненных результатов анализа на диске |
| `unihra_delete_result` | Удаляет сохраненный результат по `result_id` |
| `unihra_get_page_structure` | Получение структуры заголовков/мета-тегов по `result_id` |
| `unihra_get_gaps` | Получение семантических пробелов и рекомендаций по зонам из `result_id` |
| `unihra_get_anchors` | Получение анализа анкоров (текстов ссылок) из `result_id` |
| `unihra_get_vectors` | Получение LSI / векторных слов из `result_id` |
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

[Telegram — новости](https://t.me/mncosine) · [unihra.ru](https://unihra.ru) · [API ключ — @UniHRA_bot](https://t.me/UniHRA_bot)

</div>