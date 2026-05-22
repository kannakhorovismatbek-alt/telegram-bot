import os
import json
import time
import threading
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from telegram import Bot
from flask import Flask

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
            date_text = item.select_one(".news-date").text.strip()
            try:
                news_date = datetime.strptime(date_text, "%H:%M / %d.%m.%Y")
            except:
                news_date = datetime.now()

            if datetime.now() - news_date > timedelta(days=3):
                continue

            caption = f"⚽ {title}\n\n🔗 {full_link}"

            # Telegramga yuborish
            if image_url:
                bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=caption)
            else:
                bot.send_message(chat_id=CHAT_ID, text=caption)

            sent_news.append(full_link)
            save_news()
    except Exception as e:
        print(f"Error fetching news: {e}")

def scheduler():
    while True:
        get_news()
        # Har 5 daqiqada tekshiradi
        time.sleep(300)

# Background thread ishga tushadi
threading.Thread(target=scheduler, daemon=True).start()

@app.route("/")
def home():
    return "TopGOL Bot is running and auto-checking every 5 minutes!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
