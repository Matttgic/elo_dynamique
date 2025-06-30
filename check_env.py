import os

def check(name):
    value = os.getenv(name)
    if value:
        print(f"✅ {name} est défini ({len(value)} caractères)")
    else:
        print(f"❌ {name} est **non défini**")

print("🔍 Vérification des variables d'environnement GitHub Actions :\n")
check("API_TENNIS_KEY")
check("ODDS_API_KEY")
check("TELEGRAM_TOKEN")
check("CHAT_ID")
