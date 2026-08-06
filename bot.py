from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🇺🇿 O'zbekcha"],
        ["🇬🇧 English"],
        ["🇷🇺 Русский"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🌍 Tilni tanlang:",
        reply_markup=reply_markup
    )

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🇺🇿 O'zbekcha":
        context.user_data["language"] = "uz"
        await uz_menu(update)

    elif text == "🇬🇧 English":
        context.user_data["language"] = "en"
        await en_menu(update)

    elif text == "🇷🇺 Русский":
        context.user_data["language"] = "ru"
        await ru_menu(update)

async def uz_menu(update: Update):
    keyboard = [
        ["🤖 AI yordamchi", "🌍 Tarjimon"],
        ["📄 Hujjat", "💻 Dasturlash"],
        ["📚 Darslar", "🧮 Kalkulyator"],
        ["⚙️ Sozlamalar", "⭐ Premium"],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 Assalomu alaykum!\n\n"
        "Student AI ga xush kelibsiz.\n\n"
        "👇 Kerakli bo'limni tanlang:",
        reply_markup=reply_markup
    )
async def en_menu(update: Update):
    keyboard = [
        ["🤖 AI Assistant", "🌍 Translator"],
        ["📄 Documents", "💻 Programming"],
        ["📚 Study", "🧮 Calculator"],
        ["⚙️ Settings", "⭐ Premium"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 Welcome to Student AI!\n\n"
        "👇 Please choose a section:",
        reply_markup=reply_markup
    )
async def ru_menu(update: Update):
    keyboard = [
        ["🤖 AI Помощник", "🌍 Переводчик"],
        ["📄 Документы", "💻 Программирование"],
        ["📚 Учёба", "🧮 Калькулятор"],
        ["⚙️ Настройки", "⭐ Premium"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 Добро пожаловать в Student AI!\n\n"
        "👇 Выберите нужный раздел:",
        reply_markup=reply_markup
    )
async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        text = (
            "🤖 AI yordamchi tayyor.\n\n"
            "Savolingizni yozing, javob beraman."
        )

    elif lang == "en":
        text = (
            "🤖 AI Assistant is ready.\n\n"
            "Write your question, I will answer."
        )

    else:
        text = (
            "🤖 AI Помощник готов.\n\n"
            "Напишите свой вопрос, я отвечу."
        )

    await update.message.reply_text(text)

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import requests

    user_question = update.message.text

    await update.message.reply_text("⏳ AI o'ylayapti...")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
    "contents": [
        {
            "parts": [
                {
                    "text": user_question
                }
            ]
        }
    ],
    "generationConfig": {
        "thinkingConfig": {
            "thinkingLevel": "minimal"
        }
    }
}


    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=60
        )

        result = response.json()

        print(result)

        if "candidates" in result:
            answer = result["candidates"][0]["content"]["parts"][0]["text"]
            await update.message.reply_text(answer)
        else:
            await update.message.reply_text(
                f"❌ Xato: {result}"
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Xato: {e}"
        )

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(
        filters.Regex("^(🤖 AI yordamchi|🤖 AI Assistant|🤖 AI Помощник)$"),
        ai_assistant
    )
)

app.add_handler(
    MessageHandler(
        filters.Regex("^(🇺🇿 O'zbekcha|🇬🇧 English|🇷🇺 Русский)$"),
        language
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        ai_chat
    )
)

print("✅ Student AI ishga tushdi...")

app.run_polling()
