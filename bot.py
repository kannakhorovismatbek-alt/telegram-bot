import os
import json
import asyncio
import threading
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

import requests
import xml.etree.ElementTree as ET
from flask import Flask
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ======================
# KONFIGURATSIYA
# ======================
TOKEN = "8123494698:AAFDNeXyveuGBHAvtm9VPreF4Q2usmMZNlU"
CHAT_ID = "6633934393"
SENT_FILE = "sent_news.json"

# Ishlaydigan RSS manbalari (feedparser kerak emas)
RSS_FEEDS = [
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
# RSS PARSER (feedparsiz)
# ======================
def parse_rss_feed(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall('.//item') or root.findall('.//entry')
        entries = []
        for item in items:
            title = item.findtext('title', '').strip()
            link = item.findtext('link', '')
            if not link:
                link_elem = item.find('link')
                if link_elem is not None:
                    link = link_elem.get('href', '')
            pub_date_str = item.findtext('pubDate') or item.findtext('published')
            pub_date = None
            if pub_date_str:
                try:
                    pub_date = parsedate_to_datetime(pub_date_str)
                except:
                    pass
            img_url = None
            enclosure = item.find('enclosure')
            if enclosure is not None:
                img_url = enclosure.get('url')
            if not img_url:
                media = item.find('.//{http://search.yahoo.com/mrss/}content')
                if media is not None:
                    img_url = media.get('url')
            entries.append((title, link, pub_date, img_url))
        return entries
    except Exception as e:
        print(f"RSS xatosi {url}: {e}")
        return []

# ======================
# YANGILIKLARNI TEKSHIRISH VA YUBORISH (ASYNC)
# ======================
async def get_news():
    global sent_news
    three_days_ago = datetime.now() - timedelta(days=3)

    for rss_url in RSS_FEEDS:
        entries = parse_rss_feed(rss_url)
        for title, link, pub_date, img_url in entries:
            try:
                if pub_date and pub_date < three_days_ago:
                    continue
                if link in sent_news:
                    continue
                caption = f"⚽ {title}\n\n🔗 {link}"
                if img_url:
                    await bot.send_photo(chat_id=CHAT_ID, photo=img_url, caption=caption)
                else:
                    await bot.send_message(chat_id=CHAT_ID, text=caption)
                sent_news.append(link)
                save_news()
                print(f"✅ Yuborildi: {title} ({rss_url})")
            except Exception as e:
                print(f"❌ Yuborish xatosi: {e}")

# ======================
# START KOMANDASI
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ TopGOL Bot ishga tushdi!\n⚽ Endi yangi sport yangiliklari yuboriladi."
    )

# ======================
# FLASK SERVER
# ======================
@app.route("/")
def home():
    return "TopGOL Bot ishlayapti"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ======================
# ASOSIY ASYNC FUNKSIYA
# ======================
async def main():
    # Flask thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Telegram bot
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Scheduler (AsyncIOScheduler async funksiya uchun)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(get_news, "interval", minutes=5)
    scheduler.start()

    # Botni polling orqali ishga tushirish
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
