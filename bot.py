import json
import telebot
from flask import Flask, request

TOKEN = "8607706992:AAEhF7ySlUqx2ikuh0qCOfjhY2oJVpGMTdM"
RENDER_URL = "https://topgolsupportbot.onrender.com"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

with open("faq.json", "r", encoding="utf-8") as f:
    FAQ = json.load(f)

WEBHOOK_URL = f"{RENDER_URL}/{TOKEN}"

@app.route("/")
def index():
    return "Bot ishlayapti"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(
        request.stream.read().decode("utf-8")
    )
    bot.process_new_updates([update])
    return "ok", 200


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Assalomu alaykum!\nTopGol Support botiga xush kelibsiz."
    )


@bot.message_handler(func=lambda message: True)
def faq_handler(message):
    text = message.text.lower()

    for question, answer in FAQ.items():
        if question.lower() in text:
            bot.reply_to(message, answer)
            return

    bot.reply_to(
        message,
        "Savolingiz adminlarga yuborildi."
    )


bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )
