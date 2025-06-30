import os

keys = ["API_TENNIS_KEY", "ODDS_API_KEY", "TELEGRAM_TOKEN", "CHAT_ID"]

print("🔍 Vérification des variables d'environnement GitHub Actions :\n")

for key in keys:
    value = os.getenv(key)
    if value:
        print(f"✅ {key} est défini ({len(value)} caractères)")
    else:
        print(f"❌ {key} est **non défini**")
