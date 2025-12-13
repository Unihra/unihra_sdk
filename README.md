# 🛠️ Unihra Python SDK

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/unihra.svg?style=flat-square&color=blue)](https://pypi.org/project/unihra/)
[![Python Versions](https://img.shields.io/pypi/pyversions/unihra.svg?style=flat-square)](https://pypi.org/project/unihra/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://github.com/Unihra/unihra_sdk/blob/main/LICENSE)

**Enterprise-grade SEO & Semantic Analysis SDK.**<br>
*Compare content, find semantic gaps, and generate structure recommendations using Vector AI & Zone Analysis.*

[🇬🇧 English](#-english-documentation) | [🇷🇺 Русский](#-russian-documentation)

---

### 🚀 Ecosystem & Resources

| **Web UI** | **API Docs** | **Get API Key** | **News Channel** |
| :---: | :---: | :---: | :---: |
| 🖥️ [**unihra.ru**](https://unihra.ru) | 📚 [**unihra.ru/docs**](https://unihra.ru/docs) | 🔑 [**@UniHRA_bot**](https://t.me/UniHRA_bot) | 📢 [**@mncosine**](https://t.me/mncosine) |
| *Visual Sandbox* | *REST API Spec* | *Get Free Key Here* | *Updates & Tips* |

</div>

---

## 🇬🇧 English Documentation

### ✨ Key Features

*   **🧠 Semantic Context Analysis**: Goes beyond simple keyword frequency. It analyzes HTML zones (`H1`, `Title`, `Strong`) and the distance of terms to your target query to provide "Add to Title/H1" recommendations.
*   **⚡️ SSE Streaming Abstraction**: Automatically handles server-sent events, queue polling, and connection stability.
*   **🐼 Pandas & Excel Ready**: Export multi-sheet reports (`.xlsx`) with conditional formatting in one line of code.
*   **🛡️ Smart Retries**: Built-in exponential backoff strategy for network resilience.
*   **🪐 Jupyter Native**: Interactive HTML progress bars for Notebook environments.

### 📦 Installation

```bash
pip install unihra
```
*Optional: Install dependencies for Excel export and progress bars:*
```bash
pip install pandas openpyxl tqdm
```

### ⚡️ Quick Start

#### 1. Full Analysis with Context
To enable Zone Analysis and Gap detection, you must provide `queries` (the main keywords you want to rank for).

```python
from unihra import UnihraClient

# Initialize client
client = UnihraClient(api_key="YOUR_API_KEY", max_retries=3)

# Run Analysis
result = client.analyze(
    own_page="https://example.com/my-product",
    competitors=[
        "https://competitor.com/top-product", 
        "https://market-leader.com/item"
    ],
    queries=["buy widget", "best widgets 2025"], # <--- Required for Structure Recommendations
    lang="en",
    verbose=True # Shows interactive progress bar
)

# Access the data
gaps = result.get('semantic_context_analysis', [])
print(f"Found {len(gaps)} semantic gaps.")
```

#### 2. Export to Excel
Generate a professional SEO report with multiple sheets: *Semantic Gaps*, *Word Analysis*, *N-Grams*, and *Vectors*.

```python
client.save_report(result, "seo_report.xlsx")
```

### 📊 Data Model & Internals

The SDK returns a Python dictionary mirroring the API response. Here is a breakdown of each logic block:

<details>
<summary><b>1. Semantic Context Analysis (Zone Analysis)</b></summary>

**This is the most critical part of the analysis.** It calculates a weighted score based on *where* a word appears (Title > H1 > H2 > Text) and *how close* it is to the target query.

*   `lemma`: The base form of the word.
*   `competitor_avg_score`: The weighted score of this word across top competitors.
*   `own_score`: Your weighted score. If `0.0`, the word is missing or used in a very weak zone (e.g., footer).
*   `gap`: The difference between competitors and you. Higher gap = higher priority.
*   `coverage_percent`: Percentage of competitors that use this word in a significant context.
*   `context_snippet`: A 3-word phrase (trigram) showing how competitors use this word.
*   `recommendation`: Actionable advice based on the gap (e.g., *"Add to Title/H1"*, *"Add to H2/H3"*, *"Mention in Body"*).

```json
{
  "lemma": "battery",
  "competitor_avg_score": 10.5,
  "own_score": 0.0,
  "gap": 10.5,
  "coverage_percent": 80.0,
  "context_snippet": "long lasting battery life",
  "recommendation": "Add to Title/H1" 
}
```
</details>

<details>
<summary><b>2. Block Comparison (Lexical Analysis)</b></summary>

Classical TF-IDF comparison. Useful for finding over-optimization (spam) or general content relevancy.

*   `frequency`: Weighted frequency (TF).
*   `frequency_own_page`: How many times it appears on your page.
*   `pct_target_comp_avg`: Average density (%) on competitor pages.
*   `action_needed`: Simple recommendation (`add`, `increase`, `decrease`, `ok`).

```json
{
  "word": "price",
  "frequency": 12.5,
  "pct_target_comp_avg": 2.5,
  "action_needed": "increase",
  "present_on_own_page": true
}
```
</details>

<details>
<summary><b>3. N-grams Analysis (Phrases)</b></summary>

Analyzes stable word combinations (Bigrams and Trigrams).

*   `ngram`: The phrase (e.g., "fast delivery").
*   `pages_count`: On how many competitor sites this exact phrase appears.

</details>

<details>
<summary><b>4. DrMaxs (Vector AI)</b></summary>

Uses Neural Network Embeddings to find **Latent Semantic Indexing (LSI)** words. These are words that are semantically close to your topic but might not be direct synonyms.

*   `by_frequency`: Most frequent semantically related words.
*   `by_tfidf`: Most unique/important semantically related words.
*   `similarity_score`: Cosine similarity to the topic vector (0.0 to 1.0).

```json
{
  "word": "logistics",
  "similarity_score": 0.89,
  "present_on_own_page": false
}
```
</details>

### 💻 CLI Usage

You can use the SDK directly from your terminal.

```bash
# Run analysis and save to Excel
python -m unihra \
  --key "YOUR_KEY" \
  --own "https://mysite.com" \
  --comp "https://comp1.com" \
  --comp "https://comp2.com" \
  --query "main keyword" \
  --save report.xlsx \
  --verbose
```

---

## 🇷🇺 Russian Documentation

### ✨ Возможности

*   **🧠 Семантический анализ контекста**: Алгоритм анализирует не просто частоту слов, а их вес в зонах документа (`H1`, `Title`, `Strong`) и расстояние до ключевого запроса.
*   **⚡️ Полная абстракция API**: Библиотека берет на себя работу с очередями, SSE-стримингом и обработкой ошибок.
*   **🐼 Интеграция с Pandas**: Экспорт сложных данных в DataFrame или красивый Excel отчет одной строкой.
*   **🛡️ Smart Retries**: Автоматическая обработка лимитов (`429`) и разрывов соединения.
*   **🪐 Jupyter Support**: Красивые прогресс-бары при работе в ноутбуках.

### 📦 Установка

```bash
pip install unihra
```

### ⚡️ Быстрый старт

#### 1. Запуск анализа
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
    queries=["купить товар", "лучший товар 2025"], # <--- Важно для анализа зон
    lang="ru",
    verbose=True # Включает прогресс-бар
)

print("Анализ завершен!")
```

#### 2. Экспорт отчета
Создает `.xlsx` файл с вкладками: *Semantic Gaps*, *Word Analysis*, *N-Grams*, *Vectors*.

```python
client.save_report(result, "seo_audit.xlsx")
```

### 📊 Структура данных и Внутрянка

Результат анализа разделен на 4 логических блока.

<details>
<summary><b>1. Semantic Context Analysis (Зональный анализ и Разрывы)</b></summary>

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
<summary><b>2. Block Comparison (Лексика)</b></summary>

Классическое сравнение TF-IDF и "мешка слов". Помогает найти переспам или недоспам общей лексики.

*   `action_needed`: Рекомендация (`Добавить`, `Уменьшить`, `Ок`).
*   `pct_target_comp_avg`: Средняя плотность (%) у конкурентов.
*   `frequency_own_page`: Абсолютное число вхождений у вас.

</details>

<details>
<summary><b>3. N-grams Analysis (Фразы)</b></summary>

Показывает устойчивые словосочетания.

*   `ngram`: Фраза (биграмма или триграмма).
*   `pages_count`: На скольких сайтах конкурентов эта фраза встречается точь-в-точь.

</details>

<details>
<summary><b>4. DrMaxs (Векторный AI)</b></summary>

Использует нейросетевые эмбеддинги для поиска **LSI (Latent Semantic Indexing)**. Находит слова, которые **по смыслу** должны быть на странице, даже если конкуренты не используют их прямо, но используют их синонимы.

*   `by_frequency`: Самые частотные вектора.
*   `by_tfidf`: Самые "важные" вектора.
*   `similarity_score`: Семантическая близость к тематике (0.0 - 1.0).

</details>

### 💻 Работа через CLI

```bash
# Пример использования в терминале
python -m unihra \
  --key "ВАШ_КЛЮЧ" \
  --own "https://site.ru/page" \
  --comp "https://comp1.ru/p1" \
  --comp "https://comp2.ru/p2" \
  --query "запрос 1" \
  --save audit.xlsx \
  --verbose
```

---

<div align="center">
    <p>Developed with ❤️ by <b>Unihra Team</b></p>
    <p>
        <a href="https://t.me/mncosine">Telegram News</a> • 
        <a href="https://unihra.ru">Web Service</a> • 
        <a href="https://t.me/UniHRA_bot">Get API Key Bot</a>
    </p>
</div>
