import os
import threading
import base64
import requests
import telebot
import urllib.parse
from flask import Flask

# --- Flask ওয়েব সার্ভার (Render 24/7 চালু রাখার জন্য) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Gemini AI Core is running 24/7!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# --- কনফিগারেশন ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8963227766:AAEj9GTmOLPM3eu2fTAmo8LgD8am520Zknk")
GEMINI_KEY = os.environ.get("GEMINI_KEY", "AQ.Ab8RN6LSPbJbrfNFcbEqDpgpRHhYcakVJBUhIZulyba59GeXnw")
ACTIVE_MODEL = "gemini-2.5-flash"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# প্রতিটি ইউজারের চ্যাট হিস্ট্রি মনে রাখার মেমোরি
user_conversations = {}

# জেমিনি প্রম্পট ইঞ্জিন
def ask_gemini_with_history(user_id, user_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={GEMINI_KEY}"
    headers = {"Content-Type": "application/json"}

    if user_id not in user_conversations:
        user_conversations[user_id] = []

    user_conversations[user_id].append({
        "role": "user",
        "parts": [{"text": user_text}]
    })

    # সর্বশেষ ১০টি বার্তা মেমোরিতে রাখা
    if len(user_conversations[user_id]) > 10:
        user_conversations[user_id] = user_conversations[user_id][-10:]

    system_instruction = {
        "role": "user",
        "parts": [{
            "text": (
                "তুমি জেমিনি (Gemini)-এর মতো একজন অত্যন্ত বুদ্ধিমান, অমায়িক, স্পষ্টভাষী ও পারদর্শী ফুল এআই সহকারী। "
                "তুমি খাঁটি এবং সাবলীল বাংলায় কথা বলবে। তোমার দায়িত্ব হলো ইউজারকে কোডিং, সমস্যা সমাধান, ফেসবুক/টেলিগ্রাম পোস্ট তৈরি, "
                "যেকোনো বিশ্লেষণ, অনুবাদ এবং মানবিক আড্ডায় শতভাগ নিখুঁত ও বাস্তবিক উত্তর দিয়ে সাহায্য করা।"
            )
        }]
    }

    full_contents = [system_instruction] + user_conversations[user_id]
    payload = {"contents": full_contents}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            data = res.json()
            model_reply = data["candidates"][0]["content"]["parts"][0]["text"]
            user_conversations[user_id].append({
                "role": "model",
                "parts": [{"text": model_reply}]
            })
            return model_reply
        else:
            return f"⚠️ সার্ভার এরর ({res.status_code}): কিছুক্ষণ পর আবার চেষ্টা করুন।"
    except Exception as e:
        return f"⚠️ কানেকশন এরর: {e}"

# ছবি দেখে বোঝার ভিশন ইঞ্জিন
def analyze_gemini_image(image_bytes, caption):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={GEMINI_KEY}"
    headers = {"Content-Type": "application/json"}
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"তুমি একজন বিশেষজ্ঞ এআই। এই ছবিটি নিখুঁতভাবে পর্যবেক্ষণ করে নিচের প্রশ্নের উত্তর বাংলায় দাও:\n{caption}"},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64_image}}
                ]
            }
        ]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=35)
        if res.status_code == 200:
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        return f"⚠️ ইমেজ প্রসেসিং এরর: {res.status_code}"
    except Exception as e:
        return f"⚠️ বিশ্লেষণ এরর: {e}"

# --- বট হ্যান্ডলারস ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "👋 **হ্যালো! আমি আপনার অল-ইন-ওয়ান সুপার এআই সহকারী।**\n\n"
        "💡 **আমি কী কী করতে পারি:**\n"
        "• মানুষের মতো বাংলায় সাবলীল কথোপকথন ও আগের কথা মনে রাখা\n"
        "• জটিল প্রোগ্রামিং কোড লেখা, সমাধান ও বাগ ফিক্সিং\n"
        "• ফেসবুক/টেলিগ্রাম চ্যানেলের প্রফেশনাল পোস্ট তৈরি\n"
        "• ফটো পাঠালে তার সম্পূর্ণ বিশ্লেষণ\n"
        "• এআই ছবি তৈরি: `/image আপনার প্রম্পট`\n"
        "• স্মৃতি মুছতে: `/clear` লিখুন\n\n"
        "যেকোনো প্রশ্ন লিখে এখনই পাঠিয়ে দিন!"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['clear', 'reset'])
def reset_memory(message):
    user_conversations.pop(message.from_user.id, None)
    bot.reply_to(message, "🧹 আপনার সাথে পূর্বের চ্যাট হিস্ট্রি ক্লিয়ার করা হয়েছে। নতুন বিষয় নিয়ে কথা বলতে পারেন!")

@bot.message_handler(commands=['image', 'draw'])
def make_ai_image(message):
    prompt = message.text.replace("/image", "").replace("/draw", "").strip()
    if not prompt:
        bot.reply_to(message, "⚠️ ছবির বর্ণনা দিন। যেমন:\n`/image A cinematic sports car in neon street`")
        return

    bot.send_chat_action(message.chat.id, 'upload_photo')
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    try:
        bot.send_photo(message.chat.id, image_url, caption=f"🖼️ **প্রম্পট:** {prompt}", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"⚠️ ছবি পাঠানো যায়নি: {e}")

@bot.message_handler(content_types=['photo'])
def handle_incoming_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        caption = message.caption if message.caption else "এই ছবিতে কী কী আছে এবং এর মূল বিষয়বস্তু বাংলায় বিস্তারিত বিশ্লেষণ করো।"
        reply = analyze_gemini_image(downloaded_file, caption)
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"⚠️ এরর: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_chat(message):
    if message.chat.type in ['group', 'supergroup']:
        bot_user = bot.get_me().username
        if not (bot_user and f"@{bot_user}" in message.text):
            return
        user_text = message.text.replace(f"@{bot_user}", "").strip()
    else:
        user_text = message.text.strip()

    if not user_text:
        return

    bot.send_chat_action(message.chat.id, 'typing')
    response = ask_gemini_with_history(message.from_user.id, user_text)
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            bot.reply_to(message, response[i:i+4000])
    else:
        bot.reply_to(message, response)

def start_bot():
    print("Telegram Bot Polling started...")
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
