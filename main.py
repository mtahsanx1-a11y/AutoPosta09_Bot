import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = os.getenv("BOT_TOKEN")

# ১. মেইন চ্যানেল এবং ৩টি টার্গেট চ্যানেলের কনফিগার করা ID
SOURCE_CHANNEL_ID = -1001868030606  # মেইন চ্যানেল

# ২. মেইন চ্যানেলের পোস্টে থাকা অরিজিনাল অ্যাডমিন লিংক
TARGET_OLD_LINK = "https://t.me/BigBagSmartMoney"

# ৩. ৩টি চ্যানেল এবং সেগুলোর কাস্টম অ্যাডমিন লিংক
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
    }
]

async def auto_repost_with_custom_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # শুধু নির্দিষ্ট মেইন চ্যানেলের পোস্ট প্রসেস করবে
    if update.channel_post and update.channel_post.chat.id == SOURCE_CHANNEL_ID:
        
        original_text = update.channel_post.text or update.channel_post.caption or ""

        # ৩টি চ্যানেলে আলাদা আলাদা কাস্টম লিংক সহ রিপোস্ট
        for config in DESTINATION_CONFIG:
            group_id = config["group_id"]
            custom_link = config["new_link"]

            # অরিজিনাল অ্যাডমিন লিংক পরিবর্তন
            modified_text = original_text.replace(TARGET_OLD_LINK, custom_link)

            try:
                # ছবিসহ মেসেজ
                if update.channel_post.photo:
                    photo_id = update.channel_post.photo[-1].file_id
                    await context.bot.send_photo(chat_id=group_id, photo=photo_id, caption=modified_text)
                # ভিডিওসহ মেসেজ
                elif update.channel_post.video:
                    video_id = update.channel_post.video.file_id
                    await context.bot.send_video(chat_id=group_id, video=video_id, caption=modified_text)
                # সাধারণ টেক্সট মেসেজ
                else:
                    await context.bot.send_message(chat_id=group_id, text=modified_text)
                    
                print(f"Successfully reposted to channel: {group_id}")
            except Exception as e:
                print(f"Failed to post in {group_id}: {e}")

def main():
    if not TOKEN:
        print("BOT_TOKEN missing!")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Chat(SOURCE_CHANNEL_ID), auto_repost_with_custom_links))

    print("Auto-Repost Bot is running smoothly...")
    app.run_polling()

if __name__ == "__main__":
    main()
      
