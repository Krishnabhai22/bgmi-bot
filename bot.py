import os
import threading
import telebot
from telebot import types
from flask import Flask

app = Flask(__name__)

# Telegram Bot Token
TOKEN = os.environ.get("BOT_TOKEN")

# Private channel invite link
CHANNEL_LINK = "https://t.me/+GHjJmfql0o02YWZl"

bot = telebot.TeleBot(TOKEN)


@app.route("/")
def home():
    return "Bot is Alive!"


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


@bot.message_handler(commands=["start"])
def start(message):

    user_name = message.from_user.first_name or "Friend"

    welcome_text = (
        f"🎉 *Welcome to griishnabot!*\n\n"
        f"Hello *{user_name}*, welcome to our bot! 👋\n\n"
        f"📁 Click the button below to access the latest file."
    )

    markup = types.InlineKeyboardMarkup()

    button = types.InlineKeyboardButton(
        "📁 Get File",
        url=CHANNEL_LINK
    )

    markup.add(button)

    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.message_handler(commands=["file", "hacks"])
def send_file_link(message):

    markup = types.InlineKeyboardMarkup()

    button = types.InlineKeyboardButton(
        "📁 Get Latest File",
        url=CHANNEL_LINK
    )

    markup.add(button)

    bot.send_message(
        message.chat.id,
        "📁 Click the button below to access the latest file.",
        reply_markup=markup
    )


if __name__ == "__main__":

    # Start Flask server
    threading.Thread(target=run_flask, daemon=True).start()

    print("Bot successfully started!")

    # Start Telegram bot
    bot.infinity_polling(timeout=60)
