"""История анализов по API-ключу: список, выборка, публикация ссылкой."""
from unihra import UnihraClient

API_KEY = "YOUR_API_KEY"
client = UnihraClient(API_KEY)

# Все анализы, сохранённые под этим ключом.
analyses = client.list_analyses()
for item in analyses:
    print(item.get("task_id"), item.get("own_page"), item.get("created_at"))

if analyses:
    task_id = analyses[0]["task_id"]

    # Получить сохранённый результат без повторного запуска (0 кредитов).
    result = client.get_analysis(task_id)
    print("Секции:", sorted(result.keys()))

    # Публичная ссылка на результат.
    share = client.share_analysis(task_id)
    print("Публичная ссылка:", share.get("share_url"))

    # Отозвать ссылку.
    client.unshare_analysis(task_id)
    print("Ссылка отозвана.")
