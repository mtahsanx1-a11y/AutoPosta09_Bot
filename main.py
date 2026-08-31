import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Render Web Service-কে শান্ত রাখার জন্য ছোট ওয়েব সার্ভার
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running live on Render Web Service!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# টেলিগ্রাম বটের মেইন কনফিগারেশন
TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL_ID = -1001868030606
TARGET_OLD_LINK = "https://t.me/BigBagSmartMoney"

DESTINATION_CONFIG = [
    {
        "group_id": -1002395561078,
        "new_link": "https://t.me/ForexGlobal_support"
    },
    {
        "group_id": -1003310252089,
        "new_link": "https://t.me/KhalidAl_Ameen"
    },
    {
        "group_id": -1003028410733,
        "new_link": "https://t.me/ForexGlobal_support"
    }
]

async def auto_repost_with_custom_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post and update.channel_post.chat.id == SOURCE_CHANNEL_ID:
        original_text = update.channel_post.text or update.channel_post.caption or ""

        for config in DESTINATION_CONFIG:
            group_id = config["group_id"]
            custom_link = config["new_link"]
            modified_text = original_text.replace(TARGET_OLD_LINK, custom_link)

            try:
                if update.channel_post.photo:
                    photo_id = update.channel_post.photo[-1].file_id
                    await context.bot.send_photo(chat_id=group_id, photo=photo_id, caption=modified_text)
                elif update.channel_post.video:
                    video_id = update.channel_post.video.file_id
                    await context.bot.send_video(chat_id=group_id, video=video_id, caption=modified_text)
                else:
                    await context.bot.send_message(chat_id=group_id, text=modified_text)
                    
                print(f"Successfully reposted to channel: {group_id}")
            except Exception as e:
                print(f"Failed to post in {group_id}: {e}")

def main():
    if not TOKEN:
        print("BOT_TOKEN missing!")
        return

    # ফ্ল্যাস্ক সার্ভার ব্যাকগ্রাউন্ড থ্রেডে রান করানো
    threading.Thread(target=run_flask, daemon=True).start()

    # টেলিগ্রাম বট স্টার্ট করা
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.Chat(SOURCE_CHANNEL_ID), auto_repost_with_custom_links))

    print("Auto-Repost Bot is running smoothly on Web Service...")
    bot_app.run_polling()

if __name__ == "__main__":
    main()
            
