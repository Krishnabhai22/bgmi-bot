import os
import re
import sqlite3
import threading
import html
import time
import uuid
from datetime import datetime, timedelta

import telebot
from telebot import types
from flask import Flask


# ============================================================
# QRISHNA • ENTERPRISE VIP TELEGRAM BOT
# ============================================================

TOKEN = os.environ.get("BOT_TOKEN")

BOT_NAME = "QRISHNA VIP"
BOT_VERSION = "10.0 ULTRA ENTERPRISE"

CHANNEL_LINK = "https://t.me/+GHjJmfql0o02YWZl"
ADMIN_CONTACT = "https://t.me/qrishna"

# ------------------------------------------------------------
# PAYMENT CONFIGURATION
# ------------------------------------------------------------
UPI_ID = "lucky25october@okaxis"
PAYEE_NAME = "Krishna Singh"

OWNER_IDS = {
    1332494807
}

DB_FILE = "warnings.db"

app = Flask(__name__)
db_lock = threading.Lock()
start_time = time.time()


# ============================================================
# TOKEN VALIDATION & BOT INITIALIZATION
# ============================================================

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is missing."
    )

bot = telebot.TeleBot(
    TOKEN,
    parse_mode=None
)


# ============================================================
# AUTO DELETE UTILITY
# ============================================================

def auto_delete_message(chat_id, message_id, delay=45):
    def delete_job():
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

    timer = threading.Timer(delay, delete_job)
    timer.daemon = True
    timer.start()


def send_auto_delete_message(chat_id, text, reply_markup=None, delay=45):
    try:
        sent_msg = bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        if sent_msg:
            auto_delete_message(chat_id, sent_msg.message_id, delay)
        return sent_msg
    except Exception as e:
        print(f"Error sending message: {e}")
        return None


# ============================================================
# FLASK KEEP-ALIVE SERVER
# ============================================================

@app.route("/")
def home():
    return "QRISHNA VIP AUTOMATED SECURE ENGINE • ONLINE"


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(
        host="0.0.0.0",
        port=port
    )


# ============================================================
# DATABASE MANAGEMENT
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vip_keys (
                key_code TEXT PRIMARY KEY,
                duration_days INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                is_used INTEGER DEFAULT 0,
                used_by INTEGER,
                used_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                user_id INTEGER PRIMARY KEY,
                expiry_date TEXT NOT NULL,
                active_key TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                utr TEXT PRIMARY KEY,
                user_id INTEGER,
                pack_name TEXT,
                amount TEXT,
                status TEXT,
                submitted_at TEXT
            )
        """)

        connection.commit()
        connection.close()


def register_user(user_id, first_name):
    with db_lock:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO bot_users (user_id, first_name)
            VALUES (?, ?)
        """, (user_id, first_name))
        connection.commit()
        connection.close()


def get_total_users():
    with db_lock:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bot_users")
        count = cursor.fetchone()[0]
        connection.close()
        return count


# ============================================================
# KEY GENERATOR & REDEMPTION ENGINE
# ============================================================

def generate_key_code(days=90):
    key = f"QRISHNA-VIP-{days}D-" + str(uuid.uuid4()).upper()[:8]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with db_lock:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO vip_keys (key_code, duration_days, created_at)
            VALUES (?, ?, ?)
        """, (key, days, now_str))
        connection.commit()
        connection.close()

    return key


def redeem_vip_key(user_id, key_code):
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    with db_lock:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT duration_days, is_used FROM vip_keys WHERE key_code = ?", (key_code,))
        row = cursor.fetchone()

        if not row:
            connection.close()
            return False, "Invalid license key code. Please check and try again."

        days, is_used = row
        if is_used:
            connection.close()
            return False, "This license key has already been redeemed."

        cursor.execute("""
            UPDATE vip_keys
            SET is_used = 1, used_by = ?, used_at = ?
            WHERE key_code = ?
        """, (user_id, now_str, key_code))

        cursor.execute("SELECT expiry_date FROM user_subscriptions WHERE user_id = ?", (user_id,))
        sub_row = cursor.fetchone()

        if sub_row:
            current_expiry = datetime.strptime(sub_row[0], "%Y-%m-%d %H:%M:%S")
            start_point = max(now, current_expiry)
        else:
            start_point = now

        new_expiry = start_point + timedelta(days=days)
        expiry_str = new_expiry.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT OR REPLACE INTO user_subscriptions (user_id, expiry_date, active_key)
            VALUES (?, ?, ?)
        """, (user_id, expiry_str, key_code))

        connection.commit()
        connection.close()

    return True, expiry_str


def get_user_subscription(user_id):
    with db_lock:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT expiry_date, active_key FROM user_subscriptions WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        connection.close()

    if not row:
        return None

    expiry_dt = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
    if expiry_dt < datetime.now():
        return None

    return {"expiry": row[0], "key": row[1]}


# ============================================================
# WARNINGS SYSTEM & BAD WORD FILTER
# ============================================================

def add_warning(chat_id, user_id):
    with db_lock:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO warnings (chat_id, user_id, warning_count)
            VALUES (?, ?, 1)
            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET warning_count = warning_count + 1
            """,
            (chat_id, user_id)
        )
        connection.commit()

        cursor.execute(
            """
            SELECT warning_count FROM warnings
            WHERE chat_id = ? AND user_id = ?
            """,
            (chat_id, user_id)
        )
        result = cursor.fetchone()
        connection.close()

    return result[0] if result else 1


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
            INSERT OR IGNORE INTO welcomed_users (chat_id, user_id)
            VALUES (?, ?)
            """,
            (chat_id, user_id)
        )
        is_first_message = cursor.rowcount == 1
        connection.commit()
        connection.close()

    if not is_first_message:
        return

    name = html.escape(user.first_name or "User")
    text = (
        "<b>✦ QRISHNA ENTERPRISE</b>\n\n"
        f"Welcome <b>{name}</b> to the BGMI Resource Portal.\n"
        "Execute /start to initialize command center."
    )

    send_auto_delete_message(chat_id, text)


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

BAD_WORDS = sorted(set(BAD_WORDS), key=len, reverse=True)


def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    replacements = {
        "@": "a", "4": "a", "0": "o", "1": "i",
        "!": "i", "$": "s", "3": "e", "5": "s"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[\u200b-\u200f\uFEFF]", "", text)
    text = re.sub(r"[^a-zA-Z\u0900-\u097F]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contains_bad_language(text):
    normalized = normalize_text(text)
    if not normalized:
        return False

    for word in BAD_WORDS:
        if re.search(r"(?<![a-zA-Z])" + re.escape(word) + r"(?![a-zA-Z])", normalized):
            return True

    compact = re.sub(r"[^a-zA-Z\u0900-\u097F]", "", normalized)
    for word in BAD_WORDS:
        compact_word = re.sub(r"[^a-zA-Z\u0900-\u097F]", "", word)
        if len(compact_word) >= 4 and compact_word in compact:
            return True

    return False


def warning_text(user, number):
    name = html.escape(user.first_name or "User")
    return (
        "<b>SYSTEM WARNING</b>\n"
        "────────────────────────\n"
        f"Target User: <b>{name}</b>\n"
        "Infraction: Inappropriate Language Detected\n"
        f"Warning Level: <b>{number} / 3</b>\n\n"
        "<i>Please maintain standard decorum in the portal.</i>"
    )


def banned_text(user):
    name = html.escape(user.first_name or "User")
    return (
        "<b>USER BANNED</b>\n"
        "────────────────────────\n"
        f"User: <b>{name}</b>\n"
        "Reason: Exceeded Maximum Warnings (3/3)\n\n"
        "<i>Access to community resources has been revoked.</i>"
    )


# ============================================================
# UI MENUS & FORMATTED TEXTS
# ============================================================

def start_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("◈ DOWNLOAD HUB", callback_data="btn_files"),
        types.InlineKeyboardButton("◈ SETUP GUIDE", callback_data="btn_tutorial")
    )
    markup.add(
        types.InlineKeyboardButton("◈ VIP PASS", callback_data="btn_premium"),
        types.InlineKeyboardButton("◈ SUPPORT DESK", callback_data="btn_support")
    )
    markup.add(
        types.InlineKeyboardButton("◈ SYSTEM LOGS", callback_data="btn_updates")
    )
    return markup


def get_start_text():
    total_users = get_total_users()
    return (
        "<b>QRISHNA • VIP COMMAND CENTER</b>\n"
        "────────────────────────\n"
        "Welcome to the official <b>BGMI Enterprise Portal</b>.\n\n"
        "● <b>System Status:</b> ONLINE\n"
        f"● <b>Engine Core:</b> v{BOT_VERSION}\n"
        f"● <b>Active Users:</b> {total_users}\n"
        "● <b>Security Core:</b> Anti-Ban Active\n\n"
        "<i>Select an option from the menu below to proceed.</i>"
    )


def get_files_text():
    return (
        "<b>BGMI ENTERPRISE DOWNLOAD PORTAL</b>\n"
        "────────────────────────\n"
        "Fetch verified, anti-ban game resources:\n\n"
        "◆ <b>90 FPS + Ultra Smooth Config</b>\n"
        "◆ <b>Zero Recoil & Aim Assist Pack</b>\n"
        "◆ <b>iPad View Ultra Wide Pack</b>\n"
        "◆ <b>LagFix Performance Engine</b>\n\n"
        "<i>Tap below to access the secure download channel.</i>"
    )


def files_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("◇ OPEN DOWNLOAD CHANNEL", url=CHANNEL_LINK),
        types.InlineKeyboardButton("‹ DASHBOARD", callback_data="home")
    )
    return markup


def get_updates_text():
    uptime = int(time.time() - start_time) // 3600
    return (
        "<b>SYSTEM LOGS & METRICS</b>\n"
        "────────────────────────\n"
        f"● <b>Engine Version:</b> v{BOT_VERSION}\n"
        f"● <b>Server Uptime:</b> {uptime} Hours\n"
        "● <b>Latency:</b> 24ms (Optimal)\n\n"
        "<b>Patch Notes:</b>\n"
        "├ Optimized for latest BGMI update\n"
        "├ Enterprise Payment Verification Engine active\n"
        "└ Instant Private License Delivery online"
    )


def get_premium_text():
    return (
        "<b>VIP ACCESS PASS</b>\n"
        "────────────────────────\n"
        "Unlock elite configurations and priority bandwidth:\n\n"
        "◆ Direct High-Speed CDN Download Access\n"
        "◆ Exclusive Anti-Ban Security Engine\n"
        "◆ Instant License Key Activation\n"
        "◆ 24/7 Priority Support Desk\n\n"
        "<i>Use /buy to view packages or /redeem to activate key.</i>"
    )


def get_hooks_text():
    return (
        "<b>VIP CATALOGUE & STORE PORTAL</b>\n"
        "────────────────────────────────────────\n"
        "Select a package tier below to view full specifications:\n\n"
        "<b>01. FULL VIP ENTERPRISE PACK</b>\n"
        "└ Price: <b>INR 2,500</b> | Duration: <b>90 Days</b>\n\n"
        "<b>02. PRO COMBAT PACK</b>\n"
        "└ Price: <b>INR 1,500</b> | Duration: <b>90 Days</b>\n\n"
        "<b>03. YOUTUBER STREAMER PACK</b>\n"
        "└ Price: <b>INR 750</b> | Duration: <b>90 Days</b>\n\n"
        "────────────────────────────────────────\n"
        "<i>Tap 'VIEW DETAILS' to review features before buying.</i>"
    )


def hooks_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("◇ VIEW DETAILS: ENTERPRISE PACK (₹2,500)", callback_data="det_p1"),
        types.InlineKeyboardButton("◇ VIEW DETAILS: PRO COMBAT PACK (₹1,500)", callback_data="det_p2"),
        types.InlineKeyboardButton("◇ VIEW DETAILS: YOUTUBER PACK (₹750)", callback_data="det_p3"),
        types.InlineKeyboardButton("‹ DASHBOARD", callback_data="home")
    )
    return markup


def get_details_p1():
    return (
        "<b>PACKAGE DETAILS: FULL VIP ENTERPRISE PACK</b>\n"
        "────────────────────────────────────────\n"
        "● <b>Price:</b> INR 2,500\n"
        "● <b>Validity:</b> 90 Days (3 Months)\n"
        "● <b>Security Level:</b> Maximum Protection (100% Main ID Safe)\n\n"
        "<b>INCLUDED FEATURES:</b>\n"
        "├ High-Quality Magic Bullet Configuration\n"
        "├ Precision Lock Aimbot Engine\n"
        "├ Full ESP Wallhack Tracking System\n"
        "└ Anti-Cheat Bypass Core\n\n"
        "────────────────────────────────────────\n"
        "<i>Tap below to proceed with the payment invoice.</i>"
    )


def get_details_p2():
    return (
        "<b>PACKAGE DETAILS: PRO COMBAT PACK</b>\n"
        "────────────────────────────────────────\n"
        "● <b>Price:</b> INR 1,500\n"
        "● <b>Validity:</b> 90 Days (3 Months)\n"
        "● <b>Security Level:</b> High Protection (Main ID Safe)\n\n"
        "<b>INCLUDED FEATURES:</b>\n"
        "├ Magic Bullet Configuration\n"
        "├ Precision Aimbot System\n"
        "└ Full ESP Wallhack Tracking\n\n"
        "<b>RULES & REGULATIONS:</b>\n"
        "└ <b>8–10 Kills Limit Per Match</b> (Strictly enforce to avoid mass reports)\n\n"
        "────────────────────────────────────────\n"
        "<i>Tap below to proceed with the payment invoice.</i>"
    )


def get_details_p3():
    return (
        "<b>PACKAGE DETAILS: YOUTUBER STREAMER PACK</b>\n"
        "────────────────────────────────────────\n"
        "● <b>Price:</b> INR 750\n"
        "● <b>Validity:</b> 90 Days (3 Months)\n"
        "● <b>Security Level:</b> 100% Stream-Proof & Fully Safe\n\n"
        "<b>INCLUDED FEATURES:</b>\n"
        "├ 10% Soft Magic Bullet Module\n"
        "├ 10% Assist Aimbot Module\n"
        "└ 30% Recoil Reduction System\n\n"
        "<b>SPECIAL NOTES:</b>\n"
        "└ No ESP included. No kill limits. Designed for legit gameplay and content creation.\n\n"
        "────────────────────────────────────────\n"
        "<i>Tap below to proceed with the payment invoice.</i>"
    )


def details_menu(pack_code):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("◇ PROCEED TO PAY", callback_data=f"pay_{pack_code}"),
        types.InlineKeyboardButton("‹ BACK TO PACKAGES", callback_data="trigger_buy"),
        types.InlineKeyboardButton("‹ DASHBOARD", callback_data="home")
    )
    return markup


def payment_invoice_menu(pack_code):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ SUBMIT UTR / TRANSACTION ID", callback_data=f"sub_utr_{pack_code}"),
        types.InlineKeyboardButton("◇ SEND SCREENSHOT TO ADMIN", url=ADMIN_CONTACT),
        types.InlineKeyboardButton("‹ BACK TO PACKAGES", callback_data="trigger_buy"),
        types.InlineKeyboardButton("‹ DASHBOARD", callback_data="home")
    )
    return markup


def premium_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("◇ BUY VIP PASS", callback_data="trigger_buy"),
        types.InlineKeyboardButton("◇ CONTACT ADMIN", url=ADMIN_CONTACT),
        types.InlineKeyboardButton("‹ DASHBOARD", callback_data="home")
    )
    return markup


def get_access_text(user_id, first_name):
    name = html.escape(first_name or "User")
    sub = get_user_subscription(user_id)

    if sub:
        return (
            "<b>VIP USER STATUS & LICENSE</b>\n"
            "────────────────────────\n"
            f"User Name: <b>{name}</b>\n"
            f"Account ID: <code>{user_id}</code>\n\n"
            "<b>LICENSE DETAILS</b>\n"
            "├ Tier: <b>ACTIVE VIP MEMBER</b>\n"
            f"├ License Key: <code>{sub['key']}</code>\n"
            "├ Protection: <b>ACTIVE (ANTI-BAN)</b>\n"
            f"└ Expiry Date: <b>{sub['expiry']}</b>\n\n"
            "<i>Full-speed server downloads and premium resources active.</i>"
        )
    else:
        return (
            "<b>VIP USER STATUS & LICENSE</b>\n"
            "────────────────────────\n"
            f"User Name: <b>{name}</b>\n"
            f"Account ID: <code>{user_id}</code>\n\n"
            "<b>LICENSE DETAILS</b>\n"
            "├ Tier: <b>FREE MEMBER</b>\n"
            "└ Status: <b>NO ACTIVE VIP PASS</b>\n\n"
            "<i>Use /buy to purchase a license or /redeem to activate your key.</i>"
        )


def get_support_text():
    return (
        "<b>SUPPORT DESK</b>\n"
        "────────────────────────\n"
        "Need technical assistance with file extraction or installation?\n\n"
        "<i>Tap below to establish a direct connection with Support.</i>"
    )


def support_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("◇ CONTACT SUPPORT", url=ADMIN_CONTACT),
        types.InlineKeyboardButton("‹ DASHBOARD", callback_data="home")
    )
    return markup


def back_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("‹ DASHBOARD", callback_data="home"))
    return markup


# ============================================================
# INSTALLATION GUIDE ENGINE
# ============================================================

def language_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("ENGLISH", callback_data="guide_en"),
        types.InlineKeyboardButton("HINGLISH", callback_data="guide_hi")
    )
    markup.add(types.InlineKeyboardButton("‹ DASHBOARD", callback_data="home"))
    return markup


def get_language_text():
    return (
        "<b>INSTALLATION GUIDE ENGINE</b>\n"
        "────────────────────────\n"
        "Select your preferred language for setup steps:"
    )


ENGLISH_GUIDE = [
    "<b>STEP 01</b>\n\nDownload the required package from our official channel.",
    "<b>STEP 02</b>\n\nOpen ZArchiver or your system File Manager.",
    "<b>STEP 03</b>\n\nNavigate to the <code>/Download</code> directory.",
    "<b>STEP 04</b>\n\nExtract the downloaded <code>.zip</code> or <code>.pak</code> file.",
    "<b>STEP 05</b>\n\nVerify extracted files and copy required resources.",
    "<b>STEP 06</b>\n\nPaste files into destination:\n<code>Android/data/com.pubg.imobile/files</code>",
    "<b>STEP 07</b>\n\nRestart your device and launch BGMI."
]

HINGLISH_GUIDE = [
    "<b>STEP 01</b>\n\nOfficial channel se file download karein.",
    "<b>STEP 02</b>\n\nPhone me ZArchiver app open karein.",
    "<b>STEP 03</b>\n\nNavigate to the <code>/Download</code> directory.",
    "<b>STEP 04</b>\n\nDownloaded file ko extract karein.",
    "<b>STEP 05</b>\n\nExtracted folder ki files copy kar lein.",
    "<b>STEP 06</b>\n\nInhe is path par paste karein:\n<code>Android/data/com.pubg.imobile/files</code>",
    "<b>STEP 07</b>\n\nPhone restart karein aur game enjoy karein!"
]


def get_guide_page(language, page):
    pages = ENGLISH_GUIDE if language == "en" else HINGLISH_GUIDE
    page = max(0, min(page, len(pages) - 1))
    return f"<b>INSTALLATION GUIDE ({language.upper()})</b>\n────────────────────────\n" + pages[page]


def guide_menu(language, page):
    pages = ENGLISH_GUIDE if language == "en" else HINGLISH_GUIDE
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    if page > 0:
        btns.append(types.InlineKeyboardButton("‹ PREVIOUS", callback_data=f"guide_{language}_{page - 1}"))
    if page < len(pages) - 1:
        btns.append(types.InlineKeyboardButton("NEXT ›", callback_data=f"guide_{language}_{page + 1}"))
    if btns:
        markup.add(*btns)
    markup.add(types.InlineKeyboardButton("‹ DASHBOARD", callback_data="home"))
    return markup


# ============================================================
# COMMAND HANDLERS & VIP FILE GUARDIAN
# ============================================================

@bot.message_handler(commands=["start", "dashboard"])
def start(message):
    if message.from_user:
        register_user(message.from_user.id, message.from_user.first_name)
    send_auto_delete_message(
        message.chat.id,
        get_start_text(),
        reply_markup=start_menu()
    )


def handle_files_access(user_id, chat_id, message_id=None):
    sub = get_user_subscription(user_id)

    # Clean Premium Restricted UI
    if not sub:
        restricted_text = (
            "<b>🔒 ACCESS RESTRICTED • VIP REQUIRED</b>\n"
            "────────────────────────────────────────\n"
            "An active <b>VIP Subscription</b> is required to access the Enterprise Download Portal.\n\n"
            "<b>AVAILABLE ACTIONS:</b>\n"
            "├ Purchase License Pass: <code>/buy</code>\n"
            "└ Redeem License Key: <code>/redeem KEY_CODE</code>\n"
            "────────────────────────────────────────\n"
            "<i>High-speed CDN servers and anti-ban resources are reserved for active VIP members.</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("◇ BUY VIP PASS", callback_data="trigger_buy"),
            types.InlineKeyboardButton("‹ DASHBOARD", callback_data="home")
        )

        if message_id:
            try:
                bot.edit_message_text(restricted_text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
            except Exception:
                send_auto_delete_message(chat_id, restricted_text, reply_markup=markup)
        else:
            send_auto_delete_message(chat_id, restricted_text, reply_markup=markup)
        return

    # Authorized VIP User Access
    if message_id:
        try:
            bot.edit_message_text(get_files_text(), chat_id, message_id, reply_markup=files_menu(), parse_mode="HTML")
        except Exception:
            send_auto_delete_message(chat_id, get_files_text(), reply_markup=files_menu())
    else:
        send_auto_delete_message(chat_id, get_files_text(), reply_markup=files_menu())


@bot.message_handler(commands=["files"])
def files_command(message):
    handle_files_access(message.from_user.id, message.chat.id)


@bot.message_handler(commands=["updates"])
def updates_command(message):
    send_auto_delete_message(
        message.chat.id,
        get_updates_text(),
        reply_markup=back_menu()
    )


@bot.message_handler(commands=["tutorial"])
def tutorial_command(message):
    send_auto_delete_message(
        message.chat.id,
        get_language_text(),
        reply_markup=language_menu()
    )


@bot.message_handler(commands=["premium"])
def premium_command(message):
    send_auto_delete_message(
        message.chat.id,
        get_premium_text(),
        reply_markup=premium_menu()
    )


@bot.message_handler(commands=["buy", "pay"])
def buy_command(message):
    send_auto_delete_message(
        message.chat.id,
        get_hooks_text(),
        reply_markup=hooks_menu(),
        delay=60
    )


@bot.message_handler(commands=["access"])
def access_command(message):
    user = message.from_user
    send_auto_delete_message(
        message.chat.id,
        get_access_text(user.id, user.first_name),
        reply_markup=back_menu()
    )


@bot.message_handler(commands=["support"])
def support_command(message):
    send_auto_delete_message(
        message.chat.id,
        get_support_text(),
        reply_markup=support_menu()
    )


# ------------------------------------------------------------
# USER ID PROFILE CHECKER (HIDDEN MANUAL COMMAND)
# ------------------------------------------------------------

@bot.message_handler(commands=["userid", "id", "myid"])
def userid_command(message):
    user = message.from_user
    if not user:
        return

    full_name = html.escape(user.first_name or "")
    if user.last_name:
        full_name += f" {html.escape(user.last_name)}"

    username = f"@{user.username}" if user.username else "Not Set"
    user_id = user.id

    sub = get_user_subscription(user_id)
    if sub:
        account_tier = "<b>ACTIVE VIP MEMBER</b>"
        expiry_info = f"\n● <b>VIP Expiry Date:</b> {sub['expiry']}"
    else:
        account_tier = "<b>FREE MEMBER</b>"
        expiry_info = ""

    id_info_text = (
        "<b>🪪 TELEGRAM USER PROFILE METRICS</b>\n"
        "────────────────────────────────────────\n"
        f"● <b>Full Name:</b> {full_name}\n"
        f"● <b>Username:</b> {username}\n"
        f"● <b>Telegram User ID:</b> <code>{user_id}</code>\n"
        f"● <b>Account Status:</b> {account_tier}"
        f"{expiry_info}\n"
        "────────────────────────────────────────\n"
        "<i>Tap the User ID code above to copy it to clipboard.</i>"
    )

    send_auto_delete_message(
        message.chat.id,
        id_info_text,
        reply_markup=back_menu(),
        delay=60
    )


# ------------------------------------------------------------
# KEY REDEMPTION ENGINE
# ------------------------------------------------------------

@bot.message_handler(commands=["redeem"])
def redeem_command(message):
    parts = message.text.strip().split()

    if len(parts) < 2:
        help_text = (
            "<b>🔑 LICENSE REDEMPTION GUIDE</b>\n"
            "────────────────────────────────────────\n"
            "No license key was provided. To activate your pass, send the command using the syntax below:\n\n"
            "👉 <code>/redeem KEY_CODE</code>\n\n"
            "<b>EXAMPLE:</b>\n"
            "<code>/redeem QRISHNA-VIP-90D-A1B2C3D4</code>\n"
            "────────────────────────────────────────\n"
            "<i>Enter the VIP key provided upon payment approval to unlock full access.</i>"
        )
        send_auto_delete_message(
            message.chat.id,
            help_text,
            reply_markup=back_menu(),
            delay=45
        )
        return

    key_code = parts[1].strip()
    success, result = redeem_vip_key(message.from_user.id, key_code)

    if success:
        text = (
            "<b>🎉 VIP LICENSE ACTIVATED SUCCESSFULLY</b>\n"
            "────────────────────────────────────────\n"
            f"● <b>Activated Key:</b> <code>{key_code}</code>\n"
            f"● <b>Valid Until:</b> <b>{result}</b>\n\n"
            "────────────────────────────────────────\n"
            "<i>Your VIP Access is now active. Use /access to review your subscription.</i>"
        )
    else:
        text = (
            "<b>❌ REDEMPTION FAILED</b>\n"
            "────────────────────────────────────────\n"
            f"Reason: <b>{result}</b>\n\n"
            "<i>Verify your key code or contact support desk for assistance.</i>"
        )

    send_auto_delete_message(message.chat.id, text, reply_markup=back_menu(), delay=60)


# ------------------------------------------------------------
# FULL ADMIN SECRET COMMANDS
# ------------------------------------------------------------

@bot.message_handler(commands=["genkey"])
def genkey_command(message):
    if message.from_user.id not in OWNER_IDS:
        return

    parts = message.text.strip().split()
    days = 90
    if len(parts) > 1 and parts[1].isdigit():
        days = int(parts[1])

    new_key = generate_key_code(days)
    msg = (
        "<b>🔑 NEW VIP KEY GENERATED</b>\n"
        "────────────────────────\n"
        f"Key Code: <code>{new_key}</code>\n"
        f"Validity: <b>{days} Days</b>\n\n"
        "<i>Send this key to user for /redeem.</i>"
    )
    bot.reply_to(message, msg, parse_mode="HTML")


@bot.message_handler(commands=["resetvip"])
def resetvip_command(message):
    if message.from_user.id not in OWNER_IDS:
        return

    parts = message.text.strip().split()
    target_id = message.from_user.id

    if len(parts) > 1 and parts[1].isdigit():
        target_id = int(parts[1])

    with db_lock:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM user_subscriptions WHERE user_id = ?", (target_id,))
        connection.commit()
        connection.close()

    send_auto_delete_message(
        message.chat.id,
        f"<b>✅ VIP STATUS RESET SUCCESS</b>\n────────────────────────\nUser ID <code>{target_id}</code> is now reset to <b>FREE MEMBER</b>.",
        delay=30
    )


@bot.message_handler(commands=["broadcast"])
def broadcast_command(message):
    if message.from_user.id not in OWNER_IDS:
        return

    with db_lock:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM bot_users")
        users = cursor.fetchall()
        connection.close()

    success, failed = 0, 0
    for u in users:
        try:
            bot.send_message(u[0], f"<b>📢 SYSTEM ANNOUNCEMENT</b>\n────────────────────────\n{text_to_send}", parse_mode="HTML")
            success += 1
            time.sleep(0.05)
        except Exception:
            failed += 1

    bot.reply_to(message, f"<b>📢 Broadcast Complete!</b>\n✅ Delivered: {success}\n❌ Failed (Blocked): {failed}", parse_mode="HTML")


@bot.message_handler(commands=["stats"])
def stats_command(message):
    if message.from_user.id not in OWNER_IDS:
        return

    with db_lock:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bot_users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM user_subscriptions WHERE datetime(expiry_date) > datetime('now')")
        active_vips = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM vip_keys")
        total_keys = cursor.fetchone()[0]
        connection.close()

    msg = (
        "<b>📊 QRISHNA VIP BUSINESS METRICS</b>\n"
        "────────────────────────\n"
        f"● <b>Total Registered Users:</b> {total_users}\n"
        f"● <b>Active VIP Members:</b> {active_vips}\n"
        f"● <b>Total VIP Keys Created:</b> {total_keys}\n"
    )
    bot.reply_to(message, msg, parse_mode="HTML")


@bot.message_handler(commands=["revoke"])
def revoke_key_command(message):
    if message.from_user.id not in OWNER_IDS:
        return

    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: <code>/revoke KEY_CODE</code>", parse_mode="HTML")
        return

    key_code = parts[1].strip()
    with db_lock:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE vip_keys SET is_used = 1 WHERE key_code = ?", (key_code,))
        affected = cursor.rowcount
        connection.commit()
        connection.close()

    if affected > 0:
        bot.reply_to(message, f"<b>✅ Key <code>{key_code}</code> Has Been Revoked/Disabled!</b>", parse_mode="HTML")
    else:
        bot.reply_to(message, "Key not found.", parse_mode="HTML")


@bot.message_handler(commands=["keys"])
def list_keys_command(message):
    if message.from_user.id not in OWNER_IDS:
        return

    with db_lock:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT key_code, duration_days, is_used FROM vip_keys ORDER BY created_at DESC LIMIT 10")
        rows = cursor.fetchall()
        connection.close()

    if not rows:
        bot.reply_to(message, "No keys found in database.")
        return

    res = "<b>🔑 RECENT VIP KEYS LOG</b>\n────────────────────────\n"
    for r in rows:
        st = "USED" if r[2] else "ACTIVE"
        res += f"• <code>{r[0]}</code> | {r[1]}D | {st}\n"

    bot.reply_to(message, res, parse_mode="HTML")


# ============================================================
# CALLBACK QUERY HANDLERS
# ============================================================

user_utr_states = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("det_"))
def process_details_selection(call):
    try:
        bot.answer_callback_query(call.id)
        if call.data == "det_p1":
            text, code = get_details_p1(), "p1"
        elif call.data == "det_p2":
            text, code = get_details_p2(), "p2"
        elif call.data == "det_p3":
            text, code = get_details_p3(), "p3"
        else:
            return

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=details_menu(code),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Details error: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def process_payment_redirection(call):
    try:
        bot.answer_callback_query(call.id)

        if call.data == "pay_p1":
            pack_name, amount, code = "FULL VIP ENTERPRISE PACK", "2500", "p1"
        elif call.data == "pay_p2":
            pack_name, amount, code = "PRO COMBAT PACK", "1500", "p2"
        elif call.data == "pay_p3":
            pack_name, amount, code = "YOUTUBER STREAMER PACK", "750", "p3"
        else:
            return

        caption_text = (
            "<b>OFFICIAL INVOICE & GATEWAY</b>\n"
            "────────────────────────────────────────\n"
            f"Selected Package: <b>{pack_name}</b>\n"
            f"Amount Payable: <code>INR {amount}</code>\n"
            f"Merchant UPI ID: <code>{UPI_ID}</code> <i>(Tap to copy)</i>\n\n"
            "<b>PAYMENT INSTRUCTIONS:</b>\n"
            "1. Scan the Google Pay QR code above OR copy the UPI ID.\n"
            "2. Complete the transfer via GPay, PhonePe, or Paytm.\n"
            "3. Tap 'SUBMIT UTR' below and enter your 12-digit UTR/Txn ID."
        )

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

        markup = payment_invoice_menu(code)

        if os.path.exists("qr.png"):
            try:
                with open("qr.png", "rb") as photo:
                    sent_msg = bot.send_photo(
                        chat_id=call.message.chat.id,
                        photo=photo,
                        caption=caption_text,
                        parse_mode="HTML",
                        reply_markup=markup
                    )
                if sent_msg:
                    auto_delete_message(call.message.chat.id, sent_msg.message_id, delay=60)
            except Exception as img_err:
                print(f"Image send error, falling back to text: {img_err}")
                send_auto_delete_message(
                    call.message.chat.id,
                    caption_text,
                    reply_markup=markup,
                    delay=60
                )
        else:
            send_auto_delete_message(
                call.message.chat.id,
                caption_text,
                reply_markup=markup,
                delay=60
            )

    except Exception as e:
        print(f"Payment error: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_utr_"))
def submit_utr_callback(call):
    bot.answer_callback_query(call.id)
    pack_code = call.data.replace("sub_utr_", "")
    user_utr_states[call.from_user.id] = pack_code
    send_auto_delete_message(
        call.message.chat.id,
        "<b>⚡ ENTER 12-DIGIT UTR NUMBER</b>\n────────────────────────\nPlease send your 12-digit UPI UTR / Transaction Reference number now:",
        delay=45
    )


@bot.callback_query_handler(func=lambda call: call.data == "trigger_buy")
def trigger_buy_callback(call):
    try:
        bot.answer_callback_query(call.id)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_auto_delete_message(
            call.message.chat.id,
            get_hooks_text(),
            reply_markup=hooks_menu(),
            delay=60
        )
    except Exception as e:
        print(f"Trigger buy error: {e}")


# ============================================================
# ADMIN APPROVAL / REJECTION CALLBACK HANDLERS
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("app_"))
def admin_approve_callback(call):
    if call.from_user.id not in OWNER_IDS:
        return

    bot.answer_callback_query(call.id)
    parts = call.data.split("_")
    target_user_id = int(parts[1])
    utr = parts[2]

    auto_key = generate_key_code(90)
    success, expiry_str = redeem_vip_key(target_user_id, auto_key)

    bot.edit_message_text(
        f"<b>✅ PAYMENT APPROVED</b>\n────────────────────────\nUser ID: <code>{target_user_id}</code>\nUTR: <code>{utr}</code>\nGenerated Key: <code>{auto_key}</code>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML"
    )

    try:
        user_msg = (
            "<b>🎉 PAYMENT VERIFIED & APPROVED!</b>\n"
            "────────────────────────────────────────\n"
            "Your transaction has been verified successfully.\n\n"
            f"● <b>Your Private VIP Key:</b> <code>{auto_key}</code>\n"
            f"● <b>Valid Until:</b> <b>{expiry_str}</b>\n\n"
            "<i>Your VIP Subscription is now <b>ACTIVE</b>! Use /access to check status.</i>"
        )
        bot.send_message(target_user_id, user_msg, parse_mode="HTML")
    except Exception as e:
        print(f"Failed to send DM to user: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("rej_"))
def admin_reject_callback(call):
    if call.from_user.id not in OWNER_IDS:
        return

    bot.answer_callback_query(call.id)
    parts = call.data.split("_")
    target_user_id = int(parts[1])
    utr = parts[2]

    bot.edit_message_text(
        f"<b>❌ PAYMENT REJECTED</b>\n────────────────────────\nUser ID: <code>{target_user_id}</code>\nUTR: <code>{utr}</code>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML"
    )

    try:
        user_msg = (
            "<b>❌ PAYMENT VERIFICATION FAILED</b>\n"
            "────────────────────────────────────────\n"
            f"Submitted UTR: <code>{utr}</code>\n\n"
            "Your transaction could not be verified in our merchant statement.\n"
            "Please contact Admin if you believe this is an error."
        )
        bot.send_message(target_user_id, user_msg, parse_mode="HTML")
    except Exception:
        pass


# ============================================================
# USER UTR INPUT & GROUP MODERATION
# ============================================================

@bot.message_handler(
    func=lambda message: message.from_user and not message.from_user.is_bot,
    content_types=["text", "photo", "video", "document", "audio", "voice", "animation"]
)
def handle_all_messages(message):
    user = message.from_user
    user_id = user.id

    if user_id in user_utr_states:
        pack_code = user_utr_states[user_id]
        del user_utr_states[user_id]
        utr = message.text.strip()

        if not utr.isdigit() or len(utr) < 10:
            send_auto_delete_message(
                message.chat.id,
                "<b>❌ INVALID UTR FORMAT</b>\n────────────────────────\nUTR must be a 10-12 digit numeric code. Please try again.",
                delay=30
            )
            return

        if pack_code == "p1":
            pack_name, amount = "FULL VIP ENTERPRISE PACK", "INR 2,500"
        elif pack_code == "p2":
            pack_name, amount = "PRO COMBAT PACK", "INR 1,500"
        else:
            pack_name, amount = "YOUTUBER STREAMER PACK", "INR 750"

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with db_lock:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT OR REPLACE INTO transactions (utr, user_id, pack_name, amount, status, submitted_at) VALUES (?, ?, ?, ?, ?, ?)", (utr, user_id, pack_name, amount, "PENDING", now_str))
            connection.commit()
            connection.close()

        send_auto_delete_message(
            message.chat.id,
            "<b>⏳ PAYMENT SUBMITTED FOR VERIFICATION</b>\n────────────────────────────────────────\nYour UTR has been sent to Admin for review.\nYou will receive your VIP Key in private DM once approved.",
            delay=60
        )

        first_name = html.escape(user.first_name or "User")
        admin_alert = (
            "<b>⚡ NEW PAYMENT PENDING APPROVAL</b>\n"
            "────────────────────────────────────────\n"
            f"● <b>User:</b> {first_name} (<code>{user_id}</code>)\n"
            f"● <b>Package:</b> {pack_name}\n"
            f"● <b>Amount Paid:</b> <code>{amount}</code>\n"
            f"● <b>Submitted UTR:</b> <code>{utr}</code>\n\n"
            "────────────────────────────────────────\n"
            "<i>Verify in your merchant bank statement before approving.</i>"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ APPROVE", callback_data=f"app_{user_id}_{utr}"),
            types.InlineKeyboardButton("❌ REJECT", callback_data=f"rej_{user_id}_{utr}")
        )

        for owner_id in OWNER_IDS:
            try:
                bot.send_message(owner_id, admin_alert, reply_markup=markup, parse_mode="HTML")
            except Exception as admin_err:
                print(f"Failed to send alert to Admin DM: {admin_err}")
        return

    if message.chat.type in ["group", "supergroup"]:
        send_first_time_welcome(message)

        if user_id in OWNER_IDS:
            return

        text = message.text or message.caption or ""
        if not text or text.startswith("/") or not contains_bad_language(text):
            return

        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception:
            pass

        warning_number = add_warning(message.chat.id, user_id)

        if warning_number >= 3:
            try:
                bot.ban_chat_member(message.chat.id, user_id)
                send_auto_delete_message(message.chat.id, banned_text(user))
            except Exception:
                pass
            return

        send_auto_delete_message(message.chat.id, warning_text(user, warning_number))


# ============================================================
# CALLBACK QUERY HANDLERS WITH HTML
# ============================================================

@bot.callback_query_handler(func=lambda call: call.data == "home")
def home_callback(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_start_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=start_menu(),
            parse_mode="HTML"
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "btn_files")
def cb_files(call):
    try:
        bot.answer_callback_query(call.id)
        handle_files_access(call.from_user.id, call.message.chat.id, call.message.message_id)
    except Exception as e:
        print(f"Files callback error: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "btn_updates")
def cb_updates(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_updates_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_menu(),
            parse_mode="HTML"
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "btn_tutorial")
def cb_tutorial(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_language_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=language_menu(),
            parse_mode="HTML"
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "btn_premium")
def cb_premium(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_premium_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=premium_menu(),
            parse_mode="HTML"
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "btn_support")
def cb_support(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_support_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=support_menu(),
            parse_mode="HTML"
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "guide_en")
def guide_english_callback(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_guide_page("en", 0),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=guide_menu("en", 0),
            parse_mode="HTML"
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "guide_hi")
def guide_hinglish_callback(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_guide_page("hi", 0),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=guide_menu("hi", 0),
            parse_mode="HTML"
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("guide_en_"))
def guide_english_pages(call):
    try:
        page = int(call.data.replace("guide_en_", ""))
    except Exception:
        bot.answer_callback_query(call.id)
        return

    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_guide_page("en", page),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=guide_menu("en", page),
            parse_mode="HTML"
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("guide_hi_"))
def guide_hinglish_pages(call):
    try:
        page = int(call.data.replace("guide_hi_", ""))
    except Exception:
        bot.answer_callback_query(call.id)
        return

    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            get_guide_page("hi", page),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=guide_menu("hi", page),
            parse_mode="HTML"
        )
    except Exception:
        pass


# ============================================================
# AUTOMATIC COMMAND MENU SETTER
# ============================================================

def set_commands():
    bot.set_my_commands(
        [
            types.BotCommand("start", "Launch Command Center"),
            types.BotCommand("dashboard", "Open Main Dashboard"),
            types.BotCommand("files", "Access Download Portal"),
            types.BotCommand("updates", "View System Logs"),
            types.BotCommand("tutorial", "Installation Engine"),
            types.BotCommand("premium", "VIP Access Pass"),
            types.BotCommand("buy", "Pay via UPI / QR Code"),
            types.BotCommand("redeem", "Redeem License Key"),
            types.BotCommand("access", "Verification & Key Status"),
            types.BotCommand("support", "Contact Support Desk")
        ]
    )


# ============================================================
# BOT BOOTSTRAP
# ============================================================

if __name__ == "__main__":

    print("========================================")
    print("      QRISHNA VIP ENTERPRISE BOT")
    print("========================================")

    init_database()
    set_commands()

    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    print("QRISHNA VIP ENGINE is ONLINE.")

    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception:
        pass

    while True:
        try:
            bot.polling(non_stop=True, interval=1, timeout=30, skip_pending=True)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)
