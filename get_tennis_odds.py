import requests
import os
import pandas as pd
import unicodedata

API_KEY = os.getenv("ODDS_API_KEY")  # Définie dans Secrets GitHub

def normalize_name(name):
    # Normalise les accents et casse
    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    return name.strip().lower()

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
                "player1": normalize_name(outcomes[0]["name"]),
                "odds1": float(outcomes[0]["price"]),
                "player2": normalize_name(outcomes[1]["name"]),
                "odds2": float(outcomes[1]["price"])
            }
            all_rows.append(row)

    if not all_rows:
        print("❌ Aucun pari tennis trouvé.")
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df.to_csv("odds_debug.csv", index=False)
    print(f"✅ {len(df)} matchs tennis récupérés. Sauvegardés dans odds_debug.csv")
    return df

if __name__ == "__main__":
    df = build_odds_dataframe()
    print(df.head())
