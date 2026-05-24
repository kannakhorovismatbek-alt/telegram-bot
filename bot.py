import os
import json
import threading
from datetime import datetime, timedelta

import feedparser
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ======================
# TELEGRAM (to‘g‘ridan-to‘g‘ri kod ichida)
# ======================
TOKEN = "8123494698:AAFDNeXyveuGBHAvtm9VPreF4Q2usmMZNlU"
CHAT_ID = "6633934393"

bot = Bot(token=TOKEN)

# ======================
# RSS
# ======================
RSS_URL = "https://kun.uz/rss/sport.xml"

# ======================
# FILE
# ======================
SENT_FILE = "sent_news.json"

# ======================
# FLASK
# ======================
app = Flask(__name__)

# ======================
# LOAD NEWS
# ======================
sent_news = []

if os.path.exists(SENT_FILE):
    try:
        with open(SENT_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                sent_news = data
    except Exception:
        sent_news = []

# ======================
# SAVE FUNCTION
# ======================
def save_news():
    with open(SENT_FILE, "w") as f:
        json.dump(sent_news, f)

# ======================
# START COMMAND
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
✅ TopGOL Bot ishga tushdi!

⚽ Endi yangi sport yangiliklari sizga yuboriladi.
    """
    await update.message.reply_text(text)

# ======================
# NEWS FUNCTION
# ======================
def get_news():
    global sent_news
    try:
        feed = feedparser.parse(RSS_URL)
        three_days_ago = datetime.now() - timedelta(days=3)

        for entry in feed.entries:
            try:
                # Sana mavjudligini tekshirish
                if not hasattr(entry, 'published_parsed') or not entry.published_parsed:
                    continue

                published = datetime(*entry.published_parsed[:6])
                if published < three_days_ago:
                    continue

                if entry.link in sent_news:
                    continue

                title = entry.title
                link = entry.link

                # Rasm URL olish
                image_url = None
                if hasattr(entry, 'media_content') and entry.media_content:
                    image_url = entry.media_content[0].get('url')

                caption = f"⚽ {title}\n\n🔗 {link}"

                if image_url:
                    bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=caption)
                else:
                    bot.send_message(chat_id=CHAT_ID, text=caption)

                sent_news.append(link)
                save_news()
                print(f"Yangi yangilik yuborildi: {title}")

            except Exception as e:
                print(f"Xato (entry): {e}")

    except Exception as e:
        print(f"Xato (feed): {e}")

# ======================
# SCHEDULER
# ======================
scheduler = BackgroundScheduler()
scheduler.add_job(get_news, "interval", minutes=5)
scheduler.start()

# ======================
# FLASK ROUTE
# ======================
@app.route("/")
def home():
    return "TopGOL Bot ishlayapti"

# ======================
# TELEGRAM APP
# ======================
telegram_app = ApplicationBuilder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    # Botni alohida threadda polling qilish
    threading.Thread(target=telegram_app.run_polling, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
