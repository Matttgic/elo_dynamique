# get_tennis_odds.py

import os
import requests
import pandas as pd

# 🔐 Clé API depuis variable d’environnement
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

def build_odds_dataframe():
    url = f"https://api.the-odds-api.com/v4/sports/tennis/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Erreur Odds API - Status {response.status_code}")
        return pd.DataFrame()

    data = response.json()
    rows = []

    for item in data:
        if not item.get("bookmakers"):
            continue

        # Prend la première bookmaker disponible (souvent bet365)
        market = item["bookmakers"][0]["markets"][0]
        outcomes = market.get("outcomes", [])

        if len(outcomes) != 2:
            continue

        player1 = outcomes[0]["name"].strip()
        odds1 = outcomes[0]["price"]
        player2 = outcomes[1]["name"].strip()
        odds2 = outcomes[1]["price"]

        rows.append({
            "player1": player1,
            "player2": player2,
            "odds1": odds1,
            "odds2": odds2
        })

    return pd.DataFrame(rows)
