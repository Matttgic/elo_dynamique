import pandas as pd
import os

# 📁 Fichiers nécessaires
RESULTS_FILE = "results.csv"
ELO_FILE = "elo_dynamique_2024_K_variable.csv"

# 🔢 Fonction pour déterminer le niveau du tournoi
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
    if "olympic" in name: return "O"
    if "davis" in name: return "D"
    if "billie" in name or "fed cup" in name: return "F"
    if "challenger" in name or "itf" in name: return "I"
    return "?"

# 🔁 Calcul Elo
def update_elo(winner_elo, loser_elo, k):
    expected_win = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    new_winner_elo = winner_elo + k * (1 - expected_win)
    new_loser_elo = loser_elo + k * (0 - (1 - expected_win))
    return new_winner_elo, new_loser_elo

# 🎚️ K-factor
def get_k(level):
    return {
        "G": 50, "M": 40, "A": 35, "B": 30, "I": 25
    }.get(level, 30)

# ✅ Charger fichiers
if not os.path.exists(RESULTS_FILE) or not os.path.exists(ELO_FILE):
    print("⛔ Fichiers manquants.")
    exit()

results_df = pd.read_csv(RESULTS_FILE)
elo_df = pd.read_csv(ELO_FILE)

if results_df.empty:
    print("⚠️ Aucun résultat à traiter.")
    exit()

# ✅ Détection du niveau
results_df["level"] = results_df["tournament"].apply(detect_tournament_level)

# ➕ Ajouter joueurs absents
all_players = pd.unique(results_df[["player1", "player2"]].values.ravel())
for p in all_players:
    if p not in elo_df["player"].values:
        new_row = {"player": p, "elo_Hard": 1500, "elo_Clay": 1500, "elo_Grass": 1500}
        elo_df = pd.concat([elo_df, pd.DataFrame([new_row])], ignore_index=True)

# 🔄 Mise à jour
for _, row in results_df.iterrows():
    p1, p2 = row["player1"], row["player2"]
    surface = str(row.get("surface", "hard")).capitalize()
    winner = row["winner"]
    level = row.get("level", "?")
    k = get_k(level)

    col = f"elo_{surface}"
    if col not in ["elo_Hard", "elo_Clay", "elo_Grass"]:
        col = "elo_Hard"  # Valeur par défaut

    try:
        elo1 = elo_df.loc[elo_df["player"] == p1, col].values[0]
        elo2 = elo_df.loc[elo_df["player"] == p2, col].values[0]
    except IndexError:
        print(f"⛔ Joueur introuvable : {p1} ou {p2}")
        continue

    if winner == p1:
        new_elo1, new_elo2 = update_elo(elo1, elo2, k)
    else:
        new_elo2, new_elo1 = update_elo(elo2, elo1, k)

    elo_df.loc[elo_df["player"] == p1, col] = new_elo1
    elo_df.loc[elo_df["player"] == p2, col] = new_elo2

# 💾 Sauvegarde
elo_df.to_csv(ELO_FILE, index=False)
print("✅ Elo mis à jour par surface.")
