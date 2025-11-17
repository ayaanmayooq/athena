from athena.memory.models import ensure_db_initialized
from athena.memory.semantic import save_document, search_documents

ensure_db_initialized()
user_id = "default"

save_document(user_id, "My girlfriend is vegetarian and loves Italian food.", {"topic": "prefs"})
save_document(user_id, "I do 100 pull-ups a day.", {"topic": "fitness"})

results = search_documents(user_id, "What did I say about my girlfriend's diet?", k=3)
for d in results:
    print(d.content, d.metadata)
