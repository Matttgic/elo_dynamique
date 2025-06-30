# telegram_bot.py

import os
import telegram

# Récupère les variables d'environnement (à définir dans ton GitHub Actions)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text):
    """
    Envoie un message Telegram formaté en Markdown.
    """
    try:
        bot = telegram.Bot(token=BOT_TOKEN)
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
        print("✅ Message Telegram envoyé")
    except Exception as e:
        print(f"❌ Erreur envoi Telegram : {e}")
