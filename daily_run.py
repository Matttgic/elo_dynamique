import pandas as pd
import requests
import datetime
import os
import subprocess
from get_tennis_odds import build_odds_dataframe  # Ton script modulaire

# 🔐 Clés API
API_TENNIS_KEY = os.getenv("API_TENNIS_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 📡 Récupérer les matchs du jour
def get_matches():
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    url = f"https://api.api-tennis.com/tennis/?method=get_fixtures&APIkey={API_TENNIS_KEY}&date_start={today}&date_stop={today}"
    response = requests.get(url)

    if response.status_code != 200:
        print("❌ Erreur API:", response.status_code)
        return pd.DataFrame()

    data = response.json()
    fixtures = data.get("result", [])

    matches = [
        m for m in fixtures
        if m.get("event_type_type") in ["Atp Singles", "Wta Singles"]
    ]

    return pd.DataFrame([{
        "player1": m.get("event_first_player", "").strip(),
        "player2": m.get("event_second_player", "").strip(),
        "surface": m.get("event_court", "unknown").lower().strip() if m.get("event_court") else "unknown",
        "tournament": m.get("tournament_name", "unknown").strip()
    } for m in matches if m.get("event_first_player") and m.get("event_second_player")])

# ✉️ Envoi Telegram
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# 🤖 Lancement principal
def run_prediction_and_send_message():
    matches_df = get_matches()
    odds_df = build_odds_dataframe()

    if matches_df.empty or odds_df.empty:
        send_telegram("⚠️ Aucun match ou aucune cote disponible aujourd’hui.")
        return

    df = pd.merge(matches_df, odds_df, on=["player1", "player2"], how="inner")
    if df.empty:
        send_telegram("⚠️ Aucun match avec cotes disponibles.")
        return

    elo_path = "elo_dynamique_2024_K_variable.csv"
    if not os.path.exists(elo_path):
        send_telegram("❌ Fichier Elo manquant.")
        return

    elo_df = pd.read_csv(elo_path)
    if {"player", "elo_Hard", "elo_Clay", "elo_Grass"}.issubset(elo_df.columns):
        elo_df = elo_df.melt(id_vars="player", var_name="surface", value_name="elo")
        elo_df["surface"] = elo_df["surface"].str.replace("elo_", "").str.lower()

    if not {"player", "surface", "elo"}.issubset(elo_df.columns):
        send_telegram("❌ Fichier Elo invalide.")
        return

    elo_dict = {(row['player'], row['surface']): row['elo'] for _, row in elo_df.iterrows()}
    get_elo = lambda p, s: elo_dict.get((p, s), 1500)

    df["elo1"] = df.apply(lambda r: get_elo(r["player1"], r["surface"]), axis=1)
    df["elo2"] = df.apply(lambda r: get_elo(r["player2"], r["surface"]), axis=1)
    df["proba1"] = df.apply(lambda r: 1 / (1 + 10**((r["elo2"] - r["elo1"]) / 400)), axis=1)
    df["proba2"] = 1 - df["proba1"]
    df["value1"] = df["proba1"] * df["odds1"] - 1
    df["value2"] = df["proba2"] * df["odds2"] - 1

    bets = df[(df["value1"] > 0.05) | (df["value2"] > 0.05)]

    if bets.empty:
        send_telegram("📭 Aucun value bet détecté aujourd’hui.")
    else:
        msg = "🎾 *Value Bets du jour* 🎾\n"
        for _, row in bets.iterrows():
            line = f"\n{row['player1']} vs {row['player2']} ({row['surface']})"
            if row['value1'] > 0.05:
                line += f"\n👉 {row['player1']} @ {row['odds1']} (value: {row['value1']:.2%})"
            if row['value2'] > 0.05:
                line += f"\n👉 {row['player2']} @ {row['odds2']} (value: {row['value2']:.2%})"
            msg += line + "\n"
        send_telegram(msg)

# ▶️ Exécution automatique
if __name__ == "__main__":
    run_prediction_and_send_message()
    subprocess.run(["python", "fetch_results.py"])
    subprocess.run(["python", "update_elo.py"])
