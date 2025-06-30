# daily_run.py

import os
import requests
import datetime
import pandas as pd
from telegram_bot import send_message
from get_tennis_odds import build_odds_dataframe

# 🔐 API key
API_TENNIS_KEY = os.getenv("API_TENNIS_KEY")

# 📅 Date du jour
today = datetime.date.today().strftime("%Y-%m-%d")

# 📄 Elo file
ELO_FILE = "elo_dynamique_2024_K_variable.csv"

# 🎾 Surface mapping par tournoi (ATP/WTA)
SURFACE_MAP = {
    "wimbledon": "grass",
    "roland garros": "clay",
    "french open": "clay",
    "us open": "hard",
    "australian open": "hard",
    "miami": "hard",
    "indian wells": "hard",
    "cincinnati": "hard",
    "madrid": "clay",
    "rome": "clay",
    "monte carlo": "clay",
    "barcelona": "clay",
    "paris": "hard",
    "doha": "hard",
    "dubai": "hard",
    "adelaide": "hard",
    "brisbane": "hard",
    "houston": "clay",
    "estoril": "clay",
    "lyon": "clay",
    "s-hertogenbosch": "grass",
    "halle": "grass",
    "queens": "grass",
    "eastbourne": "grass",
    "atlanta": "hard",
    "washington": "hard",
    "toronto": "hard",
    "montreal": "hard",
    "shanghai": "hard",
    "tokyo": "hard",
    "vienna": "hard",
    "basel": "hard",
    "zhuhai": "hard",
    "chengdu": "hard",
    "antwerp": "hard",
    "stockholm": "hard",
    "metz": "hard",
    "moselle": "hard"
}

# 🔁 Fonction proba Elo
def elo_probability(elo1, elo2):
    return 1 / (1 + 10 ** ((elo2 - elo1) / 400))

# 🧹 Normalisation des noms
def normalize_name(name):
    name = name.lower().replace("-", " ").replace("'", "").strip()
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {' '.join(parts[1:])}"
    return name

# 📡 Récupération des matchs
def get_matches():
    url = f"https://api.api-tennis.com/tennis/?method=get_fixtures&APIkey={API_TENNIS_KEY}&date_start={today}&date_stop={today}"
    response = requests.get(url)
    data = response.json()

    if data.get("success") != 1:
        print("❌ Erreur récupération fixtures")
        return pd.DataFrame()

    matches = []
    for m in data["result"]:
        if m.get("event_type_type") not in ["Atp Singles", "Wta Singles"]:
            continue
        tournament = m.get("tournament_name", "").lower()
        surface = "unknown"
        for key, val in SURFACE_MAP.items():
            if key in tournament:
                surface = val
                break
        matches.append({
            "player1": normalize_name(m["event_first_player"]),
            "player2": normalize_name(m["event_second_player"]),
            "surface": surface,
            "tournament": tournament
        })
    return pd.DataFrame(matches)

# 📥 Chargement du Elo
def load_elo():
    if not os.path.exists(ELO_FILE):
        print("⛔ Fichier Elo manquant")
        return None
    df = pd.read_csv(ELO_FILE)
    df = df.melt(id_vars="player", var_name="surface", value_name="elo")
    df["surface"] = df["surface"].str.replace("elo_", "").str.lower()
    df["player"] = df["player"].apply(normalize_name)
    return df

# 🤖 Bot principal
def run_bot():
    print("🚀 Lancement du bot tennis")
    matches = get_matches()
    odds = build_odds_dataframe()
    elo_df = load_elo()

    if matches.empty or odds.empty or elo_df is None:
        send_message("⚠️ Erreur récupération des données.")
        return

    df = pd.merge(matches, odds, on=["player1", "player2"], how="inner")
    if df.empty:
        send_message(f"📊 {len(matches)} matchs récupérés mais aucun avec cotes.")
        return

    # Attribution Elo
    elo_dict = {(row["player"], row["surface"]): row["elo"] for _, row in elo_df.iterrows()}
    def get_elo(player, surface):
        return elo_dict.get((player, surface), 1500)

    df["elo1"] = df.apply(lambda row: get_elo(row["player1"], row["surface"]), axis=1)
    df["elo2"] = df.apply(lambda row: get_elo(row["player2"], row["surface"]), axis=1)
    df["proba1"] = df.apply(lambda row: elo_probability(row["elo1"], row["elo2"]), axis=1)
    df["proba2"] = 1 - df["proba1"]
    df["value1"] = df["proba1"] * df["odds1"] - 1
    df["value2"] = df["proba2"] * df["odds2"] - 1

    bets = df[(df["value1"] > 0.05) | (df["value2"] > 0.05)]

    # ✉️ Message Telegram
    message = f"📊 {len(matches)} matchs analysés aujourd’hui\n\n"
    if bets.empty:
        message += "🟡 *Aucun value bet détecté aujourd’hui.*"
    else:
        message += "🔥 *Value bets trouvés* :\n"
        for _, row in bets.iterrows():
            line = f"🎾 {row['player1']} vs {row['player2']} ({row['surface']})\n"
            if row["value1"] > 0.05:
                line += f"➡️ *{row['player1']}* @ {row['odds1']} (value: {row['value1']:.1%})\n"
            if row["value2"] > 0.05:
                line += f"➡️ *{row['player2']}* @ {row['odds2']} (value: {row['value2']:.1%})\n"
            line += "\n"
            message += line
    send_message(message.strip())

if __name__ == "__main__":
    run_bot()
