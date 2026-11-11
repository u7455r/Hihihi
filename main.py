import os
import threading
import requests
import telebot
import urllib.parse
from flask import Flask

# --- Flask ওয়েব সার্ভার (Render ২৪/৭ চালু রাখার জন্য) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "OpenRouter AI Bot is running online 24/7!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# --- কনফিগারেশন ---
BOT_TOKEN = "8963227766:AAF629TGOWqmujbsr-AA69sm6sz_cpB0jW4"
OPENROUTER_KEY = "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"

# OpenRouter এর সম্পূর্ণ ফ্রি সুপারফাস্ট মডেল
MODEL_NAME = "google/gemini-2.0-flash-exp:free"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# প্রতিটি ইউজারের চ্যাট স্মৃতি (Conversation Memory)
user_memory = {}

# OpenRouter এআই ইঞ্জিন
def ask_ai(user_id, prompt_text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://render.com",
        "X-Title": "Telegram AI Assistant"
    }

    if user_id not in user_memory:
        user_memory[user_id] = [
            {
                "role": "system",
                "content": (
                    "তুমি অত্যন্ত বুদ্ধিমান, অমায়িক এবং পারদর্শী অল-ইন-ওয়ান সুপার এআই সহকারী। "
                    "তুমি খাঁটি এবং সাবলীল বাংলায় কথা বলবে। ইউজারের যেকোনো প্রশ্ন, প্রোগ্রামিং কোড, "
                    "চ্যানেল পোস্ট রাইটিং, অংক এবং সমস্যা সমাধানের নিখুঁত ও বাস্তবসম্মত উত্তর দেবে।"
                )
            }
        ]

    user_memory[user_id].append({"role": "user", "content": prompt_text})

    # চ্যাট হিস্ট্রি বড় হলে পুরনো মেসেজ ছেঁটে ফেলা
    if len(user_memory[user_id]) > 10:
        user_memory[user_id] = [user_memory[user_id][0]] + user_memory[user_id][-9:]

    payload = {
        "model": MODEL_NAME,
        "messages": user_memory[user_id]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=35)
        if res.status_code == 200:
            data = res.json()
            reply = data["choices"][0]["message"]["content"]
            user_memory[user_id].append({"role": "assistant", "content": reply})
            return reply
        else:
            return f"⚠️ সার্ভার এরর: {res.status_code}\n{res.text}"
    except Exception as e:
        return f"⚠️ কানেকশন এরর: {e}"

# --- বট হ্যান্ডলারস ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "👋 **হ্যালো! আমি আপনার ফুল-পাওয়ারড এআই সহকারী।**\n\n"
        "💡 **আমার সুবিধাগুলো:**\n"
        "• সাবলীল বাংলায় মানুষের মতো চ্যাট ও প্রশ্ন সমাধান\n"
        "• নিখুঁত প্রোগ্রামিং কোড লেখা ও বাগ ফিক্সিং\n"
        "• প্রফেশনাল টেলিগ্রাম/ফেসবুক পোস্ট তৈরি\n"
        "• এআই ছবি তৈরি: `/image আপনার প্রম্পট`\n"
        "• স্মৃতি রিসেট করতে: `/clear` লিখুন\n\n"
        "যেকোনো প্রশ্ন লিখে এখনই পাঠিয়ে দিন!"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['clear', 'reset'])
def reset_chat_memory(message):
    user_memory.pop(message.from_user.id, None)
    bot.reply_to(message, "🧹 পূর্বের চ্যাট মেমোরি রিসেট করা হয়েছে!")

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
    response = ask_ai(message.from_user.id, user_text)

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
