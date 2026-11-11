import os
import threading
import base64
import requests
import telebot
import urllib.parse
from flask import Flask

# --- Flask ওয়েব সার্ভার (রেন্ডারের জন্য) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running online 24/7!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# --- কনফিগারেশন ও নতুন টোকেন ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8963227766:AAECckt18OkY3qbgTmU9YnJLFZ3nQHbVz-k")
GEMINI_KEY = os.environ.get("GEMINI_KEY", "AQ.Ab8RN6LSPbJbrfNFcbEqDpgpRHhYcakVJBUhIZulyba59GeXnw")
ACTIVE_MODEL = "gemini-2.5-flash"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# --- এআই লজিক ---
def ask_gemini(user_prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={GEMINI_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "তুমি একজন অমায়িক, অত্যন্ত বুদ্ধিমান এআই সহকারী। "
                            "ইউজারের সাথে সাবলীল বাংলায় কথা বলবে। যেকোনো লেখা, পোস্ট, ক্যাপশন "
                            "বা প্রশ্নের উত্তর আকর্ষণীয় ও সহজ ভাষায় বুঝিয়ে দেবে।\n\n"
                            f"ব্যবহারকারীর প্রশ্ন: {user_prompt}"
                        )
                    }
                ]
            }
        ]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        if res.status_code == 200:
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        return f"⚠️ এআই সার্ভার রেসপন্স দেয়নি (কোড: {res.status_code})"
    except Exception as e:
        return f"⚠️ কানেকশন এরর: {e}"

def analyze_gemini_image(image_bytes, caption):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={GEMINI_KEY}"
    headers = {"Content-Type": "application/json"}
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": caption},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64_image}}
                ]
            }
        ]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        return f"⚠️ ছবি প্রসেসিং এরর: {res.status_code}"
    except Exception as e:
        return f"⚠️ এরর: {e}"

# --- বট হ্যান্ডলারস ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "👋 স্বাগতম! আমি আপনার অল-ইন-ওয়ান সুপার এআই সহকারী ও গ্রুপ হেল্পার।\n\n"
        "✨ সুবিধা:\n"
        "• বাংলায় চ্যাট ও যেকোনো প্রশ্নের নিখুঁত উত্তর\n"
        "• চ্যানেলের পোস্ট ও আর্টিকেল তৈরি\n"
        "• ছবি বিশ্লেষণ (যেকোনো ফটো পাঠালে)\n"
        "• এআই ছবি তৈরি (`/image আপনার প্রম্পট`)\n"
        "• গ্রুপ মডারেশন ও স্প্যাম প্রোটেকশন"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['image', 'draw'])
def make_ai_image(message):
    prompt = message.text.replace("/image", "").replace("/draw", "").strip()
    if not prompt:
        bot.reply_to(message, "অনুগ্রহ করে ছবির বিবরণ দিন। যেমন:\n`/image A realistic sports car`")
        return

    bot.send_chat_action(message.chat.id, 'upload_photo')
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    try:
        bot.send_photo(message.chat.id, image_url, caption=f"🖼️ প্রম্পট: {prompt}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ ছবি পাঠানো যায়নি: {e}")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for member in message.new_chat_members:
        if member.id != bot.get_me().id:
            bot.send_message(message.chat.id, f"👋 স্বাগতম {member.first_name}! আমাদের গ্রুপে নিয়ম মেনে চলুন।")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.chat.type in ['group', 'supergroup']:
        status = bot.get_chat_member(message.chat.id, message.from_user.id).status
        if status in ['administrator', 'creator'] and message.reply_to_message:
            target = message.reply_to_message.from_user
            bot.ban_chat_member(message.chat.id, target.id)
            bot.reply_to(message, f"🚫 {target.first_name}-কে গ্রুপ থেকে ব্যান করা হয়েছে।")

@bot.message_handler(content_types=['photo'])
def handle_incoming_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        caption = message.caption if message.caption else "এই ছবিটি দেখে বাংলায় বিস্তারিত বলো।"
        reply = analyze_gemini_image(downloaded_file, caption)
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"⚠️ এরর: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.chat.type in ['group', 'supergroup']:
        text_lower = message.text.lower()
        if "t.me/" in text_lower or "http://" in text_lower or "https://" in text_lower:
            sender_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
            if sender_status not in ['administrator', 'creator']:
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                    bot.send_message(message.chat.id, f"⚠️ @{message.from_user.username or message.from_user.first_name}, গ্রুপে লিংক দেওয়া নিষিদ্ধ!")
                    return
                except Exception:
                    pass

    is_private = message.chat.type == 'private'
    bot_user = bot.get_me().username
    is_mentioned = bot_user and (f"@{bot_user}" in message.text)
    
    if is_private or is_mentioned:
        clean_text = message.text.replace(f"@{bot_user}", "").strip() if bot_user else message.text
        if clean_text:
            bot.send_chat_action(message.chat.id, 'typing')
            res = ask_gemini(clean_text)
            bot.reply_to(message, res)

def start_bot():
    print("Telegram Polling started...")
    try:
        bot.remove_webhook()
    except Exception:
        pass
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    run_flask()
