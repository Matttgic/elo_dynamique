# update_elo.py

import pandas as pd
import os

# 📄 Chemins de fichiers
ELO_FILE = "elo_dynamique_2024_K_variable.csv"
RESULTS_FILE = "match_results.csv"

# 🧹 Fonction de normalisation des noms
def normalize_name(name):
    if not isinstance(name, str): return ""
    parts = name.strip().lower().replace("-", " ").replace(".", "").replace("'", "").split()
    if len(parts) == 0:
        return ""
    elif len(parts) == 1:
        return parts[0]
    else:
        return f"{parts[0][0]}. {parts[-1]}"

# 📈 Fonction de mise à jour Elo
def update_elo():
    if not os.path.exists(RESULTS_FILE):
        print("⛔ Résultats non trouvés")
        return
    if not os.path.exists(ELO_FILE):
        print("⛔ Fichier Elo manquant")
        return

    results = pd.read_csv(RESULTS_FILE)
    elo = pd.read_csv(ELO_FILE)

    # Normalisation
    results["player1"] = results["player1"].apply(normalize_name)
    results["player2"] = results["player2"].apply(normalize_name)
    results["winner"] = results["winner"].apply(normalize_name)
    elo["player"] = elo["player"].apply(normalize_name)

    # 🧠 Initialisation si joueur inconnu
    def get_elo(player, surface):
        col = f"elo_{surface.capitalize()}"
        if player not in elo["player"].values:
            new_row = {"player": player, "elo_Hard": 1500, "elo_Clay": 1500, "elo_Grass": 1500}
            elo.loc[len(elo)] = new_row
        return elo.loc[elo["player"] == player, col].values[0]

    def set_elo(player, surface, new_elo):
        col = f"elo_{surface.capitalize()}"
        elo.loc[elo["player"] == player, col] = new_elo

    K = 32
    for _, row in results.iterrows():
        p1, p2, winner, surface = row["player1"], row["player2"], row["winner"], row["surface"]
        if surface not in ["hard", "clay", "grass"]:
            continue
        r1 = 1 if winner == p1 else 0
        r2 = 1 - r1

        elo1 = get_elo(p1, surface)
        elo2 = get_elo(p2, surface)

        prob1 = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
        prob2 = 1 - prob1

        new_elo1 = elo1 + K * (r1 - prob1)
        new_elo2 = elo2 + K * (r2 - prob2)

        set_elo(p1, surface, new_elo1)
        set_elo(p2, surface, new_elo2)

    # 💾 Sauvegarde finale
    elo.to_csv(ELO_FILE, index=False)
    print(f"✅ Fichier Elo mis à jour avec {len(results)} résultats.")

if __name__ == "__main__":
    print("🧠 Lancement de update_elo.py")
    update_elo()
