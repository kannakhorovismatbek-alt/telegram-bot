import os
import json
from datetime import datetime, timedelta

import feedparser
from telegram import Bot
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

# --- TELEGRAM INFO ---
TOKEN = "8123494698:AAFDNeXyveuGBHAvtm9VPreF4Q2usmMZNlU"
CHAT_ID = "@topgol_uz"

bot = Bot(token=TOKEN)
RSS_URL = "https://kun.uz/rss/sport.xml"
SENT_FILE = "sent_news.json"

app = Flask(__name__)

# Oldin yuborilgan yangiliklar
if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r") as f:
        sent_news = json.load(f)
else:
    sent_news = []

def save_news():
    with open(SENT_FILE, "w") as f:
        json.dump(sent_news, f)

def get_news():
    try:
        feed = feedparser.parse(RSS_URL)
        three_days_ago = datetime.now() - timedelta(days=3)

        for entry in feed.entries:
            # Sana
            published = datetime(*entry.published_parsed[:6])
            if published < three_days_ago:
                continue

            # Takroriy yangilikni yubormaslik
            if entry.link in sent_news:
                continue

            # Sarlavha va link
            title = entry.title
            link = entry.link

            # Rasm
            media_content = entry.get('media_content')
            image_url = media_content[0]['url'] if media_content and len(media_content) > 0 else None

            # Caption
            caption = f"⚽ {title}\n\n🔗 {link}"

            # Telegramga yuborish
            try:
                if image_url:
                    bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=caption)
                else:
                    bot.send_message(chat_id=CHAT_ID, text=caption)
            except Exception as e:
                print(f"Telegram sending error: {e}")

            sent_news.append(entry.link)
            save_news()

    except Exception as e:
        print(f"Error fetching RSS news: {e}")

# Scheduler — har 5 daqiqada yangiliklarni tekshiradi
scheduler = BackgroundScheduler()
scheduler.add_job(get_news, 'interval', minutes=5)
scheduler.start()

@app.route("/")
def home():
    return "TopGOL Bot is running and auto-checking every 5 minutes!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
