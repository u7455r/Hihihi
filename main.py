import os
import threading
import base64
import requests
import telebot
import urllib.parse
from flask import Flask

# Flask ওয়েব সার্ভার (রেন্ডার সার্ভিস চালু রাখার জন্য)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running online 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# বট ও এপিআই কনফিগারেশন
BOT_TOKEN = "8963227766:AAEDuOSx77Y-V2D3ZmjdDl3SRT_yT8E6T6E"
GEMINI_KEY = "AQ.Ab8RN6JfgufMY5HKy1Tq_MalxIhJL_UWH5JXmzJTyv24S7zmnw"
ACTIVE_MODEL = "gemini-2.5-flash"

bot = telebot.TeleBot(BOT_TOKEN)

# জেমিনি চ্যাট ও পোস্ট রাইটিং
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
        return f"⚠️ এরর কোড: {res.status_code}"
    except Exception as e:
        return f"⚠️ কানেকশন এরর: {e}"

# ছবি দেখে বোঝার ভিশন মোড
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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 স্বাগতম! আমি আপনার অল-ইন-ওয়ান সুপার এআই সহকারী।\n\n"
        "✨ সুবিধা:\n"
        "• বাংলায় চ্যাট ও প্রশ্নের উত্তর\n"
        "• চ্যানেলের পোস্ট ও আর্টিকেল তৈরি\n"
        "• ছবি বিশ্লেষণ (যেকোনো ফটো পাঠালে)\n"
        "• এআই ছবি তৈরি (`/image আপনার প্রম্পট`)"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['image', 'draw'])
def make_ai_image(message):
    prompt = message.text.replace("/image", "").replace("/draw", "").strip()
    if not prompt:
        bot.reply_to(message, "অনুগ্রহ করে ছবির প্রম্পট দিন। যেমন:\n`/image A realistic sports car`", parse_mode="Markdown")
        return

    bot.send_chat_action(message.chat.id, 'upload_photo')
    status = bot.reply_to(message, "🎨 ছবিটি তৈরি হচ্ছে...")
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

    try:
        bot.send_photo(message.chat.id, image_url, caption=f"🖼️ প্রম্পট: {prompt}")
        bot.delete_message(message.chat.id, status.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ ছবি পাঠানো যায়নি: {e}", chat_id=message.chat.id, message_id=status.message_id)

@bot.message_handler(content_types=['photo'])
def handle_incoming_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    status = bot.reply_to(message, "🔍 ছবিটি বিশ্লেষণ করা হচ্ছে...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        caption = message.caption if message.caption else "এই ছবিটি দেখে বাংলায় বিস্তারিত বলো।"
        reply = analyze_gemini_image(downloaded_file, caption)
        bot.edit_message_text(reply, chat_id=message.chat.id, message_id=status.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ এরর: {e}", chat_id=message.chat.id, message_id=status.message_id)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    ai_response = ask_gemini(message.text)
    bot.reply_to(message, ai_response)

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে ওয়েব সার্ভার চালু রাখা
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    
    print("Bot is starting polling...")
    bot.infinity_polling()
