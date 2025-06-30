import requests
import os
import pandas as pd

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

def build_odds_dataframe():
    url = f"https://api.the-odds-api.com/v4/sports/tennis/matches/?regions=eu&markets=h2h&oddsFormat=decimal&apiKey={ODDS_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Erreur Odds API : statut {response.status_code}")
        return pd.DataFrame()

    data = response.json()
    rows = []

    for match in data:
        teams = match.get("teams", [])
        bookmakers = match.get("bookmakers", [])
        if len(teams) != 2 or not bookmakers:
            continue

        outcomes = bookmakers[0]["markets"][0]["outcomes"]
        if len(outcomes) != 2:
            continue

        player1 = outcomes[0]["name"]
        player2 = outcomes[1]["name"]
        odds1 = outcomes[0]["price"]
        odds2 = outcomes[1]["price"]

        rows.append({
            "player1": player1,
            "player2": player2,
            "odds1": odds1,
            "odds2": odds2
        })

    return pd.DataFrame(rows)
