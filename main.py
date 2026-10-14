import os
import re
import asyncio
import threading
from flask import Flask
from telegram import Update, InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

TOKEN = os.getenv("BOT_TOKEN")

# মেইন চ্যানেল আইডি
SOURCE_CHANNEL_ID = -1001868030606

# মেইন চ্যানেলের ইউজারনেম
OLD_USERNAME = "BigBagSmartMoney"

# আপনার টার্গেট চ্যানেল ও গ্রুপগুলোর তালিকা
DESTINATION_CONFIG = [
    {
        "chat_id": -1002395561078,
        "new_link": "https://t.me/ForexGlobal_support"
    },
    {
        "chat_id": -1003310252089,
        "new_link": "https://t.me/KhalidAl_Ameen"
    },
    {
        "chat_id": -1003028410733,
        "new_link": "https://t.me/ForexGlobal_support"
    },
    {
        "chat_id": -100239556107,
        "new_link": "https://t.me/ForexGlobal_support"
    },
    {
        "chat_id": -1003784053762,  # আপনার কাঙ্ক্ষিত গ্রুপ আইডি
        "new_link": "https://t.me/ForexGlobal_support"
    }
]

media_groups_cache = {}

def replace_all_old_links(text, new_link):
    if not text:
        return text
    pattern = re.compile(rf'(https?://)?(www\.)?t\.me/{OLD_USERNAME}(/\S*)?|@{OLD_USERNAME}', re.IGNORECASE)
    return pattern.sub(new_link, text)

def modify_reply_markup(markup, new_link):
    if not markup:
        return None
    new_keyboard = []
    for row in markup.inline_keyboard:
        new_row = []
        for btn in row:
            url = btn.url
            if url:
                url = replace_all_old_links(url, new_link)
            new_row.append(InlineKeyboardButton(text=btn.text, url=url, callback_data=btn.callback_data))
        new_keyboard.append(new_row)
    return InlineKeyboardMarkup(new_keyboard)

async def auto_repost_with_custom_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if msg and msg.chat.id == SOURCE_CHANNEL_ID:
        print(f"New post detected in Source Channel! Processing destinations...")
        
        original_html = msg.text_html or msg.caption_html or ""

        for config in DESTINATION_CONFIG:
            chat_id = config["chat_id"]
            custom_link = config["new_link"]
            
            modified_text = replace_all_old_links(original_html, custom_link)
            modified_markup = modify_reply_markup(msg.reply_markup, custom_link)

            try:
                if msg.photo:
                    await context.bot.send_photo(chat_id=chat_id, photo=msg.photo[-1].file_id, caption=modified_text, parse_mode='HTML', reply_markup=modified_markup)
                elif msg.video:
                    await context.bot.send_video(chat_id=chat_id, video=msg.video.file_id, caption=modified_text, parse_mode='HTML', reply_markup=modified_markup)
                else:
                    await context.bot.send_message(chat_id=chat_id, text=modified_text, parse_mode='HTML', reply_markup=modified_markup)
                print(f"SUCCESS: Successfully posted to chat_id: {chat_id}")
            except Exception as e:
                print(f"ERROR: Failed to post in chat_id {chat_id} -> {e}")

def main():
    if not TOKEN:
        return
    threading.Thread(target=run_flask, daemon=True).start()
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.Chat(SOURCE_CHANNEL_ID), auto_repost_with_custom_links))
    bot_app.run_polling()

if __name__ == "__main__":
    main()
    
