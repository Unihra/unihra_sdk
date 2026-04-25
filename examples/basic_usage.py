from unihra import UnihraClient

API_KEY = "YOUR_REAL_API_KEY"

client = UnihraClient(API_KEY)

print("Начинаем анализ...")
try:
    # Стандартный анализ — 1 кредит.
    # Передайте triplet_analysis=True, чтобы дополнительно получить Граф знаний (5 кредитов).
    result = client.analyze(
        own_page="https://example.com/product",
        competitors=["https://competitor.com/p1"],
        triplet_analysis=False,
    )
    print("Готово! Результат:", result.keys())
except Exception as e:
    print("Ошибка:", e)
