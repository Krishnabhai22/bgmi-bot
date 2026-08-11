import os
import threading

import telebot
from telebot import types
from flask import Flask


# ============================================================
# QRIISHNA
# Premium Telegram Bot Interface
# ============================================================

TOKEN = os.environ.get("BOT_TOKEN")

# Private resource / channel
CHANNEL_LINK = "https://t.me/+GHjJmfql0o02YWZl"

BOT_NAME = "QRIISHNA"
BOT_VERSION = "1.0"


# ============================================================
# FLASK SERVER
# Required for Render
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
# WELCOME MENU
#
# IMPORTANT:
# No access button here.
# User must use /hacks to request access.
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
# BACK MENU
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
# ACCESS MENU
#
# This appears ONLY after /hacks
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
# START MESSAGE
# ============================================================

def get_welcome_text(first_name):

    return (
        f"<b>{BOT_NAME}</b>\n\n"
        f"Welcome, <b>{first_name}</b>.\n\n"
        "It's a pleasure to have you here.\n\n"
        "You've reached the official interface. "
        "Take a moment to explore the options below "
        "and discover what is available.\n\n"
        "<b>Welcome aboard.</b>"
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
#
# Access is intentionally available only through this command.
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

    text = (
        f"<b>{BOT_NAME} • HELP</b>\n\n"
        "Use the commands below to navigate the interface.\n\n"

        "<b>/start</b>\n"
        "Open the main welcome screen.\n\n"

        "<b>/hacks</b>\n"
        "Open the private access panel.\n\n"

        "<b>/about</b>\n"
        "Learn more about QRIISHNA."
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
#
# Does not bypass the /hacks flow.
# ============================================================

@bot.message_handler(commands=["file"])
def file_command(message):

    text = (
        f"<b>{BOT_NAME} ACCESS</b>\n\n"
        "The requested resource is available "
        "through the private access panel.\n\n"
        "Use /hacks to continue."
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=back_menu()
    )


# ============================================================
# HELP BUTTON CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "help"
)
def help_callback(call):

    text = (
        f"<b>{BOT_NAME} • HELP</b>\n\n"
        "Use the commands below to navigate the interface.\n\n"

        "<b>/start</b>\n"
        "Open the main welcome screen.\n\n"

        "<b>/hacks</b>\n"
        "Open the private access panel.\n\n"

        "<b>/about</b>\n"
        "Learn more about QRIISHNA."
    )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_menu()
    )


# ============================================================
# ABOUT BUTTON CALLBACK
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
# BACK / HOME CALLBACK
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
# UNKNOWN TEXT / COMMAND
# ============================================================

@bot.message_handler(func=lambda message: True)
def unknown_message(message):

    text = (
        f"<b>{BOT_NAME}</b>\n\n"
        "I couldn't understand that request.\n\n"
        "Use /help to view the available commands."
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

    # Start Flask server for Render
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    print("Flask server      : ONLINE")
    print("Telegram bot      : ONLINE")
    print("Bot name          : QRIISHNA")
    print("----------------------------------------")

    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60
    )
