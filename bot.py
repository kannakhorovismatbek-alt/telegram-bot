import os
import json
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
RSS_URL = "https://daryo.uz/feed"  # Siz to‘g‘ri manzilni qo‘yasiz
SENT_FILE = "sent_news.json"

# ======================
# GLOBAL
# ======================
app = Flask(__name__)
sent_news = []
bot = Bot(token=TOKEN)

# Yuborilganlarni yuklash
if os.path.exists(SENT_FILE):
    try:
        with open(SENT_FILE, "r") as f:
            sent_news = json.load(f)
            if not isinstance(sent_news, list):
                sent_news = []
    except:
        sent_news = []

def save_news():
    with open(SENT_FILE, "w") as f:
        json.dump(sent_news, f)

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ TopGOL Bot ishga tushdi!\n⚽ Sport yangiliklari keladi.")

# RSS parser (feedparsiz)
def parse_rss():
    try:
        r = requests.get(RSS_URL, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = root.findall('.//item')
        news = []
        for item in items:
            title = item.findtext('title', '').strip()
            link = item.findtext('link', '').strip()
            pub_date_str = item.findtext('pubDate', '')
            pub_date = None
            if pub_date_str:
                try:
                    pub_date = parsedate_to_datetime(pub_date_str)
                except:
                    pass
            img = None
            enc = item.find('enclosure')
            if enc is not None:
                img = enc.get('url')
            if not img:
                media = item.find('{http://search.yahoo.com/mrss/}content')
                if media is not None:
                    img = media.get('url')
            news.append((title, link, pub_date, img))
        return news
    except Exception as e:
        print(f"RSS xatosi: {e}")
        return []

# Yangiliklarni tekshirish va yuborish (async)
# context argumenti job_queue uchun kerak (ixtiyoriy)
async def check_and_send(context: ContextTypes.DEFAULT_TYPE = None):
    global sent_news
    try:
        news = parse_rss()
        if not news:
            return
        three_days_ago = datetime.now() - timedelta(days=3)
        for title, link, pub_date, img_url in news:
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
            print(f"✅ Yuborildi: {title}")
    except Exception as e:
        print(f"❌ Xato: {e}")

# Flask
@app.route("/")
def home():
    return "TopGOL Bot ishlayapti"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# MAIN – sinxron
def main():
    # Flask thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Telegram application
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    # JobQueue orqali har 5 daqiqada check_and_send ni ishga tushirish
    # interval = 300 sekund = 5 daqiqa, first=10 (birinchi marta 10 sekunddan keyin)
    application.job_queue.run_repeating(check_and_send, interval=300, first=10)
    
    # Botni ishga tushirish (bloklanadi)
    application.run_polling()

if __name__ == "__main__":
    main()
