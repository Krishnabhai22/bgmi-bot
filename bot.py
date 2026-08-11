import os
import re
import sqlite3
import threading

import telebot
from telebot import types
from flask import Flask


# ============================================================
# QRIISHNA BOT • CONFIGURATION
# ============================================================

TOKEN = os.environ.get("BOT_TOKEN")

# IMPORTANT:
# Replace this with your actual private Telegram channel/resource link.
CHANNEL_LINK = "https://t.me/qriishna_private"

BOT_NAME = "QRIISHNA"
BOT_VERSION = "2.0"

OWNER_IDS = {1332494807}


# ============================================================
# FLASK KEEP-ALIVE
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return f"{BOT_NAME} • ONLINE"


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# ============================================================
# BOT INITIALIZATION
# ============================================================

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DB_FILE = "warnings.db"
db_lock = threading.Lock()


# ============================================================
# DATABASE
# ============================================================

def init_database():
    with db_lock:
        connection = sqlite3.connect(
            DB_FILE,
            check_same_thread=False
        )

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
        connection = sqlite3.connect(
            DB_FILE,
            check_same_thread=False
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT warning_count
            FROM warnings
            WHERE chat_id = ? AND user_id = ?
            """,
            (chat_id, user_id)
        )

        result = cursor.fetchone()
        connection.close()

    return result[0] if result else 0


def add_warning(chat_id, user_id):
    with db_lock:
        connection = sqlite3.connect(
            DB_FILE,
            check_same_thread=False
        )

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
            WHERE chat_id = ? AND user_id = ?
            """,
            (chat_id, user_id)
        )

        result = cursor.fetchone()
        connection.close()

    return result[0] if result else 1


# ============================================================
# BAD LANGUAGE FILTER
# ============================================================

BAD_WORDS = [
    "loda",
    "lauda",
    "louda",
    "lawda",
    "lavda",
    "laude",
    "lode",
    "lodaa",
    "loudaa",
    "lawdaa",

    "chod",
    "chhod",
    "chud",
    "chut",
    "chutiya",
    "chutiye",
    "chutia",
    "chutiy",
    "chutiyaa",

    "madarchod",
    "madarchut",
    "madar chod",
    "madar ch0d",
    "mc",

    "bhenchod",
    "bhen chod",
    "behenchod",
    "behen chod",
    "bc",

    "gaand",
    "gand",
    "gandu",

    "randi",
    "rand",
    "randwa",

    "harami",
    "haraami",
    "haramkhor",

    "kamina",
    "kamine",
    "kaminey",

    "kutte",
    "kutta",
    "kutiya",

    "bhosdi",
    "bhosdike",
    "bhosdika",
    "bhosdiwala",
    "bhosdiwale",

    "jhatu",
    "jhaatu",

    "bakchod",
    "bakchodi",

    "chakka",
    "chakkar",
    "nalayak",

    "fuck",
    "fucking",
    "fucker",
    "motherfucker",

    "shit",
    "shitty",

    "bitch",
    "bastard",
    "asshole",

    "dick",
    "dickhead",
    "pussy",
    "cunt",
    "whore",
    "slut"
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

    # Normal word matching
    for word in BAD_WORDS:
        pattern = (
            r"(?<![a-zA-Z])"
            + re.escape(word)
            + r"(?![a-zA-Z])"
        )

        if re.search(pattern, normalized):
            return True

    # Compact matching for bypass attempts
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

def warning_text(user, warning_number):
    name = user.first_name or "User"

    return (
        "<b>⚠️ COMMUNITY WARNING</b>\n\n"
        f"👤 <b>User:</b> {name}\n"
        "📌 <b>Reason:</b> Inappropriate language\n\n"
        f"⚠️ <b>Warning:</b> {warning_number} / 3\n\n"
        "<i>Please maintain respectful language.</i>"
    )


def banned_text(user):
    name = user.first_name or "User"

    return (
        "<b>🚫 USER BANNED</b>\n\n"
        f"👤 <b>User:</b> {name}\n"
        "📌 <b>Reason:</b> 3 warnings reached\n\n"
        "<i>The user has been removed from this group.</i>"
    )


# ============================================================
# PREMIUM UI MENUS
# ============================================================

def welcome_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)

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

    markup.add(
        types.InlineKeyboardButton(
            "✦  PRIVATE ACCESS",
            callback_data="private_access"
        )
    )

    return markup


def help_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)

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
        ),
        types.InlineKeyboardButton(
            "‹  BACK",
            callback_data="home"
        )
    )

    return markup


def language_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)

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


def access_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)

    markup.add(
        types.InlineKeyboardButton(
            "✦  ENTER PRIVATE ACCESS",
            url=CHANNEL_LINK
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "‹  RETURN TO HOME",
            callback_data="home"
        )
    )

    return markup


def back_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)

    markup.add(
        types.InlineKeyboardButton(
            "‹  RETURN TO HOME",
            callback_data="home"
        )
    )

    return markup


# ============================================================
# TEXT / CONTENT
# ============================================================

def get_welcome_text(first_name):
    return (
        f"<b>✦ {BOT_NAME}</b>\n"
        f"<i>Private Resource Platform</i>\n\n"

        f"Welcome, <b>{first_name}</b>.\n\n"

        "You have reached the official interface.\n"
        "Explore the available options below to "
        "continue.\n\n"

        "<b>━━━━━━━━━━━━━━━━</b>\n"
        "<i>Private • Secure • Professional</i>"
    )


def get_help_text():
    return (
        f"<b>⌕ {BOT_NAME} • HELP</b>\n"
        f"<i>Command Center</i>\n\n"

        "<b>AVAILABLE COMMANDS</b>\n\n"

        "<b>/start</b>\n"
        "Open the main interface.\n\n"

        "<b>/hacks</b>\n"
        "Open private access portal.\n\n"

        "<b>/help</b>\n"
        "View available commands.\n\n"

        "<b>/about</b>\n"
        "View bot information.\n\n"

        "<b>/file</b>\n"
        "View access information.\n\n"

        "<b>━━━━━━━━━━━━━━━━</b>\n"
        "<i>Select an option below.</i>"
    )


def get_about_text():
    return (
        f"<b>ⓘ {BOT_NAME}</b>\n"
        f"<i>Official Interface</i>\n\n"

        "<b>VERSION</b>\n"
        f"{BOT_VERSION}\n\n"

        "<b>STATUS</b>\n"
        "● Online\n\n"

        "<b>PLATFORM</b>\n"
        "Telegram\n\n"

        "<b>━━━━━━━━━━━━━━━━</b>\n"
        "<i>Private • Secure • Reliable</i>"
    )


def get_access_text():
    return (
        f"<b>✦ {BOT_NAME} ACCESS</b>\n"
        f"<i>Private Resource Portal</i>\n\n"

        "<b>PRIVATE ACCESS</b>\n\n"

        "Your private resource area is ready.\n"
        "Use the secure access point below "
        "to continue.\n\n"

        "<b>━━━━━━━━━━━━━━━━</b>\n"
        "<i>Private • Secure • Exclusive</i>"
    )


def get_language_text():
    return (
        f"<b>▣ {BOT_NAME} • GUIDE</b>\n"
        f"<i>Installation Center</i>\n\n"

        "Choose your preferred language "
        "to continue."
    )


# ============================================================
# INSTALLATION GUIDE
# ============================================================

ENGLISH_GUIDE = [
    (
        "<b>STEP 01</b>\n\n"
        "Download the required resource."
    ),
    (
        "<b>STEP 02</b>\n\n"
        "Open your Downloads directory."
    ),
    (
        "<b>STEP 03</b>\n\n"
        "Extract the downloaded archive."
    ),
    (
        "<b>STEP 04</b>\n\n"
        "Verify that all required files are present."
    ),
    (
        "<b>STEP 05</b>\n\n"
        "Install the required files."
    ),
    (
        "<b>STEP 06</b>\n\n"
        "Complete the setup and launch the app."
    ),
    (
        "<b>IMPORTANT</b>\n\n"
        "Keep a backup of your original files."
    )
]


HINGLISH_GUIDE = [
    (
        "<b>STEP 01</b>\n\n"
        "Required resource download karo."
    ),
    (
        "<b>STEP 02</b>\n\n"
        "Apna Downloads folder open karo."
    ),
    (
        "<b>STEP 03</b>\n\n"
        "Downloaded archive ko extract karo."
    ),
    (
        "<b>STEP 04</b>\n\n"
        "Check karo ki saari required files available hain."
    ),
    (
        "<b>STEP 05</b>\n\n"
        "Required files install karo."
    ),
    (
        "<b>STEP 06</b>\n\n"
        "Setup complete karke app launch karo."
    ),
    (
        "<b>IMPORTANT</b>\n\n"
        "Original files ka backup zaroor rakho."
    )
]


def guide_menu(language, page):
    markup = types.InlineKeyboardMarkup(row_width=2)

    pages = (
        ENGLISH_GUIDE
        if language == "en"
        else HINGLISH_GUIDE
    )

    total_pages = len(pages)

    if page > 0:
        markup.add(
            types.InlineKeyboardButton(
                "‹  PREVIOUS",
                callback_data=f"guide_{language}_{page - 1}"
            )
        )

    if page < total_pages - 1:
        markup.add(
            types.InlineKeyboardButton(
                  "NEXT  ›",
                callback_data=f"guide_{language}_{page + 1}"
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            "⌂  HOME",
            callback_data="home"
        )
    )

    return markup


def get_guide_page(language, page):
    pages = (
        ENGLISH_GUIDE
        if language == "en"
        else HINGLISH_GUIDE
    )

    if page < 0:
        page = 0

    if page >= len(pages):
        page = len(pages) - 1

    return (
        f"<b>▣ {BOT_NAME} • GUIDE</b>\n"
        f"<i>{language.upper()} • "
        f"{page + 1}/{len(pages)}</i>\n\n"
        f"{pages[page]}\n\n"
        "<b>━━━━━━━━━━━━━━━━</b>"
    )


# ============================================================
# COMMANDS
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):
    first_name = (
        message.from_user.first_name
        or "there"
    )

    bot.send_message(
        message.chat.id,
        get_welcome_text(first_name),
        reply_markup=welcome_menu()
    )


@bot.message_handler(commands=["hacks"])
def hacks(message):
    bot.send_message(
        message.chat.id,
        get_access_text(),
        reply_markup=access_menu()
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        get_help_text(),
        reply_markup=help_menu()
    )


@bot.message_handler(commands=["about"])
def about_command(message):
    bot.send_message(
        message.chat.id,
        get_about_text(),
        reply_markup=back_menu()
    )


@bot.message_handler(commands=["file"])
def file_command(message):
    bot.send_message(
        message.chat.id,
        (
            f"<b>✦ {BOT_NAME} ACCESS</b>\n\n"
            "Use <b>/hacks</b> to open the "
            "private access portal."
        ),
        reply_markup=back_menu()
    )


# ============================================================
# PRIVATE ACCESS CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "private_access"
)
def private_access_callback(call):
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        get_access_text(),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=access_menu()
    )


# ============================================================
# HELP CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "help"
)
def help_callback(call):
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        get_help_text(),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=help_menu()
    )


# ============================================================
# ABOUT CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "about"
)
def about_callback(call):
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        get_about_text(),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_menu()
    )


# ============================================================
# GUIDE CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "guide"
)
def guide_callback(call):
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        get_language_text(),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=language_menu()
    )


@bot.callback_query_handler(
    func=lambda call: call.data == "guide_en"
)
def guide_english_callback(call):
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        get_guide_page("en", 0),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=guide_menu("en", 0)
    )


@bot.callback_query_handler(
    func=lambda call: call.data == "guide_hi"
)
def guide_hinglish_callback(call):
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        get_guide_page("hi", 0),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=guide_menu("hi", 0)
    )


# ============================================================
# ENGLISH GUIDE PAGES
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
    except ValueError:
        bot.answer_callback_query(call.id)
        return

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        get_guide_page("en", page),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=guide_menu("en", page)
    )


# ============================================================
# HINGLISH GUIDE PAGES
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
    except ValueError:
        bot.answer_callback_query(call.id)
        return

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        get_guide_page("hi", page),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=guide_menu("hi", page)
    )


# ============================================================
# HOME CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "home"
)
def home_callback(call):
    bot.answer_callback_query(call.id)

    first_name = (
        call.from_user.first_name
        or "there"
    )

    bot.edit_message_text(
        get_welcome_text(first_name),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=welcome_menu()
    )


# ============================================================
# GROUP MODERATION
# ============================================================

@bot.message_handler(
    func=lambda message:
        message.chat.type in ["group", "supergroup"]
        and message.from_user
        and not message.from_user.is_bot,
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

    # Owner bypass
    if user.id in OWNER_IDS:
        return

    text = (
        message.text
        or message.caption
        or ""
    )

    # Ignore empty messages
    if not text:
        return

    # Ignore commands
    if text.startswith("/"):
        return

    # Check language
    if not contains_bad_language(text):
        return

    # Delete offending message
    try:
        bot.delete_message(
            message.chat.id,
            message.message_id
        )
    except Exception:
        pass

    # Add warning
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
                bot.send_message(
                    message.chat.id,
                    (
                        "<b>🚫 MODERATION ERROR</b>\n\n"
                        f"Can't ban "
                        f"<b>{user.first_name or 'User'}</b>.\n\n"
                        "<i>Check whether the bot "
                        "has administrator permissions.</i>"
                    )
                )

            except Exception:
                pass

        return

    # Send warning
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
# BOT COMMAND MENU
# ============================================================

def set_commands():
    bot.set_my_commands([
        types.BotCommand(
            "start",
            "Open QRIISHNA"
        ),
        types.BotCommand(
            "hacks",
            "Open private access"
        ),
        types.BotCommand(
            "help",
            "View help"
        ),
        types.BotCommand(
            "about",
            "About QRIISHNA"
        ),
        types.BotCommand(
            "file",
            "Access information"
        )
    ])


# ============================================================
# START BOT
# ============================================================

if __name__ == "__main__":

    print("====================================")
    print(f"   {BOT_NAME} • STARTING")
    print(f"   VERSION: {BOT_VERSION}")
    print("====================================")

    # Database
    init_database()

    # Telegram commands
    set_commands()

    # Flask server
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    print(f"{BOT_NAME} • ONLINE")

    # Telegram polling
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60
        )
