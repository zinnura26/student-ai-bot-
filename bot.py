from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
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
import requests
from pypdf import PdfReader
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

def activate_premium(user_id):
    from datetime import date, timedelta

    premium_until = date.today() + timedelta(days=30)

    conn = sqlite3.connect("student_ai.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET premium_until = ? WHERE user_id = ?",
        (str(premium_until), user_id)
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
        ["🧮 Kalkulyator", "📄 PDF / Hujjat"],
        ["📝 Referat", "💻 Dasturlash"],
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
        ["🧮 Calculator", "📄 PDF / Documents"],
        ["📝 Essay / Report", "💻 Programming"],
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
        ["🧮 Калькулятор", "📄 PDF / Документы"],
        ["📝 Реферат", "💻 Программирование"],
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

    import requests
    from datetime import date

    user_id = update.effective_user.id
    today = str(date.today())

    # Foydalanuvchi ma'lumotlarini olish
    conn = sqlite3.connect("student_ai.db")
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

    # Yangi foydalanuvchi
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

    # Yangi kun bo'lsa limitni yangilash
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

    # ⭐ Premium holatini tekshirish
    premium_active = (
        premium_until is not None
        and premium_until != ""
        and premium_until >= today
    )

    # 🆓 Bepul foydalanuvchi uchun 5 ta limit
    if not premium_active and programming_count >= 5:

        if lang == "uz":
            limit_text = (
                "⛔ Bugungi bepul dasturlash limitingiz tugadi.\n\n"
                "⭐ Premium orqali ko'proq foydalanishingiz mumkin."
            )
        elif lang == "en":
            limit_text = (
                "⛔ Your free programming limit for today is over.\n\n"
                "⭐ Upgrade to Premium for more access."
            )
        else:
            limit_text = (
                "⛔ Ваш бесплатный лимит программирования на сегодня закончился.\n\n"
                "⭐ Premium даст больше возможностей."
            )

        await update.message.reply_text(limit_text)

        context.user_data["programming_mode"] = False

        return
    user_question = text
    # 🌍 Tilga qarab AI prompt
    if lang == "uz":
        prompt = (
            "Sen Student AI dasturlash yordamchisisan. "
            "Foydalanuvchining dasturlash savoliga o'zbek tilida "
            "tushunarli va aniq javob ber. "
            "Kerak bo'lsa kod yoz. "
            "Koddagi xatolarni ham tushuntir. "
            "Javobni keraksiz uzun qilma.\n\n"
            f"Foydalanuvchi savoli:\n{user_question}"
        )

    elif lang == "en":
        prompt = (
            "You are the Student AI programming assistant. "
            "Answer the user's programming question clearly in English. "
            "Provide code when needed and explain errors. "
            "Do not make the answer unnecessarily long.\n\n"
            f"User question:\n{user_question}"
        )

    else:
        prompt = (
            "Ты помощник Student AI по программированию. "
            "Отвечай понятно и точно на русском языке. "
            "При необходимости пиши код и объясняй ошибки. "
            "Не делай ответ unnecessarily длинным.\n\n"
            f"Вопрос пользователя:\n{user_question}"
        )

    await update.message.reply_text(
        "⏳ Kodni tahlil qilyapman..."
    )

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.5-flash:generateContent"
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

        print("🔍 PROGRAMMING GEMINI:", result)

        if "candidates" in result:
            answer = result["candidates"][0]["content"]["parts"][0]["text"]

            # 🆓 Faqat bepul foydalanuvchi limitini oshirish
            if not premium_active:
                programming_count += 1

                conn = sqlite3.connect("student_ai.db")
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
                    f"\n\n📊 Bugungi bepul dasturlash savollari: "
                    f"{programming_count}/5"
                )
            else:
                limit_text = (
                    "\n\n⭐ Premium — dasturlash limiti yo'q"
                )

            await update.message.reply_text(
                f"💻 Javob:\n\n{answer}{limit_text}"
            )

        else:
            await update.message.reply_text(
                f"❌ Dasturlash AI xatosi:\n{result}"
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Xato: {e}"
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

    try:
        import ast
        import operator as op

        operators = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
            ast.Pow: op.pow,
            ast.Mod: op.mod,
            ast.USub: op.neg,
            ast.UAdd: op.pos,
        }

        def calculate(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value

            if isinstance(node, ast.UnaryOp) and type(node.op) in operators:
                return operators[type(node.op)](calculate(node.operand))

            if isinstance(node, ast.BinOp) and type(node.op) in operators:
                return operators[type(node.op)](
                    calculate(node.left),
                    calculate(node.right)
                )

            raise ValueError("Noto'g'ri matematik ifoda")

        tree = ast.parse(text, mode="eval")
        result = calculate(tree.body)

        await update.message.reply_text(
            f"🧮 Natija: {result}"
        )

    except ZeroDivisionError:
        await update.message.reply_text(
            "❌ Nolga bo‘lish mumkin emas."
        )

    except Exception:
        if lang == "uz":
            msg = "❌ Matematik ifodani tushunmadim.\nMasalan: 25 + 17"
        elif lang == "en":
            msg = "❌ I couldn't understand the expression.\nExample: 25 + 17"
        else:
            msg = "❌ Не удалось понять выражение.\nПример: 25 + 17"

        await update.message.reply_text(msg)


async def pdf_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🖼️ Rasmlarni PDF qilish"],
        ["📑 PDF tahlil qilish"],
        ["📝 PDF xulosa"],
        ["❓ PDFdan savol berish"],
        ["🌐 PDF tarjima qilish"],
        ["📄 PDF → Rasmlar"],
        ["⬅️ Orqaga"]
    ]

    await update.message.reply_text(
        "📄 HUJJATLAR YORDAMCHISI\n\n"
        "Kerakli xizmatni tanlang:",
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
        "⭐ Premium foydalanuvchi: bir PDF uchun 30 ta rasm.\n\n"
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

    conn = sqlite3.connect("student_ai.db")
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

    # Bitta PDF uchun maksimal 30 ta rasm
    if len(images) >= 30:

        conn.close()

        await update.message.reply_text(
            "⛔ Bitta PDF uchun maksimal 30 ta rasm."
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
        import base64

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

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
                            "inline_data": {
                                "mime_type": "application/pdf",
                                "data": pdf_base64
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=120
        )

        result = response.json()

        print("🔍 GEMINI PDF STATUS:", response.status_code)
        print("🔍 GEMINI PDF RESPONSE:", result)

        if response.status_code != 200:
            return None

        if "candidates" not in result:
            return None

        parts = result["candidates"][0]["content"]["parts"]

        for part in parts:
            if "text" in part:
                return part["text"]

        return None

    except Exception as e:
        print("❌ GEMINI PDF REQUEST ERROR:", e)
        return None


def extract_pdf_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)

        text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text.strip()

    except Exception as e:
        print("PDF TEXT ERROR:", e)
        return ""

# ============================================================
# 📑 PDF TAHLIL
# ============================================================

async def pdf_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf_path = context.user_data.get("pdf_file")

    if not pdf_path or not os.path.exists(pdf_path):
        await update.message.reply_text(
            "❌ Avval PDF fayl yuboring."
        )
        return

    await update.message.reply_text(
        "⏳ PDF fayl AI tomonidan o‘qilmoqda va tahlil qilinmoqda..."
    )

    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        prompt = (
            "Sen Student AI hujjat tahlilchisisan. "
            "Berilgan PDF hujjatni to‘liq tahlil qil. "
            "PDF skanerlangan yoki rasmlar ko‘rinishida bo‘lsa ham "
            "sahifalardagi ma’lumotlarni imkon qadar o‘qishga harakat qil.\n\n"
            "Javobda:\n"
            "1. Asosiy mavzu\n"
            "2. Muhim fikrlar\n"
            "3. Muhim ma’lumotlar\n"
            "4. Qisqa xulosa\n"
            "5. Talaba uchun foydali jihatlar\n\n"
            "Javobni o‘zbek tilida, tushunarli va tartibli yoz."
        )
    elif lang == "en":
        prompt = (
            "You are the Student AI document analyst. "
            "Analyze the provided PDF completely. "
            "If the PDF contains scanned pages or images, "
            "try to read and understand the information in them.\n\n"
            "Include:\n"
            "1. Main topic\n"
            "2. Key points\n"
            "3. Important information\n"
            "4. Short conclusion\n"
            "5. Useful points for a student\n\n"
            "Answer clearly and in English."
        )
    else:
        prompt = (
            "Ты аналитик документов Student AI. "
            "Полностью проанализируй предоставленный PDF. "
            "Если PDF содержит сканированные страницы или изображения, "
            "постарайся прочитать и понять информацию на них.\n\n"
            "Укажи:\n"
            "1. Основную тему\n"
            "2. Главные мысли\n"
            "3. Важную информацию\n"
            "4. Краткий вывод\n"
            "5. Полезные моменты для студента\n\n"
            "Отвечай понятно и структурированно на русском языке."
        )

    answer = gemini_pdf_request(pdf_path, prompt)

    if answer:
        await update.message.reply_text(
            "📑 PDF TAHLILI\n\n" + answer
        )
    else:
        await update.message.reply_text(
            "❌ AI PDFni tahlil qila olmadi.\n\n"
            "PDF hajmi yoki Gemini API bilan bog‘liq muammo bo‘lishi mumkin."
        )


async def pdf_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):

    pdf_path = context.user_data.get("pdf_file")

    if not pdf_path or not os.path.exists(pdf_path):
        await update.message.reply_text(
            "❌ Avval PDF fayl yuboring."
        )
        return

    await update.message.reply_text(
        "⏳ PDF o‘qilmoqda va qisqa xulosa tayyorlanmoqda..."
    )

    pdf_text = extract_pdf_text(pdf_path)

    if not pdf_text:
        await update.message.reply_text(
            "❌ PDF ichidan matn topilmadi."
        )
        return

    pdf_text = pdf_text[:30000]

    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        prompt = (
            "Sen Student AI yordamchisisan. "
            "Quyidagi PDF matnidan talaba uchun tushunarli, "
            "aniq va mazmunli qisqa xulosa tayyorla.\n\n"
            "Eng muhim fikrlarni yo‘qotma. "
            "Keraksiz ma'lumotlarni qo‘shma.\n\n"
            f"PDF matni:\n{pdf_text}"
        )

    elif lang == "en":
        prompt = (
            "You are the Student AI assistant. "
            "Create a clear and useful summary of the following PDF "
            "for a student. Keep the important ideas and remove "
            "unnecessary details.\n\n"
            f"PDF text:\n{pdf_text}"
        )

    else:
        prompt = (
            "Ты помощник Student AI. "
            "Сделай понятное и содержательное краткое резюме "
            "следующего PDF для студента. "
            "Сохрани главные мысли и убери ненужные детали.\n\n"
            f"Текст PDF:\n{pdf_text}"
        )

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.5-flash:generateContent"
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

        print("🔍 PDF SUMMARY GEMINI:", result)

        if "candidates" in result:
            answer = (
                result["candidates"][0]
                ["content"]["parts"][0]["text"]
            )

            await update.message.reply_text(
                "📝 PDF XULOSA\n\n" + answer
            )

        else:
            await update.message.reply_text(
                "❌ AI PDF uchun xulosa tayyorlay olmadi."
            )

    except Exception as e:

        print("PDF SUMMARY ERROR:", e)

        await update.message.reply_text(
            "❌ PDF xulosa qilishda xatolik yuz berdi."
        )


# ============================================================
# ❓ PDFDAN SAVOL BERISH
# ============================================================

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

    pdf_text = extract_pdf_text(pdf_path)

    if not pdf_text:
        await update.message.reply_text(
            "❌ PDF ichidan matn topilmadi."
        )
        return

    pdf_text = pdf_text[:30000]

    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        prompt = (
            "Sen Student AI yordamchisisan. "
            "Quyidagi PDF matniga asoslanib foydalanuvchining "
            "savoliga o‘zbek tilida aniq javob ber.\n\n"
            "Agar javob PDFda bo‘lmasa, buni aniq ayt. "
            "O‘zingdan ma'lumot to‘qib chiqarmagin.\n\n"
            f"PDF matni:\n{pdf_text}\n\n"
            f"Foydalanuvchi savoli:\n{question}"
        )

    elif lang == "en":
        prompt = (
            "You are the Student AI assistant. "
            "Answer the user's question based only on the PDF text.\n\n"
            "If the answer is not in the PDF, say so clearly. "
            "Do not invent information.\n\n"
            f"PDF text:\n{pdf_text}\n\n"
            f"User question:\n{question}"
        )

    else:
        prompt = (
            "Ты помощник Student AI. "
            "Ответь на вопрос пользователя только на основе текста PDF.\n\n"
            "Если ответа в PDF нет, скажи об этом прямо. "
            "Не выдумывай информацию.\n\n"
            f"Текст PDF:\n{pdf_text}\n\n"
            f"Вопрос пользователя:\n{question}"
        )

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.5-flash:generateContent"
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

        print("🔍 PDF QUESTION GEMINI:", result)

        if "candidates" in result:
            answer = (
                result["candidates"][0]
                ["content"]["parts"][0]["text"]
            )

            await update.message.reply_text(
                "❓ PDF SAVOLIGA JAVOB\n\n" + answer
            )

        else:
            await update.message.reply_text(
                "❌ AI javob bera olmadi."
            )

    except Exception as e:

        print("PDF QUESTION ERROR:", e)

        await update.message.reply_text(
            "❌ PDF savoliga javob berishda xatolik yuz berdi."
        )

    finally:
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
        "🌐 PDF matni o‘qilmoqda va tarjima qilinmoqda..."
    )

    pdf_text = extract_pdf_text(pdf_path)

    if not pdf_text:
        await update.message.reply_text(
            "❌ PDF ichidan matn topilmadi."
        )
        return

    pdf_text = pdf_text[:30000]

    lang = context.user_data.get("language", "uz")

    if lang == "uz":
        target_language = "o‘zbek tili"

    elif lang == "en":
        target_language = "English"

    else:
        target_language = "русский язык"

    prompt = (
        f"Translate the following PDF text into {target_language}.\n\n"
        "Preserve the meaning and structure as much as possible. "
        "Do not add explanations or comments. "
        "Return only the translated text.\n\n"
        f"PDF text:\n{pdf_text}"
    )

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.5-flash:generateContent"
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

        print("🔍 PDF TRANSLATE GEMINI:", result)

        if "candidates" in result:

            answer = (
                result["candidates"][0]
                ["content"]["parts"][0]["text"]
            )

            await update.message.reply_text(
                "🌐 PDF TARJIMA\n\n" + answer
            )

        else:

            await update.message.reply_text(
                "❌ PDF tarjima qilinmadi."
            )

    except Exception as e:

        print("PDF TRANSLATE ERROR:", e)

        await update.message.reply_text(
            "❌ PDF tarjima qilishda xatolik yuz berdi."
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

        await update.message.reply_text(
            "✅ PDF qabul qilindi!\n\n"
            "Endi kerakli xizmatni tanlang:\n\n"
            "📑 PDF tahlil qilish\n"
            "📝 PDF xulosa\n"
            "❓ PDFdan savol berish\n"
            "🌐 PDF tarjima qilish\n"
            "📄 PDF → Rasmlar"
        )

    except Exception as e:
        print("PDF UPLOAD ERROR:", e)

        await update.message.reply_text(
            "❌ PDFni qabul qilishda xatolik yuz berdi."
        )

async def pdf_to_images(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📄 PDF → Rasmlar\n\n"
        "Bu funksiya hozircha tayyorlanmoqda."
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
    conn = sqlite3.connect("student_ai.db")
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
        "v1beta/models/gemini-3.5-flash:generateContent"
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

                conn = sqlite3.connect("student_ai.db")
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
                limit_text = (
                    "\n\n⭐ Premium — tarjima limiti yo‘q"
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

    question_count, last_date, premium_until = get_user(user_id)

    # Premium hali faolmi?
    premium_active = (
        premium_until is not None
        and premium_until != ""
        and premium_until >= today
    )

    # Agar Premium faol bo'lmasa, bepul limitni boshqaramiz
    if not premium_active:

        # Yangi kun bo'lsa, bepul limitni yangilash
        if last_date != today:
            question_count = 0
            update_question_count(user_id, 0, today)

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

    # Faqat bepul foydalanuvchining limitini oshiramiz
    if not premium_active:
        question_count += 1
        update_question_count(user_id, question_count, today)

        limit_text = f"📊 Bugungi bepul savollar: {question_count}/5"
    else:
        limit_text = "⭐ Premium — AI savollariga limit yo'q"

    await update.message.reply_text(
        f"⏳ AI o'ylayapti...\n\n"
        f"{limit_text}"
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


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

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

        await pdf_menu(update, context)
        return

    # 🖼️ Rasmlarni PDF qilish
    if text == "🖼️ Rasmlarni PDF qilish":
        context.user_data["pdf_images"] = []
        context.user_data["pdf_collecting"] = True

        await update.message.reply_text(
            "🖼️ Rasmlarni ketma-ket yuboring.\n\n"
            "📌 Bepul foydalanuvchi uchun: 5 ta rasm.\n"
            "📌 Rasmlarni yuborib bo‘lgach, «✅ PDF tayyorlash» tugmasini bosing."
        )

        keyboard = [
            ["✅ PDF tayyorlash"],
            ["❌ Bekor qilish"],
            ["⬅️ Orqaga"]
        ]

        await update.message.reply_text(
            "👇 Kerakli amalni tanlang:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )
        return

    # ✅ PDF tayyorlash
    if text == "✅ PDF tayyorlash":
        await make_pdf_from_images(update, context)
        return

    # ❌ PDF bekor qilish
    if text == "❌ Bekor qilish":
        await cancel_pdf_images(update, context)
        return

    # ⬅️ Orqaga
    if text in [
        "⬅️ Orqaga",
        "⬅️ Back",
        "⬅️ Назад"
    ]:
        context.user_data["pdf_mode"] = False
        context.user_data["pdf_collecting"] = False
        context.user_data["pdf_images"] = []

        lang = context.user_data.get("language", "uz")

        if lang == "uz":
            await uz_menu(update)
        elif lang == "en":
            await en_menu(update)
        else:
            await ru_menu(update)

        return

    # ⭐ Premium
    if text == "⭐ Premium":
        await premium(update, context)
        return

    # 💳 Premium sotib olish
    if text == "💳 Premium sotib olish":
        await premium_buy(update, context)
        return


    # 🤖 AI yordamchi
    if text in [
        "🤖 AI yordamchi",
        "🤖 AI Assistant",
        "🤖 AI Помощник"
    ]:
        context.user_data["ai_mode"] = True
        context.user_data["translator_mode"] = False
        context.user_data["programming_mode"] = False
        context.user_data["calculator_mode"] = False

        await ai_assistant(update, context)
        return

    # 🧮 Kalkulyator
    if text in [
        "🧮 Kalkulyator",
        "🧮 Calculator",
        "🧮 Калькулятор"
    ]:
        context.user_data["calculator_mode"] = True
        context.user_data["programming_mode"] = False
        context.user_data["translator_mode"] = False
        context.user_data["ai_mode"] = False

        await update.message.reply_text(
            "🧮 Kalkulyator\n\n"
            "Hisoblamoqchi bo‘lgan ifodangizni yuboring.\n"
            "Masalan: 25 + 17"
        )
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

        keyboard = [
            ["🖼️ Rasmlarni PDF qilish"],
            ["📑 PDF tahlil qilish"],
            ["📝 PDF xulosa"],
            ["❓ PDFdan savol berish"],
            ["🌐 PDF tarjima qilish"],
            ["📄 PDF → Rasmlar"],
            ["⬅️ Orqaga"]
        ]

        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )

        await update.message.reply_text(
            "📄 HUJJATLAR YORDAMCHISI\n\n"
            "Kerakli xizmatni tanlang:",
            reply_markup=reply_markup
        )
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

        if context.user_data.get("pdf_question_mode"):
            await pdf_question_chat(update, context)
            return

        if text == "📑 PDF tahlil qilish":
            await pdf_analysis(update, context)
            return

        if text == "📝 PDF xulosa":
            await pdf_summary(update, context)
            return

        if text == "❓ PDFdan savol berish":
            await pdf_question(update, context)
            return

        if text == "🌐 PDF tarjima qilish":
            await pdf_translate(update, context)
            return

        if text == "📄 PDF → Rasmlar":
            await pdf_to_images(update, context)
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
    MessageHandler(
        filters.PHOTO,
        pdf_photo_handler
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

app.run_polling()
