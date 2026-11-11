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
    return "Gemini AI Core is running online 24/7!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# --- কনফিগারেশন ও নতুন সঠিক API Keys ---
BOT_TOKEN = "8963227766:AAFzvFGTJIOSAIUS_v4-sqx2bMNxpp40ujs"
GEMINI_KEY = "AIzaSyDZyPULj_rCgtn3Nz2h-CbmE5qQ4JszrF0"
ACTIVE_MODEL = "gemini-2.5-flash"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# প্রতিটি ইউজারের চ্যাট স্মৃতি (Conversation Memory)
user_memory = {}

# জেমিনি ফুল এআই ব্রেন (আমার মতো উত্তর ও কোডিং করার ইঞ্জিন)
def call_gemini(user_id, prompt_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={GEMINI_KEY}"
    headers = {"Content-Type": "application/json"}

    if user_id not in user_memory:
        user_memory[user_id] = []

    # ইউজার মেসেজ মেমোরিতে যুক্ত
    user_memory[user_id].append({
        "role": "user",
        "parts": [{"text": prompt_text}]
    })

    # মেমোরি অতিরিক্ত বড় হলে পুরনো ৫টি মেসেজ কেটে ফেলা (সর্বশেষ ১০টি রাখা)
    if len(user_memory[user_id]) > 10:
        user_memory[user_id] = user_memory[user_id][-10:]

    system_instruction = (
        "তুমি জেমিনি (Gemini)-এর মতো একজন অত্যন্ত বুদ্ধিমান, অমায়িক, স্পষ্টভাষী ও অল-ইন-ওয়ান সুপার এআই সহকারী। "
        "তুমি খাঁটি এবং সাবলীল বাংলায় কথা বলবে। তোমার দায়িত্ব হলো ইউজারকে কোডিং, সমস্যা সমাধান, ফেসবুক/টেলিগ্রাম পোস্ট তৈরি, "
        "যেকোনো টেকনিক্যাল বিষয়, অনুবাদ এবং নিখুঁত বাস্তবসম্মত তথ্য দিয়ে সাহায্য করা।"
    )

    # API পেলোড তৈরি
    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": user_memory[user_id]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=35)
        if res.status_code == 200:
            data = res.json()
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
            # বটের উত্তর মেমোরিতে সেভ রাখা
            user_memory[user_id].append({
                "role": "model",
                "parts": [{"text": reply}]
            })
            return reply
        else:
            return f"⚠️ সার্ভার এরর: {res.status_code}\nবিবরণ: {res.text}"
    except Exception as e:
        return f"⚠️ কানেকশন এরর: {e}"

# ছবি দেখে বোঝার ভিশন ইঞ্জিন
def analyze_image(image_bytes, caption):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={GEMINI_KEY}"
    headers = {"Content-Type": "application/json"}
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"এই ছবিটি নিখুঁতভাবে দেখে বাংলায় বিস্তারিত বুঝিয়ে বলো:\n{caption}"},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64_image}}
                ]
            }
        ]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=40)
        if res.status_code == 200:
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        return f"⚠️ ইমেজ প্রসেসিং এরর: {res.status_code}"
    except Exception as e:
        return f"⚠️ বিশ্লেষণ এরর: {e}"

# --- টেলিগ্রাম হ্যান্ডলারস ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "👋 **হ্যালো! আমি আপনার অল-ইন-ওয়ান জেমিনি সুপার এআই বট।**\n\n"
        "✨ **আমি কী কী করতে পারি:**\n"
        "• সাবলীল বাংলায় মানুষের মতো কথা বলা ও স্মৃতি ধরে রাখা\n"
        "• নিখুঁত প্রোগ্রামিং কোড লেখা, সমাধান ও বাগ ফিক্স\n"
        "• যেকোনো ফেসবুক/টেলিগ্রাম চ্যানেলের ভাইরাল পোস্ট ও কনটেন্ট রাইটিং\n"
        "• ছবি পাঠালে তার পুরো বিশ্লেষণ ও টেক্সট পড়া\n"
        "• নতুন এআই ছবি তৈরি: `/image আপনার প্রম্পট`\n"
        "• স্মৃতি রিসেট করতে: `/clear`\n\n"
        "আমাকে যেকোনো প্রশ্ন লিখে পাঠিয়ে দিন!"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['clear', 'reset'])
def reset_chat_memory(message):
    user_memory.pop(message.from_user.id, None)
    bot.reply_to(message, "🧹 আপনার সাথে পূর্বের চ্যাট মেমোরি রিসেট করা হয়েছে!")

@bot.message_handler(commands=['image', 'draw'])
def generate_ai_image(message):
    prompt = message.text.replace("/image", "").replace("/draw", "").strip()
    if not prompt:
        bot.reply_to(message, "⚠️ ছবির বিবরণ দিন। যেমন:\n`/image A realistic sports car in cyberpunk city`")
        return

    bot.send_chat_action(message.chat.id, 'upload_photo')
    status = bot.reply_to(message, "🎨 ছবিটি তৈরি করা হচ্ছে, কিছুক্ষণ অপেক্ষা করুন...")
    
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    try:
        bot.send_photo(message.chat.id, image_url, caption=f"🖼️ **প্রম্পট:** {prompt}", parse_mode="Markdown")
        bot.delete_message(message.chat.id, status.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ ছবি পাঠানো যায়নি: {e}", chat_id=message.chat.id, message_id=status.message_id)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        caption = message.caption if message.caption else "এই ছবিতে কী আছে বাংলায় বিস্তারিত বিশ্লেষণ করো।"
        reply = analyze_image(downloaded, caption)
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"⚠️ এরর: {e}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
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
    response = call_gemini(message.from_user.id, user_text)
    
    # টেলিগ্রাম ৪০০০ ক্যারেক্টার মেসেজ লিমিট হ্যান্ডেল করা
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
    # ব্যাকগ্রাউন্ডে টেলিগ্রাম পোলিং চালু
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Render-এর জন্য ওয়েব সার্ভার চালু রাখা
    run_flask()
