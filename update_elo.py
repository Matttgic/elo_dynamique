
import pandas as pd
import os
import datetime

# 📁 Fichier de résultats (doit contenir les matchs joués récemment)
RESULTS_FILE = "results.csv"

# 📁 Fichier Elo à mettre à jour
ELO_FILE = "elo_dynamique_2024_K_variable.csv"

# 🎾 Fonction pour détecter le niveau du tournoi
def detect_tournament_level(tournament_name):
    name = tournament_name.lower()
    if any(gs in name for gs in ["roland", "wimbledon", "us open", "australian"]):
        return "G"
    if any(m1000 in name for m1000 in ["rome", "madrid", "miami", "indian wells", "monte", "cincinnati", "canada", "paris", "shanghai"]):
        return "M"
    if any(a500 in name for a500 in ["barcelona", "basel", "hamburg", "dubai", "acapulco", "washington", "beijing", "tokyo", "vienna", "rotterdam"]):
        return "A"
    if any(a250 in name for a250 in ["marseille", "lyon", "metz", "sydney", "adelaide", "geneva", "munich", "stockholm", "astana", "doha"]):
        return "B"
    if "olympic" in name:
        return "O"
    if "davis" in name:
        return "D"
    if any(team_event in name for team_event in ["billie", "fed cup"]):
        return "F"
    if any(lower_tier in name for lower_tier in ["challenger", "itf", "futures", "m25", "w60", "w100"]):
        return "I"
    return "?"

# 🧮 Fonction de mise à jour Elo
def update_elo(winner_elo, loser_elo, k):
    expected_win = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    new_winner_elo = winner_elo + k * (1 - expected_win)
    new_loser_elo = loser_elo + k * (0 - (1 - expected_win))
    return new_winner_elo, new_loser_elo

# 🎚️ Fonction pour déterminer le facteur K selon le niveau
def get_k_from_level(level):
    if level == "G": return 50
    if level == "M": return 40
    if level == "A": return 35
    if level == "B": return 30
    if level == "I": return 25
    return 30  # par défaut

# 📥 Charger les données
if not os.path.exists(RESULTS_FILE) or not os.path.exists(ELO_FILE):
    print("⛔ Fichiers manquants.")
    exit()

results_df = pd.read_csv(RESULTS_FILE)
elo_df = pd.read_csv(ELO_FILE)

# ✅ Ajouter colonne "level" à partir du nom du tournoi
results_df["level"] = results_df["tournament"].apply(detect_tournament_level)

# 📘 Dictionnaire (joueur, surface) => elo
elo_dict = {(row["player"], row["surface"]): row["elo"] for _, row in elo_df.iterrows()}

# 🔄 Mise à jour des elos pour chaque ligne
for _, row in results_df.iterrows():
    p1 = row["player1"]
    p2 = row["player2"]
    surface = row.get("surface", "hard").lower()
    winner = row["winner"]
    level = row.get("level", "?")
    k = get_k_from_level(level)

    elo1 = elo_dict.get((p1, surface), 1500)
    elo2 = elo_dict.get((p2, surface), 1500)

    if winner == p1:
        new_elo1, new_elo2 = update_elo(elo1, elo2, k)
    else:
        new_elo2, new_elo1 = update_elo(elo2, elo1, k)

    elo_dict[(p1, surface)] = new_elo1
    elo_dict[(p2, surface)] = new_elo2

# 💾 Reconstruction et sauvegarde
updated_elo_df = pd.DataFrame([
    {"player": key[0], "surface": key[1], "elo": value}
    for key, value in elo_dict.items()
])
updated_elo_df.to_csv(ELO_FILE, index=False)
print("✅ Fichier Elo mis à jour.")
