import os
import json
import threading
from datetime import datetime, timedelta

import feedparser
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import Bot
from telegram import Update
from telegram.ext import ApplicationBuilder
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes

TOKEN = "8123494698:AAFDNeXyveuGBHAvtm9VPreF4Q2usmMZNlU"

CHAT_ID = "6633934393"

RSS_URL = "https://kun.uz/rss/sport.xml"

SENT_FILE = "sent_news.json"

bot = Bot(token=TOKEN)

app = Flask(**name**)

# =========================

# JSON LOAD

# =========================

sent_news = []

try:
if os.path.exists(SENT_FILE):

```
    with open(SENT_FILE, "r") as f:

        data = json.load(f)

        if isinstance(data, list):
            sent_news = data
```

except:
sent_news = []

# =========================

# SAVE

# =========================

def save_news():

```
with open(SENT_FILE, "w") as f:

    json.dump(sent_news, f)
```

# =========================

# START

# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

```
text = """
```

✅ TopGOL Bot ishga tushdi!

⚽ Endi yangi sport yangiliklari sizga yuboriladi.
"""

```
await update.message.reply_text(text)
```

# =========================

# NEWS

# =========================

def get_news():

```
global sent_news

try:

    feed = feedparser.parse(RSS_URL)

    three_days_ago = datetime.now() - timedelta(days=3)

    for entry in feed.entries:

        try:

            published = datetime(*entry.published_parsed[:6])

            if published < three_days_ago:
                continue

            if entry.link in sent_news:
                continue

            title = entry.title

            link = entry.link

            image_url = None

            media = entry.get("media_content")

            if media:

                if len(media) > 0:

                    image_url = media[0].get("url")

            caption = f"⚽ {title}\n\n🔗 {link}"

            if image_url:

                bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=image_url,
                    caption=caption
                )

            else:

                bot.send_message(
                    chat_id=CHAT_ID,
                    text=caption
                )

            sent_news.append(link)

            save_news()

            print("Yangi yangilik yuborildi")

        except Exception as e:

            print(e)

except Exception as e:

    print(e)
```

# =========================

# SCHEDULER

# =========================

scheduler = BackgroundScheduler()

scheduler.add_job(
get_news,
"interval",
minutes=5
)

scheduler.start()

# =========================

# FLASK

# =========================

@app.route("/")
def home():

```
return "TopGOL Bot ishlayapti"
```

# =========================

# TELEGRAM

# =========================

telegram_app = ApplicationBuilder().token(TOKEN).build()

telegram_app.add_handler(
CommandHandler("start", start)
)

# =========================

# MAIN

# =========================

if **name** == "**main**":

```
threading.Thread(
    target=telegram_app.run_polling,
    daemon=True
).start()

port = int(os.environ.get("PORT", 5000))

app.run(
    host="0.0.0.0",
    port=port
)
```
