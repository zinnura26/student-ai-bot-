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
import sqlite3

load_dotenv()

TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def init_db():
    conn = sqlite3.connect("student_ai.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            question_count INTEGER DEFAULT 0,
            last_date TEXT,
            premium_until TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()

def get_user(user_id):
    conn = sqlite3.connect("student_ai.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT question_count, last_date, premium_until FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (user_id, question_count, last_date) VALUES (?, 0, ?)",
            (user_id, "")
        )
        conn.commit()
        user = (0, "", None)

    conn.close()
    return user


def update_question_count(user_id, count, date):
    conn = sqlite3.connect("student_ai.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET question_count = ?, last_date = ? WHERE user_id = ?",
        (count, date, user_id)
    )

    conn.commit()
    conn.close()

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

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        text = (
            "⭐ STUDENT AI PREMIUM\n\n"
            "🚀 30 kunlik Premium\n"
            "♾️ AI savollariga limit yo'q\n"
            "📄 Hujjatlar bilan ishlash\n"
            "💻 Dasturlash yordamchisi\n"
            "🌍 Tarjimon imkoniyatlari\n\n"
            "💳 Premiumni sotib olish uchun quyidagi tugmani bosing."
        )

    elif lang == "en":
        text = (
            "⭐ STUDENT AI PREMIUM\n\n"
            "🚀 30-day Premium\n"
            "♾️ Unlimited AI questions\n"
            "📄 Document tools\n"
            "💻 Programming assistant\n"
            "🌍 Translation features\n\n"
            "💳 Press the button below to purchase Premium."
        )

    else:
        text = (
            "⭐ STUDENT AI PREMIUM\n\n"
            "🚀 Premium на 30 дней\n"
            "♾️ Безлимитные вопросы AI\n"
            "📄 Работа с документами\n"
            "💻 Помощник по программированию\n"
            "🌍 Переводчик\n\n"
            "💳 Нажмите кнопку ниже для покупки Premium."
        )

    keyboard = [
        ["💳 Premium sotib olish"],
        ["⬅️ Orqaga"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        text,
        reply_markup=reply_markup
    )

async def premium_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        text = (
            "💳 STUDENT AI PREMIUM\n\n"
            "⭐ Premium — 30 kun\n"
            "♾️ AI savollariga limit yo'q\n"
            "📄 Hujjat va PDF tahlili\n"
            "🖼️ Rasm tahlili\n"
            "💻 Dasturlash yordamchisi\n"
            "🌍 Kengaytirilgan tarjima\n\n"
            "💰 Narx: 29 000 so'm / 30 kun\n\n"
            "🔐 To'lov tizimi tez orada ulanadi."
        )

    elif lang == "en":
        text = (
            "💳 STUDENT AI PREMIUM\n\n"
            "⭐ Premium — 30 days\n"
            "♾️ Unlimited AI questions\n"
            "📄 Document and PDF analysis\n"
            "🖼️ Image analysis\n"
            "💻 Programming assistant\n"
            "🌍 Advanced translation\n\n"
            "💰 Price: 29,000 UZS / 30 days\n\n"
            "🔐 Payment system will be connected soon."
        )

    else:
        text = (
            "💳 STUDENT AI PREMIUM\n\n"
            "⭐ Premium — 30 дней\n"
            "♾️ Безлимитные вопросы AI\n"
            "📄 Анализ документов и PDF\n"
            "🖼️ Анализ изображений\n"
            "💻 Помощник по программированию\n"
            "🌍 Расширенный перевод\n\n"
            "💰 Цена: 29 000 сум / 30 дней\n\n"
            "🔐 Платёжная система скоро будет подключена."
        )

    await update.message.reply_text(text)

    await update.message.reply_text(text)

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import requests
    from datetime import date

    user_id = update.effective_user.id
    today = str(date.today())

    question_count, last_date, premium_until = get_user(user_id)

    # Yangi kun bo'lsa, bepul limitni yangilash
    if last_date != today:
        question_count = 0
        update_question_count(user_id, 0, today)

    # Premium tekshiruvi hozircha keyingi bosqich uchun
    if premium_until:
        pass

    # Bepul limit: kuniga 5 ta savol
    if question_count >= 5:
        lang = context.user_data.get("language", "uz")

        if lang == "uz":
            text = (
                "⛔ Bugungi bepul AI limitingiz tugadi.\n\n"
                "⭐ Premium orqali ko'proq foydalanishingiz mumkin."
            )
        elif lang == "en":
            text = (
                "⛔ Your free AI limit for today is over.\n\n"
                "⭐ You can use more with Premium."
            )
        else:
            text = (
                "⛔ Ваш бесплатный лимит AI на сегодня закончился.\n\n"
                "⭐ Больше возможностей доступно с Premium."
            )

        await update.message.reply_text(text)
        return

    user_question = update.message.text

    # Savol yuborilishidan oldin limitni 1 taga oshiramiz
    question_count += 1
    update_question_count(user_id, question_count, today)

    await update.message.reply_text(
        f"⏳ AI o'ylayapti...\n\n"
        f"📊 Bugungi bepul savollar: {question_count}/5"
    )

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
        filters.Regex("^⭐ Premium$"),
        premium
    )
)

app.add_handler(
    MessageHandler(
        filters.Regex("^💳 Premium sotib olish$"),
        premium_buy
    )
)

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
