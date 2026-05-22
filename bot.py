import os
import json
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from telegram import Bot
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

# --- TELEGRAM INFO ---
TOKEN = "8123494698:AAFDNeXyveuGBHAvtm9VPreF4Q2usmMZNlU"
CHAT_ID = "@topgol_uz"

bot = Bot(token=TOKEN)
URL = "https://kun.uz/news/category/sport"
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
        r = requests.get(URL)
        soup = BeautifulSoup(r.text, "html.parser")

        news_items = soup.select(".news")[:10]

        for item in news_items:
            title = item.get_text(strip=True)
            link = item.find("a")["href"]
            full_link = "https://kun.uz" + link

            if full_link in sent_news:
                continue

            # Rasm
            image = item.find("img")
            image_url = image["src"] if image else None

            # Sana
            date_elem = item.select_one(".news-date")
            date_text = date_elem.text.strip() if date_elem else ""
            try:
                news_date = datetime.strptime(date_text, "%H:%M / %d.%m.%Y")
            except:
                news_date = datetime.now()

            if datetime.now() - news_date > timedelta(days=3):
                continue

            caption = f"⚽ {title}\n\n🔗 {full_link}"

            # Telegramga yuborish
            try:
                if image_url:
                    bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=caption)
                else:
                    bot.send_message(chat_id=CHAT_ID, text=caption)
            except Exception as e:
                print(f"Telegram sending error: {e}")

            sent_news.append(full_link)
            save_news()
    except Exception as e:
        print(f"Error fetching news: {e}")

# Scheduler ishga tushadi
scheduler = BackgroundScheduler()
scheduler.add_job(get_news, 'interval', minutes=5)
scheduler.start()

@app.route("/")
def home():
    return "TopGOL Bot is running and auto-checking every 5 minutes!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
