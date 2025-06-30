import requests
import os
import pandas as pd
import datetime

# 🔐 Clé API Tennis
API_TENNIS_KEY = os.getenv("API_TENNIS_KEY")

# 📁 Fichier CSV de sortie
OUTPUT_FILE = "results.csv"

# 📅 Récupérer la date d’hier
yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

# 📡 URL de l’API Tennis
url = f"https://api.api-tennis.com/tennis/?method=get_results&APIkey={API_TENNIS_KEY}&date={yesterday}"
response = requests.get(url)

# ✅ Vérification de la réponse avant json()
if response.status_code != 200 or not response.text.strip().startswith("{"):
    print(f"⛔ Erreur API Tennis : statut {response.status_code}")
    print("🔎 Contenu brut reçu :", response.text)
    exit()

data = response.json()

# ✅ Filtrer les résultats ATP/WTA
matches = [
    m for m in data.get("result", [])
    if m.get("category") in ["ATP", "WTA"] and m.get("event_type") == "match"
]

# 🧾 Construction des lignes de résultats
rows = []
for match in matches:
    p1 = match.get("player1_name", "").strip()
    p2 = match.get("player2_name", "").strip()
    w = match.get("winner", "").strip()
    s = match.get("surface", "unknown").lower().strip()
    t = match.get("tournament_name", "unknown").strip()

    if p1 and p2 and w and p1 != p2:
        rows.append({
            "player1": p1,
            "player2": p2,
            "winner": w,
            "surface": s,
            "tournament": t
        })

# 💾 Sauvegarde
if rows:
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ {len(df)} résultats sauvegardés dans {OUTPUT_FILE}")
else:
    print("⚠️ Aucun résultat valide récupéré.")
