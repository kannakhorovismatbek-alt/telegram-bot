import os
import json
import threading
from datetime import datetime, timedelta
import asyncio

import feedparser
from flask import Flask
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ======================
# KONFIGURATSIYA
# ======================
TOKEN = "8123494698:AAFDNeXyveuGBHAvtm9VPreF4Q2usmMZNlU"
CHAT_ID = "6633934393"
RSS_URL = "https://kun.uz/rss/sport.xml"
SENT_FILE = "sent_news.json"

# ======================
# GLOBAL O‘ZGARUVCHILAR
# ======================
app = Flask(__name__)
sent_news = []
application = None  # keyin o‘rnatiladi

# ======================
# YUBORILGANLARNI YUKLASH
# ======================
if os.path.exists(SENT_FILE):
    try:
        with open(SENT_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                sent_news = data
    except Exception:
        sent_news = []

def save_news():
    with open(SENT_FILE, "w") as f:
        json.dump(sent_news, f)

# ======================
# TELEGRAM /start
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
✅ TopGOL Bot ishga tushdi!

⚽ Endi yangi sport yangiliklari sizga yuboriladi.
    """
    await update.message.reply_text(text)

# ======================
# ASYNC YANGILIKLARNI OLISH VA YUBORISH
# ======================
async def get_news():
    global sent_news, application
    if application is None:
        return

    try:
        feed = feedparser.parse(RSS_URL)
        three_days_ago = datetime.now() - timedelta(days=3)

        for entry in feed.entries:
            try:
                if not hasattr(entry, 'published_parsed') or not entry.published_parsed:
                    continue
                published = datetime(*entry.published_parsed[:6])
                if published < three_days_ago:
                    continue
                if entry.link in sent_news:
                    continue

                title = entry.title
                link = entry.link

                # Rasm URL
                image_url = None
                if hasattr(entry, 'media_content') and entry.media_content:
                    image_url = entry.media_content[0].get('url')

                caption = f"⚽ {title}\n\n🔗 {link}"

                if image_url:
                    await application.bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=caption)
                else:
                    await application.bot.send_message(chat_id=CHAT_ID, text=caption)

                sent_news.append(link)
                save_news()
                print(f"Yangi yangilik yuborildi: {title}")
            except Exception as e:
                print(f"Xato (entry): {e}")
    except Exception as e:
        print(f"Xato (feed): {e}")

# ======================
# FLASK ROUTE
# ======================
@app.route("/")
def home():
    return "TopGOL Bot ishlayapti"

# ======================
# ASOSIY FUNKSIYA (async)
# ======================
async def main():
    global application
    # Telegram application ni yaratish
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Async scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(get_news, "interval", minutes=5)
    scheduler.start()

    # Botni polling qilish (bu ham async)
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Flask-ni alohida threadda ishga tushirish
    def run_flask():
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Botni bloklovchi ishga tushirish (asosiy oqimda)
    await application.idle()

if __name__ == "__main__":
    asyncio.run(main())
