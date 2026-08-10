import telebot
from telebot import types
import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = "8988242451:AAGEX7EHM1E6pIlUexJ-KW7ERylio7Ni4Tw"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"🎉 **Welcome to qriishnabot | BGMI Mod Zone** 🎉\n\n"
        f"Hey **{user_name}**, aapka swagat hai premium BGMI files network par!\n\n"
        f"⚡ **Active Features:**\n"
        f"🎯 **Aimbot** — 100% Headshot Lock\n"
        f"🔮 **Magic Bullet** — High Damage\n"
        f"👀 **ESP Hack** — Wallhack & Location\n\n"
        f"🛠️ Files download karne ke liye niche button par click karein."
    )
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📄 Get BGMI Hacks", callback_data="get_hacks")
    markup.add(btn1)
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['hacks'])
def send_hacks(message):
    hacks_text = (
        "📥 **BGMI 4.5 Update - Download Links** 📥\n\n"
        "🎯 [Download Aimbot File](https://t.me)\n"
        "🔮 [Download Magic Bullet](https://t.me)\n"
        "👀 [Download ESP Hack](https://t.me)"
    )
    bot.reply_to(message, hacks_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: call.data == "get_hacks")
def callback_hacks(call):
    send_hacks(call.message)

if __name__ == "__main__":
    keep_alive()
    print("🚀 Aapka BGMI Bot successfully chalu ho gaya hai...")
    bot.infinity_polling(timeout=60)
    
