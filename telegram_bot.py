# telegram_bot.py

import os
import requests

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text):
    """
    Envoie un message Telegram simple, synchrone, compatible GitHub Actions.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Message Telegram envoyé")
        else:
            print(f"❌ Erreur Telegram : {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception envoi Telegram : {e}")
