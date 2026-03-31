# Unihra Python SDK

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/unihra.svg?style=flat-square&color=blue)](https://pypi.org/project/unihra/)
[![Python Versions](https://img.shields.io/pypi/pyversions/unihra.svg?style=flat-square)](https://pypi.org/project/unihra/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://github.com/Unihra/unihra_sdk/blob/main/LICENSE)

**SEO и семантический анализ вашей страницы и конкурентов.**  
Сравнение контента, поиск семантических пробелов и рекомендации по зонам страницы и векторной семантике.

[English](../README.md) · Русский

---

### Ресурсы

| | |
| :---: | :--- |
| **Продукт** | [unihra.ru](https://unihra.ru) — веб-интерфейс |
| **Документация API** | [unihra.ru/docs](https://unihra.ru/docs) |
| **Ключ API** | Telegram: [@UniHRA_bot](https://t.me/UniHRA_bot) |
| **Новости** | [@mncosine](https://t.me/mncosine) |

</div>

---

## Возможности

- **Семантический контекст (зоны)** — вес слова зависит от того, где оно стоит (title, H1–H6, текст) и от расстояния до ваших целевых запросов; выдаются конкретные рекомендации (что добавить в title, заголовки и т.д.).
- **Структура страницы** — заголовки, мета-теги и метрики контента для вашего URL и каждого URL конкурента.
- **Сравнение слов (TF‑IDF)** — рекомендуемое действие по термину (добавить, усилить, снизить, ок).
- **Фразы (n‑граммы)** — устойчивые формулировки на страницах конкурентов.
- **Векторные / LSI термины (DrMaxs)** — семантически близкая лексика к теме.
- **Cookies** — опционально строки cookie по URL для страниц за логином или ограничениями.
- **Стриминг** — клиент сам обрабатывает поток событий анализа и ждёт завершения.
- **Повторы запросов** — опциональные повторы HTTP с уступкой для нестабильной сети.
- **Отчёты** — многостраничный Excel с оформлением (опциональные зависимости).
- **Прогресс** — опциональный прогресс-бар в ноутбуках при установленном `tqdm`.

---

## Установка

```bash
pip install unihra
```

**Дополнительные наборы** (ставьте то, что нужно):

| Команда | Состав |
|--------|--------|
| `pip install "unihra[report]"` | Экспорт в Excel (`pandas`, `openpyxl`) |
| `pip install "unihra[full]"` | Отчёты + прогресс-бар (`tqdm`) |
| `pip install "unihra[mcp]"` | MCP-сервер для Cursor / Claude Code (нужен **Python 3.10+**) |

Либо установите пакеты вручную, например: `pip install pandas openpyxl tqdm`.

---

## Быстрый старт

### 1. Запуск анализа

Передайте **`queries`** — поисковые намерения, под которые вы оптимизируетесь — тогда зональные рекомендации и анализ пробелов будут осмысленными.

```python
from unihra import UnihraClient

client = UnihraClient(api_key="ВАШ_API_КЛЮЧ", max_retries=3)

result = client.analyze(
    own_page="https://example.com/catalog/tovar",
    competitors=[
        "https://competitor.ru/item/1",
        "https://market.ru/product/2",
    ],
    queries=["купить товар", "лучший товар 2025"],
    lang="ru",
    url_cookies={
        "https://example.com/catalog/tovar": "PHPSESSID=12345; age_confirmed=yes",
    },
    verbose=True,
)

gaps = result.get("semantic_context_analysis", [])
pages = result.get("page_structure", [])

print(f"Строк семантических пробелов: {len(gaps)}")
for p in pages:
    print(p["url"], "—", p["meta_tags"]["title"])
```

### 2. Сохранение отчёта в Excel

Обычно в книге есть листы вроде *Page Structure*, *Semantic Gaps*, *Word Analysis*, *N‑Grams* и разделы по векторам.

```python
client.save_report(result, "seo_audit.xlsx")
```

---

## Состав результата анализа

SDK возвращает **словарь Python**, согласованный с API. Ключи приводятся к виду **snake_case**.

<details>
<summary><b>1. Структура страницы (page structure)</b></summary>

**Список** страниц (сначала ваша, затем конкуренты). В каждом элементе:

- `url`
- `meta_tags` — `title`, `description` и др.
- `content` — `h1_heading`, `heading_structure_raw` (иерархия заголовков текстом)
- `metrics` — например `char_count_no_spaces`, `uniqueness_percentage`

</details>

<details>
<summary><b>2. Семантический контекст (semantic context analysis)</b></summary>

Зональное сравнение лемм относительно ваших запросов:

- `lemma` — начальная форма  
- `competitor_avg_score`, `own_score` — взвешенные баллы (0.0 у вас часто значит «нет или слабая зона»)  
- `gap` — отставание от конкурентов (чем больше, тем приоритетнее)  
- `coverage_percent` — доля конкурентов, у которых термин в сильном контексте  
- `context_snippet` — короткий пример с конкурентов  
- `recommendation` — что сделать (например, добавить в Title/H1)

```json
{
  "lemma": "аккумулятор",
  "competitor_avg_score": 10.5,
  "own_score": 0.0,
  "gap": 10.5,
  "coverage_percent": 80.0,
  "context_snippet": "купить мощный аккумулятор",
  "recommendation": "Добавить в Title/H1"
}
```

</details>

<details>
<summary><b>3. Сравнение блоков / лексика (block comparison)</b></summary>

Сравнение в духе TF‑IDF:

- `frequency`, `frequency_own_page`, `pct_target_comp_avg`
- `action_needed` — после нормализации для русского языка в интерфейсе могут быть подписи вроде «Добавить», «Уменьшить», «Ок»; для английского — `add`, `increase`, `decrease`, `ok`

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
<summary><b>4. N‑граммы</b></summary>

Устойчивые фразы (биграммы / триграммы) и на скольких страницах конкурентов они встречаются.

- `ngram`, `pages_count` и др.

</details>

<details>
<summary><b>5. DrMaxs (векторы / LSI)</b></summary>

Семантические соседи темы, сгруппированные (например `by_frequency`, `by_tfidf`), с `similarity_score` и признаком наличия слова на вашей странице.

```json
{
  "word": "логистика",
  "similarity_score": 0.89,
  "present_on_own_page": false
}
```

</details>

---

## Командная строка

```bash
python -m unihra \
  --key "ВАШ_API_КЛЮЧ" \
  --own "https://site.ru/page" \
  --comp "https://comp1.ru/p1" \
  --comp "https://comp2.ru/p2" \
  --query "основной запрос" \
  --cookies "PHPSESSID=12345" \
  --save audit.xlsx \
  --verbose
```

| Параметр | Назначение |
|----------|------------|
| `--own` | URL вашей страницы (обязательно) |
| `--comp` | URL конкурента (повторите для нескольких; нужен хотя бы один) |
| `--query` | Целевой запрос (повторяемо; желательно указать) |
| `--lang` | `ru` или `en` (по умолчанию `ru`) |
| `--cookies` | Строка cookie для вашей страницы |
| `--save` | Файл отчёта `.xlsx` или `.csv` |
| `--retries` | Число повторов HTTP |
| `--verbose` | Показать прогресс |
| `--no-style` | Excel без дополнительного оформления |

Параметр `--key` можно не указывать, если задана переменная окружения **`UNIHRA_API_KEY`**.  
Без `--save` и без `--verbose` в консоль выводится JSON.

---

## Cursor, Claude и другие MCP-клиенты

Опциональный **MCP-сервер** позволяет совместимым ассистентам вызывать Unihra как **инструменты**, а не скачивать страницы самостоятельно.

1. Установка: `pip install "unihra[mcp]"` (нужен **Python 3.10+**).
2. Ключ API: переменная **`UNIHRA_API_KEY`** или флаг `--key` при запуске сервера.
3. Запуск: `python -m unihra.mcp_server` или команда `unihra-mcp`.
4. В настройках MCP вашего клиента укажите этот интерпретатор Python и модуль (см. пример ниже).

**Большие ответы:** инструмент `unihra_analyze` возвращает **отфильтрованные, компактные** данные (плюс краткое поле `_meta`), чтобы ответ помещался в типичные лимиты контекста у LLM. Полный объём «как в сыром API» доступен через **Python SDK** или **HTTP API** напрямую. При необходимости пороги можно менять через параметры фильтров, которые описаны у инструмента.

**Инструменты (кратко)**

| Инструмент | Назначение |
|------------|------------|
| `unihra_health` | Проверка доступности сервиса |
| `unihra_analyze` | Полный анализ с фильтрацией шума по умолчанию |
| `unihra_analyze_stream_events` | Тот же запуск пошагово (SSE), например чтобы взять `task_id` |
| `unihra_get_page_structure` | Отчёт по заголовкам/мета для завершённого `task_id` |
| `unihra_get_gaps` | Перегруппировка семантических пробелов из уже полученного результата |
| `unihra_get_vectors` | Векторные / LSI слова из уже полученного результата |
| `unihra_get_word_actions` | Слова TF‑IDF по категориям действий |
| `unihra_get_ngrams` | Фразы из уже полученного результата |

**Пример конфигурации MCP** (подставьте свой путь к `python.exe`):

```json
{
  "mcpServers": {
    "unihra": {
      "command": "python",
      "args": ["-m", "unihra.mcp_server"],
      "env": {
        "UNIHRA_API_KEY": "YOUR_KEY_HERE"
      }
    }
  }
}
```

Дополнительно: в репозитории есть `examples/mcp_server_usage.py` — печатает пример конфигурации и показывает локальный запуск сервера.

---

<div align="center">

**Команда Unihra**

[Telegram — новости](https://t.me/mncosine) · [unihra.ru](https://unihra.ru) · [Ключ API — @UniHRA_bot](https://t.me/UniHRA_bot)

</div>
