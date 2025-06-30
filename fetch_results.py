import pandas as pd
import requests
import datetime
import os

# 🔐 Clé API en variable d’environnement
API_TENNIS_KEY = os.getenv("API_TENNIS_KEY")

# 📁 Fichier CSV de sortie
OUTPUT_FILE = "results.csv"

# 📅 Récupérer la date d’hier
yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

# 📡 Appel API pour récupérer les résultats
url = f"https://api.api-tennis.com/tennis/?method=get_results&APIkey={API_TENNIS_KEY}&date={yesterday}"
response = requests.get(url)
data = response.json()

# ✅ Filtrer les résultats ATP/WTA uniquement
matches = [m for m in data.get("result", []) if m.get("category") in ["ATP", "WTA"] and m.get("event_type") == "match"]

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

# 📦 Sauvegarder dans results.csv
if rows:
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ {len(df)} résultats sauvegardés dans {OUTPUT_FILE}")
else:
    print("⚠️ Aucun résultat valide récupéré.") 
