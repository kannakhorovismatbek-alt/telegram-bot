import os
import json
import asyncio
import threading
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

import requests
import xml.etree.ElementTree as ET
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
bot = Bot(token=TOKEN)

# Yuborilganlarni yuklash
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

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "✅ TopGOL Bot ishga tushdi!\n⚽ Endi yangi sport yangiliklari sizga yuboriladi."
    await update.message.reply_text(text)

# RSS ni o‘qish (feedparser o‘rniga)
def parse_rss():
    try:
        response = requests.get(RSS_URL, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        entries = []
        for item in items:
            title = item.findtext('title', '').strip()
            link = item.findtext('link', '').strip()
            pub_date_str = item.findtext('pubDate', '')
            pub_date = None
            if pub_date_str:
                try:
                    pub_date = parsedate_to_datetime(pub_date_str)
                except:
                    try:
                        # Alternativ format
                        pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
                    except:
                        pass
            # Rasm URL (enclosure yoki media:content)
            image_url = None
            enclosure = item.find('enclosure')
            if enclosure is not None:
                image_url = enclosure.get('url')
            if not image_url:
                media = item.find('{http://search.yahoo.com/mrss/}content')
                if media is not None:
                    image_url = media.get('url')
            entries.append((title, link, pub_date, image_url))
        return entries
    except Exception as e:
        print(f"RSS xatosi: {e}")
        return []

# Yangiliklarni tekshirish va yuborish
async def check_and_send():
    global sent_news
    try:
        entries = parse_rss()
        three_days_ago = datetime.now() - timedelta(days=3)
        for title, link, pub_date, image_url in entries:
            if pub_date and pub_date < three_days_ago:
                continue
            if link in sent_news:
                continue

            caption = f"⚽ {title}\n\n🔗 {link}"
            if image_url:
                await bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=caption)
            else:
                await bot.send_message(chat_id=CHAT_ID, text=caption)

            sent_news.append(link)
            save_news()
            print(f"✅ Yuborildi: {title}")
    except Exception as e:
        print(f"❌ Xato: {e}")

# Har 5 daqiqada ishlovchi fon vazifasi
async def periodic_check():
    while True:
        await check_and_send()
        await asyncio.sleep(300)

# Flask marshruti
@app.route("/")
def home():
    return "TopGOL Bot ishlayapti"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Asosiy async funksiya
async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Flask ni alohida threadda ishga tushirish
    threading.Thread(target=run_flask, daemon=True).start()

    # Vaqtli tekshiruvni boshlash
    asyncio.create_task(periodic_check())

    # Botni ishga tushirish
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.idle()

if __name__ == "__main__":
    asyncio.run(main())
