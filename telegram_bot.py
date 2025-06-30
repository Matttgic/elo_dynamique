# telegram_bot.py

import os
import telegram

# 🔐 Récupération des variables d’environnement injectées par GitHub Actions
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text: str):
    """
    Envoie un message Telegram formaté en Markdown.
    """
    try:
        bot = telegram.Bot(token=BOT_TOKEN)
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
        print("✅ Message Telegram envoyé")
    except Exception as e:
        print(f"❌ Erreur envoi Telegram : {e}") 
