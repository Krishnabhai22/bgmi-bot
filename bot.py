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
BOT_VERSION = "3.0"

CHANNEL_LINK = "https://t.me/+GHjJmfql0o02YWZl"

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
# PRIVATE START UI
# ============================================================

def start_menu():

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

    markup.add(
        types.InlineKeyboardButton(
            "⌕  HELP",
            callback_data="help"
        ),
        types.InlineKeyboardButton(
            "ⓘ  ABOUT",
            callback_data="about"
        )
    )

    return markup


def get_start_text():

    return (
        "<b>✦ QRISHNA</b>\n\n"
        "<b>What service do you need for BGMI KRAFTON?</b>\n\n"
        "I'm Krishna's personal assistant bot.\n"
        "Need files or other services?\n\n"
        "<b>Use /hacks to continue.</b>"
    )


# ============================================================
# HELP UI
# ============================================================

def help_menu():

    markup = types.InlineKeyboardMarkup(
        row_width=1
    )

    markup.add(
        types.InlineKeyboardButton(
            "▣  INSTALLATION GUIDE",
            callback_data="guide"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "ⓘ  ABOUT",
            callback_data="about"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "⌂  HOME",
            callback_data="home"
        )
    )

    return markup


def get_help_text():

    return (
        "<b>▣ QRISHNA • HELP</b>\n\n"
        "<b>/start</b>\n"
        "Open the main interface.\n\n"
        "<b>/hacks</b>\n"
        "Open private access.\n\n"
        "<b>/about</b>\n"
        "View bot information.\n\n"
        "<i>Select an option below.</i>"
    )


# ============================================================
# ABOUT
# ============================================================

def get_about_text():

    return (
        "<b>ⓘ QRISHNA</b>\n"
        "<i>Premium Support & Assistant Bot</i>\n\n"
        f"Version: <b>{BOT_VERSION}</b>\n"
        "Status: <b>Online</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "<i>Private • Secure • Professional</i>"
    )


def back_menu():

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "⌂  HOME",
            callback_data="home"
        )
    )

    return markup


# ============================================================
# PRIVATE ACCESS
# ============================================================

def access_menu():

    markup = types.InlineKeyboardMarkup(
        row_width=1
    )

    markup.add(
        types.InlineKeyboardButton(
            "✦  OPEN PRIVATE ACCESS",
            url=CHANNEL_LINK
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "⌂  HOME",
            callback_data="home"
        )
    )

    return markup


def get_access_text():

    return (
        "<b>✦ QRISHNA • PRIVATE ACCESS</b>\n\n"
        "Private access is available below.\n\n"
        "<i>Tap the button to continue.</i>"
    )


# ============================================================
# INSTALLATION GUIDE
# ============================================================

def language_menu():

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

    markup.add(
        types.InlineKeyboardButton(
            "🇬🇧  ENGLISH",
            callback_data="guide_en"
        ),
        types.InlineKeyboardButton(
            "🇮🇳  HINGLISH",
            callback_data="guide_hi"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "‹  BACK",
            callback_data="help"
        )
    )

    return markup


def get_language_text():

    return (
        "<b>▣ QRISHNA • INSTALLATION GUIDE</b>\n\n"
        "Choose your preferred language."
    )


# ============================================================
# SAFE GUIDE CONTENT
# ============================================================

ENGLISH_GUIDE = [

    "<b>STEP 01</b>\n\n"
    "Download the required file from the official channel.",

    "<b>STEP 02</b>\n\n"
    "Open your downloaded file and follow the instructions "
    "provided with the resource.",

    "<b>STEP 03</b>\n\n"
    "Open your file manager and go to the Download folder.",

    "<b>STEP 04</b>\n\n"
    "Locate the downloaded resource and extract it if required.",

    "<b>STEP 05</b>\n\n"
    "Check the extracted files and make sure the required "
    "folders are present.",

    "<b>STEP 06</b>\n\n"
    "Follow the resource-specific instructions for placing "
    "the files in the correct location.",

    "<b>STEP 07</b>\n\n"
    "Installation is complete. Launch the supported app "
    "and verify that everything works correctly."
]


HINGLISH_GUIDE = [

    "<b>STEP 01</b>\n\n"
    "Official channel se required file download karlo.",

    "<b>STEP 02</b>\n\n"
    "Downloaded file open karo aur resource ke saath "
    "di gayi instructions follow karo.",

    "<b>STEP 03</b>\n\n"
    "File manager kholo aur Download folder me jao.",

    "<b>STEP 04</b>\n\n"
    "Downloaded resource ko locate karo aur zarurat ho "
    "to extract karo.",

    "<b>STEP 05</b>\n\n"
    "Extracted files check karo aur required folders "
    "present hain ya nahi dekho.",

    "<b>STEP 06</b>\n\n"
    "Files ko correct location par rakhne ke liye "
    "resource-specific instructions follow karo.",

    "<b>STEP 07</b>\n\n"
    "Installation complete hai. Supported app launch "
    "karo aur check karo ki sab properly work kar raha hai."
]


def get_guide_page(language, page):

    pages = (
        ENGLISH_GUIDE
        if language == "en"
        else HINGLISH_GUIDE
    )

    page = max(
        0,
        min(page, len(pages) - 1)
    )

    return (
        "<b>▣ QRISHNA • INSTALLATION GUIDE</b>\n\n"
        + pages[page]
    )


def guide_menu(language, page):

    pages = (
        ENGLISH_GUIDE
        if language == "en"
        else HINGLISH_GUIDE
    )

    markup = types.InlineKeyboardMarkup(
        row_width=1
    )

    if page < len(pages) - 1:

        markup.add(
            types.InlineKeyboardButton(
                "NEXT  ›",
                callback_data=(
                    f"guide_{language}_{page + 1}"
                )
            )
        )

    if page > 0:

        markup.add(
            types.InlineKeyboardButton(
                "‹  PREVIOUS",
                callback_data=(
                    f"guide_{language}_{page - 1}"
                )
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            "⌂  HOME",
            callback_data="home"
        )
    )

    return markup


# ============================================================
# /START
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):

    bot.send_message(
        message.chat.id,
        get_start_text(),
        reply_markup=start_menu()
    )


# ============================================================
# /HACKS
# ============================================================

@bot.message_handler(commands=["hacks"])
def hacks(message):

    bot.send_message(
        message.chat.id,
        get_access_text(),
        reply_markup=access_menu()
    )


# ============================================================
# /HELP
# ============================================================

@bot.message_handler(commands=["help"])
def help_command(message):

    bot.send_message(
        message.chat.id,
        get_help_text(),
        reply_markup=help_menu()
    )


# ============================================================
# /ABOUT
# ============================================================

@bot.message_handler(commands=["about"])
def about_command(message):

    bot.send_message(
        message.chat.id,
        get_about_text(),
        reply_markup=back_menu()
    )


# ============================================================
# /FILE
# ============================================================

@bot.message_handler(commands=["file"])
def file_command(message):

    bot.send_message(
        message.chat.id,
        (
            "<b>✦ QRISHNA • ACCESS</b>\n\n"
            "Use <b>/hacks</b> to open private access."
        ),
        reply_markup=access_menu()
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
        "text",
        "photo",
        "video",
        "document",
        "audio",
        "voice",
        "animation"
    ]
)
def moderation_handler(message):

    user = message.from_user

    if not user or user.is_bot:
        return

    # Automatic first-message welcome
    send_first_time_welcome(message)

    # Owner bypass
    if user.id in OWNER_IDS:
        return

    text = (
        message.text
        or message.caption
        or ""
    )

    if not text:
        return

    if text.startswith("/"):
        return

    if not contains_bad_language(text):
        return

    # Delete inappropriate message
    try:
        bot.delete_message(
            message.chat.id,
            message.message_id
        )
    except Exception:
        pass

    warning_number = add_warning(
        message.chat.id,
        user.id
    )

    # Three warnings = ban
    if warning_number >= 3:

        try:

            bot.ban_chat_member(
                message.chat.id,
                user.id
            )

            bot.send_message(
                message.chat.id,
                banned_text(user)
            )

        except Exception:

            try:

                name = html.escape(
                    user.first_name or "User"
                )

                bot.send_message(
                    message.chat.id,
                    (
                        "<b>🚫 BAN ERROR</b>\n\n"
                        f"Unable to ban <b>{name}</b>.\n\n"
                        "<i>Check bot administrator permissions.</i>"
                    )
                )

            except Exception:
                pass

        return

    # Warning
    try:

        bot.send_message(
            message.chat.id,
            warning_text(
                user,
                warning_number
            )
        )

    except Exception:
        pass


# ============================================================
# CALLBACK • HELP
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "help"
)
def help_callback(call):

    try:

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            get_help_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=help_menu()
        )

    except Exception:
        pass


# ============================================================
# CALLBACK • ABOUT
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "about"
)
def about_callback(call):

    try:

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            get_about_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_menu()
        )

    except Exception:
        pass


# ============================================================
# CALLBACK • PRIVATE ACCESS
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "private_access"
)
def private_access_callback(call):

    try:

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            get_access_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=access_menu()
        )

    except Exception:
        pass


# ============================================================
# CALLBACK • GUIDE
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "guide"
)
def guide_callback(call):

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


# ============================================================
# CALLBACK • ENGLISH
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "guide_en"
)
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


# ============================================================
# CALLBACK • HINGLISH
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "guide_hi"
)
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


# ============================================================
# CALLBACK • ENGLISH PAGES
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("guide_en_")
)
def guide_english_pages(call):

    try:
        page = int(
            call.data.replace(
                "guide_en_",
                ""
            )
        )
    except Exception:
        bot.answer_callback_query(call.id)
        return

    page = max(
        0,
        min(page, len(ENGLISH_GUIDE) - 1)
    )

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


# ============================================================
# CALLBACK • HINGLISH PAGES
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("guide_hi_")
)
def guide_hinglish_pages(call):

    try:
        page = int(
            call.data.replace(
                "guide_hi_",
                ""
            )
        )
    except Exception:
        bot.answer_callback_query(call.id)
        return

    page = max(
        0,
        min(page, len(HINGLISH_GUIDE) - 1)
    )

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
# CALLBACK • HOME
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "home"
)
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


# ============================================================
# COMMAND MENU
# ============================================================

def set_commands():

    bot.set_my_commands(
        [
            types.BotCommand(
                "start",
                "Open main interface"
            ),
            types.BotCommand(
                "hacks",
                "Open private access"
            ),
            types.BotCommand(
                "help",
                "Open help and guide"
            ),
            types.BotCommand(
                "about",
                "About QRISHNA"
            ),
            types.BotCommand(
                "file",
                "Access information"
            )
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
