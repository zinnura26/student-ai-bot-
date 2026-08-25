from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from dotenv import load_dotenv
import os
import sqlite3
import requests
from pypdf import PdfReader
load_dotenv()

DB_PATH = "/app/data/student_ai.db" if os.path.isdir("/app/data") else "student_ai.db"


TOKEN = os.getenv("TOKEN")
ADMIN_ID = 8004029780
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_WRITING_API_KEY = os.getenv("GEMINI_WRITING_API_KEY")
GEMINI_PROGRAMMING_API_KEY = os.getenv("GEMINI_PROGRAMMING_API_KEY")
GEMINI_AI_API_KEY = os.getenv("GEMINI_AI_API_KEY")

def init_db():
    print("🔵 REPORT: DB ulanish boshladi")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("🟢 REPORT: DB ulanish OK")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            question_count INTEGER DEFAULT 0,
            last_date TEXT,
            premium_until TEXT
        )
    """)

    # 📄 PDF rasmlar uchun kunlik limit
    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN pdf_image_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN pdf_image_last_date TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # 🌍 Translator uchun ustunlar
    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN translator_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN translator_last_date TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # 💻 Programming uchun ustunlar
    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN programming_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN programming_last_date TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # 📄 REFERAT uchun kunlik limit
    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN report_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN report_last_date TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # 📖 MUSTAQIL ISH uchun kunlik limit
    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN independent_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN independent_last_date TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # 📝 PDF XULOSA uchun kunlik limit
    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN pdf_summary_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN pdf_summary_last_date TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # 📝 ESSE uchun kunlik limit
    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN essay_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN essay_last_date TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN pdf_summary_last_date TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # 📝 PDF XULOSA PREMIUM — 30 / oy
    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN pdf_summary_premium_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN pdf_summary_premium_month TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # ⭐ PREMIUM — 300 TA / 30 KUN
    # Har bir Premium cheksiz xizmat uchun alohida oylik hisoblagich

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN premium_math_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN premium_math_month TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN premium_programming_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN premium_programming_month TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN premium_translation_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN premium_translation_month TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN premium_ai_count INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN premium_ai_month TEXT"
        )
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


init_db()

# ============================================================
# ⭐ PREMIUM 300 TA / 30 KUN
# Premium davrini premium_until orqali aniqlaymiz.
# Shu sababli kalendar oyiga bog‘lanmaydi.
# ============================================================

PREMIUM_FEATURE_LIMIT = 300


def premium_cycle_active(
    premium_count,
    premium_cycle,
    premium_until,
    today
):
    """
    Premium 30 kunlik davri uchun hisoblagichni tekshiradi.

    premium_cycle = o‘sha Premium davrining premium_until sanasi.
    Premium yangilanganda premium_until o‘zgaradi va
    hisoblagich avtomatik ravishda 0 dan boshlanadi.
    """

    premium_active = (
        premium_until is not None
        and premium_until != ""
        and premium_until >= today
    )

    if not premium_active:
        return False, 0

    if premium_cycle != premium_until:
        return True, 0

    return True, (premium_count or 0)


def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET question_count = ?, last_date = ? WHERE user_id = ?",
        (count, date, user_id)
    )

    conn.commit()
    conn.close()

def activate_premium(user_id):
    from datetime import date, timedelta

    premium_until = date.today() + timedelta(days=30)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET premium_until = ?, "
        "premium_ai_count = 0, premium_ai_month = ? "
        "WHERE user_id = ?",
        (str(premium_until), str(premium_until), user_id)
    )

    conn.commit()
    conn.close()

    return str(premium_until)

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
        ["🧠 Aqlli matematika", "📄 PDF / Hujjat"],
        ["📚 Yozma ishlar", "💻 Dasturlash"],
        ["⚙️ Sozlamalar", "⭐ Premium"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 Assalomu alaykum!\n\n"
        "🤖 Student AI ga xush kelibsiz!\n\n"
        "👇 Kerakli bo'limni tanlang:",
        reply_markup=reply_markup
    )


async def en_menu(update: Update):
    keyboard = [
        ["🤖 AI Assistant", "🌍 Translator"],
        ["🧠 Smart Math", "📄 PDF / Documents"],
        ["📚 Written Works", "💻 Programming"],
        ["⚙️ Settings", "⭐ Premium"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 Welcome to Student AI!\n\n"
        "🤖 Your AI assistant for study and everyday tasks.\n\n"
        "👇 Choose a section:",
        reply_markup=reply_markup
    )


async def ru_menu(update: Update):
    keyboard = [
        ["🤖 AI Помощник", "🌍 Переводчик"],
        ["🧠 Умная математика", "📄 PDF / Документы"],
        ["📚 Письменные работы", "💻 Программирование"],
        ["⚙️ Настройки", "⭐ Premium"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 Добро пожаловать в Student AI!\n\n"
        "🤖 Ваш AI-помощник для учёбы и повседневных задач.\n\n"
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

async def essay_generator(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str):
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'uz')
    from datetime import date
    today = date.today().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT essay_count, essay_last_date, premium_until FROM users WHERE user_id = ?',
        (user_id,)
    )
    row = cursor.fetchone()
    print("🟢 REPORT: SELECT OK, row =", row)

    if row is None:
        cursor.execute(
            'INSERT INTO users (user_id, essay_count, essay_last_date) VALUES (?, 0, ?)',
            (user_id, today)
        )
        conn.commit()
        essay_count = 0
        last_date = today
        premium_until = None
    else:
        essay_count = row[0] or 0
        last_date = row[1]
        premium_until = row[2]

    if last_date != today:
        essay_count = 0
        cursor.execute(
            'UPDATE users SET essay_count = 0, essay_last_date = ? WHERE user_id = ?',
            (today, user_id)
        )
        conn.commit()

    premium_active = bool(premium_until and premium_until >= today)
    daily_limit = 10 if premium_active else 2

    if essay_count >= daily_limit:
        conn.close()
        await update.message.reply_text(
            f'🔒 Bugungi esse limitingiz tugadi. {essay_count}/{daily_limit}'
        )
        return

    conn.close()

    await update.message.reply_text('⏳ AI esseingizni tayyorlamoqda...')

    prompt = (
        'Sen Student AI, akademik yozuv yordamchisisan. '
'Talaba uchun o‘zbek tilida mazmunli, tushunarli va yaxshi tuzilgan esse yoz. '
'Kirish, asosiy qism va xulosa bo‘lsin. Mavzuni to‘liq yorit.\n\n'
        f'MAVZU:\n{topic}'
    )

    url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent'
    headers = {
        'x-goog-api-key': GEMINI_WRITING_API_KEY,
        'Content-Type': 'application/json'
    }
    data = {'contents': [{'parts': [{'text': prompt}]}]}

    try:
        response = None
        result = None

        retry_delays = [0, 2, 5]

        for attempt, delay in enumerate(retry_delays, start=1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=60
                )

                print(
                    f"📝 ESSAY GEMINI attempt {attempt}/3: "
                    f"{response.status_code}"
                )

                if response.status_code == 200:
                    try:
                        result = response.json()
                    except ValueError:
                        result = None
                    break

                if response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < 3:
                        await asyncio.sleep(delay)
                        continue

                break

            except requests.exceptions.Timeout:
                print(
                    f"⏱️ ESSAY TIMEOUT attempt {attempt}/3"
                )

                if attempt < 3:
                    await asyncio.sleep(delay)
                    continue

                await update.message.reply_text(
                    "⏳ AI serveri hozir javob berishga ulgurmayapti.\n\n"
                    "Birozdan keyin yana urinib ko‘ring."
                )
                return

            except requests.exceptions.RequestException as e:
                print(
                    f"🌐 ESSAY NETWORK ERROR attempt {attempt}/3: {e}"
                )

                if attempt < 3:
                    await asyncio.sleep(delay)
                    continue

                await update.message.reply_text(
                    "🌐 AI serveriga ulanishda muammo yuz berdi.\n\n"
                    "Birozdan keyin yana urinib ko‘ring."
                )
                return

        if response is None or result is None:
            await update.message.reply_text(
                "😔 AI hozircha javob bera olmadi.\n\n"
                "Birozdan keyin yana urinib ko‘ring."
            )
            return

        if response.status_code != 200:
            if response.status_code == 503:
                await update.message.reply_text(
                "😔 Student AI hozir biroz band.\n"
                "⏳ So‘rovlar ko‘paygani sababli javob tayyorlash biroz kechikmoqda.\n"
                "🔄 Iltimos, bir necha soniyadan keyin yana urinib ko‘ring.\n"
                "💙 Noqulaylik uchun uzr!"
                )
            else:
                await update.message.reply_text(
                    f'❌ Gemini xatosi: {response.status_code}'
                )
            return

        if 'candidates' not in result:
            await update.message.reply_text('❌ Esse tayyorlashda javob olinmadi.')
            return

        answer = result['candidates'][0]['content']['parts'][0]['text']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET essay_count = ?, essay_last_date = ? WHERE user_id = ?',
            (essay_count + 1, today, user_id)
        )
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f'📝 ESSE\n\n{answer}\n\n📊 Bugungi foydalanish: {essay_count + 1}/{daily_limit}'
        )

    except Exception as e:
        print('❌ ESSAY ERROR:', e)
        await update.message.reply_text('❌ Esse tayyorlashda xatolik yuz berdi.')

async def report_generator(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str):
    print("🚀 REPORT GENERATOR ISHLADI:", topic)
    user_id = update.effective_user.id
    lang = context.user_data.get("language", "uz")
    from datetime import date
    today = date.today().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT report_count, report_last_date, premium_until FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            "INSERT INTO users (user_id, report_count, report_last_date) VALUES (?, 0, ?)",
            (user_id, today)
        )
        conn.commit()
        report_count = 0
        last_date = today
        premium_until = None
    else:
        report_count = row[0] or 0
        last_date = row[1]
        premium_until = row[2]

    if last_date != today:
        report_count = 0
        cursor.execute(
            "UPDATE users SET report_count = 0, report_last_date = ? WHERE user_id = ?",
            (today, user_id)
        )
        conn.commit()

    premium_active = bool(premium_until and premium_until >= today)
    daily_limit = 10 if premium_active else 2

    if report_count >= daily_limit:
        conn.close()

        if lang == "en":
            msg = (
                "🔒 Your daily report limit has been reached.\n\n"
                f"Today: {report_count}/{daily_limit} reports."
            )
        elif lang == "ru":
            msg = (
                "🔒 Ваш дневной лимит рефератов закончился.\n\n"
                f"Сегодня: {report_count}/{daily_limit} рефератов."
            )
        else:
            msg = (
                "🔒 Bugungi referat limitingiz tugadi.\n\n"
                f"Bugun: {report_count}/{daily_limit} ta referat."
            )

        await update.message.reply_text(msg)
        return

    conn.close()
    print("🟢 REPORT: DB yopildi, Gemini qismiga o‘tyapti")

    if lang == "en":
        waiting = "⏳ AI is preparing your report..."
        title = "📄 REPORT"
        prompt = (
            "You are Student AI, an academic writing assistant. "
            "Write a detailed, clear and well-structured academic report in English "
            "for a student. Include a title, introduction, main sections, "
            "important information, conclusion and references section. "
            "Keep the content informative, natural and suitable for student study.\n\n"
            f"TOPIC:\n{topic}"
        )

    elif lang == "ru":
        waiting = "⏳ AI готовит ваш реферат..."
        title = "📄 РЕФЕРАТ"
        prompt = (
            "Ты Student AI, помощник по академическому письму. "
            "Напиши подробный, понятный и хорошо структурированный реферат "
            "на русском языке для студента. Включи заголовок, введение, "
            "основные разделы, важную информацию, заключение и список литературы. "
            "Содержание должно быть информативным и подходить для учебы.\n\n"
            f"ТЕМА:\n{topic}"
        )

    else:
        waiting = "⏳ AI referatingizni tayyorlamoqda..."
        title = "📄 REFERAT"
        prompt = (
            "Sen Student AI, akademik yozuv yordamchisisan. "
            "Talaba uchun o‘zbek tilida batafsil, mazmunli va yaxshi "
            "tuzilgan referat yoz. Unda sarlavha, kirish, asosiy bo‘limlar, "
            "muhim ma’lumotlar, xulosa va foydalanilgan adabiyotlar bo‘lsin. "
            "Mavzuni tushunarli va o‘quv uchun foydali tarzda yorit.\n\n"
            f"MAVZU:\n{topic}"
        )

    await update.message.reply_text(waiting)

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.6-flash:generateContent"
    )

    headers = {
        "x-goog-api-key": GEMINI_WRITING_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = None
        result = None

        retry_delays = [0, 2, 5]

        for attempt, delay in enumerate(retry_delays, start=1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=60
                )

                print(
                    f"🧠 SMART MATH attempt {attempt}/3: "
                    f"{response.status_code}"
                )

                if response.status_code == 200:
                    try:
                        result = response.json()
                    except ValueError:
                        result = None
                    break

                if response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < 3:
                        await asyncio.sleep(delay)
                        continue
                    break

                break

            except requests.exceptions.Timeout:
                print(
                    f"⏱️ SMART MATH TIMEOUT attempt {attempt}/3"
                )

                if attempt < 3:
                    await asyncio.sleep(delay)
                    continue
                break

            except requests.exceptions.RequestException as e:
                print(
                    f"🌐 SMART MATH NETWORK ERROR "
                    f"attempt {attempt}/3: {e}"
                )

                if attempt < 3:
                    await asyncio.sleep(delay)
                    continue
                break

        if response is None or result is None:
            await update.message.reply_text(
                "⚠️ Aqlli matematika hozircha javob bera olmayapti.\n\n"
                "🔄 Iltimos, birozdan keyin yana urinib ko‘ring."
            )
            return

        if response.status_code != 200:
            if response.status_code == 503:
                await update.message.reply_text(
                "😔 Student AI hozir biroz band.\n"
                "⏳ So‘rovlar ko‘paygani sababli javob tayyorlash biroz kechikmoqda.\n"
                "🔄 Iltimos, bir necha soniyadan keyin yana urinib ko‘ring.\n"
                "💙 Noqulaylik uchun uzr!"
                )
            else:
                await update.message.reply_text(
                    f"❌ Gemini xatosi: {response.status_code}"
                )
            return

        if "candidates" not in result:
            await update.message.reply_text(
                "❌ Referat tayyorlashda javob olinmadi."
            )
            return

        answer = result["candidates"][0]["content"]["parts"][0]["text"]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET report_count = ?, report_last_date = ? WHERE user_id = ?",
            (report_count + 1, today, user_id)
        )

        conn.commit()
        conn.close()

        full_text = (
            f"{title}\n\n{answer}\n\n"
            f"📊 Bugungi foydalanish: {report_count + 1}/{daily_limit}"
        )

        # Telegram 4096 belgidan uzun xabarni qabul qilmaydi.
        # Shuning uchun uzun referatni bo'lib yuboramiz.
        max_length = 4000

        for i in range(0, len(full_text), max_length):
            await update.message.reply_text(
                full_text[i:i + max_length]
            )

    except Exception as e:
        print("❌ REPORT ERROR:", type(e).__name__, e)
        await update.message.reply_text(
            f"❌ Referat xatosi:\n{type(e).__name__}: {e}"
        )


async def independent_work_generator(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str):
    print("🚀 INDEPENDENT WORK GENERATOR ISHLADI:", topic)

    user_id = update.effective_user.id
    lang = context.user_data.get("language", "uz")

    from datetime import date
    today = date.today().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT independent_count, independent_last_date, premium_until FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            "INSERT INTO users (user_id, independent_count, independent_last_date) VALUES (?, ?, ?)",
            (user_id, 0, today)
        )
        conn.commit()
        independent_count = 0
        last_date = today
        premium_until = None
    else:
        independent_count = row[0] or 0
        last_date = row[1]
        premium_until = row[2]

    if last_date != today:
        independent_count = 0
        cursor.execute(
            "UPDATE users SET independent_count = 0, independent_last_date = ? WHERE user_id = ?",
            (today, user_id)
        )
        conn.commit()

    premium_active = bool(premium_until and premium_until >= today)
    daily_limit = 10 if premium_active else 2

    if independent_count >= daily_limit:
        conn.close()

        if lang == "en":
            msg = (
                "🔒 Your daily independent work limit has been reached.\n\n"
                f"Today: {independent_count}/{daily_limit}"
            )
        elif lang == "ru":
            msg = (
                "🔒 Ваш дневной лимит самостоятельных работ закончился.\n\n"
                f"Сегодня: {independent_count}/{daily_limit}"
            )
        else:
            msg = (
                "🔒 Bugungi mustaqil ish limitingiz tugadi.\n\n"
                f"Bugun: {independent_count}/{daily_limit} ta"
            )

        await update.message.reply_text(msg)
        return

    conn.close()

    if lang == "en":
        waiting = "⏳ AI is preparing your independent work..."
        title = "📖 INDEPENDENT WORK"
        prompt = (
            "You are Student AI, an academic writing assistant. "
            "Write a detailed, clear and well-structured independent work "
            "in English for a student. Include a title, plan, introduction, "
            "main sections, conclusion and references. "
            "Make it informative and suitable for student study.\n\n"
            f"TOPIC:\n{topic}"
        )

    elif lang == "ru":
        waiting = "⏳ AI готовит вашу самостоятельную работу..."
        title = "📖 САМОСТОЯТЕЛЬНАЯ РАБОТА"
        prompt = (
            "Ты Student AI, помощник по академическому письму. "
            "Напиши подробную, понятную и хорошо структурированную "
            "самостоятельную работу на русском языке для студента. "
            "Включи заголовок, план, введение, основные разделы, "
            "заключение и список литературы.\n\n"
            f"ТЕМА:\n{topic}"
        )

    else:
        waiting = "⏳ AI mustaqil ishingizni tayyorlamoqda..."
        title = "📖 MUSTAQIL ISH"
        prompt = (
            "Sen Student AI, akademik yozuv yordamchisisan. "
            "Talaba uchun o‘zbek tilida batafsil, mazmunli va yaxshi "
            "tuzilgan mustaqil ish yoz. Unda mavzu nomi, reja, kirish, "
            "asosiy bo‘limlar, muhim ma'lumotlar, xulosa va foydalanilgan "
            "adabiyotlar bo‘lsin. Mavzuni tushunarli va o‘quv uchun foydali "
            "tarzda yorit.\n\n"
            f"MAVZU:\n{topic}"
        )

    await update.message.reply_text(waiting)

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.6-flash:generateContent"
    )

    headers = {
        "x-goog-api-key": GEMINI_WRITING_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = None
        result = None

        retry_delays = [0, 2, 5]

        for attempt, delay in enumerate(retry_delays, start=1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=60
                )

                print(
                    f"🌐 TRANSLATOR GEMINI attempt "
                    f"{attempt}/3: {response.status_code}"
                )

                if response.status_code == 200:
                    try:
                        result = response.json()
                    except ValueError:
                        result = None
                    break

                if response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < 3:
                        await asyncio.sleep(delay)
                        continue
                    break

                break

            except requests.exceptions.Timeout:
                print(
                    f"⏱️ TRANSLATOR TIMEOUT attempt {attempt}/3"
                )

                if attempt < 3:
                    await asyncio.sleep(delay)
                    continue
                break

            except requests.exceptions.RequestException as e:
                print(
                    f"🌐 TRANSLATOR NETWORK ERROR "
                    f"attempt {attempt}/3: {e}"
                )

                if attempt < 3:
                    await asyncio.sleep(delay)
                    continue
                break

        if response is None or result is None:
            await update.message.reply_text(
                "🌐 Tarjimon hozircha javob bera olmayapti.\n\n"
                "🔄 Iltimos, birozdan keyin yana urinib ko‘ring."
            )
            return

        if response.status_code != 200:
            if response.status_code == 503:
                await update.message.reply_text(
                "😔 Student AI hozir biroz band.\n"
                "⏳ So‘rovlar ko‘paygani sababli javob tayyorlash biroz kechikmoqda.\n"
                "🔄 Iltimos, bir necha soniyadan keyin yana urinib ko‘ring.\n"
                "💙 Noqulaylik uchun uzr!"
                )
            else:
                await update.message.reply_text(
                    f"❌ Gemini xatosi: {response.status_code}"
                )
            return

        if "candidates" not in result:
            await update.message.reply_text(
                "❌ Mustaqil ish tayyorlashda javob olinmadi."
            )
            return

        answer = result["candidates"][0]["content"]["parts"][0]["text"]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET independent_count = ?, independent_last_date = ? WHERE user_id = ?",
            (independent_count + 1, today, user_id)
        )

        conn.commit()
        conn.close()

        full_text = (
            f"{title}\n\n"
            f"{answer}\n\n"
            f"📊 Bugungi foydalanish: {independent_count + 1}/{daily_limit}"
        )

        # Telegram xabar uzunligini oshirib yubormaslik uchun bo'lib yuboramiz.
        max_length = 4000

        for i in range(0, len(full_text), max_length):
            await update.message.reply_text(
                full_text[i:i + max_length]
            )

    except Exception as e:
        print("❌ INDEPENDENT WORK ERROR:", type(e).__name__, e)
        await update.message.reply_text(
            f"❌ Mustaqil ish xatosi:\n{type(e).__name__}: {e}"
        )

async def programming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        text = (
            "💻 DASTURLASH YORDAMCHISI\n\n"
            "🐍 Python, algoritmlar, kod yozish va xatolarni tuzatishda yordam beraman.\n\n"
            "📝 Masalangizni yozing."
        )

    elif lang == "en":
        text = (
            "💻 PROGRAMMING ASSISTANT\n\n"
            "🐍 I can help with Python, algorithms, coding and debugging.\n\n"
            "📝 Write your programming question."
        )

    else:
        text = (
            "💻 ПОМОЩНИК ПО ПРОГРАММИРОВАНИЮ\n\n"
            "🐍 Помогу с Python, алгоритмами, кодом и исправлением ошибок.\n\n"
            "📝 Напишите свой вопрос."
        )

    reply_markup = ReplyKeyboardMarkup(
        [["⬅️ Orqaga"]],
        resize_keyboard=True
    )

    await update.message.reply_text(
        text,
        reply_markup=reply_markup
    )

async def programming_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lang = context.user_data.get("language", "uz")

    # ⬅️ Orqaga
    if text in ["⬅️ Orqaga", "⬅️ Back", "⬅️ Назад"]:
        context.user_data["programming_mode"] = False

        if lang == "uz":
            await uz_menu(update)
        elif lang == "en":
            await en_menu(update)
        else:
            await ru_menu(update)

        return

    from datetime import date
    import asyncio

    user_id = update.effective_user.id
    today = str(date.today())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT programming_count, programming_last_date, premium_until
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            """
            INSERT INTO users (
                user_id,
                programming_count,
                programming_last_date
            )
            VALUES (?, 0, ?)
            """,
            (user_id, today)
        )
        conn.commit()

        programming_count = 0
        programming_last_date = today
        premium_until = None
    else:
        programming_count, programming_last_date, premium_until = user

    if programming_last_date != today:
        programming_count = 0

        cursor.execute(
            """
            UPDATE users
            SET programming_count = 0,
                programming_last_date = ?
            WHERE user_id = ?
            """,
            (today, user_id)
        )
        conn.commit()

    conn.close()

    # ============================================================
    # ⭐ PREMIUM — 300 TA / 30 KUN
    # 🆓 FREE — 5 TA / KUN
    # ============================================================

    premium_active = (
        premium_until is not None
        and premium_until != ""
        and premium_until >= today
    )

    if premium_active:

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT premium_programming_count,
                   premium_programming_month
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )

        row = cursor.fetchone()

        if row:
            premium_programming_count = row[0] or 0
            premium_programming_cycle = row[1]
        else:
            premium_programming_count = 0
            premium_programming_cycle = None

        current_premium_cycle = premium_until

        if premium_programming_cycle != current_premium_cycle:

            premium_programming_count = 0

            cursor.execute(
                """
                UPDATE users
                SET premium_programming_count = 0,
                    premium_programming_month = ?
                WHERE user_id = ?
                """,
                (current_premium_cycle, user_id)
            )

            conn.commit()

        conn.close()

        if premium_programming_count >= 300:

            if lang == "uz":
                limit_text = (
                    "⭐ Premium dasturlash limitingiz tugadi.\n\n"
                    "📊 Premium davrida: 300/300 ta so‘rov ishlatildi.\n"
                    "📅 Limit yangi Premium davri boshlanganda yangilanadi."
                )
            elif lang == "en":
                limit_text = (
                    "⭐ Your Premium programming limit has been reached.\n\n"
                    "📊 Premium period: 300/300 requests used.\n"
                    "📅 The limit resets with a new Premium period."
                )
            else:
                limit_text = (
                    "⭐ Ваш лимит Premium программирования закончился.\n\n"
                    "📊 За Premium-период: 300/300 запросов использовано.\n"
                    "📅 Лимит обновится с новым Premium-периодом."
                )

            await update.message.reply_text(limit_text)
            context.user_data["programming_mode"] = False
            return

    else:

        # 🆓 FREE — 5 TA / KUN
        if programming_count >= 5:

            if lang == "uz":
                limit_text = (
                    "⛔ Bugungi bepul dasturlash limitingiz tugadi.\n\n"
                    "⭐ Premium orqali 30 kun davomida 300 ta "
                    "dasturlash so‘rovidan foydalanishingiz mumkin."
                )
            elif lang == "en":
                limit_text = (
                    "⛔ Your free programming limit for today is over.\n\n"
                    "⭐ Premium gives you 300 programming requests "
                    "during the Premium period."
                )
            else:
                limit_text = (
                    "⛔ Ваш бесплатный лимит программирования "
                    "на сегодня закончился.\n\n"
                    "⭐ Premium даёт 300 запросов программирования "
                    "за Premium-период."
                )

            await update.message.reply_text(limit_text)
            context.user_data["programming_mode"] = False
            return

    user_question = text

    # 🌍 AI prompt
    if lang == "uz":
        prompt = (
            "Sen Student AI dasturlash yordamchisisan. "
            "Foydalanuvchining dasturlash savoliga o'zbek tilida "
            "tushunarli va aniq javob ber. "
            "Kerak bo'lsa kod yoz. "
            "Koddagi xatolarni tushuntir. "
            "Javobni keraksiz uzun qilma.\n\n"
            f"Foydalanuvchi savoli:\n{user_question}"
        )
    elif lang == "en":
        prompt = (
            "You are the Student AI programming assistant. "
            "Answer the programming question clearly in English. "
            "Provide code when needed and explain errors. "
            "Do not make the answer unnecessarily long.\n\n"
            f"User question:\n{user_question}"
        )
    else:
        prompt = (
            "Ты помощник Student AI по программированию. "
            "Отвечай понятно и точно на русском языке. "
            "При необходимости пиши код и объясняй ошибки. "
            "Не делай ответ слишком длинным.\n\n"
            f"Вопрос пользователя:\n{user_question}"
        )

    await update.message.reply_text(
        "⏳ Kodni tahlil qilyapman..."
    )

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.6-flash:generateContent"
    )

    headers = {
        "x-goog-api-key": GEMINI_PROGRAMMING_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    # 🔄 Gemini band bo'lsa avtomatik qayta urinish
    max_retries = 3
    retry_delays = [2, 5, 10]

    try:
        response = None
        result = None

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=60
                )

                result = response.json()

                print(
                    f"🔍 PROGRAMMING GEMINI "
                    f"attempt {attempt + 1}/{max_retries}: "
                    f"{response.status_code}"
                )

                # Muvaffaqiyat
                if response.status_code == 200:
                    break

                # Server band / vaqtinchalik xato
                if response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < max_retries - 1:
                        await update.message.reply_text(
                            "⏳ AI serveri hozir band. "
                            "Qayta urinib ko'ryapman..."
                        )
                        await asyncio.sleep(retry_delays[attempt])
                        continue

                break

            except requests.exceptions.Timeout:
                print(
                    f"⏱️ PROGRAMMING TIMEOUT "
                    f"attempt {attempt + 1}/{max_retries}"
                )

                if attempt < max_retries - 1:
                    await update.message.reply_text(
                        "⏳ AI serveridan javob kelmadi. "
                        "Qayta urinib ko'ryapman..."
                    )
                    await asyncio.sleep(retry_delays[attempt])
                    continue

                await update.message.reply_text(
                    "⏳ AI serveri hozir javob berishga ulgurmayapti.\n\n"
                    "Birozdan keyin yana urinib ko'ring."
                )
                return

        if response is None or result is None:
            await update.message.reply_text(
                "❌ AI bilan bog'lanib bo'lmadi. "
                "Birozdan keyin yana urinib ko'ring."
            )
            return

        if response.status_code != 200:
            if response.status_code in [429, 500, 502, 503, 504]:
                await update.message.reply_text(
                    "😔 AI serveri hozir juda band.\n\n"
                    "🔄 Bir necha soniyadan keyin yana urinib ko'ring."
                )
            else:
                await update.message.reply_text(
                    f"❌ Gemini xatosi ({response.status_code}).\n\n"
                    "Birozdan keyin yana urinib ko'ring."
                )
            return

        if "candidates" not in result:
            await update.message.reply_text(
                "😔 AI hozir javob tayyorlay olmadi.\n\n"
                "Birozdan keyin yana urinib ko'ring."
            )
            return

        answer = (
            result["candidates"][0]
            ["content"]["parts"][0]["text"]
        )

        # ========================================================
        # 💾 FAQAT MUVAFFAQIYATLI JAVOBDAN KEYIN HISOBLASH
        # ========================================================

        if not premium_active:

            programming_count += 1

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE users
                SET programming_count = ?,
                    programming_last_date = ?
                WHERE user_id = ?
                """,
                (programming_count, today, user_id)
            )

            conn.commit()
            conn.close()

            limit_text = (
                f"\\n\\n📊 Bugungi bepul dasturlash savollari: "
                f"{programming_count}/5"
            )

        else:

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE users
                SET premium_programming_count =
                        premium_programming_count + 1,
                    premium_programming_month = ?
                WHERE user_id = ?
                """,
                (premium_until, user_id)
            )

            conn.commit()
            conn.close()

            premium_programming_count += 1

            limit_text = (
                f"\\n\\n⭐ Premium dasturlash: "
                f"{premium_programming_count}/300"
            )

        await update.message.reply_text(
            f"💻 Javob:\n\n{answer}{limit_text}"
        )

    except Exception as e:
        print("❌ PROGRAMMING ERROR:", e)

        await update.message.reply_text(
            "❌ Dasturlash yordamchisida vaqtinchalik xatolik yuz berdi.\n\n"
            "Birozdan keyin yana urinib ko'ring."
        )


async def calculator_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lang = context.user_data.get("language", "uz")

    # ⬅️ Orqaga
    if text in ["⬅️ Orqaga", "⬅️ Back", "⬅️ Назад"]:
        context.user_data["calculator_mode"] = False

        if lang == "uz":
            await uz_menu(update)
        elif lang == "en":
            await en_menu(update)
        else:
            await ru_menu(update)

        return

    if not context.user_data.get("calculator_mode"):
        return

    import requests
    from datetime import date

    user_id = update.effective_user.id
    today = str(date.today())

    question_count, last_date, premium_until = get_user(user_id)

    # ⭐ Premium holatini tekshirish
    premium_active = (
        premium_until is not None
        and premium_until != ""
        and premium_until >= today
    )

    # ============================================================
    # ⭐ PREMIUM — 300 TA / 30 KUN
    # 🆓 FREE — 5 TA / KUN
    # ============================================================

    if premium_active:

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT premium_math_count,
                   premium_math_month
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )

        row = cursor.fetchone()

        if row:
            premium_math_count = row[0] or 0
            premium_math_cycle = row[1]
        else:
            premium_math_count = 0
            premium_math_cycle = None

        current_premium_cycle = premium_until

        if premium_math_cycle != current_premium_cycle:
            premium_math_count = 0

            cursor.execute(
                """
                UPDATE users
                SET premium_math_count = 0,
                    premium_math_month = ?
                WHERE user_id = ?
                """,
                (current_premium_cycle, user_id)
            )

            conn.commit()

        conn.close()

        if premium_math_count >= 300:

            if lang == "uz":
                limit_text = (
                    "⭐ Premium Aqlli matematika limitingiz tugadi.\n\n"
                    "📊 Premium davrida: 300/300 ta savol ishlatildi.\n"
                    "📅 Limit yangi Premium davri boshlanganda yangilanadi."
                )
            elif lang == "en":
                limit_text = (
                    "⭐ Your Premium Smart Math limit has been reached.\n\n"
                    "📊 Premium period: 300/300 questions used.\n"
                    "📅 The limit resets with a new Premium period."
                )
            else:
                limit_text = (
                    "⭐ Ваш лимит Premium для Умной математики закончился.\n\n"
                    "📊 За Premium-период: 300/300 вопросов использовано.\n"
                    "📅 Лимит обновится с новым Premium-периодом."
                )

            await update.message.reply_text(limit_text)
            return

    else:

        # 🆓 FREE — 5 TA / KUN
        if last_date != today:
            question_count = 0
            update_question_count(user_id, 0, today)

        if question_count >= 5:

            if lang == "uz":
                limit_text = (
                    "⛔ Bugungi Aqlli matematika limitingiz tugadi.\n\n"
                    "⭐ Premium orqali 30 kun davomida 300 ta "
                    "matematik savoldan foydalanishingiz mumkin."
                )
            elif lang == "en":
                limit_text = (
                    "⛔ Your free Smart Math limit for today is over.\n\n"
                    "⭐ Premium gives you 300 math questions "
                    "during the Premium period."
                )
            else:
                limit_text = (
                    "⛔ Ваш бесплатный лимит Умной математики "
                    "на сегодня закончился.\n\n"
                    "⭐ Premium даёт 300 математических вопросов "
                    "за Premium-период."
                )

            await update.message.reply_text(limit_text)
            return

    # 🧠 Aqlli matematika uchun maxsus prompt
    if lang == "uz":
        prompt = (
            "Sen Student AI ichidagi 'Aqlli matematika' yordamchisisan. "
            "Asosiy vazifang foydalanuvchining matematika bilan bog'liq savollarini "
            "aniq, tushunarli va bosqichma-bosqich yechish.\n\n"

            "Quyidagi mavzularda yordam ber: "
            "arifmetik amallar, tenglamalar, tengsizliklar, kasrlar, foizlar, "
            "darajalar, ildizlar, algebra, geometriya, trigonometriya, "
            "funksiyalar, formulalar, hosila, integral va boshqa matematika masalalari.\n\n"

            "Javob qoidalari:\n"
            "• Har bir hisoblashni aniq tekshir.\n"
            "• Murakkab masalani bosqichma-bosqich tushuntir.\n"
            "• Keraksiz uzun javob bermagin.\n"
            "• Yakuniy javobni aniq ko'rsat.\n"
            "• Oddiy va chiroyli Telegram formatidan foydalan.\n"
            "• LaTeX ishlatma.\n"
            "• $ belgilarini ishlatma.\n"
            "• \\text{} kabi belgilarni ishlatma.\n"
            "• Kvadrat qavslar [ ] bilan matematik ifoda yozma.\n"
            "• Matematik amallarda oddiy belgilarni ishlat: +, −, ×, ÷, =, •.\n"
            "• Zarur bo'lsa raqamlangan qadamlar va • belgilaridan foydalan.\n"
            "• Formulalarni oddiy matn ko'rinishida yoz.\n\n"

            f"Foydalanuvchi savoli:\n{text}"
        )

    elif lang == "en":
        prompt = (
            "You are the 'Smart Math' assistant inside Student AI. "
            "Your main task is to solve mathematics questions accurately, clearly "
            "and step by step.\n\n"

            "Help with arithmetic, equations, inequalities, fractions, percentages, "
            "powers, roots, algebra, geometry, trigonometry, functions, formulas, "
            "derivatives, integrals and other mathematics problems.\n\n"

            "Answer rules:\n"
            "• Check every calculation carefully.\n"
            "• Explain difficult problems step by step.\n"
            "• Do not make the answer unnecessarily long.\n"
            "• Clearly show the final answer.\n"
            "• Use simple Telegram-friendly formatting.\n"
            "• Do not use LaTeX.\n"
            "• Do not use $ signs.\n"
            "• Do not use \\text{}.\n"
            "• Do not use square brackets [ ] for mathematical expressions.\n"
            "• Use simple symbols such as +, −, ×, ÷, = and •.\n\n"

            f"User question:\n{text}"
        )

    else:
        prompt = (
            "Ты помощник 'Умная математика' внутри Student AI. "
            "Твоя основная задача — точно, понятно и пошагово решать "
            "математические задачи пользователя.\n\n"

            "Помогай с арифметикой, уравнениями, неравенствами, дробями, "
            "процентами, степенями, корнями, алгеброй, геометрией, "
            "тригонометрией, функциями, формулами, производными, интегралами "
            "и другими математическими задачами.\n\n"

            "Правила ответа:\n"
            "• Проверяй вычисления.\n"
            "• Сложные задачи объясняй пошагово.\n"
            "• Не делай ответ unnecessarily длинным.\n"
            "• Чётко показывай итоговый ответ.\n"
            "• Не используй LaTeX.\n"
            "• Не используй знаки $.\n"
            "• Не используй \\text{}.\n"
            "• Не используй квадратные скобки [ ] для математических выражений.\n"
            "• Используй простые знаки: +, −, ×, ÷, = и •.\n\n"

            f"Вопрос пользователя:\n{text}"
        )

    if lang == "uz":
        wait_text = "⏳ Aqlli matematika hisoblayapti..."
    elif lang == "en":
        wait_text = "⏳ Smart Math is calculating..."
    else:
        wait_text = "⏳ Умная математика считает..."

    await update.message.reply_text(wait_text)

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.6-flash:generateContent"
    )

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
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

        print("🧠 SMART MATH GEMINI:", result)

        # ⚠️ Gemini quota / API limitini alohida aniqlash
        if response.status_code == 429 or result.get("error", {}).get("code") == 429:
            print("⚠️ SMART MATH QUOTA:", result)

            await update.message.reply_text(
                "⏳ Aqlli matematika hozircha vaqtincha band.\n\n"
                "🔄 AI xizmatining bepul foydalanish limiti to‘lib qolgan.\n"
                "Bu sizning savolingiz bilan bog‘liq xato emas.\n\n"
                "🕐 Xizmat limiti qayta tiklangach, Aqlli matematika yana odatdagidek ishlaydi.\n\n"
                "💡 Iltimos, keyinroq yana urinib ko‘ring."
            )
            return

        if "candidates" in result:
            answer = result["candidates"][0]["content"]["parts"][0]["text"]

            # 🧹 Keraksiz matematik formatlarini tozalash
            answer = answer.replace("$", "")
            answer = answer.replace("\\text{", "")
            answer = answer.replace("\\textbf{", "")
            answer = answer.replace("\\(", "")
            answer = answer.replace("\\)", "")
            answer = answer.replace("\\[", "")
            answer = answer.replace("\\]", "")

            # 🆓 Faqat muvaffaqiyatli javobdan keyin limitni oshiramiz
            if not premium_active:

                question_count += 1

                update_question_count(
                    user_id,
                    question_count,
                    today
                )

                limit_text = (
                    f"\n\n📊 Bugungi bepul matematik savollar: "
                    f"{question_count}/5"
                )

            else:

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE users
                    SET premium_math_count = premium_math_count + 1,
                        premium_math_month = ?
                    WHERE user_id = ?
                    """,
                    (premium_until, user_id)
                )

                conn.commit()
                conn.close()

                premium_math_count += 1

                limit_text = (
                    f"\n\n⭐ Premium Aqlli matematika: "
                    f"{premium_math_count}/300"
                )

            await update.message.reply_text(
                answer + limit_text
            )

        else:
            print("❌ SMART MATH GEMINI JAVOBIDA CANDIDATES YO'Q:", result)

            await update.message.reply_text(
                "⚠️ Aqlli matematika hozircha javob bera olmayapti.\n\n"
                "🔄 AI xizmatining vaqtinchalik limiti to‘lib qolgan.\n"
                "Iltimos, birozdan keyin yana urinib ko‘ring.\n\n"
                "💡 Xizmatingiz qayta tiklangach, savolingizga odatdagidek javob beramiz."
            )

    except Exception as e:
        print("❌ SMART MATH ERROR:", e)

        await update.message.reply_text(
            "❌ Matematikani hisoblashda xatolik yuz berdi.\n"
            "Iltimos, birozdan keyin qayta urinib ko'ring."
        )

async def pdf_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "uz")

    if lang == "ru":
        keyboard = [
            ["🖼️ Сделать PDF из изображений"],
            ["📝 Краткое содержание PDF"],
            ["⬅️ Назад"]
        ]
        message = (
            "📄 ПОМОЩНИК ПО ДОКУМЕНТАМ\n\n"
            "Выберите нужную услугу:"
        )

    elif lang == "en":
        keyboard = [
            ["🖼️ Images to PDF"],
            ["📝 PDF Summary"],
            ["⬅️ Back"]
        ]
        message = (
            "📄 DOCUMENT ASSISTANT\n\n"
            "Choose the required service:"
        )

    else:
        keyboard = [
            ["🖼️ Rasmlarni PDF qilish"],
            ["📝 PDF xulosa"],
            ["⬅️ Orqaga"]
        ]
        message = (
            "📄 HUJJATLAR YORDAMCHISI\n\n"
            "Kerakli xizmatni tanlang:"
        )

    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


# ============================================================
# 🖼️ RASMLARNI PDF QILISH
# ============================================================

async def start_image_to_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pdf_collecting"] = True
    context.user_data["pdf_images"] = []

    keyboard = [
        ["✅ PDF tayyorlash"],
        ["❌ Bekor qilish"],
        ["⬅️ Orqaga"]
    ]

    await update.message.reply_text(
        "🖼️ RASMLARNI PDF QILISH\n\n"
        "Rasmlaringizni ketma-ket yuboring.\n\n"
        "🆓 Bepul foydalanuvchi: kuniga 5 ta rasm.\n"
        "⭐ Premium foydalanuvchi: bir PDF uchun 50 ta rasm.\n\n"
        "Rasmlarni yuborib bo‘lgach,\n"
        "«✅ PDF tayyorlash» tugmasini bosing.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def pdf_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("pdf_collecting"):
        return

    user_id = update.effective_user.id
    today = __import__("datetime").date.today().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT pdf_image_count,
               pdf_image_last_date,
               premium_until
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            """
            INSERT INTO users
            (user_id, pdf_image_count, pdf_image_last_date)
            VALUES (?, 0, ?)
            """,
            (user_id, today)
        )
        conn.commit()

        pdf_count = 0
        last_date = today
        premium_until = None

    else:
        pdf_count = row[0] or 0
        last_date = row[1]
        premium_until = row[2]

    # Yangi kun
    if last_date != today:

        pdf_count = 0

        cursor.execute(
            """
            UPDATE users
            SET pdf_image_count = 0,
                pdf_image_last_date = ?
            WHERE user_id = ?
            """,
            (today, user_id)
        )

        conn.commit()

    # Premium tekshirish
    premium_active = (
        premium_until is not None
        and premium_until != ""
        and premium_until >= today
    )

    # 🆓 Bepul limit tugagan bo‘lsa
    if not premium_active and pdf_count >= 5:

        conn.close()

        await update.message.reply_text(
            "⚠️ Bugungi bepul PDF rasmlar limitingiz tugadi.\n\n"
            "📸 Bugun 5 ta rasm ishlatdingiz.\n"
            "🌅 Ertaga yana 5 ta rasm beriladi.\n\n"
            "⭐ Premium orqali ko‘proq foydalanishingiz mumkin."
        )

        return

    images = context.user_data.setdefault(
        "pdf_images",
        []
    )

    # Bitta PDF uchun maksimal 50 ta rasm
    if len(images) >= 50:

        conn.close()

        await update.message.reply_text(
            "⛔ Bitta PDF uchun maksimal 50 ta rasm."
        )

        return

    photo = update.message.photo[-1]

    # Telegram file_id saqlanadi
    images.append(photo.file_id)

    # Hozircha limit hisoblagichini shu yerda oshiramiz
    # PDF muvaffaqiyatli tayyorlanganda make_pdf_from_images
    # tomonidan yana hisoblanmasligi kerak.
    if not premium_active:

        pdf_count += 1

        cursor.execute(
            """
            UPDATE users
            SET pdf_image_count = ?,
                pdf_image_last_date = ?
            WHERE user_id = ?
            """,
            (
                pdf_count,
                today,
                user_id
            )
        )

        conn.commit()

    conn.close()

    if premium_active:

        await update.message.reply_text(
            f"✅ {len(images)} ta rasm qabul qilindi.\n\n"
            "⭐ Premium foydalanuvchi.\n\n"
            "Yana rasm yuboring yoki "
            "«✅ PDF tayyorlash» tugmasini bosing."
        )

    else:

        await update.message.reply_text(
            f"✅ {pdf_count}/5 ta bepul rasm ishlatildi.\n\n"
            "Yana rasm yuboring yoki "
            "«✅ PDF tayyorlash» tugmasini bosing."
        )

async def make_pdf_from_images(update: Update, context: ContextTypes.DEFAULT_TYPE):

    images = context.user_data.get(
        "pdf_images",
        []
    )

    if not images:

        await update.message.reply_text(
            "❌ Hali hech qanday rasm yubormadingiz."
        )

        return

    user_id = update.effective_user.id

    try:

        from PIL import Image
        from io import BytesIO

        await update.message.reply_text(
            "⏳ Rasmlar PDF faylga birlashtirilmoqda..."
        )

        pil_images = []

        # Telegramdan rasmlarni olish
        for file_id in images:

            telegram_file = await context.bot.get_file(
                file_id
            )

            image_bytes = (
                await telegram_file.download_as_bytearray()
            )

            img = Image.open(
                BytesIO(image_bytes)
            ).convert("RGB")

            pil_images.append(img)

        if not pil_images:

            await update.message.reply_text(
                "❌ Rasmlarni olishda xatolik yuz berdi."
            )

            return

        # PDF nomi
        pdf_path = (
            f"Student_AI_{user_id}.pdf"
        )

        first_image = pil_images[0]
        other_images = pil_images[1:]

        # PDF yaratish
        first_image.save(
            pdf_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=other_images
        )

        # Telegramga yuborish
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT pdf_image_count,
                   pdf_image_last_date,
                   premium_until
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )

        limit_row = cursor.fetchone()
        conn.close()

        today = __import__("datetime").date.today().isoformat()

        premium_active = (
            limit_row is not None
            and limit_row[2] is not None
            and limit_row[2] != ""
            and limit_row[2] >= today
        )

        if premium_active:
            limit_display = (
                f"⭐ Premium PDF: {len(images)}/50"
            )
        else:
            free_count = (
                limit_row[0]
                if limit_row is not None and limit_row[1] == today
                else 0
            )

            limit_display = (
                f"📊 Bugungi foydalanish: {free_count}/5"
            )

        with open(
            pdf_path,
            "rb"
        ) as pdf_file:

            await update.message.reply_document(
                document=pdf_file,
                filename="Student_AI.pdf",
                caption=(
                    "✅ PDF tayyor!\n\n"
                    f"🖼️ Rasmlar soni: {len(images)} ta\n"
                    f"{limit_display}\n"
                    "🤖 Student AI"
                )
            )

        # Rasmlarni yopish
        for img in pil_images:

            try:
                img.close()

            except Exception:
                pass

        # PDFni o'chirish
        try:

            os.remove(pdf_path)

        except Exception:

            pass

        # Jarayonni tozalash
        context.user_data["pdf_images"] = []
        context.user_data["pdf_collecting"] = False

    except Exception as e:

        print(
            "PDF ERROR:",
            e
        )

        await update.message.reply_text(
            "❌ PDF yaratishda xatolik yuz berdi.\n\n"
            f"Texnik xato: {e}"
        )


# ============================================================
# ❌ PDFNI BEKOR QILISH
# ============================================================

async def cancel_pdf_images(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["pdf_images"] = []
    context.user_data["pdf_collecting"] = False

    await update.message.reply_text(
        "❌ PDF tayyorlash bekor qilindi."
    )



# ============================================================
# 📄 PDFDAN MATN OLISH
# ============================================================

# ============================================================
# 🤖 GEMINI PDF YORDAMCHI
# ============================================================
def gemini_pdf_request(pdf_path, prompt):
    try:
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY topilmadi")
            return None

        if not os.path.exists(pdf_path):
            print("❌ PDF fayl topilmadi:", pdf_path)
            return None

        import base64

        with open(pdf_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode("utf-8")

        full_prompt = (
            prompt
            + "\n\n"
            + "MUHIM: PDF faylni to‘g‘ridan-to‘g‘ri tahlil qil. "
            + "Agar PDF oddiy matnli bo‘lsa, matnini o‘qi. "
            + "Agar PDF skanerlangan yoki sahifalari rasm ko‘rinishida bo‘lsa, "
            + "sahifalardagi matn va ma’lumotlarni rasmdan o‘qi. "
            + "PDF qaysi tilda bo‘lishidan qat’i nazar, yuqoridagi promptda "
            + "ko‘rsatilgan javob tilida javob ber."
        )

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.6-flash:generateContent"
        )

        headers = {
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json"
        }

        data = {
            "contents": [
                {
                    "parts": [
                        {"text": full_prompt},
                        {
                            "inline_data": {
                                "mime_type": "application/pdf",
                                "data": pdf_data
                            }
                        }
                    ]
                }
            ]
        }

        print("⏳ Gemini'ga PDF faylning o‘zi yuborilmoqda...")
        print("📄 PDF hajmi:", os.path.getsize(pdf_path), "bayt")

        import time

        response = None

        retry_delays = [0, 5, 10]

        for attempt, delay in enumerate(retry_delays, start=1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=180
                )

                print(
                    f"🔍 GEMINI PDF attempt {attempt}/3: "
                    f"{response.status_code}"
                )

                if response.status_code == 200:
                    break

                if response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < 3:
                        time.sleep(delay)
                        continue

                break

            except requests.exceptions.Timeout:
                print(
                    f"⏱️ GEMINI PDF TIMEOUT attempt {attempt}/3"
                )

                if attempt < 3:
                    time.sleep(delay)
                    continue

                return None

            except requests.exceptions.RequestException as e:
                print(
                    f"🌐 GEMINI PDF NETWORK ERROR "
                    f"attempt {attempt}/3: {e}"
                )

                if attempt < 3:
                    time.sleep(delay)
                    continue

                return None

        if response is None:
            print("❌ GEMINI PDF: response olinmadi")
            return None

        print("🔍 GEMINI PDF STATUS:", response.status_code)

        try:
            result = response.json()
        except Exception:
            print("❌ Gemini JSON javob qaytarmadi")
            print("❌ RESPONSE:", response.text[:2000])
            return None

        if response.status_code != 200:
            print("❌ GEMINI PDF HTTP ERROR:", response.status_code)
            print("❌ GEMINI PDF RESPONSE:", result)

            if response.status_code == 429:
                print("⚠️ GEMINI QUOTA/RATE LIMIT: 429")

            return None

        candidates = result.get("candidates", [])

        if not candidates:
            print("❌ GEMINI PDF: candidates topilmadi")
            print("🔍 RESPONSE:", result)
            return None

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        texts = []

        for part in parts:
            if "text" in part:
                texts.append(part["text"])

        answer = "\n".join(texts).strip()

        if not answer:
            print("❌ GEMINI PDF: bo‘sh javob")
            print("🔍 RESPONSE:", result)
            return None

        print("✅ GEMINI PDF XULOSA TAYYOR")
        return answer

    except requests.exceptions.Timeout:
        print("❌ GEMINI PDF TIMEOUT")
        return None

    except requests.exceptions.RequestException as e:
        print("❌ GEMINI PDF NETWORK ERROR:", e)
        return None

    except Exception as e:
        print("❌ GEMINI PDF REQUEST ERROR:", e)
        return None


async def pdf_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get("language", "uz")
    today = __import__("datetime").date.today().isoformat()

    pdf_path = context.user_data.get("pdf_file")

    if not pdf_path or not os.path.exists(pdf_path):
        if lang == "ru":
            msg = "❌ Сначала отправьте PDF-файл."
        elif lang == "en":
            msg = "❌ Please send a PDF file first."
        else:
            msg = "❌ Avval PDF fayl yuboring."

        await update.message.reply_text(msg)
        return

    # ============================================================
    # 💎 PDF XULOSA LIMITI
    # FREE = 3 / kun
    # PREMIUM = 30 / oy
    # ============================================================

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT pdf_summary_count,
               pdf_summary_last_date,
               pdf_summary_premium_count,
               pdf_summary_premium_month,
               premium_until
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            """
            INSERT INTO users
            (
                user_id,
                pdf_summary_count,
                pdf_summary_last_date,
                pdf_summary_premium_count,
                pdf_summary_premium_month
            )
            VALUES (?, 0, ?, 0, ?)
            """,
            (
                user_id,
                today,
                0,
                today[:7]
            )
        )
        conn.commit()

        pdf_summary_count = 0
        last_date = today
        premium_count = 0
        premium_month = today[:7]
        premium_until = None

    else:
        pdf_summary_count = row[0] or 0
        last_date = row[1]
        premium_count = row[2] or 0
        premium_month = row[3]
        premium_until = row[4]

    # 🆓 Free kunlik hisobni yangilash
    if last_date != today:
        pdf_summary_count = 0

        cursor.execute(
            """
            UPDATE users
            SET pdf_summary_count = 0,
                pdf_summary_last_date = ?
            WHERE user_id = ?
            """,
            (today, user_id)
        )

        conn.commit()

    # ⭐ Premium holatini tekshirish
    premium_active = (
        premium_until is not None
        and premium_until != ""
        and premium_until >= today
    )

    # ⭐ Premium 30 kunlik davrini tekshirish
    # Premium sotib olingan yangi davrda hisoblagich 0 dan boshlanadi.
    premium_cycle = premium_until if premium_active else today[:7]

    if premium_active and premium_month != premium_cycle:
        premium_count = 0

        cursor.execute(
            """
            UPDATE users
            SET pdf_summary_premium_count = 0,
                pdf_summary_premium_month = ?
            WHERE user_id = ?
            """,
            (premium_cycle, user_id)
        )

        conn.commit()

    # 🆓 FREE — 3 ta / kun
    if not premium_active and pdf_summary_count >= 3:
        conn.close()

        if lang == "ru":
            msg = (
                "🔒 Ваш дневной лимит PDF-резюме закончился.\n\n"
                "Сегодня доступно: 3 PDF.\n"
                "⭐ Premium позволяет использовать больше."
            )
        elif lang == "en":
            msg = (
                "🔒 Your daily PDF summary limit has been reached.\n\n"
                "You can use 3 PDF summaries per day.\n"
                "⭐ Premium allows more usage."
            )
        else:
            msg = (
                "🔒 Bepul PDF xulosa limitingiz tugadi.\n\n"
                "Kuniga 3 ta PDF xulosa mavjud.\n"
                "⭐ Premium orqali ko‘proq foydalanishingiz mumkin."
            )

        await update.message.reply_text(msg)
        return

    # ⭐ PREMIUM — 30 ta / oy
    if premium_active and premium_count >= 30:
        conn.close()

        if lang == "ru":
            msg = (
                "⭐ Premium PDF xulosa limitingiz tugadi.\n\n"
                "📊 Bu oy: 30/30 ta PDF xulosa ishlatildi.\n"
                "📅 Limit keyingi oy yangilanadi."
            )
        elif lang == "en":
            msg = (
                "⭐ Your Premium PDF summary limit has been reached.\n\n"
                "📊 This month: 30/30 PDF summaries used.\n"
                "📅 The limit resets next month."
            )
        else:
            msg = (
                "⭐ Premium PDF xulosa limitingiz tugadi.\n\n"
                "📊 Bu oy: 30/30 ta PDF xulosa ishlatildi.\n"
                "📅 Limit keyingi oy yangilanadi."
            )

        await update.message.reply_text(msg)
        return

    conn.close()

    # ============================================================
    # ⏳ KUTILMOQDA
    # ============================================================

    if lang == "ru":
        waiting = (
            "⏳ PDF-файл читается AI, "
            "готовится краткое содержание..."
        )
    elif lang == "en":
        waiting = (
            "⏳ The AI is reading the PDF "
            "and preparing a short summary..."
        )
    else:
        waiting = (
            "⏳ PDF fayl AI tomonidan o‘qilmoqda "
            "va qisqa xulosa tayyorlanmoqda..."
        )

    await update.message.reply_text(waiting)

    # ============================================================
    # 🌐 TILGA MOS PROMPT
    # ============================================================

    if lang == "ru":
        prompt = (
            "Ты помощник Student AI. "
            "Проанализируй предоставленный PDF-документ. "
            "Сделай понятное и содержательное краткое резюме "
            "для студента.\n\n"
            "Укажи основную тему, главные мысли, важную "
            "информацию и основные выводы.\n\n"
            "Если PDF содержит таблицы, изображения или "
            "сканированные страницы, постарайся учитывать "
            "их содержание.\n\n"
            "ВАЖНО: независимо от языка самого PDF, "
            "весь ответ напиши ТОЛЬКО НА РУССКОМ ЯЗЫКЕ."
        )
        title = "📝 КРАТКОЕ СОДЕРЖАНИЕ PDF"

    elif lang == "en":
        prompt = (
            "You are Student AI, an AI assistant for students. "
            "Analyze the provided PDF document carefully.\n\n"
            "Create a clear, useful and well-structured summary "
            "for a student.\n\n"
            "Include:\n"
            "1. Main topic\n"
            "2. Main ideas\n"
            "3. Important information\n"
            "4. Key conclusions\n"
            "5. Useful points for a student\n\n"
            "If the PDF contains tables, images, scanned pages "
            "or text in another language, analyze their content "
            "as accurately as possible.\n\n"
            "IMPORTANT: regardless of the language of the PDF, "
            "write the entire answer ONLY IN ENGLISH."
        )
        title = "📝 PDF SUMMARY"

    else:
        prompt = (
            "Sen Student AI yordamchisisan. "
            "Berilgan PDF hujjatni tahlil qilib, "
            "talaba uchun tushunarli va mazmunli qisqa "
            "xulosa tayyorla.\n\n"
            "Asosiy mavzu, asosiy fikrlar, muhim ma'lumotlar "
            "va asosiy xulosalarni ber.\n\n"
            "Agar PDF ichida jadvallar, rasmlar yoki "
            "skanerlangan sahifalar bo‘lsa, ularning "
            "mazmunini ham imkon qadar hisobga ol.\n\n"
            "MUHIM: PDF qaysi tilda bo‘lishidan qat'i nazar, "
            "butun javobni FAQAT O‘ZBEK TILIDA yoz."
        )
        title = "📝 PDF XULOSA"

    # ============================================================
    # 🤖 GEMINI
    # ============================================================

    answer = gemini_pdf_request(pdf_path, prompt)

    if not answer:
        if lang == "ru":
            msg = (
                "❌ Не удалось подготовить резюме PDF.\n\n"
                "Попробуйте ещё раз через некоторое время."
            )
        elif lang == "en":
            msg = (
                "❌ I couldn't prepare the PDF summary.\n\n"
                "Please try again later."
            )
        else:
            msg = (
                "❌ PDF uchun xulosa tayyorlay olmadim.\n\n"
                "Birozdan keyin yana urinib ko‘ring."
            )

        await update.message.reply_text(msg)
        return

    # ============================================================
    # 💾 FAQAT MUVAFFAQIYATLI JAVOBDAN KEYIN LIMITNI OSHIRISH
    # ============================================================

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if premium_active:

        premium_count += 1

        cursor.execute(
            """
            UPDATE users
            SET pdf_summary_premium_count = ?,
                pdf_summary_premium_month = ?
            WHERE user_id = ?
            """,
            (
                premium_count,
                premium_cycle,
                user_id
            )
        )

    else:

        cursor.execute(
            """
            UPDATE users
            SET pdf_summary_count = ?,
                pdf_summary_last_date = ?
            WHERE user_id = ?
            """,
            (
                pdf_summary_count + 1,
                today,
                user_id
            )
        )

    conn.commit()
    conn.close()

    # ============================================================
    # 📤 TELEGRAM UZUNLIK CHEGARASI
    # Javobni xavfsiz ravishda bo‘lib yuboramiz.
    # ============================================================

    full_message = title + "\n\n" + answer

    if premium_active:
        full_message += (
            f"\n\n⭐ Premium PDF xulosalar: "
            f"{premium_count}/30"
        )

    MAX_LENGTH = 3500

    if len(full_message) <= MAX_LENGTH:
        try:
            await update.message.reply_text(full_message)
        except Exception as e:
            print("❌ PDF SUMMARY SEND ERROR:", e)
        return

    # Uzun javobni bo‘laklarga ajratish
    parts = []
    current = ""

    for paragraph in full_message.split("\n"):
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        # Juda uzun bitta qatorni ham bo‘lamiz
        while len(paragraph) > MAX_LENGTH:
            if current:
                parts.append(current.strip())
                current = ""

            parts.append(paragraph[:MAX_LENGTH])
            paragraph = paragraph[MAX_LENGTH:]

        if not current:
            current = paragraph
        elif len(current) + len(paragraph) + 2 <= MAX_LENGTH:
            current += "\n\n" + paragraph
        else:
            parts.append(current.strip())
            current = paragraph

    if current:
        parts.append(current.strip())

    print("📤 PDF xulosa bo‘laklari:", len(parts))

    for i, part in enumerate(parts, 1):
        try:
            await update.message.reply_text(part)
        except Exception as e:
            print(f"❌ PDF SUMMARY PART {i} ERROR:", e)

        await asyncio.sleep(0.3)
async def pdf_question(update: Update, context: ContextTypes.DEFAULT_TYPE):

    pdf_path = context.user_data.get("pdf_file")

    if not pdf_path or not os.path.exists(pdf_path):
        await update.message.reply_text(
            "❌ Avval PDF fayl yuboring."
        )
        return

    context.user_data["pdf_question_mode"] = True

    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        message = (
            "❓ PDF bo‘yicha savolingizni yuboring.\n\n"
            "Masalan:\n"
            "👉 Bu hujjatning asosiy mavzusi nima?\n"
            "👉 3-bobda nima haqida gapirilgan?"
        )

    elif lang == "en":
        message = (
            "❓ Send your question about the PDF.\n\n"
            "For example:\n"
            "👉 What is the main topic of this document?\n"
            "👉 What is discussed in chapter 3?"
        )

    else:
        message = (
            "❓ Отправьте свой вопрос по PDF.\n\n"
            "Например:\n"
            "👉 Какова основная тема документа?\n"
            "👉 О чём говорится в 3-й главе?"
        )

    await update.message.reply_text(message)

# ============================================================
# ❓ PDF SAVOLIGA AI JAVOB
# ============================================================

async def pdf_question_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    pdf_path = context.user_data.get("pdf_file")

    if not pdf_path or not os.path.exists(pdf_path):
        context.user_data["pdf_question_mode"] = False

        await update.message.reply_text(
            "❌ PDF fayl topilmadi. Avval PDF yuboring."
        )
        return

    question = update.message.text

    await update.message.reply_text(
        "⏳ PDF va savolingiz AI tomonidan tahlil qilinmoqda..."
    )

    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        prompt = (
            "Sen Student AI yordamchisisan. "
            "Foydalanuvchining savoliga faqat berilgan PDF hujjat "
            "asosida javob ber. PDFdagi matn, rasmlar, jadvallar va "
            "skanerlangan sahifalarni imkon qadar tahlil qil.\n\n"
            "Agar javob PDFda mavjud bo‘lmasa, buni aniq ayt. "
            "O‘zingdan ma’lumot to‘qib chiqarmagin.\n\n"
            f"Foydalanuvchi savoli:\n{question}\n\n"
            "Javobni o‘zbek tilida yoz."
        )
    elif lang == "en":
        prompt = (
            "You are the Student AI assistant. "
            "Answer the user's question using only the provided PDF. "
            "Analyze text, images, tables and scanned pages when possible. "
            "If the answer is not in the PDF, say so clearly. "
            "Do not invent information.\n\n"
            f"User question:\n{question}\n\n"
            "Answer in English."
        )
    else:
        prompt = (
            "Ты помощник Student AI. "
            "Ответь на вопрос пользователя только на основе "
            "предоставленного PDF. Анализируй текст, изображения, "
            "таблицы и сканированные страницы, если это возможно. "
            "Если ответа в PDF нет, скажи об этом прямо. "
            "Не выдумывай информацию.\n\n"
            f"Вопрос пользователя:\n{question}\n\n"
            "Отвечай на русском языке."
        )

    answer = gemini_pdf_request(pdf_path, prompt)

    if answer:
        await update.message.reply_text(
            "❓ PDF SAVOLIGA JAVOB\n\n" + answer
        )
    else:
        await update.message.reply_text(
            "❌ AI PDF savoliga javob bera olmadi."
        )

    context.user_data["pdf_question_mode"] = False


# ============================================================
# 🌐 PDF TARJIMA
# ============================================================

async def pdf_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):

    pdf_path = context.user_data.get("pdf_file")

    if not pdf_path or not os.path.exists(pdf_path):
        await update.message.reply_text(
            "❌ Avval PDF fayl yuboring."
        )
        return

    await update.message.reply_text(
        "🌐 PDF fayl AI tomonidan o‘qilmoqda va tarjima qilinmoqda..."
    )

    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        target_language = "o‘zbek tili"
    elif lang == "en":
        target_language = "English"
    else:
        target_language = "русский язык"

    prompt = (
        f"Translate the provided PDF document into {target_language}. "
        "Preserve the meaning and structure as much as possible. "
        "Read text from scanned pages, images and tables when possible. "
        "Do not add explanations or comments. "
        "Return only the translated content."
    )

    answer = gemini_pdf_request(pdf_path, prompt)

    if answer:
        await update.message.reply_text(
            "🌐 PDF TARJIMA\n\n" + answer
        )
    else:
        await update.message.reply_text(
            "❌ PDF tarjima qilinmadi."
        )


# ============================================================
# 📄 PDF → RASMLAR
# ============================================================

# ============================================================
# 📄 PDF FAYLNI QABUL QILISH
# ============================================================

async def pdf_document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document:
        return

    if not document.file_name.lower().endswith(".pdf"):
        await update.message.reply_text(
            "❌ Iltimos, faqat PDF fayl yuboring."
        )
        return

    try:
        await update.message.reply_text(
            "⏳ PDF fayl qabul qilinmoqda..."
        )

        file = await context.bot.get_file(document.file_id)

        pdf_path = f"uploaded_{update.effective_user.id}.pdf"

        await file.download_to_drive(pdf_path)

        context.user_data["pdf_file"] = pdf_path
        context.user_data["pdf_mode"] = True

        context.user_data["pdf_question_mode"] = False
        context.user_data["calculator_mode"] = False
        context.user_data["programming_mode"] = False
        context.user_data["translator_mode"] = False
        context.user_data["ai_mode"] = False

        lang = context.user_data.get("language", "uz")

        if lang == "ru":
            message = (
                "✅ PDF принят!\n\n"
                "Выберите нужную услугу:\n\n"
                "📝 Краткое содержание PDF"
            )
        elif lang == "en":
            message = (
                "✅ PDF received!\n\n"
                "Choose the required service:\n\n"
                "📝 PDF Summary"
            )
        else:
            message = (
                "✅ PDF qabul qilindi!\n\n"
                "Kerakli xizmatni tanlang:\n\n"
                "📝 PDF xulosa"
            )

        await update.message.reply_text(message)

    except Exception as e:
        print("PDF UPLOAD ERROR:", e)

        await update.message.reply_text(
            "❌ PDFni qabul qilishda xatolik yuz berdi."
        )


async def cancel_pdf_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    images = context.user_data.get("pdf_images", [])

    for image_path in images:
        try:
            os.remove(image_path)
        except Exception:
            pass

    context.user_data["pdf_images"] = []
    context.user_data["pdf_image_mode"] = False

    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        await pdf_menu(update, context)
    elif lang == "en":
        await update.message.reply_text(
            "❌ Cancelled."
        )
    else:
        await update.message.reply_text(
            "❌ Отменено."
        )

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        text = (
            "⭐ STUDENT AI PREMIUM\n\n"
            "🚀 30 kunlik Premium\n"
            "♾️ AI savollariga limit yo'q\n"
            "📄 Hujjatlar bilan ishlash\n"
            "💻 Dasturlash yordamchisi\n"
            "🧠 Aqlli matematika — oson yechimlar\n"
            "📚 Yozma ishlar — sifatli ishlar\n"
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
            "🧠 Smart Math — easy solutions\n"
            "📚 Written Works — quality work\n"
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
            "🧠 Умная математика — простые решения\n"
            "📚 Письменные работы — качественные работы\n"
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

async def translator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        text = (
            "🌍 TARJIMON\n\n"
            "Qaysi tilga tarjima qilamiz?"
        )
        keyboard = [
            ["🔤 → English", "🔤 → Русский"],
            ["🔤 → O'zbekcha", "⬅️ Orqaga"]
        ]

    elif lang == "en":
        text = (
            "🌍 TRANSLATOR\n\n"
            "Which language should we translate into?"
        )
        keyboard = [
            ["🔤 → Uzbek", "🔤 → Russian"],
            ["🔤 → English", "⬅️ Back"]
        ]

    else:
        text = (
            "🌍 ПЕРЕВОДЧИК\n\n"
            "На какой язык перевести?"
        )
        keyboard = [
            ["🔤 → Uzbek", "🔤 → English"],
            ["🔤 → Russian", "⬅️ Назад"]
        ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        text,
        reply_markup=reply_markup
    )

async def translator_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🔥 TRANSLATOR_LANGUAGE ISHLADI:", update.message.text)

    text = update.message.text
    if text in ["🔤 → English", "🔤 → Inglizcha"]:
        context.user_data["translate_to"] = "English"

    elif text in ["🔤 → Русский", "🔤 → Russian", "🔤 → Ruscha"]:
        context.user_data["translate_to"] = "Russian"

    elif text in ["🔤 → O'zbekcha", "🔤 → Uzbek", "🔤 → O'zbek"]:
        context.user_data["translate_to"] = "Uzbek"

    elif text in ["⬅️ Orqaga", "⬅️ Back", "⬅️ Назад"]:
        context.user_data["translator_mode"] = False
        context.user_data.pop("translate_to", None)

        lang = context.user_data.get("language", "uz")

        if lang == "uz":
            await uz_menu(update)
        elif lang == "en":
            await en_menu(update)
        else:
            await ru_menu(update)

        return

    else:
        return

    context.user_data["translator_mode"] = True

    reply_markup = ReplyKeyboardMarkup(
        [["⬅️ Orqaga"]],
        resize_keyboard=True
    )

    await update.message.reply_text(
        f"✅ Tarjima tili: {context.user_data['translate_to']}\n\n"
        "📝 Endi tarjima qilinadigan matnni yuboring.",
        reply_markup=reply_markup
    )

async def translator_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lang = context.user_data.get("language", "uz")

    # 🔤 Tarjima tilini tanlash
    if text in ["🔤 → English", "🔤 → Inglizcha"]:
        context.user_data["translate_to"] = "English"
        context.user_data["translator_mode"] = True

        await update.message.reply_text(
            "✅ Tarjima tili: English\n\n"
            "📝 Endi tarjima qilinadigan matnni yuboring.",
            reply_markup=ReplyKeyboardMarkup(
                [["⬅️ Orqaga"]],
                resize_keyboard=True
            )
        )
        return

    if text in ["🔤 → Русский", "🔤 → Russian", "🔤 → Ruscha"]:
        context.user_data["translate_to"] = "Russian"
        context.user_data["translator_mode"] = True

        await update.message.reply_text(
            "✅ Tarjima tili: Russian\n\n"
            "📝 Endi tarjima qilinadigan matnni yuboring.",
            reply_markup=ReplyKeyboardMarkup(
                [["⬅️ Orqaga"]],
                resize_keyboard=True
            )
        )
        return

    if text in ["🔤 → O'zbekcha", "🔤 → Uzbek", "🔤 → O'zbek"]:
        context.user_data["translate_to"] = "Uzbek"
        context.user_data["translator_mode"] = True

        await update.message.reply_text(
            "✅ Tarjima tili: Uzbek\n\n"
            "📝 Endi tarjima qilinadigan matnni yuboring.",
            reply_markup=ReplyKeyboardMarkup(
                [["⬅️ Orqaga"]],
                resize_keyboard=True
            )
        )
        return

    # ⬅️ Orqaga
    if text in ["⬅️ Orqaga", "⬅️ Back", "⬅️ Назад"]:
        context.user_data["translator_mode"] = False
        context.user_data.pop("translate_to", None)

        if lang == "uz":
            await uz_menu(update)
        elif lang == "en":
            await en_menu(update)
        else:
            await ru_menu(update)

        return

    # Tarjimon rejimi yoqilmagan bo‘lsa
    if not context.user_data.get("translator_mode"):
        return

    target_language = context.user_data.get("translate_to")

    if not target_language:
        await update.message.reply_text(
            "⚠️ Avval tarjima tilini tanlang."
        )
        return

    import requests
    from datetime import date

    user_id = update.effective_user.id
    today = str(date.today())

    # Foydalanuvchi ma'lumotlarini olish
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT translator_count, translator_last_date, premium_until "
        "FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users "
            "(user_id, translator_count, translator_last_date) "
            "VALUES (?, 0, ?)",
            (user_id, today)
        )
        conn.commit()

        translator_count = 0
        translator_last_date = today
        premium_until = None
    else:
        translator_count, translator_last_date, premium_until = user

    # Yangi kun
    if translator_last_date != today:
        translator_count = 0

        cursor.execute(
            "UPDATE users SET translator_count = 0, "
            "translator_last_date = ? WHERE user_id = ?",
            (today, user_id)
        )
        conn.commit()

    conn.close()

    # Premium
    premium_active = (
        premium_until is not None
        and premium_until != ""
        and premium_until >= today
    )

    # ⭐ PREMIUM TARJIMON — 300 / 30 KUN
    premium_translation_count = 0
    premium_translation_month = today[:7]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT premium_translation_count,
               premium_translation_month
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    premium_data = cursor.fetchone()

    if premium_data:
        premium_translation_count = premium_data[0] or 0
        premium_translation_month = (
            premium_data[1] or today[:7]
        )

    # Yangi oy bo'lsa hisoblagichni yangilash
    if premium_translation_month != today[:7]:
        premium_translation_count = 0
        premium_translation_month = today[:7]

        cursor.execute(
            """
            UPDATE users
            SET premium_translation_count = 0,
                premium_translation_month = ?
            WHERE user_id = ?
            """,
            (premium_translation_month, user_id)
        )
        conn.commit()

    conn.close()

    # ⭐ Premium 300 ta tarjimadan keyin to'xtaydi
    if premium_active and premium_translation_count >= 300:

        if lang == "uz":
            msg = (
                "⛔ Premium tarjima limitingiz tugadi.\n\n"
                "📊 Bu Premium davrida: 300/300 ta tarjima.\n"
                "📅 Limit Premium muddati yangilanganda qayta tiklanadi."
            )
        elif lang == "en":
            msg = (
                "⛔ Your Premium translation limit has been reached.\n\n"
                "📊 This Premium period: 300/300 translations.\n"
                "📅 The limit resets when Premium is renewed."
            )
        else:
            msg = (
                "⛔ Ваш Premium-лимит переводов закончился.\n\n"
                "📊 За период Premium: 300/300 переводов.\n"
                "📅 Лимит сбросится после продления Premium."
            )

        await update.message.reply_text(msg)
        return

    # 🆓 Bepul limit
    if not premium_active and translator_count >= 5:

        if lang == "uz":
            limit_text = (
                "⛔ Bugungi bepul tarjima limitingiz tugadi.\n\n"
                "⭐ Premium orqali tarjimondan cheksiz foydalanishingiz mumkin."
            )
        elif lang == "en":
            limit_text = (
                "⛔ Your free translation limit for today is over.\n\n"
                "⭐ Premium gives you unlimited translation."
            )
        else:
            limit_text = (
                "⛔ Ваш бесплатный лимит переводов на сегодня закончился.\n\n"
                "⭐ Premium даёт безлимитный перевод."
            )

        await update.message.reply_text(limit_text)
        return

    user_text = text

    prompt = (
        f"Translate the following text into {target_language}. "
        "Return only the translation, without explanations.\n\n"
        f"Text:\n{user_text}"
    )

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.6-flash:generateContent"
    )

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=60
        )

        result = response.json()
        print("🔍 TRANSLATOR GEMINI:", result)
        if "candidates" in result:
            answer = result["candidates"][0]["content"]["parts"][0]["text"]

            if not premium_active:
                translator_count += 1

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(
                    "UPDATE users SET translator_count = ?, "
                    "translator_last_date = ? WHERE user_id = ?",
                    (translator_count, today, user_id)
                )

                conn.commit()
                conn.close()

                limit_text = (
                    f"\n\n📊 Bugungi bepul tarjimalar: "
                    f"{translator_count}/5"
                )
            else:
                # ⭐ Premium hisoblagich faqat muvaffaqiyatli
                # tarjimadan keyin oshadi
                premium_translation_count += 1

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE users
                    SET premium_translation_count = ?,
                        premium_translation_month = ?
                    WHERE user_id = ?
                    """,
                    (
                        premium_translation_count,
                        today[:7],
                        user_id
                    )
                )

                conn.commit()
                conn.close()

                limit_text = (
                    f"\n\n⭐ Premium tarjimalar: "
                    f"{premium_translation_count}/300"
                )

            await update.message.reply_text(
                f"🌍 Tarjima:\n\n{answer}{limit_text}"
            )

        else:
            await update.message.reply_text(
                f"❌ Tarjima xatosi: {result}"
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Xato: {e}"
        )


async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("translator_mode"):
        return

    text = update.message.text

    if text.startswith("🔤 →"):
        return

    import requests
    from datetime import date

    user_id = update.effective_user.id
    today = str(date.today())
    lang = context.user_data.get("language", "uz")

    question_count, last_date, premium_until = get_user(user_id)

    # ============================================================
    # ⭐ PREMIUM HOLATI
    # ============================================================

    premium_active = (
        premium_until is not None
        and premium_until != ""
        and premium_until >= today
    )

    # ============================================================
    # ⭐ PREMIUM AI — 300 / 30 KUN HISOBLAGICHI
    # ============================================================

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT premium_ai_count, premium_ai_month "
        "FROM users WHERE user_id = ?",
        (user_id,)
    )

    premium_row = cursor.fetchone()

    if premium_row is None:
        premium_ai_count = 0
        premium_ai_cycle = premium_until
    else:
        premium_ai_count = premium_row[0] or 0
        premium_ai_cycle = premium_row[1]

    # ⭐ Yangi Premium davri boshlangan bo'lsa,
    # hisoblagich yangi 30 kunlik davr uchun 0 dan boshlanadi.
    if premium_active and premium_ai_cycle != premium_until:
        premium_ai_count = 0

        cursor.execute(
            "UPDATE users SET premium_ai_count = 0, "
            "premium_ai_month = ? WHERE user_id = ?",
            (premium_until, user_id)
        )

        conn.commit()

    conn.close()

    # ============================================================
    # ⭐ PREMIUM LIMIT — 300 / 30 KUN
    # ============================================================

    if premium_active and premium_ai_count >= 300:

        if lang == "uz":
            limit_text = (
                "⭐ Premium AI limitingiz tugadi.\n\n"
                "📊 Bu oy: 300/300 ta AI so‘rovi ishlatildi.\n"
                "📅 Limit keyingi oy yangilanadi."
            )

        elif lang == "en":
            limit_text = (
                "⭐ Your Premium AI limit has been reached.\n\n"
                "📊 This month: 300/300 AI requests used.\n"
                "📅 The limit resets next month."
            )

        else:
            limit_text = (
                "⭐ Ваш Premium-лимит AI закончился.\n\n"
                "📊 В этом месяце: 300/300 AI-запросов использовано.\n"
                "📅 Лимит обновится в следующем месяце."
            )

        await update.message.reply_text(limit_text)
        return

    # ============================================================
    # 🆓 FREE — 5 / KUN
    # ============================================================

    if not premium_active:

        if last_date != today:
            question_count = 0
            update_question_count(user_id, 0, today)

        if question_count >= 5:

            if lang == "uz":
                limit_text = (
                    "⛔ Bugungi bepul AI limitingiz tugadi.\n\n"
                    "⭐ Premium orqali ko‘proq foydalanishingiz mumkin."
                )

            elif lang == "en":
                limit_text = (
                    "⛔ Your free AI limit for today is over.\n\n"
                    "⭐ You can use more with Premium."
                )

            else:
                limit_text = (
                    "⛔ Ваш бесплатный лимит AI на сегодня закончился.\n\n"
                    "⭐ Больше возможностей доступно с Premium."
                )

            await update.message.reply_text(limit_text)
            return

    # ============================================================
    # 🌍 TILGA MOS PROMPT
    # ============================================================

    if lang == "uz":
        prompt = (
            "Sen Student AI yordamchisisan. "
            "Foydalanuvchiga o'zbek tilida tushunarli, aniq va foydali javob ber. "
            "Agar savol o'quv, matematika, fizika, dasturlash yoki boshqa mavzuda bo'lsa, "
            "kerakli tushuntirish va misollarni ber. "
            "Javobni keraksiz uzun qilma.\n\n"
            f"Foydalanuvchi savoli:\n{text}"
        )

    elif lang == "en":
        prompt = (
            "You are the Student AI assistant. "
            "Answer the user clearly and accurately in English. "
            "If the question is about study, mathematics, physics, programming, "
            "or another topic, provide useful explanations and examples. "
            "Do not make the answer unnecessarily long.\n\n"
            f"User question:\n{text}"
        )

    else:
        prompt = (
            "Ты помощник Student AI. "
            "Отвечай пользователю понятно, точно и на русском языке. "
            "Если вопрос касается учёбы, математики, физики, программирования "
            "или другой темы, дай полезное объяснение и примеры. "
            "Не делай ответ unnecessarily длинным.\n\n"
            f"Вопрос пользователя:\n{text}"
        )

    # ============================================================
    # ⏳ KUTILMOQDA
    # ============================================================

    if lang == "uz":
        wait_text = "⏳ AI o'ylayapti..."
    elif lang == "en":
        wait_text = "⏳ AI is thinking..."
    else:
        wait_text = "⏳ AI думает..."

    await update.message.reply_text(wait_text)

    # ============================================================
    # 🤖 GEMINI
    # ============================================================

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.6-flash:generateContent"
    )

    headers = {
        "x-goog-api-key": GEMINI_AI_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
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
        response = None

        for attempt, delay in enumerate([0, 2, 5], start=1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=60
                )

                print(
                    f"🤖 AI GEMINI attempt {attempt}/3: "
                    f"{response.status_code}"
                )

                if response.status_code == 200:
                    break

                if response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < 3:
                        await asyncio.sleep(delay)
                        continue

                break

            except requests.exceptions.Timeout:
                print(f"⏱️ AI GEMINI TIMEOUT attempt {attempt}/3")

                if attempt < 3:
                    await asyncio.sleep(delay)
                    continue

                await update.message.reply_text(
                    "⏳ AI serveridan javob kelmadi.\n\n"
                    "Birozdan keyin yana urinib ko'ring."
                )
                return

            except requests.exceptions.RequestException as e:
                print(
                    f"🌐 AI GEMINI NETWORK ERROR "
                    f"attempt {attempt}/3: {e}"
                )

                if attempt < 3:
                    await asyncio.sleep(delay)
                    continue

                await update.message.reply_text(
                    "🌐 AI serveriga ulanishda muammo yuz berdi.\n\n"
                    "Birozdan keyin yana urinib ko'ring."
                )
                return

        if response is None:
            await update.message.reply_text(
                "😔 AI hozircha javob bera olmadi.\n\n"
                "Birozdan keyin yana urinib ko'ring."
            )
            return

        result = response.json()

        print("🤖 AI GEMINI:", result)

        if "candidates" in result:

            answer = result["candidates"][0]["content"]["parts"][0]["text"]

            # ====================================================
            # 💾 FAQAT MUVAFFAQIYATLI JAVOBDAN KEYIN HISOBLASH
            # ====================================================

            if premium_active:

                premium_ai_count += 1

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(
                    "UPDATE users SET premium_ai_count = ?, "
                    "premium_ai_month = ? WHERE user_id = ?",
                    (
                        premium_ai_count,
                        premium_until,
                        user_id
                    )
                )

                conn.commit()
                conn.close()

                limit_text = (
                    f"\n\n⭐ Premium AI: "
                    f"{premium_ai_count}/300"
                )

            else:

                question_count += 1

                update_question_count(
                    user_id,
                    question_count,
                    today
                )

                limit_text = (
                    f"\n\n📊 Bugungi bepul AI savollari: "
                    f"{question_count}/5"
                )

            await update.message.reply_text(
                f"{answer}{limit_text}"
            )

        else:

            await update.message.reply_text(
                f"❌ Gemini xatosi ({response.status_code}):\n{result}"
            )

    except Exception as e:

        print("❌ AI ERROR:", e)

        await update.message.reply_text(
            f"❌ AI bilan bog'lanishda xatolik:\n{e}"
        )

app = Application.builder().token(TOKEN).build()


async def writing_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "uz")

    if lang == "en":
        text = (
            "📚 WRITTEN WORKS\n\n"
            "Choose the type of work you want to prepare:"
        )
        keyboard = [
            ["📝 Essay", "📖 Independent Work"],
            ["📄 Report", "⬅️ Back"]
        ]

    elif lang == "ru":
        text = (
            "📚 ПИСЬМЕННЫЕ РАБОТЫ\n\n"
            "Выберите тип работы:"
        )
        keyboard = [
            ["📝 Эссе", "📖 Самостоятельная работа"],
            ["📄 Реферат", "⬅️ Назад"]
        ]

    else:
        text = (
            "📚 YOZMA ISHLAR\n\n"
            "Tayyorlamoqchi bo‘lgan ish turini tanlang:"
        )
        keyboard = [
            ["📝 Esse", "📖 Mustaqil ish"],
            ["📄 Referat", "⬅️ Orqaga"]
        ]

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )




# ============================================================
# ⚙️ SOZLAMALAR
# ============================================================

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "uz")

    if lang == "en":
        keyboard = [
            ["👤 My Profile"],
            ["💎 Premium Status"],
            ["ℹ️ About Student AI"],
            ["⬅️ Back"],
        ]
        title = "⚙️ Settings\n\n👇 Choose a section:"
    elif lang == "ru":
        keyboard = [
            ["👤 Мой профиль"],
            ["💎 Статус Premium"],
            ["ℹ️ О Student AI"],
            ["⬅️ Назад"],
        ]
        title = "⚙️ Настройки\n\n👇 Выберите раздел:"
    else:
        keyboard = [
            ["👤 Mening profilim"],
            ["💎 Premium holati"],
            ["ℹ️ Student AI haqida"],
            ["⬅️ Orqaga"],
        ]
        title = "⚙️ Sozlamalar\n\n👇 Kerakli bo'limni tanlang:"

    await update.message.reply_text(
        title,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def settings_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get("language", "uz")

    _, _, premium_until = get_user(user_id)

    if premium_until:
        premium_text = "Faol" if lang == "uz" else (
            "Active" if lang == "en" else "Активен"
        )
        premium_date = premium_until
    else:
        premium_text = "Faol emas" if lang == "uz" else (
            "Not active" if lang == "en" else "Не активен"
        )
        premium_date = "—"

    if lang == "en":
        msg = (
            "👤 My Profile\n\n"
            f"🆔 Telegram ID: {user_id}\n"
            "🌐 Language: English\n"
            f"💎 Premium: {premium_text}\n"
            f"📅 Premium until: {premium_date}"
        )
    elif lang == "ru":
        msg = (
            "👤 Мой профиль\n\n"
            f"🆔 Telegram ID: {user_id}\n"
            "🌐 Язык: Русский\n"
            f"💎 Premium: {premium_text}\n"
            f"📅 Premium до: {premium_date}"
        )
    else:
        msg = (
            "👤 Mening profilim\n\n"
            f"🆔 Telegram ID: {user_id}\n"
            "🌐 Til: O'zbekcha\n"
            f"💎 Premium: {premium_text}\n"
            f"📅 Premium muddati: {premium_date}"
        )

    await update.message.reply_text(msg)


async def settings_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get("language", "uz")

    _, _, premium_until = get_user(user_id)

    if premium_until:
        if lang == "en":
            msg = (
                "💎 Premium Status\n\n"
                "✅ Status: Active\n"
                f"📅 Valid until: {premium_until}\n\n"
                "⭐ You can use Premium features."
            )
        elif lang == "ru":
            msg = (
                "💎 Статус Premium\n\n"
                "✅ Статус: Активен\n"
                f"📅 Действует до: {premium_until}\n\n"
                "⭐ Вам доступны Premium-возможности."
            )
        else:
            msg = (
                "💎 Premium holati\n\n"
                "✅ Holat: Faol\n"
                f"📅 Amal qilish muddati: {premium_until}\n\n"
                "⭐ Premium imkoniyatlaridan foydalanishingiz mumkin."
            )
    else:
        if lang == "en":
            msg = (
                "💎 Premium Status\n\n"
                "❌ Status: Not active\n\n"
                "⭐ Open the Premium section to learn more."
            )
        elif lang == "ru":
            msg = (
                "💎 Статус Premium\n\n"
                "❌ Статус: Не активен\n\n"
                "⭐ Откройте раздел Premium, чтобы узнать больше."
            )
        else:
            msg = (
                "💎 Premium holati\n\n"
                "❌ Holat: Faol emas\n\n"
                "⭐ Batafsil ma'lumot uchun Premium bo'limini oching."
            )

    await update.message.reply_text(msg)


async def settings_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "uz")

    if lang == "en":
        msg = (
            "ℹ️ About Student AI\n\n"
            "🤖 Student AI — an intelligent assistant "
            "created to help students.\n\n"
            "🧠 AI Assistant\n"
            "🧮 Smart Math\n"
            "🌍 Translator\n"
            "📄 PDF / Documents\n"
            "📚 Written Works\n"
            "💻 Programming\n\n"
            "🚀 Student AI — your study assistant."
        )
    elif lang == "ru":
        msg = (
            "ℹ️ О Student AI\n\n"
            "🤖 Student AI — интеллектуальный помощник "
            "для студентов.\n\n"
            "🧠 AI-помощник\n"
            "🧮 Умная математика\n"
            "🌍 Переводчик\n"
            "📄 PDF / Документы\n"
            "📚 Письменные работы\n"
            "💻 Программирование\n\n"
            "🚀 Student AI — ваш помощник в учёбе."
        )
    else:
        msg = (
            "ℹ️ Student AI haqida\n\n"
            "🤖 Student AI — talabalar uchun yaratilgan "
            "aqlli yordamchi.\n\n"
            "🧠 AI yordamchi\n"
            "🧮 Aqlli matematika\n"
            "🌍 Tarjimon\n"
            "📄 PDF / Hujjat\n"
            "📚 Yozma ishlar\n"
            "💻 Dasturlash\n\n"
            "🚀 Student AI — o'qishdagi yordamchingiz."
        )

    await update.message.reply_text(msg)



async def payment_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("payment_waiting_receipt"):
        await pdf_photo_handler(update, context)
        return

    user = update.effective_user
    user_id = user.id
    name = user.full_name or "Noma'lum"
    username = "@" + user.username if user.username else "username yo'q"

    context.user_data["payment_waiting_receipt"] = False

    caption = (
        "💳 YANGI PREMIUM TO'LOVI\\n\\n"
        f"👤 Ism: {name}\\n"
        f"🔗 Username: {username}\\n"
        f"🆔 User ID: {user_id}\\n\\n"
        "👇 Chekni tekshiring:"
    )

    keyboard = [[
        InlineKeyboardButton(
            "✅ Tasdiqlash",
            callback_data=f"premium_ok:{user_id}"
        ),
        InlineKeyboardButton(
            "❌ Rad etish",
            callback_data=f"premium_no:{user_id}"
        )
    ]]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text(
        "✅ Chekingiz adminga yuborildi.\\n\\n"
        "⏳ To'lov tekshirilgach Premium faollashtiriladi."
    )


async def premium_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    await query.answer()

    if query.data.startswith("premium_ok:"):
        user_id = int(query.data.split(":", 1)[1])
        premium_until = activate_premium(user_id)

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 TO'LOV TASDIQLANDI!\\n\\n"
                "⭐ Premium 30 kunga faollashtirildi.\\n"
                f"📅 Amal qilish muddati: {premium_until}"
            )
        )

        await query.edit_message_caption(
            caption=query.message.caption + "\\n\\n✅ TASDIQLANDI",
            reply_markup=None
        )
        return

    if query.data.startswith("premium_no:"):
        user_id = int(query.data.split(":", 1)[1])

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ To'lov tasdiqlanmadi.\\n\\n"
                "Iltimos, chekni qayta tekshirib yuboring."
            )
        )

        await query.edit_message_caption(
            caption=query.message.caption + "\\n\\n❌ RAD ETILDI",
            reply_markup=None
        )


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # ⚙️ SOZLAMALAR
    if text in [
        "⚙️ Sozlamalar",
        "⚙️ Settings",
        "⚙️ Настройки"
    ]:
        context.user_data["ai_mode"] = False
        context.user_data["translator_mode"] = False
        context.user_data["calculator_mode"] = False
        context.user_data["programming_mode"] = False
        context.user_data["writing_mode"] = False
        context.user_data["pdf_mode"] = False
        context.user_data["pdf_question_mode"] = False

        await settings_menu(update, context)
        return

    # 👤 Mening profilim
    if text in [
        "👤 Mening profilim",
        "👤 My Profile",
        "👤 Мой профиль"
    ]:
        await settings_profile(update, context)
        return

    # 💎 Premium holati
    if text in [
        "💎 Premium holati",
        "💎 Premium Status",
        "💎 Статус Premium"
    ]:
        await settings_premium(update, context)
        return

    # ⭐ Premium
    if text == "⭐ Premium":
        await premium(update, context)
        return

    if text == "💳 Premium sotib olish":
        context.user_data["payment_waiting_receipt"] = True

        await update.message.reply_text(
            "💳 PREMIUM TO'LOV\\n\\n"
            "⭐ Narx: 29 000 so'm / 30 kun\\n\\n"
            f"💳 To'lov kartasi: {PAYMENT_CARD or 'Karta hali sozlanmagan'}\\n\\n"
            "1️⃣ Yuqoridagi karta raqamiga to'lov qiling.\\n"
            "2️⃣ To'lov chekini shu botga RASM qilib yuboring.\\n"
            "3️⃣ Administrator chekni tekshiradi.\\n"
            "4️⃣ Tasdiqlangach Premium 30 kunga ochiladi.\\n\\n"
            "📸 Endi chek rasmini yuboring."
        )
        return

    # ℹ️ Student AI haqida
    if text in [
        "ℹ️ Student AI haqida",
        "ℹ️ About Student AI",
        "ℹ️ О Student AI"
    ]:
        await settings_about(update, context)
        return


    # 🤖 AI yordamchi
    if text in [
        "🤖 AI yordamchi",
        "🤖 AI Assistant",
        "🤖 AI Помощник"
    ]:
        context.user_data["pdf_mode"] = False
        context.user_data["pdf_question_mode"] = False
        context.user_data["calculator_mode"] = False
        context.user_data["programming_mode"] = False
        context.user_data["translator_mode"] = False
        context.user_data["ai_mode"] = True

        await ai_assistant(update, context)
        return

    # 📄 PDF / Hujjat
    if text in [
        "📄 PDF / Hujjat",
        "📄 PDF / Documents",
        "📄 PDF / Документы"
    ]:
        context.user_data["pdf_mode"] = True
        context.user_data["calculator_mode"] = False
        context.user_data["programming_mode"] = False
        context.user_data["translator_mode"] = False
        context.user_data["ai_mode"] = False
        context.user_data["pdf_question_mode"] = False

        await pdf_menu(update, context)
        return

    # 🧮 KALKULYATOR — 3 TIL
    if text in [
        "🧠 Aqlli matematika",
        "🧠 Smart Math",
        "🧠 Умная математика"
    ]:
        context.user_data["pdf_mode"] = False
        context.user_data["pdf_question_mode"] = False
        context.user_data["calculator_mode"] = True
        context.user_data["programming_mode"] = False
        context.user_data["translator_mode"] = False
        context.user_data["ai_mode"] = False

        lang = context.user_data.get("language", "uz")

        if lang == "uz":
            await update.message.reply_text(
                "🧠 Aqlli matematika tayyor!\n\n"
                "Oddiy hisob-kitobdan tortib murakkab matematik masalalargacha yuborishingiz mumkin.\n\n"
                "• Tenglamalar va tengsizliklar\n"
                "• Kasrlar, foizlar, darajalar va ildizlar\n"
                "• Funksiyalar va matematik formulalar\n"
                "• Geometriya va trigonometriya\n"
                "• Hosila, integral va murakkab hisoblashlar\n"
                "• Bosqichma-bosqich matematik masalalar\n\n"
                "📌 Masalangizni qanday bo‘lsa, shunday yozing — Aqlli matematika uni tushuntirib, yechishga yordam beradi."
            )
        elif lang == "en":
            await update.message.reply_text(
                "🧠 Smart Math is ready!\n\n"
                "You can send anything from simple calculations to complex mathematics.\n\n"
                "• Equations and inequalities\n"
                "• Fractions, percentages, powers and roots\n"
                "• Functions and mathematical formulas\n"
                "• Geometry and trigonometry\n"
                "• Derivatives, integrals and advanced calculations\n"
                "• Step-by-step mathematical problems\n\n"
                "📌 Send your problem as it is — Smart Math will help you understand and solve it."
            )
        else:
            await update.message.reply_text(
                "🧠 Умная математика готова!\n\n"
                "Вы можете отправить всё — от простых вычислений до сложных математических задач.\n\n"
                "• Уравнения и неравенства\n"
                "• Дроби, проценты, степени и корни\n"
                "• Функции и математические формулы\n"
                "• Геометрия и тригонометрия\n"
                "• Производные, интегралы и сложные вычисления\n"
                "• Пошаговое решение математических задач\n\n"
                "📌 Отправьте задачу как есть — Умная математика поможет понять её и решить."
            )

        return

    # 📚 YOZMA ISHLAR
    if text in [
        "📚 Yozma ishlar",
        "📚 Written Works",
        "📚 Письменные работы"
    ]:
        context.user_data["pdf_mode"] = False
        context.user_data["pdf_question_mode"] = False
        context.user_data["calculator_mode"] = False
        context.user_data["programming_mode"] = False
        context.user_data["translator_mode"] = False
        context.user_data["ai_mode"] = False
        context.user_data["writing_mode"] = True

        await writing_menu(update, context)
        return


    # 💻 Dasturlash
    if text in [
        "💻 Dasturlash",
        "💻 Programming",
        "💻 Программирование"
    ]:
        context.user_data["calculator_mode"] = False
        context.user_data["programming_mode"] = True
        context.user_data["translator_mode"] = False
        context.user_data["ai_mode"] = False

        await programming(update, context)
        return


    # 🌍 Tarjimon
    if text in [
        "🌍 Tarjimon",
        "🌍 Translator",
        "🌍 Переводчик"
    ]:
        context.user_data["calculator_mode"] = False
        context.user_data["translator_mode"] = False
        context.user_data["ai_mode"] = False

        await translator(update, context)
        return


    # 🔤 Tarjima tilini tanlash
    if text in [
        "🔤 → English",
        "🔤 → Inglizcha",
        "🔤 → Русский",
        "🔤 → Russian",
        "🔤 → Ruscha",
        "🔤 → O'zbekcha",
        "🔤 → Uzbek",
        "🔤 → O'zbek"
    ]:
        context.user_data["ai_mode"] = False
        await translator_chat(update, context)
        return

    # ⬅️ Orqaga
    if text in [
        "⬅️ Orqaga",
        "⬅️ Back",
        "⬅️ Назад"
    ]:
        context.user_data["translator_mode"] = False
        context.user_data["ai_mode"] = False

        lang = context.user_data.get("language", "uz")

        if lang == "uz":
            await uz_menu(update)
        elif lang == "en":
            await en_menu(update)
        else:
            await ru_menu(update)

        return

    # 🇺🇿🇬🇧🇷🇺 Til tanlash
    if text in [
        "🇺🇿 O'zbekcha",
        "🇬🇧 English",
        "🇷🇺 Русский"
    ]:
        context.user_data["translator_mode"] = False
        context.user_data["ai_mode"] = False

        await language(update, context)
        return

    # 📝 ESSE MAVZUSI
    if context.user_data.get("essay_topic_mode"):
        topic = text.strip()

        if not topic:
            await update.message.reply_text("❌ Esse mavzusini yozing.")
            return

        context.user_data["essay_topic_mode"] = False
        await essay_generator(update, context, topic)
        return

    # 📄 REFERAT MAVZUSI
    if context.user_data.get("report_topic_mode"):
        topic = text.strip()

        if not topic:
            await update.message.reply_text("❌ Referat mavzusini yozing.")
            return

        context.user_data["report_topic_mode"] = False
        await report_generator(update, context, topic)
        return

    # 📖 MUSTAQIL ISH MAVZUSI
    if context.user_data.get("independent_topic_mode"):
        topic = text.strip()

        if not topic:
            await update.message.reply_text(
                "❌ Mustaqil ish mavzusini yozing."
            )
            return

        context.user_data["independent_topic_mode"] = False
        await independent_work_generator(update, context, topic)
        return

    # 📚 YOZMA ISHLAR REJIMI
    if context.user_data.get("writing_mode"):

        # 📝 ESSE
        if text in [
            "📝 Esse",
            "📝 Essay",
            "📝 Эссе"
        ]:
            context.user_data["essay_topic_mode"] = True

            lang = context.user_data.get("language", "uz")

            if lang == "en":
                msg = (
                    "📝 ESSAY\n\n"
                    "Send the topic of your essay.\n\n"
                    "Example: The role of artificial intelligence in education"
                )
            elif lang == "ru":
                msg = (
                    "📝 ЭССЕ\n\n"
                    "Отправьте тему эссе.\n\n"
                    "Например: Роль искусственного интеллекта в образовании"
                )
            else:
                msg = (
                    "📝 ESSE\n\n"
                    "Esse mavzusini yuboring.\n\n"
                    "Masalan: Sun’iy intellektning ta’limdagi o‘rni"
                )

            await update.message.reply_text(msg)
            return

        # 📖 MUSTAQIL ISH
        if text in [
            "📖 Mustaqil ish",
            "📖 Independent Work",
            "📖 Самостоятельная работа"
        ]:
            context.user_data["independent_topic_mode"] = True

            lang = context.user_data.get("language", "uz")

            if lang == "en":
                msg = (
                    "📖 INDEPENDENT WORK\n\n"
                    "Send the topic of your independent work.\n\n"
                    "Example: The importance of digital technologies in education"
                )
            elif lang == "ru":
                msg = (
                    "📖 САМОСТОЯТЕЛЬНАЯ РАБОТА\n\n"
                    "Отправьте тему самостоятельной работы.\n\n"
                    "Например: Значение цифровых технологий в образовании"
                )
            else:
                msg = (
                    "📖 MUSTAQIL ISH\n\n"
                    "Mustaqil ish mavzusini yuboring.\n\n"
                    "Masalan: Ta’limda raqamli texnologiyalarning ahamiyati"
                )

            await update.message.reply_text(msg)
            return

        # 📄 REFERAT
        if text in [
            "📄 Referat",
            "📄 Report",
            "📄 Реферат"
        ]:
            context.user_data["report_topic_mode"] = True

            lang = context.user_data.get("language", "uz")

            if lang == "en":
                msg = (
                    "📄 REPORT\n\n"
                    "Send the topic of your report.\n\n"
                    "Example: The role of artificial intelligence in education"
                )
            elif lang == "ru":
                msg = (
                    "📄 РЕФЕРАТ\n\n"
                    "Отправьте тему реферата.\n\n"
                    "Например: Роль искусственного интеллекта в образовании"
                )
            else:
                msg = (
                    "📄 REFERAT\n\n"
                    "Referat mavzusini yuboring.\n\n"
                    "Masalan: Sun’iy intellektning ta’limdagi o‘rni"
                )

            await update.message.reply_text(msg)
            return

    # 🌍 Agar tarjimon rejimi yoqilgan bo'lsa
    if context.user_data.get("translator_mode"):
        await translator_chat(update, context)
        return

    # 🧮 Agar kalkulyator rejimi yoqilgan bo‘lsa
    if context.user_data.get("calculator_mode"):
        await calculator_chat(update, context)
        return

    # 🤖 Agar AI rejimi yoqilgan bo'lsa
    if context.user_data.get("ai_mode"):
        await ai_chat(update, context)
        return

    # 📄 Agar PDF rejimi yoqilgan bo'lsa
    if context.user_data.get("pdf_mode"):

        # 📝 PDF XULOSA — 3 TIL
        if text in [
            "📝 PDF xulosa",
            "📝 Краткое содержание PDF",
            "📝 PDF Summary"
        ]:
            await pdf_summary(update, context)
            return

        # 🖼️ RASMLARNI PDF QILISH — 3 TIL
        if text in [
            "🖼️ Rasmlarni PDF qilish",
            "🖼️ Сделать PDF из изображений",
            "🖼️ Images to PDF"
        ]:
            await start_image_to_pdf(update, context)
            return

        # ✅ PDF TAYYORLASH
        if text in [
            "✅ PDF tayyorlash",
            "✅ Создать PDF",
            "✅ Create PDF"
        ]:
            await make_pdf_from_images(update, context)
            return

        return

    # 💻 Agar dasturlash rejimi yoqilgan bo'lsa
    if context.user_data.get("programming_mode"):
        await programming_chat(update, context)
        return

    # Hech qanday rejim tanlanmagan bo'lsa
    await update.message.reply_text(
        "👇 Avval menyudan kerakli bo'limni tanlang."
    )


app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CallbackQueryHandler(
        premium_payment_callback,
        pattern=r"^premium_(ok|no):"
    )
)

app.add_handler(
    MessageHandler(
        filters.PHOTO,
        payment_photo_handler
    )
)

app.add_handler(
    MessageHandler(
        filters.Document.PDF,
        pdf_document_handler
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        text_router
    )
)

print("✅ Student AI ishga tushdi...")

async def error_handler(update, context):
    import traceback

    error_text = "".join(
        traceback.format_exception(
            type(context.error),
            context.error,
            context.error.__traceback__
        )
    )

    print("❌ GLOBAL ERROR FULL:", repr(error_text))

app.add_error_handler(error_handler)

app.run_polling()
