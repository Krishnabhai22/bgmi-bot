import os
import threading
import telebot
from telebot import types
from flask import Flask

# =========================
# CONFIGURATION
# =========================

TOKEN = os.environ.get("BOT_TOKEN")

CHANNEL_LINK = "https://t.me/+GHjJmfql0o02YWZl"

BOT_NAME = "qriishabot"

# =========================
# FLASK APP
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is Alive! ✅"


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# =========================
# TELEGRAM BOT
# =========================

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")


# =========================
# MAIN MENU
# =========================

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)

    latest_file = types.InlineKeyboardButton(
        "📁 Latest File",
        url=CHANNEL_LINK
    )

    help_button = types.InlineKeyboardButton(
        "❓ Help",
        callback_data="help"
    )

    about_button = types.InlineKeyboardButton(
        "ℹ️ About",
        callback_data="about"
    )

    markup.add(latest_file)
    markup.add(help_button, about_button)

    return markup


# =========================
# START COMMAND
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    user_name = message.from_user.first_name or "there"

    welcome_text = (
        f"👋 *Welcome to {BOT_NAME}*\n\n"
        f"Hello *{user_name}*!\n\n"
        "You're now connected to our official bot.\n\n"
        "📌 Use the buttons below to access available "
        "resources or learn more about the bot.\n\n"
        "🔒 *Simple • Fast • Secure*"
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=main_menu()
    )


# =========================
# HELP COMMAND
# =========================

@bot.message_handler(commands=["help"])
def help_command(message):

    help_text = (
        "❓ *Help & Commands*\n\n"
        "Here are the available commands:\n\n"
        "📁 /file — Get the latest file\n"
        "ℹ️ /about — About this bot\n"
        "🏠 /start — Open the main menu\n"
        "❓ /help — Show this help message\n\n"
        "If you need the latest available resource, "
        "use the *Latest File* button below."
    )

    markup = types.InlineKeyboardMarkup()

    back_button = types.InlineKeyboardButton(
        "⬅️ Main Menu",
        callback_data="home"
    )

    markup.add(back_button)

    bot.send_message(
        message.chat.id,
        help_text,
        reply_markup=markup
    )


# =========================
# FILE COMMAND
# =========================

@bot.message_handler(commands=["file"])
def file_command(message):

    file_text = (
        "📁 *Latest File*\n\n"
        "The latest available file can be accessed "
        "using the button below.\n\n"
        "👇 Tap the button to continue."
    )

    markup = types.InlineKeyboardMarkup()

    button = types.InlineKeyboardButton(
        "📁 Get Latest File",
        url=CHANNEL_LINK
    )

    back_button = types.InlineKeyboardButton(
        "⬅️ Main Menu",
        callback_data="home"
    )

    markup.add(button)
    markup.add(back_button)

    bot.send_message(
        message.chat.id,
        file_text,
        reply_markup=markup
    )


# =========================
# ABOUT COMMAND
# =========================

@bot.message_handler(commands=["about"])
def about_command(message):

    about_text = (
        f"ℹ️ *About {BOT_NAME}*\n\n"
        "This bot provides quick access to the latest "
        "available resources.\n\n"
        "⚡ Fast access\n"
        "📁 Latest files\n"
        "🔔 Easy navigation\n\n"
        "Use /start to return to the main menu."
    )

    markup = types.InlineKeyboardMarkup()

    back_button = types.InlineKeyboardButton(
        "⬅️ Main Menu",
        callback_data="home"
    )

    markup.add(back_button)

    bot.send_message(
        message.chat.id,
        about_text,
        reply_markup=markup
    )


# =========================
# BUTTON CALLBACKS
# =========================

@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_callback(call):

    help_text = (
        "❓ *Help & Commands*\n\n"
        "📁 /file — Get the latest file\n"
        "ℹ️ /about — About this bot\n"
        "🏠 /start — Main menu\n"
        "❓ /help — Help menu\n\n"
        "Choose an option below."
    )

    markup = types.InlineKeyboardMarkup(row_width=2)

    file_button = types.InlineKeyboardButton(
        "📁 Latest File",
        url=CHANNEL_LINK
    )

    home_button = types.InlineKeyboardButton(
        "⬅️ Main Menu",
        callback_data="home"
    )

    markup.add(file_button)
    markup.add(home_button)

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        help_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "about")
def about_callback(call):

    about_text = (
        f"ℹ️ *About {BOT_NAME}*\n\n"
        "This bot provides quick and easy access "
        "to the latest available resources.\n\n"
        "⚡ Fast\n"
        "📁 Organized\n"
        "🔒 Simple\n\n"
        "Use the button below to return to the main menu."
    )

    markup = types.InlineKeyboardMarkup()

    home_button = types.InlineKeyboardButton(
        "⬅️ Main Menu",
        callback_data="home"
    )

    markup.add(home_button)

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        about_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "home")
def home_callback(call):

    user_name = call.from_user.first_name or "there"

    welcome_text = (
        f"👋 *Welcome to {BOT_NAME}*\n\n"
        f"Hello *{user_name}*!\n\n"
        "You're now connected to our official bot.\n\n"
        "📌 Choose an option below to continue."
    )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        welcome_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu()
    )


# =========================
# UNKNOWN COMMAND / MESSAGE
# =========================

@bot.message_handler(func=lambda message: True)
def unknown_message(message):

    bot.send_message(
        message.chat.id,
        "⚠️ *I didn't understand that command.*\n\n"
        "Use /help to see the available commands.",
        reply_markup=main_menu()
    )


# =========================
# BOT COMMAND MENU
# =========================

def set_commands():

    commands = [
        types.BotCommand("start", "Open the main menu"),
        types.BotCommand("file", "Get the latest file"),
        types.BotCommand("help", "Show help"),
        types.BotCommand("about", "About the bot"),
    ]

    bot.set_my_commands(commands)


# =========================
# START BOT
# =========================

if __name__ == "__main__":

    set_commands()

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    print("Bot successfully started! ✅")

    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60
    )
