# get_tennis_odds.py

import requests
import os
import pandas as pd

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# ✂️ Fonction de normalisation des noms : initiale prénom + nom
def normalize_name(name):
    name = name.lower().replace("-", " ").replace("'", "").strip()
    parts = name.split()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0][0]}. {parts[-1]}"

def build_odds_dataframe(name_formatter=normalize_name):
    url = f"https://api.the-odds-api.com/v4/sports/tennis/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Erreur API Odds : statut {response.status_code}")
            return pd.DataFrame()
        data = response.json()
        rows = []
        for item in data:
            if "bookmakers" not in item or not item["bookmakers"]:
                continue
            market = item["bookmakers"][0]["markets"][0]
            outcomes = market["outcomes"]
            if len(outcomes) != 2:
                continue
            player1 = name_formatter(outcomes[0]["name"])
            player2 = name_formatter(outcomes[1]["name"])
            odds1 = outcomes[0]["price"]
            odds2 = outcomes[1]["price"]
            rows.append({
                "player1": player1,
                "player2": player2,
                "odds1": odds1,
                "odds2": odds2
            })
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"❌ Exception lors du fetch des cotes : {e}")
        return pd.DataFrame()
