from unihra import UnihraClient, InsufficientCreditsError, UnihraError

API_KEY = "YOUR_REAL_API_KEY"

client = UnihraClient(API_KEY)

# Проверка баланса перед запуском (стандартный анализ — 1 кредит,
# с triplet_analysis=True — 5 кредитов за Граф знаний).
limits = client.get_limits()
print(f"Баланс: {limits.get('current_balance')} кредитов")

print("Начинаем анализ...")
try:
    result = client.analyze(
        own_page="https://example.com/product",
        competitors=["https://competitor.com/p1"],
        triplet_analysis=False,
    )
except InsufficientCreditsError as e:
    print("Недостаточно кредитов:", e)
    raise SystemExit(1)
except UnihraError as e:
    print("Ошибка:", e)
    raise SystemExit(1)

print("Готово! Секции результата:", sorted(result.keys()))

# Покрытие: какие из запрошенных страниц вошли в анализ.
page_status = result.get("_meta", {}).get("page_status", {})
parsed = page_status.get("parsed", [])
failed = page_status.get("failed", [])
print(f"В анализ вошло страниц: {len(parsed)}")
for page in failed:
    print("Не удалось включить:", page.get("url"))

# Экспорт в Excel (требует pip install 'unihra[excel]').
# client.save_report(result, "report.xlsx")
