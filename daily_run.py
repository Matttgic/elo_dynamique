import os
import requests
import datetime
import pandas as pd
from telegram_bot import send_message

# 🎾 Clés API depuis les variables d'environnement
API_TENNIS_KEY = os.getenv("API_TENNIS_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# 📅 Date du jour
today = datetime.date.today().strftime("%Y-%m-%d")

# 🎯 Types de tournois ciblés
TARGET_TOURNAMENTS = ['tennis_atp_wimbledon', 'tennis_wta_wimbledon']

def get_matches():
    url = f"https://api.the-odds-api.com/v4/sports/tennis/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Erreur Odds API : statut {response.status_code}")
            return None
        data = response.json()
        matches = []
        for item in data:
            if item["sport_key"] in TARGET_TOURNAMENTS:
                match = {
                    "commence_time": item["commence_time"],
                    "sport_key": item["sport_key"],
                    "team1": item["bookmakers"][0]["markets"][0]["outcomes"][0]["name"],
                    "team2": item["bookmakers"][0]["markets"][0]["outcomes"][1]["name"],
                    "odds1": item["bookmakers"][0]["markets"][0]["outcomes"][0]["price"],
                    "odds2": item["bookmakers"][0]["markets"][0]["outcomes"][1]["price"]
                }
                matches.append(match)
        return matches
    except Exception as e:
        print(f"❌ Exception : {e}")
        return None

def detect_value_bets(matches):
    # 🎯 Exemple simple : value si une cote est > 2.20
    value_bets = []
    for m in matches:
        if float(m["odds1"]) > 2.2:
            m["value_team"] = m["team1"]
            m["value_odds"] = m["odds1"]
            value_bets.append(m)
        elif float(m["odds2"]) > 2.2:
            m["value_team"] = m["team2"]
            m["value_odds"] = m["odds2"]
            value_bets.append(m)
    return value_bets

def main():
    print("🚀 Lancement du bot tennis")
    matches = get_matches()
    if matches is None:
        print("⚠️ Aucun match récupéré")
        send_message("⚠️ Erreur lors de la récupération des matchs.")
        return

    # 💾 Sauvegarde brute pour debug
    df = pd.DataFrame(matches)
    df.to_csv("odds_debug.csv", index=False)
    print(f"✅ {len(matches)} matchs tennis récupérés. Sauvegardés dans odds_debug.csv")

    # 📊 Détection de value bets
    values = detect_value_bets(matches)
    if not values:
        print("🟡 Aucun value bet détecté aujourd’hui.")
        send_message("📭 Aucun pari value détecté aujourd’hui.")
        return

    # ✉️ Envoi Telegram des values détectés
    for bet in values:
        message = (
            f"🎾 *Value Bet détecté !*\n\n"
            f"📍 Tournoi : `{bet['sport_key']}`\n"
            f"🕒 Heure : `{bet['commence_time']}`\n"
            f"🔹 Match : *{bet['team1']}* vs *{bet['team2']}*\n"
            f"💰 Pari recommandé : *{bet['value_team']}* à *{bet['value_odds']}*\n"
        )
        send_message(message)

    # 🧪 Message test pour debug (supprime cette ligne quand tout est ok)
    send_message("🧪 Test Telegram : ce message prouve que le bot fonctionne ✅")

if __name__ == "__main__":
    main()
