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

# Ishlatiladigan RSS manbalari
RSS_FEEDS = [
    "https://daryo.uz/feed",
    "https://championat.asia/feed",
    "http://feeds.bbci.co.uk/sport/rss.xml",
    "https://www.theguardian.com/football/rss",
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
        with open(SENT_FILE) as f:
            sent_news = json.load(f)
            if not isinstance(sent_news, list):
                sent_news = []
    except:
        sent_news = []

def save_news():
    with open(SENT_FILE, "w") as f:
        json.dump(sent_news, f)

def parse_rss(url):
    """RSS ni o‘qiydi va (sarlavha, havola, sana, rasm) ro‘yxatini qaytaradi"""
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
            pub_str = item.findtext('pubDate') or item.findtext('published')
            pub_date = None
            if pub_str:
                try:
                    pub_date = parsedate_to_datetime(pub_str)
                except:
                    pass
            img = None
            enc = item.find('enclosure')
            if enc is not None:
                img = enc.get('url')
            if not img:
                media = item.find('.//{http://search.yahoo.com/mrss/}content')
                if media is not None:
                    img = media.get('url')
            entries.append((title, link, pub_date, img))
        return entries
    except Exception as e:
        print(f"RSS xatosi {url}: {e}")
        return []

async def get_news():
    """Yangiliklarni tekshirish va yuborish"""
    global sent_news
    three_days_ago = datetime.now() - timedelta(days=3)
    for url in RSS_FEEDS:
        for title, link, pub_date, img in parse_rss(url):
            if pub_date and pub_date < three_days_ago:
                continue
            if link in sent_news:
                continue
            caption = f"⚽ {title}\n\n🔗 {link}"
            try:
                if img:
                    await bot.send_photo(chat_id=CHAT_ID, photo=img, caption=caption)
                else:
                    await bot.send_message(chat_id=CHAT_ID, text=caption)
                sent_news.append(link)
                save_news()
                print(f"✅ Yuborildi: {title}")
            except Exception as e:
                print(f"❌ Yuborish xatosi: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ TopGOL Bot ishga tushdi!\n⚽ Yangi sport yangiliklari keladi.")

@app.route("/")
def home():
    return "TopGOL Bot ishlayapti"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    scheduler = AsyncIOScheduler()
    scheduler.add_job(get_news, "interval", minutes=5)
    scheduler.start()
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
