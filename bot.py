import os
import json
import threading
from datetime import datetime, timedelta

import feedparser
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import Update, Bot
from telegram.ext import (
ApplicationBuilder,
CommandHandler,
ContextTypes,
)

# =========================

# TELEGRAM

# =========================

TOKEN = "8123494698:AAFDNeXyveuGBHAvtm9VPreF4Q2usmMZNlU"

CHAT_ID = "6633934393"

bot = Bot(token=TOKEN)

# =========================

# RSS

# =========================

RSS_URL = "https://kun.uz/rss/sport.xml"

# =========================

# FILE

# =========================

SENT_FILE = "sent_news.json"

# JSON faylni o'qish

try:
if os.path.exists(SENT_FILE):
with open(SENT_FILE, "r") as f:
sent_news = json.load(f)

```
        if not isinstance(sent_news, list):
            sent_news = []

else:
    sent_news = []
```

except:
sent_news = []

# =========================

# SAVE FUNCTION

# =========================

def save_news():
with open(SENT_FILE, "w") as f:
json.dump(sent_news, f)

# =========================

# FLASK

# =========================

app = Flask(**name**)

@app.route("/")
def home():
return "TopGOL Bot ishlayapti!"

# =========================

# START COMMAND

# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

```
text = f"""
```

✅ TopGOL Bot ishga tushdi!

🆔 Sizning ID:
{update.effective_user.id}

⚽ Endi yangi sport yangiliklari sizga yuboriladi.
"""

```
await update.message.reply_text(text)
```

# =========================

# NEWS FUNCTION

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

            # 3 kundan eski bo'lsa skip
            if published < three_days_ago:
                continue

            # Takroriy bo'lsa skip
            if entry.link in sent_news:
                continue

            title = entry.title
            link = entry.link

            # Rasm
            image_url = None

            media_content = entry.get("media_content")

            if media_content and len(media_content) > 0:
                image_url = media_content[0].get("url")

            caption = f"""
```

⚽ {title}

🔗 {link}
"""

```
            # Telegramga yuborish
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

            print("Yangi yangilik yuborildi!")

            sent_news.append(entry.link)

            save_news()

        except Exception as e:
            print(f"Yangilik xatosi: {e}")

except Exception as e:
    print(f"RSS xatosi: {e}")
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

# TELEGRAM BOT

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
# Telegram polling
threading.Thread(
    target=telegram_app.run_polling,
    daemon=True
).start()

# Flask
port = int(os.environ.get("PORT", 5000))

app.run(
    host="0.0.0.0",
    port=port
)
```
