# 🛠️ Unihra Python SDK

[![PyPI version](https://img.shields.io/pypi/v/unihra.svg)](https://pypi.org/project/unihra/)
[![Python Versions](https://img.shields.io/pypi/pyversions/unihra.svg)](https://pypi.org/project/unihra/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Unihra/unihra_sdk/blob/main/LICENSE)
[![Build Status](https://github.com/Unihra/unihra_sdk/actions/workflows/publish.yml/badge.svg)](https://github.com/Unihra/unihra_sdk/actions)

Official Python SDK for Unihra API. Enterprise-grade SEO analysis with SSE streaming, Pandas integration, and Jupyter support.

---

### 🗺 Navigation / Навигация
*   **[🇬🇧 English Documentation](#-english-documentation)**
    *   [Installation](#-installation)
    *   [Quick Start](#-quick-start)
    *   [Jupyter Support](#-jupyter-notebook-support)
    *   [Data Model](#-response-structure-data-model)
*   **[🇷🇺 Документация на русском](#-документация-на-русском)**
    *   [Установка](#-установка)
    *   [Быстрый старт](#-быстрый-старт)
    *   [Работа в Jupyter](#-поддержка-jupyter-notebook)
    *   [Структура данных](#-структура-ответа-json)

---

## 🇬🇧 English Documentation

### ✨ Key Features

*   **⚡️ SSE Streaming Abstraction**: Automatically handles server-sent events. No manual socket management required.
*   **🐼 Pandas & Excel Ready**: Export analysis results to `DataFrame`, `.xlsx`, or `.csv` with a single line of code.
*   **🛡️ Smart Retries**: Built-in exponential backoff strategy to handle API Rate Limits (`429`) and server errors (`50x`) gracefully.
*   **🪐 Jupyter Native**: Detects notebook environments and displays interactive HTML progress bars.

### 📦 Installation

```bash
pip install unihra
```

*Optional: To enable Excel export and progress bars:*
```bash
pip install pandas openpyxl tqdm
```

### 🚀 Quick Start

#### 1. Synchronous Analysis (Blocking)
The simplest way to get results. The client handles the queue and polling.

```python
from unihra import UnihraClient

# Initialize with Smart Retries (recommended for production)
client = UnihraClient(api_key="YOUR_API_KEY", max_retries=3)

# Blocks until analysis is complete
result = client.analyze(
    own_page="https://mysite.com/product",
    competitors=["https://competitor.com/item1", "https://competitor.com/item2"],
    lang="en"
)

print(f"Task ID: {result.get('task_id')}")
```

#### 2. Export to Excel / Pandas
Convert complex nested JSON into ready-to-use tables.

```python
# Get a Pandas DataFrame
df = client.get_dataframe(result, section="block_comparison")

# Save full report (creates multiple sheets for Words and N-grams)
client.save_report(result, "seo_report.xlsx")
```

### 🪐 Jupyter Notebook Support

If you are working in **JupyterLab**, **Google Colab**, or **VS Code Notebooks**, pass `verbose=True`.
The library will automatically use `tqdm` to render a visual HTML progress bar instead of text logs.

```python
result = client.analyze(
    own_page="https://mysite.com", 
    competitors=["https://comp.com"],
    verbose=True  # <--- Triggers interactive progress bar
)
```

### 📊 Response Structure (Data Model)

The SDK returns a dictionary reflecting the API response. The most important section is `block_comparison`.

| Field | Description |
|-------|-------------|
| `block_comparison` | Main SEO analysis. Compares your page vs competitors. |
| `action_needed` | **Key Metric**. Suggests action: `add`, `increase`, `decrease`, or `ok`. |
| `ngrams_analysis` | Analysis of phrases (Bigrams/Trigrams). |
| `drmaxs` | Vector analysis (TF-IDF, Similarity scores). |

**Full JSON Schema:**
```json
{
  "task_id": "uuid-1234-5678",
  "state": "SUCCESS",
  "result": {
    "block_comparison": [
      {
        "word": "buy",
        "lemma": "buy", 
        "frequency": 12.5,
        "frequency_own_page": 2,
        "pct_target": 1.2,
        "pct_target_comp_avg": 2.5,
        "ratio_comp_avg": 0.48,
        "action_needed": "increase", 
        "present_on_own_page": true
      }
    ],
    "ngrams_analysis": [
      {
        "ngram": "buy online",
        "ngram_type": "bigrams",
        "frequency_sum": 45.0,
        "frequency_avg": 4.5,
        "percentage_avg": 0.8,
        "pages_count": 5
      }
    ],
    "drmaxs": {
      "by_frequency": [
        {
          "word": "delivery",
          "frequency": 8.0,
          "similarity_score": 0.95
        }
      ],
      "by_tfidf": [...],
      "by_sites_count": [...]
    }
  }
}
```

### 💻 CLI Usage
You can run analysis directly from the terminal:

```bash
# Analyze and save to Excel with verbose output
python -m unihra --key "KEY" --own "https://site.com" --comp "https://comp.com" --save report.xlsx --verbose
```

### ⚠️ Exception Handling

| Exception Class | Description |
|-----------------|-------------|
| `ParserError` (1001) | Failed to download/parse the target page. |
| `AnalysisServiceError` (1002)| Internal engine failure. |
| `CriticalOwnPageError` (1003)| Your page is unavailable (404/500). |
| `UnihraConnectionError` | Network timeouts or connection issues. |


---

## 🇷🇺 Документация на русском

### ✨ Основные возможности

*   **⚡️ Полная абстракция API**: Библиотека берет на себя всю работу с SSE (Server-Sent Events), очередями и пулингом.
*   **🐼 Интеграция с Pandas**: Получайте `DataFrame` или выгружайте отчеты в `Excel` одной командой.
*   **🛡️ Smart Retries (Умные повторы)**: Клиент автоматически обрабатывает лимиты API (`429`) и кратковременные сбои сети.
*   **🪐 Поддержка Jupyter**: Красивые, интерактивные прогресс-бары при запуске в ноутбуках.

### 📦 Установка

```bash
pip install unihra
```

*Рекомендуется установить дополнительные пакеты для работы с Excel:*
```bash
pip install pandas openpyxl tqdm
```

### 🚀 Быстрый старт

#### 1. Синхронный режим
Получение результата одной командой.

```python
from unihra import UnihraClient

# max_retries=3 включает механизм защиты от сбоев сети
client = UnihraClient(api_key="ВАШ_КЛЮЧ", max_retries=3)

# Метод ждет окончания анализа
result = client.analyze(
    own_page="https://mysite.com/product",
    competitors=["https://competitor.com/item1", "https://competitor.com/item2"],
    lang="ru"
)

print(f"Найдено слов: {len(result.get('block_comparison', []))}")
```

#### 2. Экспорт данных
```python
# Получить Pandas DataFrame для аналитики
df = client.get_dataframe(result, section="block_comparison")

# Сохранить полный отчет (создаст вкладки "Word Analysis" и "N-Grams")
client.save_report(result, "отчет.xlsx")
```

### 🪐 Поддержка Jupyter Notebook

Если вы запускаете код в **Jupyter**, **Colab** или **VS Code**, добавьте флаг `verbose=True`.
Библиотека определит среду и отобразит графический прогресс-бар вместо текстового вывода.

```python
result = client.analyze(
    own_page="https://mysite.com", 
    competitors=["https://comp.com"],
    verbose=True  # <--- Включает графический прогресс-бар
)
```

### 📊 Структура ответа (JSON)

Результат содержит вложенные структуры данных.

| Поле | Описание |
|------|----------|
| `block_comparison` | Сравнение частотности слов (Word Bag). |
| `action_needed` | **Главная метрика**. Рекомендация: `add` (добавить), `increase` (увеличить), `decrease` (уменьшить) или `ok`. |
| `ngrams_analysis` | Анализ фраз (биграммы и триграммы). |
| `drmaxs` | Семантический векторный анализ. |

**Пример JSON ответа:**
```json
{
  "task_id": "uuid-1234-5678",
  "state": "SUCCESS",
  "result": {
    "block_comparison": [
      {
        "word": "buy",
        "lemma": "buy", 
        "frequency": 12.5,
        "frequency_own_page": 2,
        "pct_target": 1.2,
        "pct_target_comp_avg": 2.5,
        "ratio_comp_avg": 0.48,
        "action_needed": "increase", 
        "present_on_own_page": true
      }
    ],
    "ngrams_analysis": [
      {
        "ngram": "buy online",
        "ngram_type": "bigrams",
        "frequency_sum": 45.0,
        "frequency_avg": 4.5,
        "percentage_avg": 0.8,
        "pages_count": 5
      }
    ],
    "drmaxs": {
      "by_frequency": [
        {
          "word": "delivery",
          "frequency": 8.0,
          "similarity_score": 0.95
        }
      ],
      "by_tfidf": [...],
      "by_sites_count": [...]
    }
  }
}
```

### 💻 Работа через консоль (CLI)

```bash
# Запуск анализа с сохранением в Excel и выводом прогресса
python -m unihra --key "КЛЮЧ" --own "https://site.com" --comp "https://comp.com" --save report.xlsx --verbose
```

### ⚠️ Обработка ошибок

Библиотека преобразует коды ошибок API в Python-исключения:

| Ошибка | Код | Описание |
|--------|-----|----------|
| `ParserError` | 1001 | Не удалось скачать страницу (проверьте доступность сайта). |
| `CriticalOwnPageError` | 1003 | Ваша страница не отвечает (404/500). |
| `ReportGenerationError`| 1004 | Ошибка при формировании итогового отчета. |


---
<p align="center">
    Developed with ❤️ by <a href="https://github.com/Unihra/unihra_sdk">Unihra Team</a>
</p>
