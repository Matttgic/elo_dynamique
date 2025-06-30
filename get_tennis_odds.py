# get_tennis_odds.py

import os
import requests
import pandas as pd

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# 🔠 Fonction de normalisation
def normalize_name(name):
    return name.lower().replace('.', '').replace('-', ' ').replace("'", "").strip()

# 📦 Construction du DataFrame de cotes
def build_odds_dataframe():
    url = f"https://api.the-odds-api.com/v4/sports/tennis/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Erreur The Odds API : {response.status_code}")
            return pd.DataFrame()

        data = response.json()
        odds_data = []

        for match in data:
            try:
                bookmaker = match["bookmakers"][0]
                outcomes = bookmaker["markets"][0]["outcomes"]

                player1 = normalize_name(outcomes[0]["name"])
                player2 = normalize_name(outcomes[1]["name"])
                odds1 = float(outcomes[0]["price"])
                odds2 = float(outcomes[1]["price"])

                odds_data.append({
                    "player1": player1,
                    "player2": player2,
                    "odds1": odds1,
                    "odds2": odds2
                })
            except (IndexError, KeyError, TypeError) as e:
                continue  # skip invalid entries

        return pd.DataFrame(odds_data)

    except Exception as e:
        print(f"❌ Exception lors de la récupération des cotes : {e}")
        return pd.DataFrame()
