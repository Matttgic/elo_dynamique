import os
import requests
import datetime
import pandas as pd
import difflib
from telegram_bot import send_message
from get_tennis_odds import build_odds_dataframe

API_TENNIS_KEY = os.getenv("API_TENNIS_KEY")
ELO_FILE = "elo_dynamique_2024_K_variable.csv"
today = datetime.date.today().strftime("%Y-%m-%d")

def elo_probability(elo1, elo2):
    return 1 / (1 + 10 ** ((elo2 - elo1) / 400))

def get_odds():
    return build_odds_dataframe()

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

def load_elo():
    if not os.path.exists(ELO_FILE):
        print("⛔ Fichier Elo manquant")
        return None
    df = pd.read_csv(ELO_FILE)
    if {"player", "elo_Hard", "elo_Clay", "elo_Grass"}.issubset(df.columns):
        df = df.melt(id_vars="player", var_name="surface", value_name="elo")
        df["surface"] = df["surface"].str.replace("elo_", "").str.lower()
    return df

def fuzzy_merge(df1, df2, key1, key2, threshold=0.8):
    """
    Associe les noms proches entre df1[key1] et df2[key2] avec difflib.
    """
    df1 = df1.copy()
    df2 = df2.copy()
    matches = []
    for i, name1 in enumerate(df1[key1]):
        close_matches = difflib.get_close_matches(name1, df2[key2], n=1, cutoff=threshold)
        if close_matches:
            match_name = close_matches[0]
            match_row = df2[df2[key2] == match_name]
            if not match_row.empty:
                row = match_row.iloc[0]
                match = row.to_dict()
                match[f"{key2}_original"] = name1
                matches.append((i, match))
    for i, match in matches:
        for col, val in match.items():
            df1.at[i, col] = val
    return df1

def run_bot():
    print("🚀 Lancement du bot")
    matches = get_matches()
    odds = get_odds()
    elo_df = load_elo()

    if matches.empty or odds.empty or elo_df is None:
        send_message("⚠️ Erreur récupération des données.")
        return

    # Fuzzy match sur les deux colonnes joueurs
    merged = matches.copy()
    merged = fuzzy_merge(merged, odds, "player1", "player1")
    merged = fuzzy_merge(merged, odds, "player2", "player2")
    merged["odds1"] = merged["odds1"]
    merged["odds2"] = merged["odds2"]

    merged = merged.dropna(subset=["odds1", "odds2"])
    if merged.empty:
        send_message("📭 Aucun match avec cotes trouvés aujourd’hui.")
        return

    elo_dict = {(row["player"], row["surface"]): row["elo"] for _, row in elo_df.iterrows()}
    def get_elo(player, surface):
        return elo_dict.get((player, surface), 1500)

    merged["elo1"] = merged.apply(lambda row: get_elo(row["player1"], row["surface"]), axis=1)
    merged["elo2"] = merged.apply(lambda row: get_elo(row["player2"], row["surface"]), axis=1)
    merged["proba1"] = merged.apply(lambda row: elo_probability(row["elo1"], row["elo2"]), axis=1)
    merged["proba2"] = 1 - merged["proba1"]
    merged["value1"] = merged["proba1"] * merged["odds1"] - 1
    merged["value2"] = merged["proba2"] * merged["odds2"] - 1

    bets = merged[(merged["value1"] > 0.05) | (merged["value2"] > 0.05)]

    message = f"📊 *{len(merged)} matchs analysés aujourd’hui*\n\n"
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
    run_bot()d
