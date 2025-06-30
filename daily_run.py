# daily_run.py

import os
import requests
import datetime
import pandas as pd
from telegram_bot import send_message

# 🔐 Clés API depuis variables d’environnement
API_TENNIS_KEY = os.getenv("API_TENNIS_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# 📅 Date du jour
today = datetime.date.today().strftime("%Y-%m-%d")

# 📁 Chargement du fichier Elo
ELO_FILE = "elo_dynamique_2024_K_variable.csv"
if not os.path.exists(ELO_FILE):
    send_message("❌ Fichier Elo manquant.")
    exit()

elo_df = pd.read_csv(ELO_FILE)
if {"player", "elo_Hard", "elo_Clay", "elo_Grass"}.issubset(elo_df.columns):
    elo_df = elo_df.melt(id_vars="player", var_name="surface", value_name="elo")
    elo_df["surface"] = elo_df["surface"].str.replace("elo_", "").str.lower()
else:
    send_message("❌ Colonnes Elo invalides.")
    exit()

elo_dict = {(row['player'], row['surface']): row['elo'] for _, row in elo_df.iterrows()}

# 📡 Récupération des matchs via API-Tennis
def get_fixtures():
    url = f"https://api.api-tennis.com/tennis/?method=get_fixtures&APIkey={API_TENNIS_KEY}&date_start={today}&date_stop={today}"
    r = requests.get(url)
    data = r.json()
    if data.get("success") != 1:
        return []
    results = []
    for match in data["result"]:
        if match.get("event_type_type") not in ["Atp Singles", "Wta Singles"]:
            continue
        results.append({
            "player1": match["event_first_player"].strip(),
            "player2": match["event_second_player"].strip(),
            "tournament": match["tournament_name"].strip(),
            "surface": match.get("event_surface", "hard").lower().strip()
        })
    return pd.DataFrame(results)

# 📡 Récupération des cotes via Odds API
def get_odds():
    url = f"https://api.the-odds-api.com/v4/sports/tennis/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
    r = requests.get(url)
    if r.status_code != 200:
        return pd.DataFrame()
    matches = []
    for item in r.json():
        try:
            team1 = item["bookmakers"][0]["markets"][0]["outcomes"][0]
            team2 = item["bookmakers"][0]["markets"][0]["outcomes"][1]
            matches.append({
                "player1": team1["name"].strip(),
                "player2": team2["name"].strip(),
                "odds1": team1["price"],
                "odds2": team2["price"]
            })
        except:
            continue
    return pd.DataFrame(matches)

# 🔍 Probabilité Elo
def elo_prob(elo1, elo2):
    return 1 / (1 + 10 ** ((elo2 - elo1) / 400))

# ▶️ Script principal
def main():
    fixtures = get_fixtures()
    odds = get_odds()

    if fixtures.empty or odds.empty:
        send_message("📭 Aucun match ou cote trouvée aujourd’hui.")
        return

    df = pd.merge(fixtures, odds, on=["player1", "player2"], how="inner")
    if df.empty:
        send_message("📭 Aucun match avec cotes exploitables.")
        return

    # 🔁 Application du modèle Elo
    def get_elo(player, surface):
        return elo_dict.get((player, surface), 1500)

    df["elo1"] = df.apply(lambda row: get_elo(row["player1"], row["surface"]), axis=1)
    df["elo2"] = df.apply(lambda row: get_elo(row["player2"], row["surface"]), axis=1)
    df["proba_model1"] = df.apply(lambda row: elo_prob(row["elo1"], row["elo2"]), axis=1)
    df["proba_model2"] = 1 - df["proba_model1"]

    df["proba_book1"] = 1 / df["odds1"]
    df["proba_book2"] = 1 / df["odds2"]
    df["proba_book1_norm"] = df["proba_book1"] / (df["proba_book1"] + df["proba_book2"])
    df["proba_book2_norm"] = 1 - df["proba_book1_norm"]

    df["value1"] = df["proba_model1"] - df["proba_book1_norm"]
    df["value2"] = df["proba_model2"] - df["proba_book2_norm"]

    bets = df[(df["value1"] > 0.05) | (df["value2"] > 0.05)]

    if bets.empty:
        send_message("🟡 Aucun value bet détecté aujourd’hui.")
        return

    msg = "🎯 *Value Bets détectés aujourd’hui* :\n"
    for _, row in bets.iterrows():
        line = f"\n🎾 *{row['player1']}* vs *{row['player2']}* ({row['surface'].capitalize()})\n"
        if row["value1"] > 0.05:
            line += f"🔹 *{row['player1']}* @ {row['odds1']} (Value: {row['value1']:.1%})\n"
        if row["value2"] > 0.05:
            line += f"🔹 *{row['player2']}* @ {row['odds2']} (Value: {row['value2']:.1%})\n"
        msg += line

    send_message(msg)

if __name__ == "__main__":
    main()
