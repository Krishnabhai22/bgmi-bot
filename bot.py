import os
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
#
# Generic legitimate resource installation guidance.
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
#
# Natural Hinglish, not literal translation.
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

    first_name = message.from_user.first_name or "there"

    bot.send_message(
        message.chat.id,
        get_welcome_text(first_name),
        reply_markup=welcome_menu()
    )


# ============================================================
# /HACKS
# ============================================================

@bot.message_handler(commands=["hacks"])
def hacks(message):

    text = (
        f"<b>{BOT_NAME} ACCESS</b>\n\n"
        "Access request received.\n\n"
        "The private resource area is now available "
        "for you to open.\n\n"
        "Use the secure access point below to continue."
    )

    bot.send_message(
        message.chat.id,
        text,
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

    text = (
        f"<b>{BOT_NAME}</b>\n\n"
        "A clean and dedicated Telegram interface "
        "designed for simple, direct and controlled access.\n\n"

        "<b>VERSION</b>\n"
        f"{BOT_VERSION}\n\n"

        "<b>STATUS</b>\n"
        "Online"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=back_menu()
    )


# ============================================================
# /FILE
# ============================================================

@bot.message_handler(commands=["file"])
def file_command(message):

    text = (
        f"<b>{BOT_NAME} ACCESS</b>\n\n"
        "The requested resource is available "
        "through the private access panel.\n\n"
        "Use <b>/hacks</b> to continue."
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=back_menu()
    )


# ============================================================
# MAIN HELP BUTTON
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
# ABOUT BUTTON
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "about"
)
def about_callback(call):

    text = (
        f"<b>{BOT_NAME}</b>\n\n"
        "A clean and dedicated Telegram interface "
        "designed for simple, direct and controlled access.\n\n"

        "<b>VERSION</b>\n"
        f"{BOT_VERSION}\n\n"

        "<b>STATUS</b>\n"
        "Online"
    )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_menu()
    )


# ============================================================
# INSTALLATION GUIDE BUTTON
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


# ============================================================
# ENGLISH GUIDE START
# ============================================================

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


# ============================================================
# HINGLISH GUIDE START
# ============================================================

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
# GUIDE PAGE NAVIGATION
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("guide_en_")
)
def guide_english_pages(call):

    try:
        page = int(
            call.data.replace("guide_en_", "")
        )

    except ValueError:
        bot.answer_callback_query(call.id)
        return

    if page < 0 or page >= len(ENGLISH_GUIDE):
        bot.answer_callback_query(
            call.id,
            "This page is not available."
        )
        return

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        get_guide_page("en", page),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=guide_menu("en", page)
    )


# ============================================================
# HINGLISH GUIDE PAGE NAVIGATION
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("guide_hi_")
)
def guide_hinglish_pages(call):

    try:
        page = int(
            call.data.replace("guide_hi_", "")
        )

    except ValueError:
        bot.answer_callback_query(call.id)
        return

    if page < 0 or page >= len(HINGLISH_GUIDE):
        bot.answer_callback_query(
            call.id,
            "This page is not available."
        )
        return

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        get_guide_page("hi", page),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=guide_menu("hi", page)
    )


# ============================================================
# BACK TO HOME
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "home"
)
def home_callback(call):

    first_name = call.from_user.first_name or "there"

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        get_welcome_text(first_name),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=welcome_menu()
    )


# ============================================================
# TELEGRAM COMMAND MENU
# ============================================================

def set_commands():

    commands = [

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
            "View help and installation guide"
        ),

        types.BotCommand(
            "about",
            "About QRIISHNA"
        ),

        types.BotCommand(
            "file",
            "Access information"
        )

    ]

    bot.set_my_commands(commands)


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    print("----------------------------------------")
    print("          QRIISHNA INITIALIZING")
    print("----------------------------------------")

    set_commands()

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    print("Flask server : ONLINE")
    print("Telegram bot : ONLINE")
    print("Bot name     : QRIISHNA")
    print("----------------------------------------")

    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60
        )
