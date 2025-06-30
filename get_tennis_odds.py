# get_tennis_odds.py

import os
import requests
import datetime
import pandas as pd

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
today = datetime.date.today().strftime("%Y-%m-%d")

def build_odds_dataframe():
    url = f"https://api.the-odds-api.com/v4/sports/tennis/events?regions=eu&markets=h2h&dateFormat=iso&oddsFormat=decimal&apiKey={ODDS_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Erreur API Odds: {response.status_code}")
        return pd.DataFrame()

    data = response.json()
    rows = []

    for event in data:
        try:
            bookmakers = event.get("bookmakers", [])
            if not bookmakers:
                continue

            outcomes = bookmakers[0]["markets"][0]["outcomes"]
            if len(outcomes) != 2:
                continue

            player1 = outcomes[0]["name"].strip()
            player2 = outcomes[1]["name"].strip()
            odds1 = float(outcomes[0]["price"])
            odds2 = float(outcomes[1]["price"])

            rows.append({
                "player1": player1,
                "player2": player2,
                "odds1": odds1,
                "odds2": odds2
            })
        except Exception as e:
            print("⚠️ Erreur parsing match odds:", e)
            continue

    return pd.DataFrame(rows)
