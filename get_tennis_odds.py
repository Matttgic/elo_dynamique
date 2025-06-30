import requests
import pandas as pd
import os

# Clé API The Odds API
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# Nettoyage standardisé des noms
def clean_name(name):
    return name.lower().strip().replace(".", "").replace("-", " ")

def build_odds_dataframe():
    url = f"https://api.the-odds-api.com/v4/sports/tennis/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Erreur API Odds: {response.status_code}")
        return pd.DataFrame()

    data = response.json()
    rows = []

    for event in data:
        try:
            players = event["participants"]
            if len(players) != 2:
                continue

            outcomes = event["bookmakers"][0]["markets"][0]["outcomes"]
            if len(outcomes) != 2:
                continue

            # Récupération brute
            p1 = clean_name(players[0])
            p2 = clean_name(players[1])
            o1 = outcomes[0]["price"]
            o2 = outcomes[1]["price"]

            rows.append({
                "player1": p1,
                "player2": p2,
                "odds1": o1,
                "odds2": o2
            })
        except Exception as e:
            print(f"⚠️ Erreur lecture match : {e}")
            continue

    df = pd.DataFrame(rows)

    # Nettoyage final
    df["player1"] = df["player1"].str.strip()
    df["player2"] = df["player2"].str.strip()

    return df
