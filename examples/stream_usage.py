from unihra import UnihraClient, UnihraError

API_KEY = "YOUR_API_KEY"
client = UnihraClient(API_KEY)

print("Анализ с прогрессом:")
try:
    # triplet_analysis=True включит расширенный Граф знаний (5 кредитов).
    for event in client.analyze_stream(
        "https://site.com",
        ["https://comp.com"],
        triplet_analysis=False,
    ):
        state = event.get("state")
        progress = event.get("progress", 0)
        details = event.get("details") or {}
        message = details.get("message", "")
        print(f"\r{state} {progress}% {message[:50]:<50}", end="", flush=True)

        if state == "SUCCESS":
            print("\nУспешно завершено!")
            result = event.get("result", {})

            # Покрытие: запрошенные страницы, не вошедшие в анализ.
            failed = event.get("page_status", {}).get("failed", [])
            if failed:
                print("Не вошли в анализ:", [p.get("url") for p in failed])
except UnihraError as e:
    print("\nОшибка:", e)
