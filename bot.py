import os
import re
import sqlite3
import threading

import telebot
from telebot import types
from flask import Flask


# ============================================================
# QRIISHNA
# Premium Telegram Resource Bot
# ============================================================

TOKEN = os.environ.get("BOT_TOKEN")

# Private channel / resource link
CHANNEL_LINK = "https://t.me/+GHjJmfql0o02YWZl"

BOT_NAME = "QRIISHNA"
BOT_VERSION = "1.0"

# ============================================================
# OWNER / WHITELIST
# ============================================================
# This ID will never receive warnings or bans.

OWNER_IDS = {
    1332494807
}


# ============================================================
# FLASK SERVER
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "QRIISHNA • ONLINE"


def run_flask():
    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port
    )


# ============================================================
# BOT INITIALIZATION
# ============================================================

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is missing."
    )

bot = telebot.TeleBot(
    TOKEN,
    parse_mode="HTML"
)


# ============================================================
# WARNING DATABASE
# ============================================================

DB_FILE = "warnings.db"

db_lock = threading.Lock()


def init_database():

    with db_lock:

        connection = sqlite3.connect(
            DB_FILE,
            check_same_thread=False
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS warnings (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                warning_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
            """
        )

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

    if result:
        return result[0]

    return 0


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

    return result[0]


# ============================================================
# PROFANITY FILTER
# ============================================================

# Common Hindi / Hinglish / English abusive words and
# frequently used variations.

BAD_WORDS = [

    # Hindi / Hinglish
    "loda",
    "lauda",
    "louda",
    "lawda",
    "lavda",
    "laude",
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

    # English
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


# Sort longer words first so compound words are detected properly.
BAD_WORDS = sorted(
    set(BAD_WORDS),
    key=len,
    reverse=True
)


def normalize_text(text):

    if not text:
        return ""

    text = text.lower()

    # Common leetspeak replacements.
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

    # Remove zero-width characters.
    text = re.sub(
        r"[\u200b-\u200f\uFEFF]",
        "",
        text
    )

    # Convert punctuation/separators into spaces.
    text = re.sub(
        r"[^a-zA-Z\u0900-\u097F]+",
        " ",
        text
    )

    # Normalize repeated spaces.
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def contains_bad_language(text):

    normalized = normalize_text(text)

    if not normalized:
        return False

    # Direct phrase/word matching.
    for word in BAD_WORDS:

        pattern = r"(?<![a-zA-Z])" + re.escape(word) + r"(?![a-zA-Z])"

        if re.search(pattern, normalized):
            return True

    # Also check a compact version for cases like:
    # "l o d a", "f.u.c.k", etc.
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
# WARNING UI
# ============================================================

def warning_text(user, warning_number):

    first_name = user.first_name or "User"

    return (
        "<b>⚠️ COMMUNITY WARNING</b>\n\n"
        f"👤 <b>User:</b> {first_name}\n"
        "📌 <b>Reason:</b> Inappropriate language\n\n"
        f"⚠️ <b>Warning:</b> {warning_number} / 3\n\n"
        "<i>Please maintain respectful language.</i>\n"
        "<i>Further violations may result in a ban.</i>"
    )


def banned_text(user):

    first_name = user.first_name or "User"

    return (
        "<b>🚫 USER BANNED</b>\n\n"
        f"👤 <b>User:</b> {first_name}\n"
        "📌 <b>Reason:</b> 3 warnings reached\n\n"
        "<i>The user has been removed from this group "
        "for repeated inappropriate language.</i>"
    )


# ============================================================
# MODERATION HANDLER
# ============================================================

@bot.message_handler(
    func=lambda message: (
        message.chat.type in ["group", "supergroup"]
        and message.from_user is not None
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

    # Owner is completely protected.
    if user.id in OWNER_IDS:
        return

    # Only text/caption needs profanity checking.
    text = message.text or message.caption or ""

    if not text:
        return

    # No bad language -> do nothing.
    if not contains_bad_language(text):
        return

    chat_id = message.chat.id
    user_id = user.id

    # Delete the abusive message.
    try:

        bot.delete_message(
            chat_id,
            message.message_id
        )

    except Exception as error:

        print(
            f"Could not delete message: {error}"
        )

    # Increase warning count.
    warning_number = add_warning(
        chat_id,
        user_id
    )

    # ========================================================
    # THIRD WARNING -> BAN
    # ========================================================

    if warning_number >= 3:

        try:

            bot.ban_chat_member(
                chat_id,
                user_id
            )

            bot.send_message(
                chat_id,
                banned_text(user)
            )

            print(
                f"BANNED: {user.id} "
                f"after {warning_number} warnings"
            )

        except Exception as error:

            print(
                f"Could not ban user {user.id}: {error}"
            )

            # If ban fails, tell the group that the
            # third warning was reached.
            try:

                bot.send_message(
                    chat_id,
                    (
                        "<b>🚫 MODERATION ACTION</b>\n\n"
                        f"👤 <b>User:</b> "
                        f"{user.first_name or 'User'}\n"
                        "⚠️ <b>Warnings:</b> 3 / 3\n\n"
                        "<i>The ban could not be completed. "
                        "Please check the bot's Ban Users permission.</i>"
                    )
                )

            except Exception:
                pass

        return

    # ========================================================
    # FIRST / SECOND WARNING
    # ========================================================

    try:

        bot.send_message(
            chat_id,
            warning_text(
                user,
                warning_number
            )
        )

        print(
            f"WARNING {warning_number}/3: "
            f"{user.id}"
        )

    except Exception as error:

        print(
            f"Could not send warning: {error}"
        )


# ============================================================
# MAIN WELCOME MENU
# ============================================================

def welcome_menu():

    markup = types.InlineKeyboardMarkup(row_width=2)

    help_button = types.InlineKeyboardButton(
        "⌕  HELP",
        callback_data="help"
    )

    about_button = types.InlineKeyboardButton(
        "ⓘ  ABOUT",
        callback_data="about"
    )

    markup.add(
        help_button,
        about_button
    )

    return markup


# ============================================================
# HELP MENU
# ============================================================

def help_menu():

    markup = types.InlineKeyboardMarkup(row_width=2)

    guide_button = types.InlineKeyboardButton(
        "▣  INSTALLATION GUIDE",
        callback_data="guide"
    )

    about_button = types.InlineKeyboardButton(
        "ⓘ  ABOUT",
        callback_data="about"
    )

    back_button = types.InlineKeyboardButton(
        "‹  BACK",
        callback_data="home"
    )

    markup.add(guide_button)
    markup.add(about_button)
    markup.add(back_button)

    return markup


# ============================================================
# LANGUAGE SELECTION MENU
# ============================================================

def language_menu():

    markup = types.InlineKeyboardMarkup(row_width=2)

    english_button = types.InlineKeyboardButton(
        "🇬🇧  ENGLISH",
        callback_data="guide_en"
    )

    hinglish_button = types.InlineKeyboardButton(
        "🇮🇳  HINGLISH",
        callback_data="guide_hi"
    )

    back_button = types.InlineKeyboardButton(
        "‹  BACK",
        callback_data="help"
    )

    markup.add(
        english_button,
        hinglish_button
    )

    markup.add(back_button)

    return markup


# ============================================================
# ACCESS MENU
# ============================================================

def access_menu():

    markup = types.InlineKeyboardMarkup()

    access_button = types.InlineKeyboardButton(
        "▣  OPEN PRIVATE ACCESS",
        url=CHANNEL_LINK
    )

    back_button = types.InlineKeyboardButton(
        "‹  BACK",
        callback_data="home"
    )

    markup.add(access_button)
    markup.add(back_button)

    return markup


# ============================================================
# GENERIC BACK MENU
# ============================================================

def back_menu():

    markup = types.InlineKeyboardMarkup()

    back_button = types.InlineKeyboardButton(
        "‹  BACK",
        callback_data="home"
    )

    markup.add(back_button)

    return markup


# ============================================================
# WELCOME TEXT
# ============================================================

def get_welcome_text(first_name):

    return (
        f"<b>{BOT_NAME}</b>\n\n"
        f"Welcome, <b>{first_name}</b>.\n\n"
        "It's a pleasure to have you here.\n\n"
        "You've reached the official interface. "
        "Explore the available options below to learn "
        "more about the service and its resources.\n\n"
        "<b>Welcome aboard.</b>"
    )


# ============================================================
# HELP TEXT
# ============================================================

def get_help_text():

    return (
        f"<b>{BOT_NAME} • HELP</b>\n\n"
        "Use the options below to navigate the bot.\n\n"

        "<b>/start</b>\n"
        "Open the main welcome screen.\n\n"

        "<b>/hacks</b>\n"
        "Open the private access panel.\n\n"

        "<b>Installation Guide</b>\n"
        "View the setup guide in English or Hinglish.\n\n"

        "<b>/about</b>\n"
        "Learn more about QRIISHNA."
    )


# ============================================================
# INSTALLATION GUIDE LANGUAGE SCREEN
# ============================================================

def get_language_text():

    return (
        f"<b>{BOT_NAME} • INSTALLATION GUIDE</b>\n\n"
        "Choose your preferred language to continue.\n\n"
        "Select the language in which you would like "
        "the installation process explained."
    )


# ============================================================
# ENGLISH INSTALLATION GUIDE
# ============================================================

ENGLISH_GUIDE = [

    (
        "<b>STEP 01 • DOWNLOAD</b>\n\n"
        "Download the required resource from the official "
        "Telegram source.\n\n"
        "Wait until the download is completely finished "
        "before continuing.\n\n"
        "<i>Do not open or move the file while it is still downloading.</i>"
    ),

    (
        "<b>STEP 02 • LOCATE THE FILE</b>\n\n"
        "Open your file manager and go to the device's "
        "<b>Download</b> directory.\n\n"
        "Locate the folder or archive containing the "
        "resource you have just downloaded."
    ),

    (
        "<b>STEP 03 • EXTRACT THE PACKAGE</b>\n\n"
        "Select the downloaded archive and choose the "
        "<b>Extract</b> option.\n\n"
        "Allow the extraction process to finish completely "
        "before opening the extracted folder."
    ),

    (
        "<b>STEP 04 • CHECK THE CONTENT</b>\n\n"
        "Open the extracted folder and verify that the "
        "required files and folders are present.\n\n"
        "If the package contains instructions or a README "
        "file, review them before continuing."
    ),

    (
        "<b>STEP 05 • INSTALL THE RESOURCE</b>\n\n"
        "Follow the official instructions supplied with "
        "the resource to place the files in their supported "
        "destination.\n\n"
        "Do not overwrite protected application files unless "
        "the official documentation specifically requires it."
    ),

    (
        "<b>STEP 06 • FINISH SETUP</b>\n\n"
        "Once the supported installation process is complete, "
        "close your file manager and launch the application normally.\n\n"
        "If anything does not work correctly, restore your "
        "original files and review the supplied documentation."
    ),

    (
        "<b>IMPORTANT • BEFORE YOU CONTINUE</b>\n\n"
        "Always keep a backup of your original files before "
        "making changes.\n\n"
        "Only install resources from sources you trust and "
        "follow the application's supported installation "
        "requirements."
    )

]


# ============================================================
# HINGLISH INSTALLATION GUIDE
# ============================================================

HINGLISH_GUIDE = [

    (
        "<b>STEP 01 • FILE DOWNLOAD KARO</b>\n\n"
        "Sabse pehle required resource ko official Telegram "
        "source se download karo.\n\n"
        "Aage badhne se pehle ensure karo ki download "
        "poori tarah complete ho chuka hai.\n\n"
        "<i>Download complete hone se pehle file ko move ya open mat karo.</i>"
    ),

    (
        "<b>STEP 02 • FILE KO LOCATE KARO</b>\n\n"
        "Apna file manager open karo aur device ke "
        "<b>Download</b> folder me jao.\n\n"
        "Ab jo resource tumne download kiya hai uska "
        "folder ya archive locate karo."
    ),

    (
        "<b>STEP 03 • PACKAGE EXTRACT KARO</b>\n\n"
        "Downloaded archive ko select karo aur "
        "<b>Extract</b> option choose karo.\n\n"
        "Extraction complete hone tak wait karo. "
        "Uske baad hi extracted folder open karo."
    ),

    (
        "<b>STEP 04 • FILES CHECK KARO</b>\n\n"
        "Extracted folder open karke check karo ki required "
        "files aur folders properly available hain.\n\n"
        "Agar package ke andar README ya instructions di gayi hain, "
        "to next step se pehle unhe zaroor read karo."
    ),

    (
        "<b>STEP 05 • RESOURCE INSTALL KARO</b>\n\n"
        "Resource ke saath di gayi official instructions follow "
        "karke files ko unke supported destination par place karo.\n\n"
        "Protected application files ko bina official instructions "
        "ke overwrite ya modify mat karo."
    ),

    (
        "<b>STEP 06 • SETUP COMPLETE KARO</b>\n\n"
        "Supported installation complete hone ke baad file manager "
        "close karo aur application ko normally open karo.\n\n"
        "Agar resource properly work nahi karta, original files "
        "restore karo aur provided documentation dobara check karo."
    ),

    (
        "<b>IMPORTANT • START KARNE SE PEHLE</b>\n\n"
        "Kisi bhi file me change karne se pehle original files ka "
        "backup zaroor rakho.\n\n"
        "Sirf trusted source se resources install karo aur "
        "application ki supported requirements ko follow karo."
    )

]


# ============================================================
# GUIDE NAVIGATION MENU
# ============================================================

def guide_menu(language, page):

    markup = types.InlineKeyboardMarkup(row_width=2)

    total_pages = (
        len(ENGLISH_GUIDE)
        if language == "en"
        else len(HINGLISH_GUIDE)
    )

    if page > 0:

        previous_button = types.InlineKeyboardButton(
            "‹  BACK",
            callback_data=f"guide_{language}_{page - 1}"
        )

    else:

        previous_button = types.InlineKeyboardButton(
            "‹  LANGUAGE",
            callback_data="guide"
        )

    if page < total_pages - 1:

        next_button = types.InlineKeyboardButton(
     
