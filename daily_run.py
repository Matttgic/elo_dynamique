import pandas as pd
import requests
import datetime
import os
import subprocess
from get_tennis_odds import build_odds_dataframe  # Fonction modulaire pour les cotes

# 🔐 Clés API depuis les variables d’environnement
API_TENNIS_KEY = os.getenv("API_TENNIS_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 📦 Fonction modulaire pour les cotes
def get_odds():
    return build_odds_dataframe()

# 📡 Fonction pour récupérer les matchs du jour via API-Tennis
def get_matches():
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    url_events = f"https://api.api-tennis.com/tennis/?method=get_events&APIkey={API_TENNIS_KEY}&date={today}"
    response = requests.get(url_events)
    data = response.json()
    matches = [m for m in data.get("result", []) if m.get("event_type") == "match" and m.get("category") in ["ATP", "WTA"]]
    return pd.DataFrame([{
        "player1": m.get("player1_name", "unknown").strip(),
        "player2": m.get("player2_name", "unknown").strip(),
        "surface": m.get("surface", "unknown").lower().strip() if m.get("surface") else "unknown",
        "tournament": m.get("tournament_name", "unknown").strip()
    } for m in matches])

# ✉️ Envoi de message Telegram
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# 🤖 Fonction principale du bot
def run_prediction_and_send_message():
    matches_df = get_matches()
    odds_df = get_odds()

    if matches_df.empty or odds_df.empty:
        send_telegram("⚠️ Aucun match ou aucune cote disponible aujourd’hui.")
        return

    try:
        df = pd.merge(matches_df, odds_df, on=["player1", "player2"], how="inner")
    except Exception as e:
        send_telegram(f"❌ Erreur de fusion des données : {e}")
        return

    if df.empty:
        send_telegram("⚠️ Aucun match avec cotes disponibles aujourd’hui.")
        return

    # 📥 Charger et reformater le fichier Elo
    elo_path = "elo_dynamique_2024_K_variable.csv"
    if not os.path.exists(elo_path):
        send_telegram("❌ Fichier Elo manquant.")
        return

    elo_df = pd.read_csv(elo_path)

    # 🔄 Restructuration : format long avec colonnes 'player', 'surface', 'elo'
    if {"player", "elo_Hard", "elo_Clay", "elo_Grass"}.issubset(elo_df.columns):
        elo_df = elo_df.melt(id_vars="player", var_name="surface", value_name="elo")
        elo_df["surface"] = elo_df["surface"].str.replace("elo_", "").str.lower()

    required_cols = {"player", "surface", "elo"}
    if not required_cols.issubset(elo_df.columns):
        send_telegram("❌ Le fichier Elo est invalide. Il doit contenir les colonnes : player, surface, elo.")
        return

    # 🔍 Création dictionnaire (player, surface) → elo
    elo_dict = {(row['player'], row['surface']): row['elo'] for _, row in elo_df.iterrows()}
    def get_elo(player, surface):
        return elo_dict.get((player, surface), 1500)

    df["elo1"] = df.apply(lambda row: get_elo(row["player1"], row["surface"]), axis=1)
    df["elo2"] = df.apply(lambda row: get_elo(row["player2"], row["surface"]), axis=1)
    df["proba1"] = df.apply(lambda row: 1 / (1 + 10 ** ((row["elo2"] - row["elo1"]) / 400)), axis=1)
    df["proba2"] = 1 - df["proba1"]
    df["value1"] = df["proba1"] * df["odds1"] - 1
    df["value2"] = df["proba2"] * df["odds2"] - 1

    bets = df[(df["value1"] > 0.05) | (df["value2"] > 0.05)]

    if bets.empty:
        send_telegram("🟡 Aucun value bet trouvé aujourd’hui.")
    else:
        msg = "📈 Value bets détectés :\n"
        for _, row in bets.iterrows():
            line = f"{row['player1']} vs {row['player2']} ({row['surface']})\n"
            if row['value1'] > 0.05:
                line += f"→ {row['player1']} @ {row['odds1']} (value: {row['value1']:.2%})\n"
            if row['value2'] > 0.05:
                line += f"→ {row['player2']} @ {row['odds2']} (value: {row['value2']:.2%})\n"
            msg += "\n" + line
        send_telegram(msg)

# ▶️ Lancement automatique
if __name__ == "__main__":
    run_prediction_and_send_message()
    subprocess.run(["python", "fetch_results.py"])
    subprocess.run(["python", "update_elo.py"])
