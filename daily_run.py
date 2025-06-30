import os
import requests
import datetime
import pandas as pd
from telegram_bot import send_message
from get_tennis_odds import build_odds_dataframe

# 🔐 Clés API depuis les variables d'environnement
API_TENNIS_KEY = os.getenv("API_TENNIS_KEY")

# 📅 Date du jour
today = datetime.date.today().strftime("%Y-%m-%d")

# 📄 Fichier Elo
ELO_FILE = "elo_dynamique_2024_K_variable.csv"

# 🔁 Proba Elo
def elo_probability(elo1, elo2):
    return 1 / (1 + 10 ** ((elo2 - elo1) / 400))

# 📦 Obtenir les cotes
def get_odds():
    return build_odds_dataframe()

# 📡 Obtenir les matchs du jour
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
        matches.append({
            "player1": m["event_first_player"].strip(),
            "player2": m["event_second_player"].strip(),
            "surface": m.get("surface", "unknown").lower().strip(),
            "tournament": m.get("tournament_name", "unknown").strip()
        })
    return pd.DataFrame(matches)

# 🧠 Charger Elo
def load_elo():
    if not os.path.exists(ELO_FILE):
        print("⛔ Fichier Elo manquant")
        return None

    df = pd.read_csv(ELO_FILE)
    if {"player", "elo_Hard", "elo_Clay", "elo_Grass"}.issubset(df.columns):
        df = df.melt(id_vars="player", var_name="surface", value_name="elo")
        df["surface"] = df["surface"].str.replace("elo_", "").str.lower()
    return df

# 🤖 Routine principale
def run_bot():
    print("🚀 Lancement du bot")
    matches = get_matches()
    odds = get_odds()
    elo_df = load_elo()

    if matches.empty or odds.empty or elo_df is None:
        send_message("⚠️ Erreur récupération des données.")
        return

    df = pd.merge(matches, odds, on=["player1", "player2"], how="inner")
    match_count = len(df)

    if df.empty:
        send_message(f"📊 *{match_count} matchs analysés aujourd’hui*\n🟡 *Aucun match avec cotes disponibles.*")
        return

    # Récup Elo
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

    # 📬 Résultat Telegram
    message = f"📊 *{match_count} matchs analysés aujourd’hui*\n\n"
    if bets.empty:
        message += "🟡 *Aucun value bet détecté*"
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
