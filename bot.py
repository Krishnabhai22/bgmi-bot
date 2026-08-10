import telebot
from telebot import types

# ⚠️ APNA NAYA VALA TOKEN ISS INVERTED COMMAS ("") KE ANDAR PASTE KARO
TOKEN = "8988242451:AAGEX7EHM1E6pIIUexJ-KW7ERylio7Ni4Tw"


bot = telebot.TeleBot(TOKEN)

# 1. /start Command ka code (Welcome Screen)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    
    welcome_text = (
        f"🎉 **Welcome to qriishnabot | BGMI Mod Zone** 🎉\n\n"
        f"Hey **{user_name}**, aapka swagat hai premium BGMI files network par! "
        f"Yahan aapko **BGMI 4.5 Update** ke saare latest aur updated configs milenge.\n\n"
        f"⚡ **Current Active Features:**\n"
        f"🎯 **Aimbot** — 100% Headshot Lock (Less Recoil)\n"
        f"🔮 **Magic Bullet** — Bullet Tracking Enabled (High Damage)\n"
        f"👀 **ESP Hack** — Wallhack, Enemy Location & Distance\n"
        f"📦 **All-in-One Combo** — Full features in a single file\n\n"
        f"🛠️ **Files Kaise Download Karein?**\n"
        f"Niche diye gaye button par click karein ya fir chat mein direct `/hacks` type karein.\n\n"
        f"⚠️ *Important Note: Safety ke liye pehle Guest account par try karein!*"
    )
    
    # Inline Buttons Settings
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📄 Get BGMI Hacks", callback_data="get_hacks")
    markup.add(btn1)
    
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=markup)

# 2. /hacks Command aur button click ka code
@bot.message_handler(commands=['hacks'])
def send_hacks(message):
    hacks_text = (
        "📥 **BGMI 4.5 Update - Download Links** 📥\n\n"
        "Niche diye gaye links se apni files download karein:\n\n"
        "🎯 [Download Aimbot File](https://t.me)\n"
        "🔮 [Download Magic Bullet](https://t.me)\n"
        "👀 [Download ESP Hack](https://t.me)\n"
        "📦 [Download All-in-One Combo](https://t.me)\n\n"
        "*(Note: 'your_channel_link' ki jagah aap apna Telegram channel link badal sakte hain)*"
    )
    bot.reply_to(message, hacks_text, parse_mode="Markdown", disable_web_page_preview=True)

# Button click listener
@bot.callback_query_handler(func=lambda call: call.data == "get_hacks")
def callback_hacks(call):
    send_hacks(call.message)

print("🚀 Aapka BGMI Bot successfully chalu ho gaya hai...")
bot.infinity_polling()
