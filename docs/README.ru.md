# Unihra Python SDK

Официальный клиент для [Unihra](https://unihra.ru): семантический и SEO-анализ страниц, сравнение с конкурентами, отчёты.  
Англоязычная версия: [README.md](../README.md).

---

## ✨ Возможности

*   **🧠 Семантический анализ контекста**: Алгоритм анализирует не просто частоту слов, а их вес в зонах документа (`H1`, `Title`, `Strong`) и расстояние до ключевого запроса.
*   **🏗️ Анализ структуры страницы**: Автоматически извлекает и сравнивает заголовки H1-H6, Meta-теги и техническую уникальность контента по **всем** анализируемым страницам.
*   **🍪 Работа с закрытым контентом**: Поддержка передачи Cookies для анализа страниц за логином или заглушкой.
*   **⚡️ Полная абстракция API**: Библиотека берет на себя работу с очередями, SSE-стримингом и обработкой ошибок.
*   **🐼 Интеграция с Pandas**: Экспорт сложных данных в DataFrame или красивый Excel отчет одной строкой.
*   **🛡️ Smart Retries**: Автоматическая обработка лимитов (`429`) и разрывов соединения.
*   **🪐 Jupyter Support**: Красивые прогресс-бары при работе в ноутбуках.

## 📦 Установка

```bash
pip install unihra
```

## ⚡️ Быстрый старт

### 1. Запуск анализа

Для получения рекомендаций по структуре (H1-H6) обязательно передавайте параметр `queries` (целевые поисковые запросы, под которые оптимизируется страница).

```python
from unihra import UnihraClient

# Инициализация
client = UnihraClient(api_key="ВАШ_КЛЮЧ")

# Запуск (синхронный режим)
result = client.analyze(
    own_page="https://example.com/catalog/tovar",
    competitors=[
        "https://competitor.ru/item/1",
        "https://market.ru/product/2"
    ],
    queries=["купить товар", "лучший товар 2025"],  # Важно для анализа зон
    lang="ru",
    # Опционально: Куки для доступа к закрытым страницам
    url_cookies={
        "https://example.com/catalog/tovar": "PHPSESSID=12345; age_confirmed=yes"
    },
    verbose=True  # Включает прогресс-бар
)

print("Анализ завершен!")

# Получаем список структур (Своя страница + Конкуренты)
structures = result.get('page_structure', [])

if structures:
    my_page = structures[0]
    print(f"Мой H1: {my_page['content']['h1_heading']}")
    print(f"Уникальность: {my_page['metrics']['uniqueness_percentage']}%")
```

### 2. Экспорт отчета

Создает `.xlsx` файл с вкладками: *Page Structure*, *Semantic Gaps*, *Word Analysis*, *N-Grams*, *Vectors*.

```python
client.save_report(result, "seo_audit.xlsx")
```

## 📊 Структура данных и Внутрянка

Результат анализа разделен на 5 логических блоков.

<details>
<summary><b>1. Page Structure (Структура страницы)</b></summary>

Возвращает **список** объектов. Каждый объект содержит:

*   `url`: Ссылка на страницу.
*   `content`: Заголовки H1-H6 (`h1_heading`, `heading_structure_raw`).
*   `meta_tags`: Мета-теги (`title`, `description`).
*   `metrics`: Технические метрики (`uniqueness_percentage`, `char_count_no_spaces`).

</details>

<details>
<summary><b>2. Semantic Context Analysis (Зональный анализ и Разрывы)</b></summary>

**Самый важный блок.** Алгоритм взвешивает слова. Слово в `Title` получает больше баллов, чем слово в футере. Также учитывается расстояние слова до вашего `query`.

*   `lemma`: Лемма слова.
*   `competitor_avg_score`: Средний взвешенный балл конкурентов.
*   `own_score`: Ваш балл. Если `0.0`, значит слово отсутствует в важных зонах.
*   `gap`: Величина отставания. Чем больше, тем важнее слово.
*   `coverage_percent`: Процент конкурентов, у которых это слово есть в контексте.
*   `context_snippet`: Пример использования (триграмма) из текстов конкурентов.
*   `recommendation`: Конкретное ТЗ (например, *"Добавить в Title/H1"*, *"Добавить в H2/H3"* или *"Вписать в контекст"*).

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
<summary><b>3. Block Comparison (Лексика)</b></summary>

Классическое сравнение TF-IDF и "мешка слов". Помогает найти переспам или недоспам общей лексики.

*   `action_needed`: Рекомендация (`Добавить`, `Уменьшить`, `Ок`).
*   `pct_target_comp_avg`: Средняя плотность (%) у конкурентов.
*   `frequency_own_page`: Абсолютное число вхождений у вас.

</details>

<details>
<summary><b>4. N-grams Analysis (Фразы)</b></summary>

Показывает устойчивые словосочетания.

*   `ngram`: Фраза (биграмма или триграмма).
*   `pages_count`: На скольких сайтах конкурентов эта фраза встречается точь-в-точь.

</details>

<details>
<summary><b>5. DrMaxs (Векторный AI)</b></summary>

Использует нейросетевые эмбеддинги для поиска **LSI (Latent Semantic Indexing)**. Находит слова, которые **по смыслу** должны быть на странице, даже если конкуренты не используют их прямо, но используют их синонимы.

*   `by_frequency`: Самые частотные вектора.
*   `by_tfidf`: Самые "важные" вектора.
*   `similarity_score`: Семантическая близость к тематике (0.0 - 1.0).

</details>

## 💻 Работа через CLI

```bash
# Пример использования в терминале
python -m unihra \
  --key "ВАШ_КЛЮЧ" \
  --own "https://site.ru/page" \
  --comp "https://comp1.ru/p1" \
  --comp "https://comp2.ru/p2" \
  --query "запрос 1" \
  --cookies "PHPSESSID=12345" \
  --save audit.xlsx \
  --verbose
```

## 🤖 MCP-сервер (Model Context Protocol)

В SDK есть опциональный **MCP-сервер**: редакторы вроде **Cursor** или **Claude Code** могут вызывать анализ Unihra через [Model Context Protocol](https://modelcontextprotocol.io/). Под капотом используется тот же `UnihraClient`; без установки extra поведение обычного SDK не меняется.

**Требования:** Python **3.10+** и extra `mcp` (пакет `mcp` из PyPI подтягивается только на поддерживаемых версиях Python).

```bash
pip install "unihra[mcp]"
```

**Запуск** (ключ через флаг или переменную `UNIHRA_API_KEY`):

```bash
python -m unihra.mcp_server --key ВАШ_API_КЛЮЧ
# или
export UNIHRA_API_KEY=ВАШ_API_КЛЮЧ
python -m unihra.mcp_server
```

Также доступна консольная команда `unihra-mcp` (эквивалент `python -m unihra.mcp_server`).

**Доп. параметры:** `--retries` (число повторов HTTP, по умолчанию `3`), `--base-url` (базовый URL API, по умолчанию `https://unihra.ru`).

**Инструменты (tools):** `unihra_health`, `unihra_analyze`, `unihra_analyze_stream_events`, `unihra_get_page_structure`, `unihra_extract_section`, `unihra_summarize_gaps`, `unihra_summarize_vectors`, `unihra_word_actions`.

**Пример конфигурации MCP** (в духе Cursor / Claude Code):

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

Пример скрипта в репозитории: `examples/mcp_server_usage.py`.
