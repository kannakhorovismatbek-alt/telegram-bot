import os
import json
import threading
from datetime import datetime, timedelta

import feedparser
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ======================
# KONFIGURATSIYA
# ======================
TOKEN = "8123494698:AAFDNeXyveuGBHAvtm9VPreF4Q2usmMZNlU"
CHAT_ID = "6633934393"
SENT_FILE = "sent_news.json"

RSS_FEEDS = [
    "https://kun.uz/rss/sport.xml",
    "https://daryo.uz/feed",
    "http://feeds.bbci.co.uk/sport/rss.xml",
    "https://www.theguardian.com/football/rss",
    "https://championat.asia/feed"
]

# ======================
# GLOBAL O‘ZGARUVCHILAR
# ======================
app = Flask(__name__)
sent_news = []
bot = Bot(token=TOKEN)

# Yuborilgan xabarlarni yuklash
if os.path.exists(SENT_FILE):
    try:
        with open(SENT_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                sent_news = data
    except:
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

⚽ Endi yangi sport yangiliklari sizga avtomatik yuboriladi.
    """
    await update.message.reply_text(text)

# ======================
# YANGILIKLARNI TEKSHIRISH VA YUBORISH
# ======================
def get_news():
    global sent_news
    three_days_ago = datetime.now() - timedelta(days=3)

    for rss_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries:
                try:
                    # Sanani olish
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    else:
                        published = datetime.now()

                    if published < three_days_ago:
                        continue
                    if entry.link in sent_news:
                        continue

                    title = entry.title
                    link = entry.link

                    # Rasm URL
                    image_url = None
                    media = entry.get("media_content")
                    if media and len(media) > 0:
                        image_url = media[0].get("url")

                    if not image_url and "links" in entry:
                        for l in entry.links:
                            if l.get("type", "").startswith("image"):
                                image_url = l.get("href")
                                break

                    caption = f"⚽ {title}\n\n🔗 {link}"

                    # Yuborish (sync usulda)
                    if image_url:
                        bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=caption)
                    else:
                        bot.send_message(chat_id=CHAT_ID, text=caption)

                    sent_news.append(link)
                    save_news()
                    print(f"✅ Yangilik yuborildi: {title} (manba: {rss_url})")

                except Exception as e:
                    print(f"❌ Entry xatosi: {e}")

        except Exception as e:
            print(f"❌ RSS xatosi ({rss_url}): {e}")

# ======================
# FLASK
# ======================
@app.route("/")
def home():
    return "TopGOL Bot ishlayapti"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ======================
# JADVAL (Scheduler)
# ======================
scheduler = BackgroundScheduler()
scheduler.add_job(get_news, "interval", minutes=5)
scheduler.start()

# ======================
# TELEGRAM APPLICATION
# ======================
telegram_app = Application.builder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))

# ======================
# ASOSIY BOSHQARUV
# ======================
if __name__ == "__main__":
    # Flask-ni alohida threadda ishga tushirish
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Botni ishga tushirish (to‘g‘ridan-to‘g‘ri, asyncio.runsiz)
    print("Bot ishga tushmoqda...")
    telegram_app.run_polling()
