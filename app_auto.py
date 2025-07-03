from flask import Flask, request, redirect, render_template_string
import csv
import os
from datetime import datetime

app = Flask(__name__)

TELEGRAM_TOKEN = "7484011068:AAE1WXvqYnN6JOSVyMx2BZRWiishwa7nNk0"
CSV_FILE = os.path.expanduser("~/bilan_telegram.csv")

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bilan Tennis Telegram</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; padding: 20px; }
        table { border-collapse: collapse; width: 100%; font-size: 14px; }
        th, td { border: 1px solid #ccc; padding: 6px; text-align: center; }
        th { background-color: #f4f4f4; }
        h1 { font-size: 24px; }
        input[type=submit] { margin: 10px 0; padding: 8px 14px; font-size: 14px; }
    </style>
</head>
<body>
    <h1>📊 Bilan Tennis</h1>
    <p>Total : {{ total }} | ✅ Gagnés : {{ wins }} | ❌ Perdus : {{ losses }} | 🔁 Taux de réussite : {{ winrate }}% | 💰 ROI : {{ roi }}% | 💵 Bilan : {{ profit }} €</p>

    <form method="post">
        <input type="submit" value="💾 Enregistrer les résultats">
        <table>
            <tr>
                <th>Date</th><th>Joueur</th><th>Adversaire</th><th>Surface</th>
                <th>Cote</th><th>Value</th><th>Résultat</th><th>Action</th>
            </tr>
            {% for i in range(rows|length) %}
            <tr>
                {% for cell in rows[i][:7] %}
                <td>{{ cell }}</td>
                {% endfor %}
                <td>
                    <select name="result_{{ i }}">
                        <option value="">-</option>
                        <option value="1" {% if rows[i][6] == "1" %}selected{% endif %}>✅</option>
                        <option value="0" {% if rows[i][6] == "0" %}selected{% endif %}>❌</option>
                    </select>
                </td>
            </tr>
            {% endfor %}
        </table>
        <input type="submit" value="💾 Enregistrer les résultats">
    </form>
</body>
</html>
"""

def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Joueur", "Adversaire", "Surface", "Cote", "Value", "Résultat"])

@app.route("/", methods=["GET", "POST"])
def index():
    ensure_csv()
    with open(CSV_FILE, newline='', encoding="utf-8") as f:
        reader = list(csv.reader(f))
        header = reader[0]
        rows = reader[1:]

    try:
        rows.sort(key=lambda x: datetime.strptime(x[0], "%Y-%m-%d"), reverse=True)
    except:
        pass

    if request.method == "POST":
        for i in range(len(rows)):
            new_result = request.form.get(f"result_{i}")
            if new_result in ("0", "1"):
                rows[i][6] = new_result
        with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        return redirect("/")

    stake = 20
    wins = sum(1 for row in rows if row[6] == "1")
    losses = sum(1 for row in rows if row[6] == "0")
    profit = sum((float(row[4]) * stake - stake) if row[6] == "1" else -stake for row in rows if row[6] in ("0", "1"))
    total = wins + losses
    winrate = round(100 * wins / total, 1) if total > 0 else 0
    roi = round(100 * profit / (total * stake), 1) if total > 0 else 0

    return render_template_string(TEMPLATE, rows=rows, total=total, wins=wins, losses=losses, winrate=winrate, roi=roi, profit=round(profit, 2))

@app.route(f"/telegram/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    ensure_csv()
    data = request.get_json()
    message = data.get("message", {}).get("text", "")

    lines = message.strip().split("\n")
    entries = []

    for i in range(len(lines)):
        if lines[i].startswith("🎾") and i+1 < len(lines) and lines[i+1].startswith("➡️"):
            try:
                match_info = lines[i][2:].strip()
                bet_info = lines[i+1][2:].strip()

                joueur, adversaire = match_info.split(" vs ")
                adversaire = adversaire.split(" (")[0].strip()
                surface = match_info.split("(")[-1].replace(")", "").strip()
                joueur_parie = bet_info.split("@")[0].strip()
                cote = float(bet_info.split("@")[-1].split("(")[0].strip())
                value = bet_info.split("value:")[-1].replace("%)", "").replace("%", "").strip()

                today = datetime.today().strftime("%Y-%m-%d")
                entries.append([today, joueur_parie, adversaire, surface, cote, value, ""])
            except Exception as e:
                print("Erreur de parsing:", e)
                continue

    if entries:
        with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(entries)

    return "OK"

if __name__ == "__main__":
    app.run(debug=True)
