import os
import re
import json
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
# OWNER
# ============================================================

OWNER_ID = 1332494807


# ============================================================
# WARNING SYSTEM
# ============================================================

WARNING_FILE = "warnings.json"

warning_lock = threading.Lock()


def load_warnings():

    if not os.path.exists(WARNING_FILE):
        return {}

    try:

        with open(
            WARNING_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, dict):
                return data

    except Exception:
        pass

    return {}


warnings = load_warnings()


def save_warnings():

    with warning_lock:

        try:

            with open(
                WARNING_FILE,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    warnings,
                    file,
                    ensure_ascii=False,
                    indent=2
                )

        except Exception as error:

            print(
                f"Warning save error: {error}"
            )


# ============================================================
# BAD WORD FILTER
#
# Common English + Hindi/Hinglish abusive words.
# ============================================================

BAD_WORDS = [

    # English
    "fuck",
    "fucker",
    "fucking",
    "motherfucker",
    "shit",
    "bullshit",
    "bitch",
    "bastard",
    "asshole",
    "dumbass",
    "dickhead",
    "dick",
    "pussy",
    "cunt",
    "whore",
    "slut",

    # Hindi / Hinglish
    "madarchod",
    "maderchod",
    "madarchood",
    "madrchod",
    "mc",
    "behenchod",
    "bhenchod",
    "behench*d",
    "bhosdike",
    "bhosdika",
    "bhosdi",
    "bhosda",
    "chutiya",
    "chutiye",
    "chutia",
    "chutiyapa",
    "chut",
    "gandu",
    "gaand",
    "gand",
    "randi",
    "harami",
    "haraami",
    "kamina",
    "kamine",
    "kaminey",
    "kutte",
    "kutta",
    "kutti",
    "saala",
    "sala",
    "saale",
    "suar",
    "suwar",
    "lavde",
    "lavda",
    "lodu",
    "laude",
    "lauda",
    "lund",
    "lulli",
    "jhatu",
    "jhaatu",
    "bakchod",
    "bakchodi",
    "rand",
    "randi",
    "teri ma",
    "teri maa",
    "teri behen",
    "teri bahin"
]


def normalize_text(text):

    text = text.lower()

    # Common symbols/spaces remove
    text = re.sub(
        r"[\s\W_]+",
        "",
        text,
        flags=re.UNICODE
    )

    return text


def contains_bad_word(text):

    if not text:
        return False

    lower_text = text.lower()

    # Normal text check
    for word in BAD_WORDS:

        if " " in word:

            if word in lower_text:
                return True

        else:

            pattern = (
                r"(?<![\w])"
                + re.escape(word)
                + r"(?![\w])"
            )

            if re.search(
                pattern,
                lower_text,
                flags=re.IGNORECASE
            ):

                return True

    # Obfuscated text check
    normalized_text = normalize_text(text)

    for word in BAD_WORDS:

        normalized_word = normalize_text(word)

        if len(normalized_word) >= 3:

            if normalized_word in normalized_text:
                return True

    return False


# ============================================================
# WARNING KEY
# ============================================================

def get_warning_key(chat_id, user_id):

    return f"{chat_id}:{user_id}"


def get_warning_count(chat_id, user_id):

    key = get_warning_key(
        chat_id,
        user_id
    )

    return int(
        warnings.get(key, 0)
    )


def add_warning(chat_id, user_id):

    key = get_warning_key(
        chat_id,
        user_id
    )

    current_count = int(
        warnings.get(key, 0)
    )

    current_count += 1

    warnings[key] = current_count

    save_warnings()

    return current_count


# ============================================================
# CHECK ADMIN STATUS
# ============================================================

def is_protected_user(chat_id, user_id):

    # Owner is always protected
    if user_id == OWNER_ID:
        return True

    try:

        member = bot.get_chat_member(
            chat_id,
            user_id
        )

        # Telegram admins should not be automatically banned
        if member.status in (
            "administrator",
            "creator"
        ):

            return True

    except Exception:
        pass

    return False


# ============================================================
# HANDLE BAD LANGUAGE
# ============================================================

def handle_bad_language(message):

    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    # Owner/admin protection
    if is_protected_user(
        chat_id,
        user_id
    ):

        return

    count = add_warning(
        chat_id,
        user_id
    )

    # Delete abusive message
    try:

        bot.delete_message(
            chat_id,
            message.message_id
        )

    except Exception as error:

        print(
            f"Message delete error: {error}"
        )

    first_name = (
        message.from_user.first_name
        or "User"
    )

    # ========================================================
    # WARNING 1
    # ========================================================

    if count == 1:

        bot.send_message(
            chat_id,
            (
                f"⚠️ <b>WARNING 1/3</b>\n\n"
                f"<b>{first_name}</b>, abusive language is not allowed here.\n\n"
                "Please keep the chat respectful.\n\n"
                "<i>Next violation will result in another warning.</i>"
            )
        )

    # ========================================================
    # WARNING 2
    # ========================================================

    elif count == 2:

        bot.send_message(
            chat_id,
            (
                f"⚠️ <b>WARNING 2/3</b>\n\n"
                f"<b>{first_name}</b>, this is your second warning.\n\n"
                "Please stop using abusive language.\n\n"
                "<i>One more violation will result in a ban.</i>"
            )
        )

    # ========================================================
    # WARNING 3 = BAN
    # ========================================================

    elif count >= 3:

        try:

            bot.ban_chat_member(
                chat_id,
                user_id
            )

            bot.send_message(
                chat_id,
                (
                    f"🚫 <b>USER BANNED</b>\n\n"
                    f"<b>{first_name}</b> has been banned "
                    "for repeated abusive language.\n\n"
                    "<b>Reason:</b> 3 warnings reached."
                )
            )

        except Exception as error:

            print(
                f"Ban error: {error}"
            )

            bot.send_message(
                chat_id,
                (
                    f"⚠️ <b>WARNING 3/3</b>\n\n"
                    f"<b>{first_name}</b> reached the maximum "
                    "warning limit.\n\n"
                    "The bot could not ban the user. "
                    "Please check that the bot has permission "
                    "to ban users."
                )
            )


# ============================================================
# FLASK SERVER
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():

    return "QRIISHNA • ONLINE"


def run_flask():

    port = int(
        os.environ.get(
            "PORT",
            8080
        )
    )

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
# MESSAGE MODERATION
# ============================================================

@bot.message_handler(
    func=lambda message: (
        message.content_type == "text"
        and contains_bad_word(
            message.text or ""
        )
    ),
    content_types=["text"]
)
def profanity_handler(message):

    handle_bad_language(message)


# ============================================================
# MAIN WELCOME MENU
# ============================================================

def welcome_menu():

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

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

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

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

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

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

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

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
            "NEXT  ›",
            callback_data=f"guide_{language}_{page + 1}"
        )

        markup.add(
            previous_button,
            next_button
        )

    else:

        markup.add(previous_button)

    return markup


# ============================================================
# GUIDE PAGE TEXT
# ============================================================

def get_guide_page(language, page):

    if language == "en":

        pages = ENGLISH_GUIDE
        language_name = "ENGLISH"

    else:

        pages = HINGLISH_GUIDE
        language_name = "HINGLISH"

    total_pages = len(pages)

    page_text = pages[page]

    return (
        f"<b>{BOT_NAME} • INSTALLATION GUIDE</b>\n"
        f"<i>{language_name} • {page + 1}/{total_pages}</i>\n\n"
        f"{page_text}"
    )


# ============================================================
# /START
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
        reply_markup=welc
