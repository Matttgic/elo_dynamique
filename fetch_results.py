# fetch_results.py

import os
import requests
import datetime
import pandas as pd

API_TENNIS_KEY = os.getenv("API_TENNIS_KEY")
RESULTS_FILE = "match_results.csv"

# 📌 Fonction de normalisation
def normalize_name(name):
    if not isinstance(name, str): return ""
    parts = name.strip().lower().replace("-", " ").replace(".", "").replace("'", "").split()
    if len(parts) == 0:
        return ""
    elif len(parts) == 1:
        return parts[0]
    else:
        return f"{parts[0][0]}. {parts[-1]}"

# 📆 Date d'hier
yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

# 📡 Requête à l'API
def fetch_results():
    url = f"https://api.api-tennis.com/tennis/?method=get_results&APIkey={API_TENNIS_KEY}&date_start={yesterday}&date_stop={yesterday}"
    response = requests.get(url)

    if response.status_code != 200:
        print("❌ Erreur API Tennis :", response.status_code)
        print("📄 Contenu brut reçu :", response.text)
        return

    data = response.json()
    if data.get("success") != 1:
        print("❌ Résultat invalide ou vide")
        return

    results = []
    for match in data["result"]:
        if match.get("event_type_type") not in ["Atp Singles", "Wta Singles"]:
            continue
        try:
            p1 = normalize_name(match["event_first_player"])
            p2 = normalize_name(match["event_second_player"])
            winner = normalize_name(match["event_winner"])
            surface = match.get("surface", "unknown").lower().strip()

            results.append({
                "player1": p1,
                "player2": p2,
                "winner": winner,
                "surface": surface
            })
        except Exception as e:
            print("⚠️ Erreur lecture match :", e)
            continue

    if not results:
        print("📭 Aucun résultat enregistré.")
        return

    df = pd.DataFrame(results)
    df.to_csv(RESULTS_FILE, index=False)
    print(f"✅ {len(df)} résultats enregistrés dans {RESULTS_FILE}")

if __name__ == "__main__":
    print("📡 Lancement de fetch_results.py")
    fetch_results()
