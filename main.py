import os
import asyncio
import threading
from flask import Flask
from telegram import Update, InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running live on Render Web Service!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

TOKEN = os.getenv("BOT_TOKEN")

# মেইন চ্যানেল আইডি
SOURCE_CHANNEL_ID = -1001868030606

# মেইন চ্যানেলের পোস্টে থাকা অরিজিনাল অ্যাডমিন লিংক (যা রিপ্লেস হবে)
TARGET_OLD_LINK = "https://t.me/BigBagSmartMoney"

# টার্গেট চ্যানেল এবং সেগুলোর কাস্টম অ্যাডমিন লিংক (নতুন চ্যানেলসহ মোট ৪টি টার্গেট চ্যানেল)
DESTINATION_CONFIG = [
    {
        "group_id": -1002395561078,  # Channel 2
        "new_link": "https://t.me/ForexGlobal_support"
    },
    {
        "group_id": -1003310252089,  # Channel 3
        "new_link": "https://t.me/KhalidAl_Ameen"
    },
    {
        "group_id": -1003028410733,  # Channel 4
        "new_link": "https://t.me/ForexGlobal_support"
    },
    {
        "group_id": -1002749561168,  # নতুন চ্যানেল Global Link (আইডি ভিন্ন হলে সেটি বসাবেন)
        "new_link": "https://t.me/ForexGlobal_support"
    }
]

media_groups_cache = {}

# ইনলাইন বাটনের লিংক পরিবর্তনের লজিক
def modify_reply_markup(markup, old_link, new_link):
    if not markup:
        return None
    new_keyboard = []
    for row in markup.inline_keyboard:
        new_row = []
        for btn in row:
            url = btn.url
            if url and old_link in url:
                url = url.replace(old_link, new_link)
            new_row.append(InlineKeyboardButton(text=btn.text, url=url, callback_data=btn.callback_data))
        new_keyboard.append(new_row)
    return InlineKeyboardMarkup(new_keyboard)

# অ্যালবামের সব ছবি/ভিডিও একসাথে ৩ সেকেন্ড পর রিপোস্ট করার লজিক
async def process_media_group(mg_id, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(3)  # অ্যালবামের সব ছবি আসা পর্যন্ত ৩ সেকেন্ড অপেক্ষা
    messages = media_groups_cache.pop(mg_id, [])
    if not messages:
        return

    messages.sort(key=lambda x: x.message_id)

    for config in DESTINATION_CONFIG:
        group_id = config["group_id"]
        custom_link = config["new_link"]
        
        media_list = []
        for i, msg in enumerate(messages):
            caption_text = ""
            if i == 0:  # শুধু প্রথম ছবিতে ক্যাপশন থাকবে
                orig_html = msg.caption_html or ""
                caption_text = orig_html.replace(TARGET_OLD_LINK, custom_link)

            if msg.photo:
                media_list.append(InputMediaPhoto(media=msg.photo[-1].file_id, caption=caption_text, parse_mode='HTML'))
            elif msg.video:
                media_list.append(InputMediaVideo(media=msg.video.file_id, caption=caption_text, parse_mode='HTML'))

        try:
            if media_list:
                await context.bot.send_media_group(chat_id=group_id, media=media_list)
        except Exception as e:
            print(f"Failed to post album in {group_id}: {e}")

async def auto_repost_with_custom_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if msg and msg.chat.id == SOURCE_CHANNEL_ID:
        
        # একাধিক মিডিয়া (অ্যালবাম) হলে
        if msg.media_group_id:
            mg_id = msg.media_group_id
            if mg_id not in media_groups_cache:
                media_groups_cache[mg_id] = []
                asyncio.create_task(process_media_group(mg_id, context))
            media_groups_cache[mg_id].append(msg)
            return

        # একক টেক্সট বা সিঙ্গেল ছবি/ভিডিও হলে
        original_html = msg.text_html or msg.caption_html or ""

        for config in DESTINATION_CONFIG:
            group_id = config["group_id"]
            custom_link = config["new_link"]
            
            modified_text = original_html.replace(TARGET_OLD_LINK, custom_link)
            modified_markup = modify_reply_markup(msg.reply_markup, TARGET_OLD_LINK, custom_link)

            try:
                if msg.photo:
                    await context.bot.send_photo(chat_id=group_id, photo=msg.photo[-1].file_id, caption=modified_text, parse_mode='HTML', reply_markup=modified_markup)
                elif msg.video:
                    await context.bot.send_video(chat_id=group_id, video=msg.video.file_id, caption=modified_text, parse_mode='HTML', reply_markup=modified_markup)
                else:
                    await context.bot.send_message(chat_id=group_id, text=modified_text, parse_mode='HTML', reply_markup=modified_markup)
            except Exception as e:
                print(f"Failed to post in {group_id}: {e}")

def main():
    if not TOKEN:
        print("BOT_TOKEN missing!")
        return
    threading.Thread(target=run_flask, daemon=True).start()
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.Chat(SOURCE_CHANNEL_ID), auto_repost_with_custom_links))
    print("Auto-Repost Bot updated and running...")
    bot_app.run_polling()

if __name__ == "__main__":
    main()
