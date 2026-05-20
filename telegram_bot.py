import os
import subprocess
import ctypes
import time
import pyautogui
import pygetwindow as gw

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ==========================================
# SETTINGS
# ==========================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID"))

# Chrome path
CHROME_PATH = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
)

# ==========================================
# CONTACTS
# ==========================================

CONTACTS = {
    "AnjanaYasodhaSureshSantosh": "https://www.messenger.com/e2ee/t/1595472291528180/",
    "Santosh": "https://www.messenger.com/e2ee/t/7807929559273698",
    "SantoshYasodha": "https://www.messenger.com/e2ee/t/974591568661526",
}

# ==========================================
# REPLY KEYBOARD
# ==========================================

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📞 Call",        "📸 Screenshot"],
        ["🔊 Volume",      "🌐 Open URL"],
        ["🗂 Tabs",        "🗑 Clear Chrome"],
        ["✅ Status",      "👤 Who Am I"],
    ],
    resize_keyboard=True,
    is_persistent=True,
)

# ==========================================
# WAKE COMPUTER
# ==========================================

def wake_computer():
    ES_SYSTEM_REQUIRED  = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )
    pyautogui.press("escape")
    time.sleep(1.5)


# ==========================================
# SECURITY
# ==========================================

def allowed(update: Update):

    user = update.effective_user

    if user is None:
        return False

    return user.id == ALLOWED_USER_ID


# ==========================================
# POST INIT
# ==========================================

async def post_init(application):

    await application.bot.set_my_commands([
        BotCommand("start",      "Start the bot"),
        BotCommand("call",       "Call someone"),
        BotCommand("screenshot", "Take a screenshot"),
        BotCommand("volume",     "Set volume"),
        BotCommand("open",       "Open a URL"),
        BotCommand("tabs",       "Show Chrome tabs"),
        BotCommand("clear",      "Close Chrome"),
        BotCommand("status",     "Bot status"),
        BotCommand("whoami",     "Your Telegram ID"),
    ])

    await application.bot.send_message(
        chat_id=ALLOWED_USER_ID,
        text="Hello, I am BatuliBot. How can I help you today? ",
        reply_markup=MAIN_KEYBOARD,
    )


# ==========================================
# START
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "✅ Bot running. Choose a command below.",
        reply_markup=MAIN_KEYBOARD
    )


# ==========================================
# WHOAMI
# ==========================================

async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user:
        await update.message.reply_text(
            f"Your Telegram ID:\n{user.id}",
            reply_markup=MAIN_KEYBOARD
        )


# ==========================================
# CALL
# ==========================================

async def call(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):
        await update.message.reply_text("Not allowed.")
        return

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"call_{name}")]
        for name in CONTACTS
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Who do you want to call?",
        reply_markup=reply_markup
    )


async def call_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    name = query.data.replace("call_", "")

    if name not in CONTACTS:
        await query.edit_message_text("Contact not found.")
        return

    link = CONTACTS[name]

    wake_computer()

    try:
        subprocess.Popen([CHROME_PATH, link], shell=False)
        await query.edit_message_text(f"📞 Calling {name}...")

    except Exception as e:
        await query.edit_message_text(f"Error:\n{e}")


# ==========================================
# OPEN URL
# ==========================================

async def open_url(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):
        await update.message.reply_text("Not allowed.")
        return

    if len(context.args) == 0:
        context.user_data["waiting_for_url"] = True
        await update.message.reply_text(
            "Send the URL you want to open.",
            reply_markup=MAIN_KEYBOARD
        )
        return

    url = context.args[0]

    if not url.startswith("http"):
        url = "https://" + url

    wake_computer()

    try:
        subprocess.Popen([CHROME_PATH, url], shell=False)
        await update.message.reply_text(
            f"Opened:\n{url}",
            reply_markup=MAIN_KEYBOARD
        )

    except Exception as e:
        await update.message.reply_text(
            f"Error:\n{e}",
            reply_markup=MAIN_KEYBOARD
        )


# ==========================================
# SHOW CHROME TABS
# ==========================================

async def tabs(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):
        await update.message.reply_text("Not allowed.")
        return

    wake_computer()

    try:

        windows = gw.getWindowsWithTitle("")

        chrome_tabs = []

        for w in windows:
            title = w.title.strip()
            if title and "Chrome" in title:
                chrome_tabs.append(title)

        if not chrome_tabs:
            await update.message.reply_text(
                "No Chrome tabs found.",
                reply_markup=MAIN_KEYBOARD
            )
            return

        text = "Chrome tabs:\n\n"

        for i, tab in enumerate(chrome_tabs, start=1):
            text += f"{i}. {tab}\n"

        await update.message.reply_text(
            text,
            reply_markup=MAIN_KEYBOARD
        )

    except Exception as e:
        await update.message.reply_text(
            f"Error:\n{e}",
            reply_markup=MAIN_KEYBOARD
        )


# ==========================================
# SCREENSHOT
# ==========================================

async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):
        await update.message.reply_text("Not allowed.")
        return

    wake_computer()

    try:

        file_path = os.path.join(os.environ["TEMP"], "screenshot.png")

        image = pyautogui.screenshot()

        image.save(file_path)

        with open(file_path, "rb") as f:
            await update.message.reply_photo(photo=f)

        os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(
            f"Error:\n{e}",
            reply_markup=MAIN_KEYBOARD
        )


# ==========================================
# VOLUME
# ==========================================

async def volume(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):
        await update.message.reply_text("Not allowed.")
        return

    if len(context.args) == 0:
        context.user_data["waiting_for_volume"] = True
        await update.message.reply_text(
            "Send the volume level (0-100).",
            reply_markup=MAIN_KEYBOARD
        )
        return

    wake_computer()

    try:

        level = int(context.args[0])

        if level < 0:
            level = 0

        if level > 100:
            level = 100

        devices = AudioUtilities.GetSpeakers()

        activate = devices._dev.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )

        volume_control = cast(
            activate,
            POINTER(IAudioEndpointVolume)
        )

        volume_control.SetMasterVolumeLevelScalar(
            level / 100,
            None
        )

        await update.message.reply_text(
            f"Volume set to {level}%",
            reply_markup=MAIN_KEYBOARD
        )

    except Exception as e:
        await update.message.reply_text(
            f"Error:\n{e}",
            reply_markup=MAIN_KEYBOARD
        )


# ==========================================
# CLEAR
# ==========================================

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):
        await update.message.reply_text("Not allowed.")
        return

    wake_computer()

    try:
        os.system("taskkill /F /IM chrome.exe")
        await update.message.reply_text(
            "Closed all Chrome windows.",
            reply_markup=MAIN_KEYBOARD
        )

    except Exception as e:
        await update.message.reply_text(
            f"Error:\n{e}",
            reply_markup=MAIN_KEYBOARD
        )


# ==========================================
# STATUS
# ==========================================

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):
        await update.message.reply_text("Not allowed.")
        return

    await update.message.reply_text(
        "✅ Telegram bot is running and connected.",
        reply_markup=MAIN_KEYBOARD
    )


# ==========================================
# HANDLE NORMAL MESSAGE
# ==========================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):
        return

    text = update.message.text.strip()

    # Handle reply keyboard buttons
    if text == "📞 Call":
        await call(update, context)
        return

    if text == "📸 Screenshot":
        await screenshot(update, context)
        return

    if text == "🔊 Volume":
        context.user_data["waiting_for_volume"] = True
        await update.message.reply_text(
            "Send the volume level (0-100).",
            reply_markup=MAIN_KEYBOARD
        )
        return

    if text == "🌐 Open URL":
        context.user_data["waiting_for_url"] = True
        await update.message.reply_text(
            "Send the URL you want to open.",
            reply_markup=MAIN_KEYBOARD
        )
        return

    if text == "🗂 Tabs":
        await tabs(update, context)
        return

    if text == "🗑 Clear Chrome":
        await clear(update, context)
        return

    if text == "✅ Status":
        await status(update, context)
        return

    if text == "👤 Who Am I":
        await whoami(update, context)
        return

    # Handle waiting states
    if context.user_data.get("waiting_for_volume"):
        context.user_data["waiting_for_volume"] = False
        try:
            level = int(text)
            context.args = [str(level)]
            await volume(update, context)
        except ValueError:
            await update.message.reply_text(
                "Please send a number between 0 and 100.",
                reply_markup=MAIN_KEYBOARD
            )
        return

    if context.user_data.get("waiting_for_url"):
        context.user_data["waiting_for_url"] = False
        url = text
        if not url.startswith("http"):
            url = "https://" + url
        wake_computer()
        try:
            subprocess.Popen([CHROME_PATH, url], shell=False)
            await update.message.reply_text(
                f"Opened:\n{url}",
                reply_markup=MAIN_KEYBOARD
            )
        except Exception as e:
            await update.message.reply_text(
                f"Error:\n{e}",
                reply_markup=MAIN_KEYBOARD
            )
        return


# ==========================================
# MAIN
# ==========================================

def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in .env file")

    if not ALLOWED_USER_ID:
        raise ValueError("ALLOWED_USER_ID not found in .env file")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("whoami", whoami))
    app.add_handler(CommandHandler("call", call))
    app.add_handler(CommandHandler("open", open_url))
    app.add_handler(CommandHandler("tabs", tabs))
    app.add_handler(CommandHandler("screenshot", screenshot))
    app.add_handler(CommandHandler("volume", volume))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("status", status))

    # Callback handler for call buttons
    app.add_handler(CallbackQueryHandler(call_callback, pattern="^call_"))

    # Message handler
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("Telegram bot running...")

    app.run_polling()


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":
    main()