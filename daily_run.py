import os import requests import datetime import pandas as pd from telegram_bot import send_message

🎾 Clés API depuis les variables d'environnement

API_TENNIS_KEY = os.getenv("API_TENNIS_KEY") ODDS_API_KEY = os.getenv("ODDS_API_KEY")

📅 Date du jour

today = datetime.date.today().strftime("%Y-%m-%d")

✅ Fonction pour récupérer les matchs de l'API OddsAPI

def get_matches_with_odds(): url = f"https://api.the-odds-api.com/v4/sports/tennis/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h" try: response = requests.get(url) if response.status_code != 200: print(f"❌ Erreur Odds API : statut {response.status_code}") return []

data = response.json()
    matches = []
    for item in data:
        if not item.get("bookmakers"):
            continue

        outcomes = item["bookmakers"][0]["markets"][0]["outcomes"]
        if len(outcomes) != 2:
            continue

        matches.append({
            "player1": outcomes[0]["name"].strip(),
            "player2": outcomes[1]["name"].strip(),
            "odds1": float(outcomes[0]["price"]),
            "odds2": float(outcomes[1]["price"]),
            "commence_time": item["commence_time"],
            "tournament": item.get("sport_title", "unknown"),
            "surface": "hard"  # à améliorer plus tard
        })
    return matches

except Exception as e:
    print(f"❌ Exception : {e}")
    return []

🔄 Chargement Elo par surface

def load_elo(): path = "elo_dynamique_2024_K_variable.csv" if not os.path.exists(path): send_message("❌ Fichier Elo manquant.") return None

df = pd.read_csv(path)
if {"player", "elo_Hard", "elo_Clay", "elo_Grass"}.issubset(df.columns):
    df = df.melt(id_vars="player", var_name="surface", value_name="elo")
    df["surface"] = df["surface"].str.replace("elo_", "").str.lower()
return df

📊 Fusion, calcul des value bets, message Telegram

def process_and_notify(): matches = get_matches_with_odds() if not matches: send_message("⚠️ Aucun match récupéré aujourd’hui.") return

matches_df = pd.DataFrame(matches)
elo_df = load_elo()
if elo_df is None:
    return

elo_dict = {(row["player"], row["surface"]): row["elo"] for _, row in elo_df.iterrows()}
def get_elo(player, surface):
    return elo_dict.get((player, surface), 1500)

matches_df["elo1"] = matches_df.apply(lambda row: get_elo(row["player1"], row["surface"]), axis=1)
matches_df["elo2"] = matches_df.apply(lambda row: get_elo(row["player2"], row["surface"]), axis=1)

matches_df["proba1"] = 1 / (1 + 10 ** ((matches_df["elo2"] - matches_df["elo1"]) / 400))
matches_df["proba2"] = 1 - matches_df["proba1"]

matches_df["value1"] = matches_df["proba1"] * matches_df["odds1"] - 1
matches_df["value2"] = matches_df["proba2"] * matches_df["odds2"] - 1

bets = matches_df[(matches_df["value1"] > 0.05) | (matches_df["value2"] > 0.05)]
if bets.empty:
    send_message("🟡 Aucun value bet détecté aujourd’hui.")
    return

msg = "📊 *Value bets détectés aujourd’hui*\n"
for _, row in bets.iterrows():
    msg += f"\n🎾 *{row['player1']}* vs *{row['player2']}*\n"
    msg += f"Tournoi : `{row['tournament']}` | Surface : `{row['surface']}`\n"
    if row["value1"] > 0.05:
        msg += f"➡️ {row['player1']} @ {row['odds1']} (value: {row['value1']:.1%})\n"
    if row["value2"] > 0.05:
        msg += f"➡️ {row['player2']} @ {row['odds2']} (value: {row['value2']:.1%})\n"
send_message(msg)

if name == "main": process_and_notify()

