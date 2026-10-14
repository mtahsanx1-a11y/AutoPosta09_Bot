import os
import re
import asyncio
import threading
from flask import Flask
from telegram import Update, InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

app_web = Flask(__name__)

# Cron-job এবং UptimeRobot এর জন্য রুট পেজ
@app_web.route('/')
def home():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

TOKEN = os.getenv("BOT_TOKEN")

# মেইন চ্যানেল আইডি (যেখান থেকে পোস্ট নেওয়া হবে)
SOURCE_CHANNEL_ID = -1001868030606

# মেইন চ্যানেলের ইউজারনেম (লিংক বা ইউজারনেম বদলানোর জন্য)
OLD_USERNAME = "BigBagSmartMoney"

# আপনার ৪টি চ্যানেল এবং ১টি গ্রুপের সঠিক কনফিগারেশন তালিকা
DESTINATION_CONFIG = [
    {
        "chat_id": -1002395561078,  # চ্যানেল ১
        "new_link": "https://t.me/ForexGlobal_support"
    },
    {
        "chat_id": -1003310252089,  # চ্যানেল ২
        "new_link": "https://t.me/KhalidAl_Ameen"
    },
    {
        "chat_id": -1003028410733,  # চ্যানেল ৩
        "new_link": "https://t.me/ForexGlobal_support"
    },
    {
        "chat_id": -100239556107,   # চ্যানেল ৪
        "new_link": "https://t.me/ForexGlobal_support"
    },
    {
        "chat_id": -1003784053762,  # গ্রুপ (নতুন যুক্ত হওয়া ৫ম ডেস্টিনেশন)
        "new_link": "https://t.me/ForexGlobal_support"
    }
]

media_groups_cache = {}

# ডায়নামিক লিংক রিপ্লেসমেন্ট ফাংশন
def replace_all_old_links(text, new_link):
    if not text:
        return text
    pattern = re.compile(rf'(https?://)?(www\.)?t\.me/{OLD_USERNAME}(/\S*)?|@{OLD_USERNAME}', re.IGNORECASE)
    return pattern.sub(new_link, text)

# ইনলাইন বাটনের লিংক পরিবর্তন করার ফাংশন
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

# মিডিয়া অ্যালবামের জন্য হ্যান্ডেলার
async def process_media_group(mg_id, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(3)
    messages = media_groups_cache.pop(mg_id, [])
    if not messages:
        return

    messages.sort(key=lambda x: x.message_id)

    for config in DESTINATION_CONFIG:
        chat_id = config["chat_id"]
        custom_link = config["new_link"]
        
        media_list = []
        for i, msg in enumerate(messages):
            caption_text = ""
            if i ==0:
                orig_html = msg.caption_html or ""
                caption_text = replace_all_old_links(orig_html, custom_link)

            if msg.photo:
                media_list.append(InputMediaPhoto(media=msg.photo[-1].file_id, caption=caption_text, parse_mode='HTML'))
            elif msg.video:
                media_list.append(InputMediaVideo(media=msg.video.file_id, caption=caption_text, parse_mode='HTML'))

        try:
            if media_list:
                await context.bot.send_media_group(chat_id=chat_id, media=media_list)
        except Exception as e:
            print(f"Failed to post album in {chat_id}: {e}")

# মূল রিপোস্ট হ্যান্ডেলার ফাংশন
async def auto_repost_with_custom_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if msg and msg.chat.id == SOURCE_CHANNEL_ID:
        
        # যদি পোস্টটি অ্যালবাম (একাধিক ছবি/ভিডিও) হয়
        if msg.media_group_id:
            mg_id = msg.media_group_id
            if mg_id not in media_groups_cache:
                media_groups_cache[mg_id] = []
                asyncio.create_task(process_media_group(mg_id, context))
            media_groups_cache[mg_id].append(msg)
            return

        # সাধারণ টেক্সট, সিঙ্গেল ছবি বা ভিডিওর জন্য
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
            except Exception as e:
                print(f"Failed to post in {chat_id}: {e}")

def main():
    if not TOKEN:
        return
    threading.Thread(target=run_flask, daemon=True).start()
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.Chat(SOURCE_CHANNEL_ID), auto_repost_with_custom_links))
    bot_app.run_polling()

if __name__ == "__main__":
    main()
                                                   
