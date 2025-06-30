import os
import telegram

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text):
    try:
        bot = telegram.Bot(token=BOT_TOKEN)
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
        print("✅ Message Telegram envoyé")
    except Exception as e:
        print(f"❌ Erreur envoi Telegram : {e}")
