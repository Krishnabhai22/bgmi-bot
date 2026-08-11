import os
import threading
import telebot
from telebot import types
from flask import Flask

# ============================================================
# QRIISHNA
# Premium Telegram Interface
# ============================================================

TOKEN = os.environ.get("BOT_TOKEN")

# Private resource / channel link
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
# TELEGRAM BOT
# ============================================================

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is not configured in environment variables."
    )

bot = telebot.TeleBot(
    TOKEN,
    parse_mode="HTML"
)


# ============================================================
# MAIN / WELCOME MENU
#
# IMPORTANT:
# No access button is shown here.
# User must manually use /hacks for access.
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
# ACCESS MENU
#
# This menu appears ONLY after /hacks
# ============================================================

def access_menu():

    markup = types.InlineKeyboardMarkup(row_width=1)

    access_button = types.InlineKeyboardButton(
        "▣  OPEN PRIVATE ACCESS",
        url=CHANNEL_LINK
    )

    back_button = types.InlineKeyboardButton(
        "‹  RETURN TO QRIISHNA",
        callback_data="home"
    )

    markup.add(access_button)
    markup.add(back_button)

    return markup


# ============================================================
# BACK BUTTON
# ============================================================

def back_menu():

    markup = types.InlineKeyboardMarkup()

    back_button = types.InlineKeyboardButton(
        "‹  RETURN TO QRIISHNA",
        callback_data="home"
    )

    markup.add(back_button)

    return markup


# ============================================================
# /START
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):

    first_name = message.from_user.first_name or "there"

    text = (
        "<b>QRIISHNA</b>\n\n"

        f"Welcome, <b>{first_name}</b>.\n\n"

        "It's a pleasure to have you here.\n\n"

        "You've reached the official interface. "
        "Take a moment to explore the options below "
        "and discover how everything works.\n\n"

        "<i>Your journey starts here.</i>"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=welcome_menu()
    )


# ============================================================
# /HACKS
#
# Access is intentionally gated behind this command.
# ============================================================

@bot.message_handler(commands=["hacks"])
def hacks(message):

    text = (
        "<b>QRIISHNA ACCESS</b>\n\n"

        "Access request received.\n\n"

        "The private resource area is now available "
        "for you to open.\n\n"

        "<i>Use the secure access point below to continue.</i>"
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

    text = (
        "<b>QRIISHNA • HELP</b>\n\n"

        "Everything you need is available through "
        "the commands below.\n\n"

        "<b>/start</b>\n"
        "Return to the main welcome interface.\n\n"

        "<b>/hacks</b>\n"
        "Open the private access panel.\n\n"

        "<b>/about</b>\n"
        "Learn more about QRIISHNA.\n\n"

        "<i>Choose a command whenever you're ready.</i>"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=back_menu()
    )


# ============================================================
# /ABOUT
# ============================================================

@bot.message_handler(commands=["about"])
def about_command(message):

    text = (
        "<b>QRIISHNA</b>\n\n"

        "A dedicated Telegram interface designed "
        "around a simple principle — keep the experience "
        "clean, direct and easy to navigate.\n\n"

        "<b>INTERFACE</b>\n"
        "Premium access experience\n\n"

        "<b>VERSION</b>\n"
        f"{BOT_VERSION}\n\n"

        "<b>STATUS</b>\n"
        "Online\n\n"

        "<i>Thank you for being here.</i>"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=back_menu()
    )


# ============================================================
# /FILE
#
# Does NOT bypass the /hacks access flow.
# ============================================================

@bot.message_handler(commands=["file"])
def file_command(message):

    text = (
        "<b>PRIVATE ACCESS</b>\n\n"

        "This resource is available through "
        "the QRIISHNA access panel.\n\n"

        "Use <b>/hacks</b> to continue."
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=back_menu()
    )


# ============================================================
# HELP CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "help"
)
def help_callback(call):

    text = (
        "<b>QRIISHNA • HELP</b>\n\n"

        "Everything you need is available through "
        "the commands below.\n\n"

        "<b>/start</b>\n"
        "Return to the main welcome interface.\n\n"

        "<b>/hacks</b>\n"
        "Open the private access panel.\n\n"

        "<b>/about</b>\n"
        "Learn more about QRIISHNA.\n\n"

        "<i>Choose a command whenever you're ready.</i>"
    )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_menu()
    )


# ============================================================
# ABOUT CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "about"
)
def about_callback(call):

    text = (
        "<b>QRIISHNA</b>\n\n"

        "A dedicated Telegram interface designed "
        "around a simple principle — keep the experience "
        "clean, direct and easy to navigate.\n\n"

        "<b>INTERFACE</b>\n"
        "Premium access experience\n\n"

        "<b>VERSION</b>\n"
        f"{BOT_VERSION}\n\n"

        "<b>STATUS</b>\n"
        "Online\n\n"

        "<i>Thank you for being here.</i>"
    )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_menu()
    )


# ============================================================
# HOME CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "home"
)
def home_callback(call):

    first_name = call.from_user.first_name or "there"

    text = (
        "<b>QRIISHNA</b>\n\n"

        f"Welcome, <b>{first_name}</b>.\n\n"

        "It's a pleasure to have you here.\n\n"

        "You've reached the official interface. "
        "Take a moment to explore the options below "
        "and discover how everything works.\n\n"

        "<i>Your journey starts here.</i>"
    )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=welcome_menu()
    )


# ============================================================
# UNKNOWN COMMAND / MESSAGE
# ============================================================

@bot.message_handler(func=lambda message: True)
def unknown_message(message):

    text = (
        "<b>QRIISHNA</b>\n\n"

        "I couldn't understand that request.\n\n"

        "Use <b>/help</b> to view the available commands."
    )

    bot.send_message(
        message.chat.id,
        text,
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
            "View help"
        ),

        types.BotCommand(
            "about",
            "About QRIISHNA"
        ),

        types.BotCommand(
            "file",
            "Resource access information"
        )

    ]

    bot.set_my_commands(commands)


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    print("----------------------------------------")
    print("        QRIISHNA INITIALIZING")
    print("----------------------------------------")

    set_commands()

    # Render web server
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    print("Web server        : ONLINE")
    print("Telegram interface: ONLINE")
    print("Bot               : QRIISHNA")
    print("----------------------------------------")

    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60
)
