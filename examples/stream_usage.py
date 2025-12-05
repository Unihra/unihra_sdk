from unihra import UnihraClient
import sys

API_KEY = "YOUR_API_KEY"
client = UnihraClient(API_KEY)

print("Анализ с прогрессом:")
try:
    for event in client.analyze_stream("https://site.com", ["https://comp.com"]):
        state = event.get('state')
        print(f"\rТекущий статус: {state}", end="")
        sys.stdout.flush()

        if state == 'SUCCESS':
            print("\nУспешно завершено!")
except Exception as e:
    print("\nОшибка:", e)
