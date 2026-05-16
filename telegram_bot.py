import os
import subprocess
import pyautogui
import pygetwindow as gw

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume,ISimpleAudioVolume
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    "YasodhaSantosh": "https://www.messenger.com/e2ee/t/974591568661526",
    "Santosh": "https://www.messenger.com/e2ee/t/7807929559273698",
    "SureshAnjanaYasodhaSantosh": "https://www.messenger.com/e2ee/t/1595472291528180/",
}

# ==========================================
# SECURITY
# ==========================================

def allowed(update: Update):

    user = update.effective_user

    if user is None:
        return False

    return user.id == ALLOWED_USER_ID


# ==========================================
# START
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "✅ Bot running.\n\n"
        "/whoami\n"
        "/call\n"
        "/open <url>\n"
        "/tabs\n"
        "/screenshot\n"
        "/volume <0-100>\n"
        "/clear\n"
        "/status"
    )


# ==========================================
# WHOAMI
# ==========================================

async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user:

        await update.message.reply_text(
            f"Your Telegram ID:\n{user.id}"
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

    try:
        subprocess.Popen([CHROME_PATH, link], shell=False)
        await query.edit_message_text(f"📞 Calling {name}...")

    except Exception as e:
        await query.edit_message_text(f"Error:\n{e}")


# ==========================================
# HANDLE NORMAL MESSAGE
# ==========================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):
        return


# ==========================================
# OPEN URL
# ==========================================

async def open_url(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):

        await update.message.reply_text("Not allowed.")
        return

    if len(context.args) == 0:

        await update.message.reply_text(
            "Usage:\n/open google.com"
        )
        return

    url = context.args[0]

    if not url.startswith("http"):
        url = "https://" + url

    try:

        subprocess.Popen(
            [CHROME_PATH, url],
            shell=False
        )

        await update.message.reply_text(
            f"Opened:\n{url}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"Error:\n{e}"
        )


# ==========================================
# SHOW CHROME TABS
# ==========================================

async def tabs(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):

        await update.message.reply_text("Not allowed.")
        return

    try:

        windows = gw.getWindowsWithTitle("")

        chrome_tabs = []

        for w in windows:

            title = w.title.strip()

            if title and "Chrome" in title:
                chrome_tabs.append(title)

        if not chrome_tabs:

            await update.message.reply_text(
                "No Chrome tabs found."
            )
            return

        text = "Chrome tabs:\n\n"

        for i, tab in enumerate(chrome_tabs, start=1):
            text += f"{i}. {tab}\n"

        await update.message.reply_text(text)

    except Exception as e:

        await update.message.reply_text(
            f"Error:\n{e}"
        )


# ==========================================
# SCREENSHOT
# ==========================================

async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):
        await update.message.reply_text("Not allowed.")
        return

    try:

        file_path = os.path.join(os.environ["TEMP"], "screenshot.png")

        image = pyautogui.screenshot()

        image.save(file_path)

        with open(file_path, "rb") as f:
            await update.message.reply_photo(photo=f)

        os.remove(file_path)

    except Exception as e:

        await update.message.reply_text(
            f"Error:\n{e}"
        )


# ==========================================
# VOLUME
# ==========================================

async def volume(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):
        await update.message.reply_text("Not allowed.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Usage:\n/volume 50")
        return

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
            f"Volume set to {level}%"
        )

    except Exception as e:
        await update.message.reply_text(f"Error:\n{e}")

# ==========================================
# CLEAR
# ==========================================

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):

        await update.message.reply_text("Not allowed.")
        return

    try:

        os.system("taskkill /F /IM chrome.exe")

        await update.message.reply_text(
            "Closed all Chrome windows."
        )

    except Exception as e:

        await update.message.reply_text(
            f"Error:\n{e}"
        )


# ==========================================
# STATUS
# ==========================================

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not allowed(update):

        await update.message.reply_text("Not allowed.")
        return

    await update.message.reply_text(
        "✅ Telegram bot is running and connected."
    )


# ==========================================
# MAIN
# ==========================================

def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in .env file")

    if not ALLOWED_USER_ID:
        raise ValueError("ALLOWED_USER_ID not found in .env file")

    app = Application.builder().token(BOT_TOKEN).build()

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