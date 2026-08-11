import os
import re
import sqlite3
import threading
import html

import telebot
from telebot import types
from flask import Flask


# ============================================================
# QRISHNA • PREMIUM TELEGRAM BOT
# ============================================================

TOKEN = os.environ.get("BOT_TOKEN")

BOT_NAME = "QRISHNA"
BOT_VERSION = "3.2"

CHANNEL_LINK = "https://t.me/+GHjJmfql0o02YWZl"
ADMIN_CONTACT = "https://t.me/+GHjJmfql0o02YWZl"  # Update with your Telegram username if needed

OWNER_IDS = {
    1332494807
}

DB_FILE = "warnings.db"

app = Flask(__name__)
db_lock = threading.Lock()


# ============================================================
# FLASK
# ============================================================

@app.route("/")
def home():
    return "QRISHNA • ONLINE"


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(
        host="0.0.0.0",
        port=port
    )


# ============================================================
# TOKEN
# ============================================================

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is missing."
    )


# ============================================================
# TELEGRAM
# ============================================================

bot = telebot.TeleBot(
    TOKEN,
    parse_mode="HTML"
)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False,
        timeout=30
    )


def init_database():

    with db_lock:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                warning_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS welcomed_users (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        connection.commit()
        connection.close()


# ============================================================
# WARNINGS
# ============================================================

def add_warning(chat_id, user_id):

    with db_lock:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO warnings (
                chat_id,
                user_id,
                warning_count
            )
            VALUES (?, ?, 1)

            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET
                warning_count = warning_count + 1
            """,
            (chat_id, user_id)
        )

        connection.commit()

        cursor.execute(
            """
            SELECT warning_count
            FROM warnings
            WHERE chat_id = ?
            AND user_id = ?
            """,
            (chat_id, user_id)
        )

        result = cursor.fetchone()

        connection.close()

    return result[0] if result else 1


# ============================================================
# FIRST MESSAGE WELCOME
# ============================================================

def send_first_time_welcome(message):

    user = message.from_user

    if not user or user.is_bot:
        return

    chat_id = message.chat.id
    user_id = user.id

    with db_lock:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO welcomed_users (
                chat_id,
                user_id
            )
            VALUES (?, ?)
            """,
            (chat_id, user_id)
        )

        is_first_message = cursor.rowcount == 1

        connection.commit()
        connection.close()

    if not is_first_message:
        return

    name = html.escape(
        user.first_name or "User"
    )

    text = (
        "<b>QRISHNA</b>\n\n"
        "Welcome to our Premium Support & Assistant Bot. 👋\n\n"
        f"Welcome, <b>{name}</b>."
    )

    try:
        bot.send_message(
            chat_id,
            text
        )
    except Exception:
        pass


# ============================================================
# BAD WORD FILTER
# ============================================================

BAD_WORDS = [
    "loda", "lauda", "louda", "lawda", "lavda",
    "laude", "lode", "lodaa", "loudaa", "lawdaa",
    "chod", "chhod", "chud", "chut", "chutiya",
    "chutiye", "chutia", "chutiy", "chutiyaa",
    "madarchod", "madarchut", "madar chod",
    "madar ch0d", "mc",
    "bhenchod", "bhen chod", "behenchod",
    "behen chod", "bc",
    "gaand", "gand", "gandu",
    "randi", "rand", "randwa",
    "harami", "haraami", "haramkhor",
    "kamina", "kamine", "kaminey",
    "kutte", "kutta", "kutiya",
    "bhosdi", "bhosdike", "bhosdika",
    "bhosdiwala", "bhosdiwale",
    "jhatu", "jhaatu",
    "bakchod", "bakchodi",
    "chakka", "chakkar", "nalayak",
    "fuck", "fucking", "fucker", "motherfucker",
    "shit", "shitty",
    "bitch", "bastard",
    "asshole", "dick", "dickhead",
    "pussy", "cunt", "whore", "slut"
]

BAD_WORDS = sorted(
    set(BAD_WORDS),
    key=len,
    reverse=True
)


def normalize_text(text):

    if not text:
        return ""

    text = text.lower()

    replacements = {
        "@": "a",
        "4": "a",
        "0": "o",
        "1": "i",
        "!": "i",
        "$": "s",
        "3": "e",
        "5": "s"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(
        r"[\u200b-\u200f\uFEFF]",
        "",
        text
    )

    text = re.sub(
        r"[^a-zA-Z\u0900-\u097F]+",
        " ",
        text
    )

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def contains_bad_language(text):

    normalized = normalize_text(text)

    if not normalized:
        return False

    for word in BAD_WORDS:

        if re.search(
            r"(?<![a-zA-Z])"
            + re.escape(word)
            + r"(?![a-zA-Z])",
            normalized
        ):
            return True

    compact = re.sub(
        r"[^a-zA-Z\u0900-\u097F]",
        "",
        normalized
    )

    for word in BAD_WORDS:

        compact_word = re.sub(
            r"[^a-zA-Z\u0900-\u097F]",
            "",
            word
        )

        if len(compact_word) >= 4 and compact_word in compact:
            return True

    return False


# ============================================================
# MODERATION MESSAGES
# ============================================================

def warning_text(user, number):

    name = html.escape(
        user.first_name or "User"
    )

    return (
        "<b>⚠️ COMMUNITY WARNING</b>\n\n"
        f"👤 <b>User:</b> {name}\n"
        "📌 <b>Reason:</b> Inappropriate language\n\n"
        f"⚠️ <b>Warning:</b> {number} / 3\n\n"
        "<i>Please maintain respectful language.</i>"
    )


def banned_text(user):

    name = html.escape(
        user.first_name or "User"
    )

    return (
        "<b>🚫 USER BANNED</b>\n\n"
        f"👤 <b>User:</b> {name}\n"
        "📌 <b>Reason:</b> 3 warnings reached\n\n"
        "<i>The user has been removed from this group.</i>"
    )


# ============================================================
# UI MENUS & TEXTS
# ============================================================

def start_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📁 DOWNLOAD PORTAL", callback_data="btn_files"),
        types.InlineKeyboardButton("📖 SETUP GUIDE", callback_data="btn_tutorial")
    )
    markup.add(
        types.InlineKeyboardButton("💎 VIP ACCESS", callback_data="btn_premium"),
        types.InlineKeyboardButton("💬 SUPPORT DESK", callback_data="btn_support")
    )
    return markup


def get_start_text():
    return (
        "<b>💎 QRISHNA • COMMAND CENTER</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Welcome to <b>QRISHNA BGMI Portal</b>! 👋\n\n"
        "⚡ <b>System Status:</b> <code>ONLINE 🟢</code>\n"
        f"📌 <b>Version:</b> <code>v{BOT_VERSION}</code>\n"
        "🛡️ <b>Security:</b> <code>100% Anti-Ban Safe</code>\n\n"
        "<i>Select an option below or use menu commands to continue.</i>"
    )


def get_files_text():
    return (
        "<b>📥 BGMI DOWNLOAD PORTAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Access latest files, configs, and optimization packages below:\n\n"
        "• <b>90 FPS + Extreme Smooth Config</b>\n"
        "• <b>LagFix & High Performance Pack</b>\n"
        "• <b>iPad View Configs</b>\n\n"
        "<i>Tap the button below to open private channel downloads.</i>"
    )


def files_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚀 OPEN PRIVATE DOWNLOAD CHANNEL", url=CHANNEL_LINK),
        types.InlineKeyboardButton("⌂ HOME", callback_data="home")
    )
    return markup


def get_updates_text():
    return (
        "<b>📢 SYSTEM LOGS & RELEASES</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Current Build:</b> <code>v{BOT_VERSION}</code>\n"
        "📅 <b>Status:</b> <code>Up to date</code>\n\n"
        "✨ <b>Changelog:</b>\n"
        "├ Optimized for latest BGMI updates\n"
        "├ Enhanced Anti-Ban Protection\n"
        "└ Fixed Lag & Frame Drops"
    )


def get_premium_text():
    return (
        "<b>💎 BGMI VIP ACCESS PASS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Unlock premium files, zero recoil keys, and priority updates:\n\n"
        "👑 <b>VIP Features:</b>\n"
        "├ High-Speed Server Downloads\n"
        "├ 100% Anti-Ban Guarantee\n"
        "├ Custom Config Settings\n"
        "└ 24/7 Dedicated Admin Support\n\n"
        "<i>Contact Admin to upgrade to VIP access.</i>"
    )


def premium_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💬 BUY VIP / CONTACT ADMIN", url=ADMIN_CONTACT),
        types.InlineKeyboardButton("⌂ HOME", callback_data="home")
    )
    return markup


def get_access_text(user_id, first_name):
    name = html.escape(first_name or "User")
    return (
        "<b>🔐 VERIFICATION & KEY STATUS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>User:</b> {name}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        "⭐ <b>Plan Level:</b> <code>FREE USER</code>\n"
        "🔑 <b>License Key:</b> <code>INACTIVE</code>\n\n"
        "💡 <i>Use <b>/premium</b> to upgrade and activate license keys.</i>"
    )


def get_support_text():
    return (
        "<b>👨‍💻 PREMIUM SUPPORT DESK</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Facing issues with installation or files?\n"
        "Our team is here to assist you.\n\n"
        "<i>Tap below to reach Admin support.</i>"
    )


def support_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💬 CONTACT ADMIN", url=ADMIN_CONTACT),
        types.InlineKeyboardButton("⌂ HOME", callback_data="home")
    )
    return markup


def back_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⌂ HOME", callback_data="home"))
    return markup


# ============================================================
# INSTALLATION GUIDE CONTENT & MENUS
# ============================================================

def language_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇬🇧 ENGLISH", callback_data="guide_en"),
        types.InlineKeyboardButton("🇮🇳 HINGLISH", callback_data="guide_hi")
    )
    markup.add(types.InlineKeyboardButton("⌂ HOME", callback_data="home"))
    return markup


def get_language_text():
    return (
        "<b>📖 INSTALLATION & SETUP GUIDE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Choose your preferred language to read setup steps:"
    )


ENGLISH_GUIDE = [
    "<b>STEP 01</b>\n\nDownload the required file from the official channel.",
    "<b>STEP 02</b>\n\nOpen your downloaded file and follow the provided instructions.",
    "<b>STEP 03</b>\n\nOpen your File Manager and go to the Download folder.",
    "<b>STEP 04</b>\n\nLocate the downloaded resource and extract it using ZArchiver.",
    "<b>STEP 05</b>\n\nCheck extracted files and verify required folders exist.",
    "<b>STEP 06</b>\n\nCopy and paste files into:\n<code>Android > data > com.pubg.imobile > files</code>",
    "<b>STEP 07</b>\n\nInstallation complete. Restart phone and launch BGMI."
]


HINGLISH_GUIDE = [
    "<b>STEP 01</b>\n\nOfficial channel se required file download karlo.",
    "<b>STEP 02</b>\n\nDownloaded file open karo aur instructions follow karo.",
    "<b>STEP 03</b>\n\nFile Manager kholo aur Download folder me jao.",
    "<b>STEP 04</b>\n\nFile locate karke ZArchiver se extract karlo.",
    "<b>STEP 05</b>\n\nExtracted files check karo ki sabhi files properly extracted hain.",
    "<b>STEP 06</b>\n\nFiles copy karke yaha paste karo:\n<code>Android > data > com.pubg.imobile > files</code>",
    "<b>STEP 07</b>\n\nSetup complete! Phone restart karke BGMI launch karein."
]


def get_guide_page(language, page):
    pages = ENGLISH_GUIDE if language == "en" else HINGLISH_GUIDE
    page = max(0, min(page, len(pages) - 1))
    return f"<b>📖 INSTALLATION GUIDE ({language.upper()})</b>\n\n" + pages[page]


def guide_menu(language, page):
    pages = ENGLISH_GUIDE if language == "en" else HINGLISH_GUIDE
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btns = []
    if page > 0:
        btns.append(types.InlineKeyboardButton("‹ PREVIOUS", callback_data=f"guide_{language}_{page - 1}"))
    if page < len(pages) - 1:
        btns.append(types.InlineKeyboardButton("NEXT ›", callback_data=f"guide_{language}_{page + 1}"))
    
    if btns:
        markup.add(*btns)
        
    markup.add(types.InlineKeyboardButton("⌂ HOME", callback_data="home"))
    return markup


# ============================================================
# COMMAND HANDLERS (7 MAIN COMMANDS)
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        get_start_text(),
        reply_markup=start_menu()
    )


@bot.message_handler(commands=["files"])
def files_command(message):
    bot.send_message(
        message.chat.id,
        get_files_text(),
        reply_markup=files_menu()
    )


@bot.message_handler(commands=["updates"])
def updates_command(message):
    bot.send_message(
        message.chat.id,
        get_updates_text(),
        reply_markup=back_menu()
    )


@bot.message_handler(commands=["tutorial"])
def tutorial_command(message):
    bot.send_message(
        message.chat.id,
        get_language_text(),
        reply_markup=language_menu()
    )


@bot.message_handler(commands=["premium"])
def premium_command(message):
    bot.send_message(
        message.chat.id,
        get_premium_text(),
        reply_markup=premium_menu()
    )


@bot.message_handler(commands=["access"])
def access_command(message):
    user = message.from_user
    bot.send_message(
        message.chat.id,
        get_access_text(user.id, user.first_name),
        reply_markup=back_menu()
    )


@bot.message_handler(commands=["support"])
def support_command(message):
    bot.send_message(
        message.chat.id,
        get_support_text(),
        reply_markup=support_menu()
    )


# ============================================================
# GROUP MODERATION
# ============================================================

@bot.message_handler(
    func=lambda message: (
        message.chat.type in ["group", "supergroup"]
        and message.from_user
        and not message.from_user.is_bot
    ),
    content_types=[
        "text", "photo", "video", "document",
        "audio", "voice", "animation"
    ]
)
def moderation_handler(message):

    user = message.from_user

    if not user or user.is_bot:
        return

    send_first_time_welcome(message)

    if user.id in OWNER_IDS:
        return

    text = message.text or message.caption or ""

    if not text or text.startswith("/"):
        return

    if not contains_bad_language(text):
        return

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

    warning_number = add_warning(message.chat.id, user.id)

    if warning_number >= 3:
        try:
            bot.ban_chat_member(message.chat.id, user.id)
            bot.send_message(message.chat.id, banned_text(user))
        except Exception:
            try:
                name = html.escape(user.first_name or "User")
                bot.send_message(
                    message.chat.id,
                    f"<b>🚫 BAN ERROR</b>\n\nUnable to ban <b>{name}</b>."
                )
            except Exception:
                pass
        return

    try:
        bot.send_message(message.chat.id, warning_text(user, warning_number))
    except Exception:
        pass


# ============================================================
# CALLBACK QUERY HANDLERS
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "home")
def home_callback(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_start_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=start_menu()
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "btn_files")
def cb_files(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_files_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=files_menu()
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "btn_tutorial")
def cb_tutorial(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_language_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=language_menu()
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "btn_premium")
def cb_premium(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_premium_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=premium_menu()
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "btn_support")
def cb_support(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_support_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=support_menu()
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "guide_en")
def guide_english_callback(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_guide_page("en", 0),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=guide_menu("en", 0)
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "guide_hi")
def guide_hinglish_callback(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_guide_page("hi", 0),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=guide_menu("hi", 0)
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("guide_en_"))
def guide_english_pages(call):
    try:
        page = int(call.data.replace("guide_en_", ""))
    except Exception:
        bot.answer_callback_query(call.id)
        return

    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_guide_page("en", page),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=guide_menu("en", page)
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("guide_hi_"))
def guide_hinglish_pages(call):
    try:
        page = int(call.data.replace("guide_hi_", ""))
    except Exception:
        bot.answer_callback_query(call.id)
        return

    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_guide_page("hi", page),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=guide_menu("hi", page)
        )
    except Exception:
        pass


# ============================================================
# COMMAND MENU SETTER
# ============================================================

def set_commands():
    bot.set_my_commands(
        [
            types.BotCommand("start", "Launch Command Center"),
            types.BotCommand("files", "Access Download Portal & Configs"),
            types.BotCommand("updates", "View System Logs & Releases"),
            types.BotCommand("tutorial", "Installation & Setup Guide"),
            types.BotCommand("premium", "Upgrade to VIP Access"),
            types.BotCommand("access", "Verification & Key Status"),
            types.BotCommand("support", "Contact Premium Support Desk")
        ]
    )


# ============================================================
# START BOT
# ============================================================

if __name__ == "__main__":

    print("========================================")
    print("        QRISHNA • PREMIUM BOT")
    print("========================================")

    init_database()
    set_commands()

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    print("QRISHNA is ONLINE.")

    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60,
        skip_pending=True
    )
