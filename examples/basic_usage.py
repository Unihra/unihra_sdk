from unihra import UnihraClient

API_KEY = "YOUR_REAL_API_KEY"

client = UnihraClient(API_KEY)

print("Начинаем анализ...")
try:
    result = client.analyze(
        own_page="https://example.com/product",
        competitors=["https://competitor.com/p1"]
    )
    print("Готово! Результат:", result.keys())
except Exception as e:
    print("Ошибка:", e)
