import pandas as pd
import requests
import datetime
import os

# Configuration (API keys à remplacer)
ODDS_API_KEY = "YOUR_ODDS_API_KEY"
API_TENNIS_KEY = "YOUR_API_TENNIS_KEY"
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def get_matches():
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    url_events = f"https://api.api-tennis.com/tennis/?method=get_events&APIkey={API_TENNIS_KEY}&date={today}"
    response = requests.get(url_events)
    data = response.json()
    matches = [m for m in data.get("result", []) if m.get("event_type") == "match" and m.get("category") in ["ATP", "WTA"]]
    return pd.DataFrame([{
        "player1": m.get("player1_name", "unknown"),
        "player2": m.get("player2_name", "unknown"),
        "surface": m.get("surface", "unknown").lower() if m.get("surface") else "unknown",
        "tournament": m.get("tournament_name", "unknown")
    } for m in matches])

def get_odds():
    url_odds = f"https://api.the-odds-api.com/v4/sports/tennis/events/?apiKey={ODDS_API_KEY}&regions=eu"
    odds_response = requests.get(url_odds)
    odds_data = odds_response.json()
    odds_list = []
    for event in odds_data:
        try:
            bookmaker = event['bookmakers'][0]
            markets = bookmaker['markets'][0]['outcomes']
            odds_list.append({
                "player1": markets[0]['name'],
                "player2": markets[1]['name'],
                "odds1": float(markets[0]['price']),
                "odds2": float(markets[1]['price'])
            })
        except:
            continue
    return pd.DataFrame(odds_list)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

def run_prediction_and_send_message():
    matches_df = get_matches()
    odds_df = get_odds()
    if matches_df.empty or odds_df.empty:
        send_telegram("⚠️ Aucun match ou aucune cote disponible aujourd’hui.")
        return

    df = pd.merge(matches_df, odds_df, on=["player1", "player2"], how="inner")
    if df.empty:
        send_telegram("⚠️ Aucun match avec cotes disponibles aujourd’hui.")
        return

    # Load Elo
    elo_path = "elo_dynamique_2024_K_variable.csv"
    if not os.path.exists(elo_path):
        send_telegram("❌ Fichier Elo manquant.")
        return
    elo_df = pd.read_csv(elo_path)
    elo_dict = {(row['player'], row['surface']): row['elo'] for _, row in elo_df.iterrows()}

    def get_elo(player, surface):
        return elo_dict.get((player, surface), 1500)

    df["elo1"] = df.apply(lambda row: get_elo(row["player1"], row["surface"]), axis=1)
    df["elo2"] = df.apply(lambda row: get_elo(row["player2"], row["surface"]), axis=1)
    df["proba1"] = df.apply(lambda row: 1 / (1 + 10 ** ((row["elo2"] - row["elo1"]) / 400)), axis=1)
    df["proba2"] = 1 - df["proba1"]
    df["value1"] = df["proba1"] * df["odds1"] - 1
    df["value2"] = df["proba2"] * df["odds2"] - 1

    value_bets = df[(df["value1"] > 0.05) | (df["value2"] > 0.05)]
    if value_bets.empty:
        send_telegram("📭 Aucun value bet détecté aujourd’hui.")
    else:
        msg = "📈 Value bets détectés :
"
        for _, row in value_bets.iterrows():
            msg += f"{row['player1']} vs {row['player2']} ({row['surface']})
"
            msg += f"➡️ Value1: {row['value1']:.2f}, Value2: {row['value2']:.2f}
"
            msg += f"Cotes: {row['odds1']} / {row['odds2']}

"
        send_telegram(msg.strip())

if __name__ == "__main__":
    run_prediction_and_send_message()
