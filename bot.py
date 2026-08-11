import os
import threading
import telebot
from telebot import types
from flask import Flask

# ============================================================
# QRIISHNA BOT — PREMIUM TELEGRAM INTERFACE
# ============================================================

TOKEN = os.environ.get("BOT_TOKEN")

# Your private channel / latest resource link
CHANNEL_LINK = "https://t.me/+GHjJmfql0o02YWZl"

BOT_NAME = "QRIISHNA"

# ============================================================
# FLASK SERVER
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "QRIISHNA is online."


def run_flask():
    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port
    )


# ============================================================
# TELEGRAM BOT
# ============================================================

bot = telebot.TeleBot(
    TOKEN,
    parse_mode="HTML"
)


# ============================================================
# MAIN MENU
# ============================================================

def main_menu():

    markup = types.InlineKeyboardMarkup(row_width=2)

    latest_button = types.InlineKeyboardButton(
        "▣  LATEST RELEASE",
        url=CHANNEL_LINK
    )

    help_button = types.InlineKeyboardButton(
        "⌕  HELP",
        callback_data="help"
    )

    about_button = types.InlineKeyboardButton(
        "ⓘ  ABOUT",
        callback_data="about"
    )

    markup.add(latest_button)
    markup.add(help_button, about_button)

    return markup


# ============================================================
# START
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):

    user_name = message.from_user.first_name or "there"

    text = (
        f"<b>{BOT_NAME}</b>\n\n"
        f"Hello, <b>{user_name}</b>.\n\n"
        "Your access panel is ready.\n\n"
        "Select an option below to continue."
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )


# ============================================================
# HELP
# ============================================================

@bot.message_handler(commands=["help"])
def help_command(message):

    text = (
        "<b>HELP</b>\n\n"
        "Use the options below to navigate the bot.\n\n"
        "<b>/start</b>\n"
        "Open the main interface.\n\n"
        "<b>/file</b>\n"
        "Open the latest available release.\n\n"
        "<b>/about</b>\n"
        "View information about this service."
    )

    markup = types.InlineKeyboardMarkup(row_width=2)

    latest_button = types.InlineKeyboardButton(
        "▣  LATEST RELEASE",
        url=CHANNEL_LINK
    )

    back_button = types.InlineKeyboardButton(
        "‹  BACK",
        callback_data="home"
    )

    markup.add(latest_button)
    markup.add(back_button)

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup
    )


# ============================================================
# FILE
# ============================================================

@bot.message_handler(commands=["file"])
def file_command(message):

    text = (
        "<b>LATEST RELEASE</b>\n\n"
        "The latest release is available through "
        "the secure access point below.\n\n"
        "Tap the button to continue."
    )

    markup = types.InlineKeyboardMarkup()

    latest_button = types.InlineKeyboardButton(
        "▣  OPEN LATEST RELEASE",
        url=CHANNEL_LINK
    )

    back_button = types.InlineKeyboardButton(
        "‹  BACK",
        callback_data="home"
    )

    markup.add(latest_button)
    markup.add(back_button)

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup
    )


# ============================================================
# ABOUT
# ============================================================

@bot.message_handler(commands=["about"])
def about_command(message):

    text = (
        f"<b>{BOT_NAME}</b>\n\n"
        "A private access interface designed to provide "
        "a clean and direct way to reach the latest available "
        "resources.\n\n"
        "<b>Version</b>  •  1.0\n"
        "<b>Status</b>   •  Online"
    )

    markup = types.InlineKeyboardMarkup()

    back_button = types.InlineKeyboardButton(
        "‹  BACK",
        callback_data="home"
    )

    markup.add(back_button)

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup
    )


# ============================================================
# HELP BUTTON
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_callback(call):

    text = (
        "<b>HELP</b>\n\n"
        "Use the options below to navigate the bot.\n\n"
        "<b>/start</b>\n"
        "Open the main interface.\n\n"
        "<b>/file</b>\n"
        "Open the latest available release.\n\n"
        "<b>/about</b>\n"
        "View information about this service."
    )

    markup = types.InlineKeyboardMarkup(row_width=2)

    latest_button = types.InlineKeyboardButton(
        "▣  LATEST RELEASE",
        url=CHANNEL_LINK
    )

    back_button = types.InlineKeyboardButton(
        "‹  BACK",
        callback_data="home"
    )

    markup.add(latest_button)
    markup.add(back_button)

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


# ============================================================
# ABOUT BUTTON
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "about")
def about_callback(call):

    text = (
        f"<b>{BOT_NAME}</b>\n\n"
        "A private access interface designed to provide "
        "a clean and direct way to reach the latest available "
        "resources.\n\n"
        "<b>Version</b>  •  1.0\n"
        "<b>Status</b>   •  Online"
    )

    markup = types.InlineKeyboardMarkup()

    back_button = types.InlineKeyboardButton(
        "‹  BACK",
        callback_data="home"
    )

    markup.add(back_button)

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


# ============================================================
# HOME BUTTON
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "home")
def home_callback(call):

    user_name = call.from_user.first_name or "there"

    text = (
        f"<b>{BOT_NAME}</b>\n\n"
        f"Hello, <b>{user_name}</b>.\n\n"
        "Your access panel is ready.\n\n"
        "Select an option below to continue."
    )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu()
    )


# ============================================================
# UNKNOWN COMMAND / MESSAGE
# ============================================================

@bot.message_handler(func=lambda message: True)
def unknown_message(message):

    text = (
        f"<b>{BOT_NAME}</b>\n\n"
        "I couldn't recognize that request.\n\n"
        "Use <b>/help</b> to see the available commands."
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )


# ============================================================
# TELEGRAM COMMAND MENU
# ============================================================

def set_commands():

    commands = [
        types.BotCommand(
            "start",
            "Open main interface"
        ),
        types.BotCommand(
            "file",
            "Open latest release"
        ),
        types.BotCommand(
            "help",
            "View help"
        ),
        types.BotCommand(
            "about",
            "About QRIISHNA"
        )
    ]

    bot.set_my_commands(commands)


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    # Set Telegram command menu
    set_commands()

    # Start Flask server for Render
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    print("======================================")
    print("       QRIISHNA BOT IS ONLINE")
    print("======================================")

    # Start Telegram bot
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60
    )
