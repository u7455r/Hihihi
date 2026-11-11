import os
import threading
import base64
import requests
import telebot
import urllib.parse
from flask import Flask

# --- ওয়েব সার্ভার কনফিগারেশন (২৪/৭ চালু রাখার জন্য) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "AI All-in-One & Group Helper Bot is running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- ক্রেডেনশিয়াল ও মডেল কনফিগারেশন ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8963227766:AAECckt18OkY3qbgTmU9YnJLFZ3nQHbVz-k")
GEMINI_KEY = os.environ.get("GEMINI_KEY", "AQ.Ab8RN6LSPbJbrfNFcbEqDpgpRHhYcakVJBUhIZulyba59GeXnw")
ACTIVE_MODEL = "gemini-2.5-flash"

bot = telebot.TeleBot(BOT_TOKEN)

# --- জেমিনি এআই লজিক ---
def ask_gemini(user_prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{ACTIVE_MODEL}:generateContent?key={GEMINI_KEY}"
    headers = {"Content-Type": "application/json"}
    
    system_prompt = (
        "তুমি একজন অত্যন্ত পারদর্শী, অভিজ্ঞ এবং অমায়িক এআই সহকারী। "
        "ইউজারের সাথে নিখুঁত ও সাবলীল বাংলায় কথা বলবে। "
        "পোস্ট রাইটিং, কনটেন্ট তৈরি, সমস্যা সমাধান, কোডিং বা তথ্য জানানোর ক্ষেত্রে প্রফেশনাল উত্তর দেবে।"
    )
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_prompt}\n\nইউজারের প্রশ্ন: {user_prompt}"}
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
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_image
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        return f"⚠️ ছবি প্রসেসিং এরর (কোড: {res.status_code})"
    except Exception as e:
        return f"⚠️ এরর: {e}"

# --- বট কমান্ডস ও হ্যান্ডলার্স ---

# /start কমান্ড
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 স্বাগতম! আমি আপনার অল-ইন-ওয়ান এআই সহকারী ও গ্রুপ ম্যানেজার বট।\n\n"
        "✨ **মূল সুবিধাসমূহ:**\n"
        "১. বাংলায় যেকোনো বিষয়ে প্রশ্ন ও চ্যাট\n"
        "২. টেলিগ্রাম/ফেসবুক পোস্ট, ক্যাপশন ও আর্টিকেল তৈরি\n"
        "৩. ছবি বিশ্লেষণ (যেকোনো ছবি সেন্ড করুন)\n"
        "৪. এআই ছবি তৈরি: `/image আপনার প্রম্পট`\n"
        "৫. গ্রুপের স্প্যাম প্রোটেকশন ও মেম্বার ওয়েলকাম\n\n"
        "🛡️ **গ্রুপ অ্যাডমিন কমান্ড:** `/ban` বা `/mute` (মেসেজে রিপ্লাই দিয়ে লিখুন)"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# ছবি জেনারেটর (/image বা /draw)
@bot.message_handler(commands=['image', 'draw'])
def make_ai_image(message):
    prompt = message.text.replace("/image", "").replace("/draw", "").strip()
    if not prompt:
        bot.reply_to(message, "⚠️ অনুগ্রহ করে ছবির বিবরণ দিন। যেমন:\n`/image A realistic lion in neon forest`", parse_mode="Markdown")
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

# গ্রুপে নতুন সদস্য যুক্ত হলে ওয়েলকাম মেসেজ
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for member in message.new_chat_members:
        if member.id != bot.get_me().id:
            welcome_msg = f"👋 স্বাগতম {member.first_name}! আমাদের গ্রুপে আপনাকে স্বাগতম। গ্রুপের নিয়ম মেনে চলুন।"
            bot.send_message(message.chat.id, welcome_msg)

# অ্যাডমিন মডারেশন: /ban (মেসেজে রিপ্লাই দিয়ে ব্যবহার করতে হয়)
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.chat.type in ['group', 'supergroup']:
        sender_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
        if sender_status in ['administrator', 'creator']:
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
                try:
                    bot.ban_chat_member(message.chat.id, target_user.id)
                    bot.reply_to(message, f"🚫 {target_user.first_name}-কে গ্রুপ থেকে ব্যান করা হয়েছে।")
                except Exception as e:
                    bot.reply_to(message, f"ব্যান করা সম্ভব হয়নি: {e}")
            else:
                bot.reply_to(message, "যাকে ব্যান করবেন তার মেসেজে রিপ্লাই দিয়ে `/ban` লিখুন।")
        else:
            bot.reply_to(message, "⚠️ শুধুমাত্র গ্রুপ অ্যাডমিনরা এই কমান্ড ব্যবহার করতে পারবেন।")

# ছবি পেলে বিশ্লেষণ করা
@bot.message_handler(content_types=['photo'])
def handle_incoming_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    status = bot.reply_to(message, "🔍 ছবিটি দেখছি এবং বুঝছি...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        caption = message.caption if message.caption else "এই ছবিটি বিশ্লেষণ করে বাংলায় বিস্তারিত তথ্য বলো।"
        reply = analyze_gemini_image(downloaded_file, caption)
        bot.edit_message_text(reply, chat_id=message.chat.id, message_id=status.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ বিশ্লেষণ ব্যর্থ হয়েছে: {e}", chat_id=message.chat.id, message_id=status.message_id)

# গ্রুপ ও প্রাইভেট চ্যাটে সাধারণ মেসেজ হ্যান্ডলার
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # গ্রুপে অনুমতিহীন টেলিগ্রাম লিংক বা লিংক পাঠানো ব্লক/সতর্ক করা
    if message.chat.type in ['group', 'supergroup']:
        text_lower = message.text.lower()
        if "t.me/" in text_lower or "http://" in text_lower or "https://" in text_lower:
            sender_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
            if sender_status not in ['administrator', 'creator']:
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                    bot.send_message(message.chat.id, f"⚠️ @{message.from_user.username or message.from_user.first_name}, গ্রুপে লিংক শেয়ার করা নিষিদ্ধ!")
                    return
                except Exception:
                    pass

    # গ্রুপে বটকে মেনশন করলে বা প্রাইভেট চ্যাটে প্রশ্ন করলে উত্তর দেবে
    is_private = message.chat.type == 'private'
    bot_username = bot.get_me().username
    is_mentioned = bot_username and (f"@{bot_username}" in message.text)
    
    if is_private or is_mentioned:
        clean_text = message.text.replace(f"@{bot_username}", "").strip() if bot_username else message.text
        if clean_text:
            bot.send_chat_action(message.chat.id, 'typing')
            ai_response = ask_gemini(clean_text)
            bot.reply_to(message, ai_response)

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ড ওয়েব সার্ভার চালু
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    
    print("✅ All-in-One Bot & Group Helper is now Online!")
    bot.infinity_polling()
