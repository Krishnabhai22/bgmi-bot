import os
import re
import sqlite3
import threading

import telebot
from telebot import types
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_LINK = "https://t.me"
BOT_NAME = "QRIISHNA"
BOT_VERSION = "1.0"
OWNER_IDS = {1332494807}

app = Flask(__name__)

@app.route("/")
def home():
    return "QRIISHNA • ONLINE"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DB_FILE = "warnings.db"
db_lock = threading.Lock()

def init_database():
    with db_lock:
        connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                warning_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        connection.commit()
        connection.close()

def get_warning_count(chat_id, user_id):
    with db_lock:
        connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = connection.cursor()
        cursor.execute("SELECT warning_count FROM warnings WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        result = cursor.fetchone()
        connection.close()
    return result[0] if result else 0

def add_warning(chat_id, user_id):
    with db_lock:
        connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO warnings (chat_id, user_id, warning_count)
            VALUES (?, ?, 1)
            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET warning_count = warning_count + 1
        """, (chat_id, user_id))
        connection.commit()
        cursor.execute("SELECT warning_count FROM warnings WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        result = cursor.fetchone()
        connection.close()
    return result[0] if result else 1

BAD_WORDS = [
    "loda", "lauda", "louda", "lawda", "lavda", "laude", "lode", "lodaa", "loudaa", "lawdaa",
    "chod", "chhod", "chud", "chut", "chutiya", "chutiye", "chutia", "chutiy", "chutiyaa",
    "madarchod", "madarchut", "madar chod", "madar ch0d", "mc",
    "bhenchod", "bhen chod", "behenchod", "behen chod", "bc",
    "gaand", "gand", "gandu", "randi", "rand", "randwa",
    "harami", "haraami", "haramkhor", "kamina", "kamine", "kaminey",
    "kutte", "kutta", "kutiya", "bhosdi", "bhosdike", "bhosdika", "bhosdiwala", "bhosdiwale",
    "jhatu", "jhaatu", "bakchod", "bakchodi", "chakka", "chakkar", "nalayak",
    "fuck", "fucking", "fucker", "motherfucker", "shit", "shitty", "bitch", "bastard", "asshole",
    "dick", "dickhead", "pussy", "cunt", "whore", "slut"
]
BAD_WORDS = sorted(set(BAD_WORDS), key=len, reverse=True)

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    replacements = {"@": "a", "4": "a", "0": "o", "1": "i", "!": "i", "$": "s", "3": "e", "5": "s"}
    for old, new in replacements.items(): text = text.replace(old, new)
    text = re.sub(r"[\u200b-\u200f\uFEFF]", "", text)
    text = re.sub(r"[^a-zA-Z\u0900-\u097F]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def contains_bad_language(text):
    normalized = normalize_text(text)
    if not normalized: return False
    for word in BAD_WORDS:
        if re.search(r"(?<![a-zA-Z])" + re.escape(word) + r"(?![a-zA-Z])", normalized): return True
    compact = re.sub(r"[^a-zA-Z\u0900-\u097F]", "", normalized)
    for word in BAD_WORDS:
        cw = re.sub(r"[^a-zA-Z\u0900-\u097F]", "", word)
        if len(cw) >= 4 and cw in compact: return True
    return False
def warning_text(user, warning_number):
    return f"<b>⚠️ COMMUNITY WARNING</b>\n\n👤 <b>User:</b> {user.first_name or 'User'}\n📌 <b>Reason:</b> Inappropriate language\n\n⚠️ <b>Warning:</b> {warning_number} / 3\n\n<i>Please maintain respectful language.</i>"

def banned_text(user):
    return f"<b>🚫 USER BANNED</b>\n\n👤 <b>User:</b> {user.first_name or 'User'}\n📌 <b>Reason:</b> 3 warnings reached\n\n<i>The user has been removed from this group.</i>"

def welcome_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("⌕  HELP", callback_data="help"), types.InlineKeyboardButton("ⓘ  ABOUT", callback_data="about"))
    return markup

def help_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("▣  INSTALLATION GUIDE", callback_data="guide"))
    markup.add(types.InlineKeyboardButton("ⓘ  ABOUT", callback_data="about"), types.InlineKeyboardButton("‹  BACK", callback_data="home"))
    return markup

def language_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🇬🇧  ENGLISH", callback_data="guide_en"), types.InlineKeyboardButton("🇮🇳  HINGLISH", callback_data="guide_hi"))
    markup.add(types.InlineKeyboardButton("‹  BACK", callback_data="help"))
    return markup

def access_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▣  OPEN PRIVATE ACCESS", url=CHANNEL_LINK), types.InlineKeyboardButton("‹  BACK", callback_data="home"))
    return markup

def back_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("‹  BACK", callback_data="home"))
    return markup

def get_welcome_text(first_name):
    return f"<b>{BOT_NAME}</b>\n\nWelcome, <b>{first_name}</b>.\n\nIt's a pleasure to have you here.\n\nExplore available options below.\n\n<b>Welcome aboard.</b>"

def get_help_text():
    return f"<b>{BOT_NAME} • HELP</b>\n\n<b>/start</b>\nOpen welcome screen.\n<b>/hacks</b>\nOpen private access.\n<b>/about</b>\nLearn more."

def get_language_text():
    return f"<b>{BOT_NAME} • GUIDE</b>\n\nChoose language."

ENGLISH_GUIDE = ["<b>STEP 01</b>\n\nDownload resource.", "<b>STEP 02</b>\n\nOpen Download directory.", "<b>STEP 03</b>\n\nExtract archive.", "<b>STEP 04</b>\n\nVerify files.", "<b>STEP 05</b>\n\nInstall files.", "<b>STEP 06</b>\n\nLaunch app.", "<b>IMPORTANT</b>\n\nKeep backup."]
HINGLISH_GUIDE = ["<b>STEP 01</b>\n\nFile download karo.", "<b>STEP 02</b>\n\nDownload folder jao.", "<b>STEP 03</b>\n\nPackage extract karo.", "<b>STEP 04</b>\n\nFiles check karo.", "<b>STEP 05</b>\n\nResource install karo.", "<b>STEP 06</b>\n\nSetup complete karo.", "<b>IMPORTANT</b>\n\nBackup rakho."]

def guide_menu(language, page):
    markup = types.InlineKeyboardMarkup(row_width=2)
    tp = len(ENGLISH_GUIDE) if language == "en" else len(HINGLISH_GUIDE)
    pb = types.InlineKeyboardButton("‹ BACK", callback_data=f"guide_{language}_{page-1}" if page > 0 else "guide")
    if page < tp - 1:
        markup.add(pb, types.InlineKeyboardButton("NEXT ›", callback_data=f"guide_{language}_{page+1}"))
    else:
        markup.add(pb)
    return markup

def get_guide_page(language, page):
    pages = ENGLISH_GUIDE if language == "en" else HINGLISH_GUIDE
    return f"<b>{BOT_NAME} • GUIDE</b>\n<i>{language.upper()} • {page+1}/{len(pages)}</i>\n\n{pages[page]}"

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, get_welcome_text(message.from_user.first_name or "there"), reply_markup=welcome_menu())

@bot.message_handler(commands=["hacks"])
def hacks(message):
    bot.send_message(message.chat.id, f"<b>{BOT_NAME} ACCESS</b>\n\nPrivate resource available.", reply_markup=access_menu())

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(message.chat.id, get_help_text(), reply_markup=help_menu())

@bot.message_handler(commands=["about"])
def about_command(message):
    bot.send_message(message.chat.id, f"<b>{BOT_NAME}</b>\n\nVersion: {BOT_VERSION}\nStatus: Online", reply_markup=back_menu())

@bot.message_handler(commands=["file"])
def file_command(message):
    bot.send_message(message.chat.id, f"<b>{BOT_NAME} ACCESS</b>\n\nUse <b>/hacks</b>.", reply_markup=back_menu())

@bot.message_handler(
    func=lambda message: message.chat.type in ["group", "supergroup"] and message.from_user and not message.from_user.is_bot,
    content_types=["text", "photo", "video", "document", "audio", "voice", "animation"]
)
def moderation_handler(message):
    user = message.from_user
    if user.id in OWNER_IDS: return
    text = message.text or message.caption or ""
    if not text or text.startswith('/'): return
    if not contains_bad_language(text): return
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    wn = add_warning(message.chat.id, user.id)
    if wn >= 3:
        try:
            bot.ban_chat_member(message.chat.id, user.id)
            bot.send_message(message.chat.id, banned_text(user))
        except:
            try: bot.send_message(message.chat.id, f"<b>🚫 ERROR</b>\n\nCan't ban {user.first_name}. Check bot permissions.")
            except: pass
        return
    try: bot.send_message(message.chat.id, warning_text(user, wn))
    except: pass

@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(get_help_text(), call.message.chat.id, call.message.message_id, reply_markup=help_menu())

@bot.callback_query_handler(func=lambda call: call.data == "about")
def about_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(f"<b>{BOT_NAME}</b>\n\nVersion: {BOT_VERSION}\nStatus: Online", call.message.chat.id, call.message.message_id, reply_markup=back_menu())

@bot.callback_query_handler(func=lambda call: call.data == "guide")
def guide_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(get_language_text(), call.message.chat.id, call.message.message_id, reply_markup=language_menu())

@bot.callback_query_handler(func=lambda call: call.data == "guide_en")
def guide_english_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(get_guide_page("en", 0), call.message.chat.id, call.message.message_id, reply_markup=guide_menu("en", 0))

@bot.callback_query_handler(func=lambda call: call.data == "guide_hi")
def guide_hinglish_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(get_guide_page("hi", 0), call.message.chat.id, call.message.message_id, reply_markup=guide_menu("hi", 0))

@bot.callback_query_handler(func=lambda call: call.data.startswith("guide_en_"))
def guide_english_pages(call):
    try: page = int(call.data.replace("guide_en_", ""))
    except: bot.answer_callback_query(call.id); return
    bot.answer_callback_query(call.id)
    bot.edit_message_text(get_guide_page("en", page), call.message.chat.id, call.message.message_id, reply_markup=guide_menu("en", page))

@bot.callback_query_handler(func=lambda call: call.data.startswith("guide_hi_"))
def guide_hinglish_pages(call):
    try: page = int(call.data.replace("guide_hi_", ""))
    except: bot.answer_callback_query(call.id); return
    bot.answer_callback_query(call.id)
    bot.edit_message_text(get_guide_page("hi", page), call.message.chat.id, call.message.message_id, reply_markup=guide_menu("hi", page))

@bot.callback_query_handler(func=lambda call: call.data == "home")
def home_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(get_welcome_text(call.from_user.first_name or "there"), call.message.chat.id, call.message.message_id, reply_markup=welcome_menu())

def set_commands():
    bot.set_my_commands([
        types.BotCommand("start", "Open QRIISHNA"),
        types.BotCommand("hacks", "Open private access"),
        types.BotCommand("help", "View guide"),
        types.BotCommand("about", "About bot"),
        types.BotCommand("file", "Access info")
    ])

if __name__ == "__main__":
    init_database()
    set_commands()
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
            
