import requests
import os
import pandas as pd

API_KEY = os.getenv("ODDS_API_KEY")  # Assure-toi que ta clé est bien définie dans les Secrets GitHub

def get_active_tennis_keys():
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        print("❌ Erreur de récupération des sports :", response.status_code)
        return []

    sports = response.json()
    tennis_keys = [sport["key"] for sport in sports if sport["group"] == "Tennis" and sport["active"]]
    print(f"🎾 Sports tennis actifs : {tennis_keys}")
    return tennis_keys

def get_odds_for_key(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"⚠️ Erreur pour {sport_key} : {response.status_code}")
        return []

    return response.json()

def build_odds_dataframe():
    tennis_keys = get_active_tennis_keys()
    all_rows = []

    for key in tennis_keys:
        odds_data = get_odds_for_key(key)
        for event in odds_data:
            if not event.get("bookmakers"):
                continue

            bookie = event["bookmakers"][0]
            markets = bookie.get("markets", [])
            if not markets or not markets[0]["outcomes"]:
                continue

            outcomes = markets[0]["outcomes"]
            if len(outcomes) != 2:
                continue

            row = {
                "tournament": event.get("sport_title", ""),
                "player1": outcomes[0]["name"].strip(),
                "odds1": float(outcomes[0]["price"]),
                "player2": outcomes[1]["name"].strip(),
                "odds2": float(outcomes[1]["price"])
            }
            all_rows.append(row)

    if not all_rows:
        print("❌ Aucun pari tennis trouvé.")
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    print(f"✅ {len(df)} matchs tennis récupérés.")
    return df

# Exécution simple pour test local
if __name__ == "__main__":
    df = build_odds_dataframe()
    print(df.head()) 
