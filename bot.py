import os
import json
import asyncio
import threading
from datetime import datetime, timedelta

import feedparser
from flask import Flask
from telegram import Bot, Update
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
bot = Bot(token=TOKEN)  # <-- Bu global bot obyekti

# Yuborilgan yangiliklarni yuklash
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

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
✅ TopGOL Bot ishga tushdi!

⚽ Endi yangi sport yangiliklari sizga yuboriladi.
    """
    await update.message.reply_text(text)

# Yangiliklarni tekshirish va yuborish (async)
async def check_and_send():
    global sent_news
    try:
        feed = feedparser.parse(RSS_URL)
        uch_kun_oldin = datetime.now() - timedelta(days=3)

        for entry in feed.entries:
            # Sanani tekshirish
            if not hasattr(entry, 'published_parsed') or not entry.published_parsed:
                continue
            published = datetime(*entry.published_parsed[:6])
            if published < uch_kun_oldin:
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

            # Xabarni yuborish (await bilan)
            if image_url:
                await bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=caption)
            else:
                await bot.send_message(chat_id=CHAT_ID, text=caption)

            sent_news.append(link)
            save_news()
            print(f"Yangi yangilik yuborildi: {title}")

    except Exception as e:
        print(f"Xatolik: {e}")

# Har 5 daqiqada ishlaydigan fon vazifasi
async def periodic_check():
    while True:
        await check_and_send()
        await asyncio.sleep(300)  # 5 daqiqa

# Flask marshruti
@app.route("/")
def home():
    return "TopGOL Bot ishlayapti"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Asosiy async funksiya
async def main():
    # Telegram aplikatsiyasini yaratish
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Flaskni alohida threadda ishga tushirish
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Vaqtli tekshirish vazifasini boshlash
    asyncio.create_task(periodic_check())

    # Botni ishga tushirish
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.idle()  # Bot to‘xtaguncha kutadi

if __name__ == "__main__":
    asyncio.run(main())
