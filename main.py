"""
SYRAX Signal Bot
- Majburiy kanal obunasi
- 1WIN reg (SYRAX) + birinchi depozit orqali mini-app
- Postback: /postback?event=reg|ftd|dep&sub1=TELEGRAM_ID
- 7 til
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

import aiosqlite
from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.enums import ChatMemberStatus
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("syrax")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@syraxapp")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/syraxapp")
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/syrax_admin")
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://syrax-app.github.io/SYRAX-MINI-APP/")
PARTNER_LINK = os.getenv("PARTNER_LINK", "https://shorturl.at/eqDTy")
PROMO_CODE = os.getenv("PROMO_CODE", "SYRAX")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
DB_PATH = os.getenv("DB_PATH", "syrax.db")
PORT = int(os.getenv("PORT", "8000"))

# ---------- Translations (7 langs) ----------
T = {
    "uz": {
        "choose_lang": "🌐 Tilni tanlang / Choose language:",
        "need_sub": "📢 Botdan foydalanish uchun kanalga obuna bo‘ling:",
        "check_sub": "✅ Obunani tekshirish",
        "not_sub": "❌ Siz hali obuna bo‘lmadingiz. Avval kanalga qo‘shiling.",
        "welcome": (
            "👋🏻 <b>🔸SYRAX - SIGNAL BOT🔸</b> ga xush kelibsiz!\n\n"
            "🚀 Ushbu bot mashhur o‘yinlardan imkoniyatlarni foydalanishingiz "
            "va maksimal foyda olishingiz uchun yaratilgan.\n\n"
            "🧠 Bot <b>maxsus tizimli AI</b> asosida ishlaydi — "
            "1WIN / Spribe o‘yinlar provayderi API ma’lumotlarini olib "
            "real vaqtda qayta ishlaydi.\n"
            "🎰 O‘qitish uchun <b>10,000+</b> o‘yin tahlil qilingan.\n"
            "💰 Foydalanuvchilar kuniga <b>15–25%</b> daromad olishmoqda!\n"
            "📈 Bashorat aniqligi: <b>~89%</b> (doimiy yaxshilanmoqda).\n\n"
            "🔥 O‘yinni boshlang va signalimizdan foydalaning!"
        ),
        "btn_guide": "📖 Ko‘rsatma",
        "btn_signal": "❗ Signalni olish ❗",
        "btn_account": "🆔 Mening hisobim",
        "btn_lang": "🌐 Tilni tanlash",
        "btn_video": "🎬 Video qo‘llanma",
        "btn_support": "🆘 Qo‘llab-quvvatlash",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ Havola ochilmayapti",
        "btn_cancel": "❌ Bekor qilish",
        "btn_check_id": "🔍 ID ni tekshirish",
        "btn_deposit_how": "💰 Balansni qanday to‘ldirish mumkin?",
        "btn_check_dep": "🔍 Depozitni tekshirish",
        "btn_open_app": "🎮 Signallarni ochish",
        "btn_main": "⬅️ Asosiy menyu",
        "reg_text": (
            "💸 <b>1.</b> Saytda ro‘yxatdan o‘tish uchun <b>1WIN</b> tugmasini bosing.\n\n"
            "💸 <b>2.</b> Ro‘yxatdan o‘tishda promo kodini kiriting: <b>{promo}</b>\n\n"
            "💸 <b>3.</b> Ro‘yxatdan so‘ng bot akkauntingizni avtomatik tekshiradi "
            "va xabar yuboradi.\n"
            "Agar xabar kelmasa — «ID ni tekshirish» tugmasini bosing va ID yuboring.\n\n"
            "Agar muammo bo‘lsa: {support}\n\n"
            "💸 <b>4.</b> Muhim: agar sizda hisob bo‘lsa, yangi elektron pochta "
            "bilan yangi hisob yarating.\n"
            "Telefon raqami ixtiyoriy; eng muhimi — elektron pochtangiz."
        ),
        "reg_ok": (
            "✅ <b>Siz muvaffaqiyatli ro‘yxatdan o‘tdingiz!</b> 🎉\n\n"
            "Endi signallarga kirish uchun o‘yin hisobingiz balansini to‘ldiring. 💳"
        ),
        "dep_need": (
            "🌐 <b>Signalga kirish uchun birinchi depozitni amalga oshirishingiz kerak.</b>\n\n"
            "✦ Depozit miqdori botdagi LVL (daraja), status va signal muvaffaqiyati "
            "ehtimoliga bog‘liq. Katta depozit qanchalik katta bo‘lsa, LVLingiz "
            "shunchalik yuqori bo‘ladi va muvaffaqiyat ehtimoli yuqori signallar olasiz.\n\n"
            "✦ Hisobingizni faollashtirish uchun birinchi depozitni amalga oshiring. "
            "Ushbu mablag‘lar HISOBINGIZGA kiritiladi — o‘yin va g‘alaba uchun ishlatasiz.\n\n"
            "● Depozitdan so‘ng «🔎 Depozitni tekshirish» tugmasini bosing."
        ),
        "dep_ok": (
            "🎉 Hisob faollashtirildi!\n\n"
            "Endi signallarni ochishingiz mumkin:"
        ),
        "balance_zero": (
            "⚠️ <b>Balansingiz 0 ga tushgan.</b>\n\n"
            "Shu sababli signallardan foydalana olmaysiz.\n"
            "Foydalanish uchun 1WIN hisobingizni to‘ldiring."
        ),
        "account": (
            "👤 <b>Profil</b>\n"
            "————————————\n"
            "🆔 ID: <code>{tg_id}</code>\n"
            "💰 Depozit: {dep_label}\n"
            "🏅 Daraja: {level_name}\n"
            "🎯 Signal aniqligi: ~{accuracy}%\n"
            "📊 Keyingi darajagacha: {next_need}\n"
            "{progress_bar} {progress_pct}%\n"
            "————————————\n"
            "Til: {lang} | Obuna: {sub}\n"
            "Reg: {reg} | Status: {status}"
        ),
        "guide": (
            "📖 <b>Ko‘rsatma</b>\n\n"
            "🧠 Bot <b>maxsus tizimli AI</b> asosida ishlaydi — "
            "1WIN / Spribe o‘yinlar provayderi API ma’lumotlarini olib "
            "real vaqtda qayta ishlaydi.\n"
            "🎰 O‘qitish uchun 10,000+ o‘yin tahlil qilingan.\n"
            "💰 Foydalanuvchilar kuniga 15–25% daromad olishmoqda!\n"
            "📈 Bashorat aniqligi ~89% (yaxshilanmoqda).\n\n"
            "<b>Daromad olish uchun:</b>\n\n"
            "🟢 1. O‘yinni tanlang (mini-app).\n"
            "🟢 2. Botdan signal so‘rang va shu asosida tikish qiling.\n"
            "🟢 3. Signal ishlamasa — keyingi signalga yo‘qotishni qoplash uchun "
            "tikishni ikki baravar oshiring (X²).\n\n"
            "⚠️ Muhim: X² strategiyasini doimiy ishlatmang, xavfdan saqlaning.\n\n"
            "Bugun sinab ko‘ring — kapitalni oshirishni o‘zingiz ko‘ring! 🚀"
        ),
        "video": "🎬 Video qo‘llanma tez orada qo‘shiladi.\nSupport: {support}",
        "send_id": "1WIN yoki Telegram ID raqamingizni yuboring:",
        "id_saved": "✅ Qabul qilindi. Tekshiruv kutilmoqda / postback orqali tasdiqlanadi.",
        "link_fail_help": (
            "⚠️ Havola ochilmasa:\n"
            "• VPN yoqing\n"
            "• Boshqa brauzer / Chrome ni sinab ko‘ring\n"
            "• Supportga yozing: {support}"
        ),
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 Faol",
        "status_wait_dep": "🟡 Depozit kutilmoqda",
        "status_wait_reg": "🟠 Ro‘yxatdan o‘tish kerak",
        "status_sub": "🔴 Avval obuna",
    },
    "ru": {
        "choose_lang": "🌐 Выберите язык:",
        "need_sub": "📢 Подпишитесь на канал, чтобы пользоваться ботом:",
        "check_sub": "✅ Проверить подписку",
        "not_sub": "❌ Вы ещё не подписаны. Сначала подпишитесь на канал.",
        "welcome": (
            "👋 Добро пожаловать в <b>Syrax Signals</b>!\n\n"
            "🚀 Бот создан для сигналов по популярным играм.\n"
            "🎯 Система анализирует данные и выдаёт сигналы.\n"
            "🔥 Начните и используйте прогнозы!"
        ),
        "btn_guide": "📖 Инструкция",
        "btn_signal": "❗ Получить сигнал ❗",
        "btn_account": "🆔 Мой аккаунт",
        "btn_lang": "🌐 Язык",
        "btn_video": "🎬 Видео",
        "btn_support": "🆘 Поддержка",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ Ссылка не открывается",
        "btn_cancel": "❌ Отмена",
        "btn_check_id": "🔍 Проверить ID",
        "btn_deposit_how": "💰 Как пополнить баланс?",
        "btn_check_dep": "🔍 Проверить депозит",
        "btn_open_app": "🎮 Открыть сигналы",
        "btn_main": "⬅️ Главное меню",
        "reg_text": (
            "📋 <b>Регистрация</b>\n\n"
            "1️⃣ Нажмите <b>1WIN</b> для регистрации.\n"
            "2️⃣ Введите промокод: <b>{promo}</b>\n"
            "3️⃣ После регистрации бот проверит аккаунт.\n"
            "Если нет сообщения — «Проверить ID».\n\n"
            "Поддержка: {support}\n\n"
            "4️⃣ Важно: при необходимости создайте новый аккаунт на новый email."
        ),
        "reg_ok": (
            "✅ <b>Регистрация успешна!</b> 🎉\n\n"
            "Для доступа к сигналам пополните баланс. 💳"
        ),
        "dep_need": (
            "💳 Для доступа нужен первый депозит.\n\n"
            "После депозита нажмите «Проверить депозит»."
        ),
        "dep_ok": "🎉 Аккаунт активирован!\n\nМожно открыть сигналы:",
        "balance_zero": "⚠️ Баланс 0. Пополните счёт для сигналов.",
        "account": (
            "🆔 <b>Аккаунт</b>\n\n"
            "Telegram ID: <code>{tg_id}</code>\n"
            "Язык: {lang}\n"
            "Подписка: {sub}\n"
            "1WIN reg: {reg}\n"
            "Депозит: {dep}\n"
            "Статус: {status}"
        ),
        "guide": (
            "📖 <b>Как пользоваться</b>\n\n"
            "🟢 1. Выберите игру в mini-app.\n"
            "🟢 2. Возьмите сигнал и ставьте.\n"
            "🟢 3. При неудаче осторожно управляйте следующей ставкой.\n\n"
            "⚠️ Не используйте x2 постоянно."
        ),
        "video": "🎬 Видео скоро.\nПоддержка: {support}",
        "send_id": "Отправьте ID (Telegram или 1WIN):",
        "id_saved": "✅ Принято. Ожидаем подтверждение / postback.",
        "link_fail_help": "⚠️ Если ссылка не открывается — VPN / другой браузер.\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 Активен",
        "status_wait_dep": "🟡 Ждём депозит",
        "status_wait_reg": "🟠 Нужна регистрация",
        "status_sub": "🔴 Сначала подписка",
    },
    "en": {
        "choose_lang": "🌐 Choose language:",
        "need_sub": "📢 Subscribe to the channel to use the bot:",
        "check_sub": "✅ Check subscription",
        "not_sub": "❌ You are not subscribed yet.",
        "welcome": (
            "👋 Welcome to <b>Syrax Signals</b>!\n\n"
            "🚀 Signals for popular games.\n"
            "🎯 Analysis-based predictions.\n"
            "🔥 Start and use the signals!"
        ),
        "btn_guide": "📖 Guide",
        "btn_signal": "❗ Get signal ❗",
        "btn_account": "🆔 My account",
        "btn_lang": "🌐 Language",
        "btn_video": "🎬 Video guide",
        "btn_support": "🆘 Support",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ Link not opening",
        "btn_cancel": "❌ Cancel",
        "btn_check_id": "🔍 Check ID",
        "btn_deposit_how": "💰 How to deposit?",
        "btn_check_dep": "🔍 Check deposit",
        "btn_open_app": "🎮 Open signals",
        "btn_main": "⬅️ Main menu",
        "reg_text": (
            "📋 <b>Registration</b>\n\n"
            "1️⃣ Tap <b>1WIN</b> to register.\n"
            "2️⃣ Enter promo: <b>{promo}</b>\n"
            "3️⃣ Bot will verify your account.\n"
            "If no message — use Check ID.\n\n"
            "Support: {support}"
        ),
        "reg_ok": "✅ <b>Registered!</b> 🎉\n\nDeposit to unlock signals. 💳",
        "dep_need": "💳 First deposit required for access.\n\nThen tap Check deposit.",
        "dep_ok": "🎉 Account activated!\n\nOpen signals:",
        "balance_zero": "⚠️ Balance is 0. Deposit to continue.",
        "account": (
            "🆔 <b>Account</b>\n\n"
            "Telegram ID: <code>{tg_id}</code>\n"
            "Lang: {lang}\n"
            "Sub: {sub}\n"
            "Reg: {reg}\n"
            "Deposit: {dep}\n"
            "Status: {status}"
        ),
        "guide": "📖 Pick a game → get signal → bet carefully. Don’t always use x2.",
        "video": "🎬 Video soon.\nSupport: {support}",
        "send_id": "Send your ID:",
        "id_saved": "✅ Saved. Waiting for confirmation.",
        "link_fail_help": "⚠️ Try VPN / another browser.\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 Active",
        "status_wait_dep": "🟡 Waiting deposit",
        "status_wait_reg": "🟠 Need registration",
        "status_sub": "🔴 Subscribe first",
    },
    "tr": {
        "choose_lang": "🌐 Dil seçin:",
        "need_sub": "📢 Botu kullanmak için kanala abone olun:",
        "check_sub": "✅ Aboneliği kontrol et",
        "not_sub": "❌ Henüz abone değilsiniz.",
        "welcome": "👋 <b>Syrax Signals</b>’a hoş geldiniz!\n\n🚀 Popüler oyunlar için sinyaller.",
        "btn_guide": "📖 Rehber",
        "btn_signal": "❗ Sinyal al ❗",
        "btn_account": "🆔 Hesabım",
        "btn_lang": "🌐 Dil",
        "btn_video": "🎬 Video",
        "btn_support": "🆘 Destek",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ Link açılmıyor",
        "btn_cancel": "❌ İptal",
        "btn_check_id": "🔍 ID kontrol",
        "btn_deposit_how": "💰 Nasıl yatırım yapılır?",
        "btn_check_dep": "🔍 Yatırımı kontrol et",
        "btn_open_app": "🎮 Sinyalleri aç",
        "btn_main": "⬅️ Ana menü",
        "reg_text": "📋 <b>Kayıt</b>\n\n1️⃣ 1WIN’e bas.\n2️⃣ Promo: <b>{promo}</b>\n\nDestek: {support}",
        "reg_ok": "✅ Kayıt başarılı! Yatırım yapın. 💳",
        "dep_need": "💳 İlk yatırım gerekli.",
        "dep_ok": "🎉 Aktif! Sinyalleri açın:",
        "balance_zero": "⚠️ Bakiye 0. Yatırım yapın.",
        "account": "🆔 ID: <code>{tg_id}</code>\nDil: {lang}\nReg: {reg}\nDep: {dep}\n{status}",
        "guide": "📖 Oyun seç → sinyal al → dikkatli oyna.",
        "video": "🎬 Video yakında.\n{support}",
        "send_id": "ID gönderin:",
        "id_saved": "✅ Alındı.",
        "link_fail_help": "⚠️ VPN deneyin.\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 Aktif",
        "status_wait_dep": "🟡 Yatırım bekleniyor",
        "status_wait_reg": "🟠 Kayıt gerekli",
        "status_sub": "🔴 Önce abone ol",
    },
    "ar": {
        "choose_lang": "🌐 اختر اللغة:",
        "need_sub": "📢 اشترك في القناة لاستخدام البوت:",
        "check_sub": "✅ تحقق من الاشتراك",
        "not_sub": "❌ أنت غير مشترك بعد.",
        "welcome": "👋 مرحباً بك في <b>Syrax Signals</b>!",
        "btn_guide": "📖 الدليل",
        "btn_signal": "❗ الحصول على إشارة ❗",
        "btn_account": "🆔 حسابي",
        "btn_lang": "🌐 اللغة",
        "btn_video": "🎬 فيديو",
        "btn_support": "🆘 الدعم",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ الرابط لا يفتح",
        "btn_cancel": "❌ إلغاء",
        "btn_check_id": "🔍 تحقق من المعرف",
        "btn_deposit_how": "💰 كيف أشحن الرصيد؟",
        "btn_check_dep": "🔍 تحقق من الإيداع",
        "btn_open_app": "🎮 فتح الإشارات",
        "btn_main": "⬅️ القائمة",
        "reg_text": "📋 <b>التسجيل</b>\n\n1️⃣ اضغط 1WIN\n2️⃣ البرومو: <b>{promo}</b>\n\n{support}",
        "reg_ok": "✅ تم التسجيل! أودع للوصول. 💳",
        "dep_need": "💳 الإيداع الأول مطلوب.",
        "dep_ok": "🎉 تم التفعيل!",
        "balance_zero": "⚠️ الرصيد 0. أودع للمتابعة.",
        "account": "🆔 <code>{tg_id}</code>\n{lang}\n{reg}\n{dep}\n{status}",
        "guide": "📖 اختر لعبة → خذ إشارة → راهن بحذر.",
        "video": "🎬 قريباً\n{support}",
        "send_id": "أرسل المعرف:",
        "id_saved": "✅ تم.",
        "link_fail_help": "⚠️ جرّب VPN\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 نشط",
        "status_wait_dep": "🟡 بانتظار الإيداع",
        "status_wait_reg": "🟠 يلزم التسجيل",
        "status_sub": "🔴 اشترك أولاً",
    },
    "hi": {
        "choose_lang": "🌐 भाषा चुनें:",
        "need_sub": "📢 बॉट उपयोग के लिए चैनल सब्सक्राइब करें:",
        "check_sub": "✅ सब्सक्रिप्शन जांचें",
        "not_sub": "❌ आप अभी सब्सक्राइब नहीं हैं।",
        "welcome": "👋 <b>Syrax Signals</b> में स्वागत है!",
        "btn_guide": "📖 गाइड",
        "btn_signal": "❗ सिग्नल लें ❗",
        "btn_account": "🆔 मेरा अकाउंट",
        "btn_lang": "🌐 भाषा",
        "btn_video": "🎬 वीडियो",
        "btn_support": "🆘 सपोर्ट",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ लिंक नहीं खुल रहा",
        "btn_cancel": "❌ रद्द",
        "btn_check_id": "🔍 ID जांचें",
        "btn_deposit_how": "💰 डिपॉजिट कैसे करें?",
        "btn_check_dep": "🔍 डिपॉजिट जांचें",
        "btn_open_app": "🎮 सिग्नल खोलें",
        "btn_main": "⬅️ मेन मेनू",
        "reg_text": "📋 <b>रजिस्ट्रेशन</b>\n\n1️⃣ 1WIN दबाएं\n2️⃣ प्रोमो: <b>{promo}</b>\n\n{support}",
        "reg_ok": "✅ रजिस्टर हो गया! डिपॉजिट करें। 💳",
        "dep_need": "💳 पहले डिपॉजिट की जरूरत।",
        "dep_ok": "🎉 सक्रिय!",
        "balance_zero": "⚠️ बैलेंस 0। डिपॉजिट करें।",
        "account": "🆔 <code>{tg_id}</code>\n{lang}\n{reg}\n{dep}\n{status}",
        "guide": "📖 गेम चुनें → सिग्नल लें → सावधानी से खेलें।",
        "video": "🎬 जल्द\n{support}",
        "send_id": "ID भेजें:",
        "id_saved": "✅ सेव।",
        "link_fail_help": "⚠️ VPN आज़माएं\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 सक्रिय",
        "status_wait_dep": "🟡 डिपॉजिट प्रतीक्षा",
        "status_wait_reg": "🟠 रजिस्टर करें",
        "status_sub": "🔴 पहले सब्सक्राइब",
    },
    "es": {
        "choose_lang": "🌐 Elige el idioma:",
        "need_sub": "📢 Suscríbete al canal para usar el bot:",
        "check_sub": "✅ Verificar suscripción",
        "not_sub": "❌ Aún no estás suscrito.",
        "welcome": "👋 ¡Bienvenido a <b>Syrax Signals</b>!\n\n🚀 Señales para juegos populares.",
        "btn_guide": "📖 Guía",
        "btn_signal": "❗ Obtener señal ❗",
        "btn_account": "🆔 Mi cuenta",
        "btn_lang": "🌐 Idioma",
        "btn_video": "🎬 Video",
        "btn_support": "🆘 Soporte",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ El enlace no abre",
        "btn_cancel": "❌ Cancelar",
        "btn_check_id": "🔍 Verificar ID",
        "btn_deposit_how": "💰 ¿Cómo depositar?",
        "btn_check_dep": "🔍 Verificar depósito",
        "btn_open_app": "🎮 Abrir señales",
        "btn_main": "⬅️ Menú principal",
        "reg_text": "📋 <b>Registro</b>\n\n1️⃣ Pulsa <b>1WIN</b>\n2️⃣ Promo: <b>{promo}</b>\n\n{support}",
        "reg_ok": "✅ ¡Registrado! Deposita para continuar. 💳",
        "dep_need": "💳 Se requiere el primer depósito.",
        "dep_ok": "🎉 ¡Cuenta activada!",
        "balance_zero": "⚠️ Saldo 0. Deposita para continuar.",
        "account": "🆔 <code>{tg_id}</code>\n{lang}\n{reg}\n{dep}\n{status}",
        "guide": "📖 Elige juego → toma señal → apuesta con cuidado.",
        "video": "🎬 Pronto\n{support}",
        "send_id": "Envía tu ID:",
        "id_saved": "✅ Guardado.",
        "link_fail_help": "⚠️ Prueba VPN\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 Activo",
        "status_wait_dep": "🟡 Esperando depósito",
        "status_wait_reg": "🟠 Necesita registro",
        "status_sub": "🔴 Suscríbete primero",
    },
    "az": {
        "choose_lang": "🌐 Dili seçin:",
        "need_sub": "📢 Botdan istifadə üçün kanala abunə olun:",
        "check_sub": "✅ Abunəliyi yoxla",
        "not_sub": "❌ Hələ abunə deyilsiniz.",
        "welcome": "👋 <b>Syrax Signals</b>-ə xoş gəlmisiniz!\n\n🚀 Populyar oyunlar üçün siqnallar.",
        "btn_guide": "📖 Təlimat",
        "btn_signal": "❗ Siqnal al ❗",
        "btn_account": "🆔 Hesabım",
        "btn_lang": "🌐 Dil",
        "btn_video": "🎬 Video",
        "btn_support": "🆘 Dəstək",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ Link açılmır",
        "btn_cancel": "❌ Ləğv et",
        "btn_check_id": "🔍 ID yoxla",
        "btn_deposit_how": "💰 Necə depozit?",
        "btn_check_dep": "🔍 Depoziti yoxla",
        "btn_open_app": "🎮 Siqnalları aç",
        "btn_main": "⬅️ Əsas menyu",
        "reg_text": "📋 <b>Qeydiyyat</b>\n\n1️⃣ 1WIN bas\n2️⃣ Promo: <b>{promo}</b>\n\n{support}",
        "reg_ok": "✅ Qeydiyyat uğurlu! Depozit edin. 💳",
        "dep_need": "💳 İlk depozit tələb olunur.",
        "dep_ok": "🎉 Aktiv!",
        "balance_zero": "⚠️ Balans 0. Depozit edin.",
        "account": "🆔 <code>{tg_id}</code>\n{lang}\n{reg}\n{dep}\n{status}",
        "guide": "📖 Oyun seç → siqnal al → diqqətlə oyna.",
        "video": "🎬 Tezliklə\n{support}",
        "send_id": "ID göndərin:",
        "id_saved": "✅ Qəbul edildi.",
        "link_fail_help": "⚠️ VPN sınayın\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 Aktiv",
        "status_wait_dep": "🟡 Depozit gözlənilir",
        "status_wait_reg": "🟠 Qeydiyyat lazımdır",
        "status_sub": "🔴 Əvvəlcə abunə ol",
    },
    "pt_br": {
        "choose_lang": "🌐 Escolha o idioma:",
        "need_sub": "📢 Inscreva-se no canal para usar o bot:",
        "check_sub": "✅ Verificar inscrição",
        "not_sub": "❌ Você ainda não está inscrito.",
        "welcome": "👋 Bem-vindo ao <b>Syrax Signals</b>!\n\n🚀 Sinais para jogos populares.",
        "btn_guide": "📖 Guia",
        "btn_signal": "❗ Obter sinal ❗",
        "btn_account": "🆔 Minha conta",
        "btn_lang": "🌐 Idioma",
        "btn_video": "🎬 Vídeo",
        "btn_support": "🆘 Suporte",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ Link não abre",
        "btn_cancel": "❌ Cancelar",
        "btn_check_id": "🔍 Verificar ID",
        "btn_deposit_how": "💰 Como depositar?",
        "btn_check_dep": "🔍 Verificar depósito",
        "btn_open_app": "🎮 Abrir sinais",
        "btn_main": "⬅️ Menu principal",
        "reg_text": "📋 <b>Registro</b>\n\n1️⃣ Toque em <b>1WIN</b>\n2️⃣ Promo: <b>{promo}</b>\n\n{support}",
        "reg_ok": "✅ Registrado! Deposite para continuar. 💳",
        "dep_need": "💳 Primeiro depósito necessário.",
        "dep_ok": "🎉 Conta ativada!",
        "balance_zero": "⚠️ Saldo 0. Deposite para continuar.",
        "account": "🆔 <code>{tg_id}</code>\n{lang}\n{reg}\n{dep}\n{status}",
        "guide": "📖 Escolha o jogo → pegue o sinal → aposte com cuidado.",
        "video": "🎬 Em breve\n{support}",
        "send_id": "Envie seu ID:",
        "id_saved": "✅ Salvo.",
        "link_fail_help": "⚠️ Tente VPN\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 Ativo",
        "status_wait_dep": "🟡 Aguardando depósito",
        "status_wait_reg": "🟠 Precisa registrar",
        "status_sub": "🔴 Inscreva-se primeiro",
    },
    "pt": {
        "choose_lang": "🌐 Escolha o idioma:",
        "need_sub": "📢 Subscreva o canal para usar o bot:",
        "check_sub": "✅ Verificar subscrição",
        "not_sub": "❌ Ainda não está subscrito.",
        "welcome": "👋 Bem-vindo ao <b>Syrax Signals</b>!\n\n🚀 Sinais para jogos populares.",
        "btn_guide": "📖 Guia",
        "btn_signal": "❗ Obter sinal ❗",
        "btn_account": "🆔 A minha conta",
        "btn_lang": "🌐 Idioma",
        "btn_video": "🎬 Vídeo",
        "btn_support": "🆘 Suporte",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ O link não abre",
        "btn_cancel": "❌ Cancelar",
        "btn_check_id": "🔍 Verificar ID",
        "btn_deposit_how": "💰 Como depositar?",
        "btn_check_dep": "🔍 Verificar depósito",
        "btn_open_app": "🎮 Abrir sinais",
        "btn_main": "⬅️ Menu principal",
        "reg_text": "📋 <b>Registo</b>\n\n1️⃣ Toque em <b>1WIN</b>\n2️⃣ Promo: <b>{promo}</b>\n\n{support}",
        "reg_ok": "✅ Registado! Deposite para continuar. 💳",
        "dep_need": "💳 Primeiro depósito necessário.",
        "dep_ok": "🎉 Conta ativada!",
        "balance_zero": "⚠️ Saldo 0. Deposite para continuar.",
        "account": "🆔 <code>{tg_id}</code>\n{lang}\n{reg}\n{dep}\n{status}",
        "guide": "📖 Escolha o jogo → pegue o sinal → aposte com cuidado.",
        "video": "🎬 Em breve\n{support}",
        "send_id": "Envie o seu ID:",
        "id_saved": "✅ Guardado.",
        "link_fail_help": "⚠️ Tente VPN\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 Ativo",
        "status_wait_dep": "🟡 A aguardar depósito",
        "status_wait_reg": "🟠 Precisa de registo",
        "status_sub": "🔴 Subscreva primeiro",
    },
    "th": {
        "choose_lang": "🌐 เลือกภาษา:",
        "need_sub": "📢 สมัครสมาชิกช่องเพื่อใช้บอท:",
        "check_sub": "✅ ตรวจสอบการสมัคร",
        "not_sub": "❌ คุณยังไม่ได้สมัครสมาชิก",
        "welcome": "👋 ยินดีต้อนรับสู่ <b>Syrax Signals</b>!\n\n🚀 สัญญาณสำหรับเกมยอดนิยม",
        "btn_guide": "📖 คู่มือ",
        "btn_signal": "❗ รับสัญญาณ ❗",
        "btn_account": "🆔 บัญชีของฉัน",
        "btn_lang": "🌐 ภาษา",
        "btn_video": "🎬 วิดีโอ",
        "btn_support": "🆘 ฝ่ายสนับสนุน",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ ลิงก์เปิดไม่ได้",
        "btn_cancel": "❌ ยกเลิก",
        "btn_check_id": "🔍 ตรวจสอบ ID",
        "btn_deposit_how": "💰 วิธีฝากเงิน?",
        "btn_check_dep": "🔍 ตรวจสอบการฝาก",
        "btn_open_app": "🎮 เปิดสัญญาณ",
        "btn_main": "⬅️ เมนูหลัก",
        "reg_text": "📋 <b>ลงทะเบียน</b>\n\n1️⃣ กด <b>1WIN</b>\n2️⃣ โปรโม: <b>{promo}</b>\n\n{support}",
        "reg_ok": "✅ ลงทะเบียนแล้ว! ฝากเงินเพื่อดำเนินการต่อ 💳",
        "dep_need": "💳 ต้องมีการฝากครั้งแรก",
        "dep_ok": "🎉 เปิดใช้งานแล้ว!",
        "balance_zero": "⚠️ ยอดคงเหลือ 0 ฝากเงินเพื่อดำเนินการต่อ",
        "account": "🆔 <code>{tg_id}</code>\n{lang}\n{reg}\n{dep}\n{status}",
        "guide": "📖 เลือกเกม → รับสัญญาณ → เดิมพันอย่างระมัดระวัง",
        "video": "🎬 เร็วๆ นี้\n{support}",
        "send_id": "ส่ง ID ของคุณ:",
        "id_saved": "✅ บันทึกแล้ว",
        "link_fail_help": "⚠️ ลองใช้ VPN\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 ใช้งานได้",
        "status_wait_dep": "🟡 รอการฝาก",
        "status_wait_reg": "🟠 ต้องลงทะเบียน",
        "status_sub": "🔴 สมัครสมาชิกก่อน",
    },
    "ko": {
        "choose_lang": "🌐 언어를 선택하세요:",
        "need_sub": "📢 봇을 사용하려면 채널을 구독하세요:",
        "check_sub": "✅ 구독 확인",
        "not_sub": "❌ 아직 구독하지 않았습니다.",
        "welcome": "👋 <b>Syrax Signals</b>에 오신 것을 환영합니다!\n\n🚀 인기 게임 시그널.",
        "btn_guide": "📖 가이드",
        "btn_signal": "❗ 시그널 받기 ❗",
        "btn_account": "🆔 내 계정",
        "btn_lang": "🌐 언어",
        "btn_video": "🎬 영상",
        "btn_support": "🆘 지원",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ 링크가 열리지 않음",
        "btn_cancel": "❌ 취소",
        "btn_check_id": "🔍 ID 확인",
        "btn_deposit_how": "💰 입금 방법?",
        "btn_check_dep": "🔍 입금 확인",
        "btn_open_app": "🎮 시그널 열기",
        "btn_main": "⬅️ 메인 메뉴",
        "reg_text": "📋 <b>등록</b>\n\n1️⃣ <b>1WIN</b> 누르기\n2️⃣ 프로모: <b>{promo}</b>\n\n{support}",
        "reg_ok": "✅ 등록 완료! 입금하세요. 💳",
        "dep_need": "💳 첫 입금이 필요합니다.",
        "dep_ok": "🎉 활성화됨!",
        "balance_zero": "⚠️ 잔액 0. 입금하세요.",
        "account": "🆔 <code>{tg_id}</code>\n{lang}\n{reg}\n{dep}\n{status}",
        "guide": "📖 게임 선택 → 시그널 받기 → 신중히 베팅.",
        "video": "🎬 곧 제공\n{support}",
        "send_id": "ID를 보내세요:",
        "id_saved": "✅ 저장됨.",
        "link_fail_help": "⚠️ VPN을 사용해 보세요\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 활성",
        "status_wait_dep": "🟡 입금 대기",
        "status_wait_reg": "🟠 등록 필요",
        "status_sub": "🔴 먼저 구독하세요",
    },
}

LANG_NAMES = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "hi": "🇮🇳 हिंदी",
    "pt_br": "🇧🇷 Brazilian",
    "es": "🇪🇸 Español",
    "uz": "🇺🇿 O'zbek",
    "az": "🇦🇿 Azərbaycanca",
    "tr": "🇹🇷 Türkçe",
    "pt": "🇵🇹 Português",
    "ar": "🇦🇪 العربية",
    "th": "🇹🇭 ไทย",
    "ko": "🇰🇷 한국어",
}


def t(lang: str, key: str, **kw) -> str:
    pack = T.get(lang) or T["uz"]
    text = pack.get(key) or T["uz"].get(key, key)
    try:
        return text.format(**kw)
    except Exception:
        return text


# ---------- DB ----------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY,
                lang TEXT DEFAULT 'uz',
                subscribed INTEGER DEFAULT 0,
                registered INTEGER DEFAULT 0,
                deposited INTEGER DEFAULT 0,
                balance_ok INTEGER DEFAULT 1,
                win_user_id TEXT,
                waiting_id INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


async def get_user(tg_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
        row = await cur.fetchone()
        if row:
            return dict(row)
        await db.execute("INSERT INTO users (tg_id) VALUES (?)", (tg_id,))
        await db.commit()
        return {
            "tg_id": tg_id,
            "lang": "uz",
            "subscribed": 0,
            "registered": 0,
            "deposited": 0,
            "balance_ok": 1,
            "win_user_id": None,
            "waiting_id": 0,
        }


async def update_user(tg_id: int, **fields):
    if not fields:
        return
    keys = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [tg_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {keys} WHERE tg_id=?", vals)
        await db.commit()


# ---------- Keyboards ----------
def kb_langs() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=name, callback_data=f"lang:{code}")
        for code, name in LANG_NAMES.items()
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_sub(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 SYRAX Channel", url=CHANNEL_URL)],
            [InlineKeyboardButton(text=t(lang, "check_sub"), callback_data="check_sub")],
        ]
    )


def kb_main(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_guide"), callback_data="guide")],
            [InlineKeyboardButton(text=t(lang, "btn_signal"), callback_data="signal")],
            [
                InlineKeyboardButton(text=t(lang, "btn_account"), callback_data="account"),
                InlineKeyboardButton(text=t(lang, "btn_lang"), callback_data="set_lang"),
            ],
            [
                InlineKeyboardButton(text=t(lang, "btn_video"), callback_data="video"),
                InlineKeyboardButton(text=t(lang, "btn_support"), url=SUPPORT_URL),
            ],
        ]
    )


def partner_url(tg_id: int) -> str:
    base = PARTNER_LINK
    sep = "&" if "?" in base else "?"
    # sub1 = telegram id for postback matching
    if "sub1=" in base:
        return base
    return f"{base}{sep}sub1={tg_id}"


def kb_reg(lang: str, tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_1win"), url=partner_url(tg_id))],
            [InlineKeyboardButton(text=t(lang, "btn_link_fail"), callback_data="link_fail")],
            [InlineKeyboardButton(text=t(lang, "btn_check_id"), callback_data="check_id")],
            [InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="main")],
        ]
    )


def kb_deposit(lang: str, tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_deposit_how"), callback_data="dep_how")],
            [InlineKeyboardButton(text=t(lang, "btn_1win"), url=partner_url(tg_id))],
            [InlineKeyboardButton(text=t(lang, "btn_check_dep"), callback_data="check_dep")],
            [InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="main")],
        ]
    )


def kb_open_app(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "btn_open_app"),
                    web_app=WebAppInfo(url=MINIAPP_URL),
                )
            ],
            [InlineKeyboardButton(text=t(lang, "btn_main"), callback_data="main")],
        ]
    )


def kb_back(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(lang, "btn_main"), callback_data="main")]]
    )


# ---------- Subscription check ----------
async def is_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        )
    except Exception as e:
        logger.warning("sub check failed: %s", e)
        return False


# ---------- Handlers ----------
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user = await get_user(message.from_user.id)
    # Always ask language first if default and first time — still show lang if needed
    if not user.get("lang") or message.text == "/start":
        # soft: show lang picker once then flow
        pass
    await message.answer(t(user["lang"], "choose_lang"), reply_markup=kb_langs())


@router.callback_query(F.data.startswith("lang:"))
async def on_lang(cq: CallbackQuery, bot: Bot):
    lang = cq.data.split(":")[1]
    if lang not in T:
        lang = "uz"
    await update_user(cq.from_user.id, lang=lang)
    user = await get_user(cq.from_user.id)

    sub = await is_subscribed(bot, cq.from_user.id)
    if sub:
        await update_user(cq.from_user.id, subscribed=1)
        await cq.message.edit_text(t(lang, "welcome"), reply_markup=kb_main(lang))
    else:
        await cq.message.edit_text(t(lang, "need_sub"), reply_markup=kb_sub(lang))
    await cq.answer()


@router.callback_query(F.data == "check_sub")
async def on_check_sub(cq: CallbackQuery, bot: Bot):
    user = await get_user(cq.from_user.id)
    lang = user["lang"]
    sub = await is_subscribed(bot, cq.from_user.id)
    if sub:
        await update_user(cq.from_user.id, subscribed=1)
        await cq.message.edit_text(t(lang, "welcome"), reply_markup=kb_main(lang))
        await cq.answer("✅")
    else:
        await cq.answer(t(lang, "not_sub"), show_alert=True)


@router.callback_query(F.data == "main")
async def on_main(cq: CallbackQuery, bot: Bot):
    user = await get_user(cq.from_user.id)
    lang = user["lang"]
    sub = await is_subscribed(bot, cq.from_user.id)
    if not sub:
        await cq.message.edit_text(t(lang, "need_sub"), reply_markup=kb_sub(lang))
    else:
        await cq.message.edit_text(t(lang, "welcome"), reply_markup=kb_main(lang))
    await cq.answer()


@router.callback_query(F.data == "set_lang")
async def on_set_lang(cq: CallbackQuery):
    await cq.message.edit_text(t("uz", "choose_lang"), reply_markup=kb_langs())
    await cq.answer()


@router.callback_query(F.data == "guide")
async def on_guide(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    await cq.message.edit_text(t(user["lang"], "guide"), reply_markup=kb_back(user["lang"]))
    await cq.answer()


@router.callback_query(F.data == "video")
async def on_video(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    await cq.message.edit_text(
        t(user["lang"], "video", support=SUPPORT_URL),
        reply_markup=kb_back(user["lang"]),
    )
    await cq.answer()


def _level_info(deposited: int, balance_ok: int) -> dict:
    """Daraja va aniqlik (depozit holatiga qarab)."""
    # Real depozit summasini 1WIN dan olmaymiz — holat bo‘yicha taxminiy LVL
    if not deposited:
        return {
            "level_name": "🟢 Boshlovchi",
            "accuracy": "82.3",
            "dep_label": "so‘m0",
            "next_need": "so‘m133 333",
            "progress_bar": "░░░░░░░░░░",
            "progress_pct": "0",
        }
    if not balance_ok:
        return {
            "level_name": "🟢 Boshlovchi",
            "accuracy": "82.3",
            "dep_label": "so‘m0 (balans 0)",
            "next_need": "Hisobni to‘ldiring",
            "progress_bar": "░░░░░░░░░░",
            "progress_pct": "0",
        }
    # Faol depozit — O‘rta daraja (keyinroq summa bo‘yicha kengaytirish mumkin)
    return {
        "level_name": "🔵 O‘rta",
        "accuracy": "85.7",
        "dep_label": "✅ Faol",
        "next_need": "so‘m666 666",
        "progress_bar": "███░░░░░░░",
        "progress_pct": "30",
    }


@router.callback_query(F.data == "account")
async def on_account(cq: CallbackQuery, bot: Bot):
    user = await get_user(cq.from_user.id)
    lang = user["lang"]
    sub = await is_subscribed(bot, cq.from_user.id)
    if sub and not user["subscribed"]:
        await update_user(cq.from_user.id, subscribed=1)
        user["subscribed"] = 1

    if not user["subscribed"] and not sub:
        status = t(lang, "status_sub")
    elif not user["registered"]:
        status = t(lang, "status_wait_reg")
    elif not user["deposited"]:
        status = t(lang, "status_wait_dep")
    elif not user.get("balance_ok", 1):
        status = "⚠️ Balans 0"
    else:
        status = t(lang, "status_active")

    lvl = _level_info(int(user.get("deposited") or 0), int(user.get("balance_ok", 1)))

    text = t(
        lang,
        "account",
        tg_id=cq.from_user.id,
        lang=LANG_NAMES.get(lang, lang),
        sub=t(lang, "yes") if (user["subscribed"] or sub) else t(lang, "no"),
        reg=t(lang, "yes") if user["registered"] else t(lang, "no"),
        dep=t(lang, "yes") if user["deposited"] else t(lang, "no"),
        status=status,
        dep_label=lvl["dep_label"],
        level_name=lvl["level_name"],
        accuracy=lvl["accuracy"],
        next_need=lvl["next_need"],
        progress_bar=lvl["progress_bar"],
        progress_pct=lvl["progress_pct"],
    )
    # account kaliti eski formatda bo‘lsa ham ishlashi uchun fallback
    try:
        await cq.message.edit_text(text, reply_markup=kb_back(lang))
    except Exception:
        await cq.message.edit_text(
            f"👤 Profil\nID: <code>{cq.from_user.id}</code>\n"
            f"Depozit: {lvl['dep_label']}\nDaraja: {lvl['level_name']}\n"
            f"Aniqlik: ~{lvl['accuracy']}%\nStatus: {status}",
            reply_markup=kb_back(lang),
        )
    await cq.answer()


@router.callback_query(F.data == "signal")
async def on_signal(cq: CallbackQuery, bot: Bot):
    user = await get_user(cq.from_user.id)
    lang = user["lang"]
    tg_id = cq.from_user.id

    sub = await is_subscribed(bot, tg_id)
    if not sub:
        await cq.message.edit_text(t(lang, "need_sub"), reply_markup=kb_sub(lang))
        await cq.answer()
        return

    if not user["registered"]:
        await cq.message.edit_text(
            t(lang, "reg_text", promo=PROMO_CODE, support=SUPPORT_URL),
            reply_markup=kb_reg(lang, tg_id),
        )
        await cq.answer()
        return

    if not user["deposited"]:
        await cq.message.edit_text(t(lang, "reg_ok"), reply_markup=kb_deposit(lang, tg_id))
        await cq.answer()
        return

    if not user.get("balance_ok", 1):
        await cq.message.edit_text(
            t(lang, "balance_zero"),
            reply_markup=kb_deposit(lang, tg_id),
        )
        await cq.answer()
        return

    await cq.message.edit_text(t(lang, "dep_ok"), reply_markup=kb_open_app(lang))
    await cq.answer()


@router.callback_query(F.data == "link_fail")
async def on_link_fail(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    await cq.message.edit_text(
        t(user["lang"], "link_fail_help", support=SUPPORT_URL),
        reply_markup=kb_reg(user["lang"], cq.from_user.id),
    )
    await cq.answer()


@router.callback_query(F.data == "check_id")
async def on_check_id(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    await update_user(cq.from_user.id, waiting_id=1)
    await cq.message.edit_text(t(user["lang"], "send_id"), reply_markup=kb_back(user["lang"]))
    await cq.answer()


@router.callback_query(F.data == "dep_how")
async def on_dep_how(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    await cq.message.edit_text(
        t(user["lang"], "dep_need"),
        reply_markup=kb_deposit(user["lang"], cq.from_user.id),
    )
    await cq.answer()


@router.callback_query(F.data == "check_dep")
async def on_check_dep(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    lang = user["lang"]
    # Refresh from DB (postback may have updated)
    user = await get_user(cq.from_user.id)
    if user["deposited"]:
        await cq.message.edit_text(t(lang, "dep_ok"), reply_markup=kb_open_app(lang))
    else:
        await cq.answer(t(lang, "dep_need")[:180], show_alert=True)
    await cq.answer() if not user["deposited"] else None


@router.message(F.text & ~F.text.startswith("/"))
async def on_text(message: Message):
    user = await get_user(message.from_user.id)
    if user.get("waiting_id"):
        await update_user(
            message.from_user.id,
            waiting_id=0,
            win_user_id=message.text.strip()[:64],
        )
        # Manual path: if admin later confirms; for now store only
        await message.answer(t(user["lang"], "id_saved"), reply_markup=kb_main(user["lang"]))
        return
    # fallback
    await message.answer(t(user["lang"], "welcome"), reply_markup=kb_main(user["lang"]))


# ---------- Admin panel ----------
def kb_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="adm:stats")],
            [InlineKeyboardButton(text="👤 User tekshirish", callback_data="adm:user")],
            [
                InlineKeyboardButton(text="✅ Set REG", callback_data="adm:setreg"),
                InlineKeyboardButton(text="💰 Set DEP", callback_data="adm:setdep"),
            ],
            [
                InlineKeyboardButton(text="🔄 Reset DEP", callback_data="adm:resetdep"),
                InlineKeyboardButton(text="🗑 Reset USER", callback_data="adm:resetuser"),
            ],
            [InlineKeyboardButton(text="⬅️ Yopish", callback_data="adm:close")],
        ]
    )


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(
        "🛠 <b>Admin panel</b>\n\n"
        "Buyruqlar:\n"
        "/setreg &lt;tg_id&gt; — faqat registratsiya\n"
        "/setdep &lt;tg_id&gt; — reg + depozit + aktiv\n"
        "/resetdep &lt;tg_id&gt; — depozitni 0 qilish\n"
        "/resetuser &lt;tg_id&gt; — to‘liq tozalash\n"
        "/setbalance &lt;tg_id&gt; 0|1 — balans\n"
        "/user &lt;tg_id&gt; — user ma’lumoti\n"
        "/stats — statistika",
        reply_markup=kb_admin(),
    )


@router.callback_query(F.data.startswith("adm:"))
async def on_admin_cb(cq: CallbackQuery):
    if cq.from_user.id not in ADMIN_IDS:
        await cq.answer("Ruxsat yo‘q", show_alert=True)
        return
    action = cq.data.split(":")[1]
    if action == "close":
        await cq.message.delete()
        await cq.answer()
        return
    if action == "stats":
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("SELECT COUNT(*) FROM users")
            total = (await cur.fetchone())[0]
            cur = await db.execute("SELECT COUNT(*) FROM users WHERE registered=1")
            regs = (await cur.fetchone())[0]
            cur = await db.execute("SELECT COUNT(*) FROM users WHERE deposited=1")
            deps = (await cur.fetchone())[0]
            cur = await db.execute("SELECT COUNT(*) FROM users WHERE subscribed=1")
            subs = (await cur.fetchone())[0]
        await cq.message.edit_text(
            f"📊 <b>Statistika</b>\n\n"
            f"Jami user: <b>{total}</b>\n"
            f"Obuna: <b>{subs}</b>\n"
            f"Registratsiya: <b>{regs}</b>\n"
            f"Depozit: <b>{deps}</b>",
            reply_markup=kb_admin(),
        )
        await cq.answer()
        return
    hints = {
        "user": "Yuboring: /user <tg_id>",
        "setreg": "Yuboring: /setreg <tg_id>",
        "setdep": "Yuboring: /setdep <tg_id>",
        "resetdep": "Yuboring: /resetdep <tg_id>",
        "resetuser": "Yuboring: /resetuser <tg_id>",
    }
    await cq.answer(hints.get(action, "OK"), show_alert=True)


@router.message(Command("stats"))
async def admin_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        total = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM users WHERE registered=1")
        regs = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM users WHERE deposited=1")
        deps = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM users WHERE subscribed=1")
        subs = (await cur.fetchone())[0]
    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"Jami user: <b>{total}</b>\n"
        f"Obuna: <b>{subs}</b>\n"
        f"Registratsiya: <b>{regs}</b>\n"
        f"Depozit: <b>{deps}</b>"
    )


@router.message(Command("user"))
async def admin_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /user <tg_id>")
        return
    tid = int(parts[1])
    user = await get_user(tid)
    await message.answer(
        f"👤 <b>User {tid}</b>\n\n"
        f"Lang: {user.get('lang')}\n"
        f"Subscribed: {user.get('subscribed')}\n"
        f"Registered: {user.get('registered')}\n"
        f"Deposited: {user.get('deposited')}\n"
        f"Balance OK: {user.get('balance_ok')}\n"
        f"Win ID: {user.get('win_user_id') or '-'}\n"
        f"Waiting ID: {user.get('waiting_id')}"
    )


@router.message(Command("setreg"))
async def admin_setreg(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Usage: /setreg <tg_id>")
        return
    tid = int(parts[1])
    await update_user(tid, registered=1)
    await message.answer(f"✅ registered=1 for {tid}")


@router.message(Command("setdep"))
async def admin_setdep(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Usage: /setdep <tg_id>")
        return
    tid = int(parts[1])
    await update_user(tid, registered=1, deposited=1, balance_ok=1)
    await message.answer(f"✅ deposited=1 for {tid}")


@router.message(Command("resetdep"))
async def admin_resetdep(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Usage: /resetdep <tg_id>")
        return
    tid = int(parts[1])
    await update_user(tid, deposited=0, balance_ok=0)
    await message.answer(f"🔄 deposited=0, balance_ok=0 for {tid}")


@router.message(Command("resetuser"))
async def admin_resetuser(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Usage: /resetuser <tg_id>")
        return
    tid = int(parts[1])
    await update_user(
        tid,
        registered=0,
        deposited=0,
        balance_ok=1,
        win_user_id=None,
        waiting_id=0,
    )
    await message.answer(f"🗑 User {tid} tozalandi (reg=0, dep=0)")


@router.message(Command("setbalance"))
async def admin_setbalance(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer("Usage: /setbalance <tg_id> <0|1>")
        return
    tid = int(parts[1])
    ok = int(parts[2])
    await update_user(tid, balance_ok=ok)
    await message.answer(f"balance_ok={ok} for {tid}")


# ---------- Postback HTTP ----------
async def postback_handler(request: web.Request) -> web.Response:
    """
    1WIN postback example:
    /postback?event=reg&sub1=123456&user_id=abc
    /postback?event=ftd&sub1=123456&amount=50
    """
    q = request.rel_url.query
    event = (q.get("event") or "").lower()
    sub1 = q.get("sub1") or q.get("sub_id") or ""
    user_id_1win = q.get("user_id") or ""
    amount = q.get("amount") or ""

    logger.info("POSTBACK event=%s sub1=%s user_id=%s amount=%s all=%s", event, sub1, user_id_1win, amount, dict(q))

    tg_id = None
    if sub1.isdigit():
        tg_id = int(sub1)

    if tg_id:
        if event in ("reg", "registration", "register"):
            await update_user(tg_id, registered=1, win_user_id=user_id_1win or None)
            try:
                bot: Bot = request.app["bot"]
                user = await get_user(tg_id)
                await bot.send_message(
                    tg_id,
                    t(user["lang"], "reg_ok"),
                    reply_markup=kb_deposit(user["lang"], tg_id),
                )
            except Exception as e:
                logger.warning("notify reg failed: %s", e)

        elif event in ("ftd", "first_deposit", "firstdep"):
            # Faqat birinchi depozit — signal ochiladi
            await update_user(tg_id, registered=1, deposited=1, balance_ok=1, win_user_id=user_id_1win or None)
            try:
                bot: Bot = request.app["bot"]
                user = await get_user(tg_id)
                await bot.send_message(
                    tg_id,
                    t(user["lang"], "dep_ok"),
                    reply_markup=kb_open_app(user["lang"]),
                )
            except Exception as e:
                logger.warning("notify ftd failed: %s", e)

        elif event in ("dep", "deposit"):
            # Qayta depozit — faqat deposited=1 qilamiz, lekin xabar yubormaymiz
            # (agar allaqachon faol bo‘lsa kerak emas)
            user = await get_user(tg_id)
            if not user.get("deposited"):
                await update_user(tg_id, registered=1, deposited=1, balance_ok=1, win_user_id=user_id_1win or None)
                try:
                    bot: Bot = request.app["bot"]
                    user = await get_user(tg_id)
                    await bot.send_message(
                        tg_id,
                        t(user["lang"], "dep_ok"),
                        reply_markup=kb_open_app(user["lang"]),
                    )
                except Exception as e:
                    logger.warning("notify dep failed: %s", e)
            else:
                await update_user(tg_id, balance_ok=1, win_user_id=user_id_1win or None)

    return web.Response(text="OK")



async def access_handler(request: web.Request) -> web.Response:
    """Mini-app access check: ?tg_id=123"""
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
    if request.method == "OPTIONS":
        return web.Response(status=204, headers=cors)

    try:
        tg_raw = (request.rel_url.query.get("tg_id") or "").strip()
        if not tg_raw.isdigit():
            body = {"ok": False, "reason": "no_id"}
            return web.json_response(body, headers=cors)

        tg_id = int(tg_raw)
        user = await get_user(tg_id)
        registered = int(user.get("registered") or 0) == 1
        deposited = int(user.get("deposited") or 0) == 1
        balance_ok = int(user.get("balance_ok", 1) or 0) == 1
        ok = registered and deposited and balance_ok
        if not registered:
            reason = "need_reg"
        elif not deposited:
            reason = "need_dep"
        elif not balance_ok:
            reason = "balance_zero"
        else:
            reason = "ok"

        body = {
            "ok": ok,
            "reason": reason,
            "registered": registered,
            "deposited": deposited,
            "balance_ok": balance_ok,
        }
        return web.json_response(body, headers=cors)
    except Exception as e:
        logger.exception("access_handler error: %s", e)
        return web.json_response(
            {"ok": False, "reason": "error", "detail": str(e)[:120]},
            headers=cors,
            status=200,
        )


async def health_handler(request: web.Request) -> web.Response:
    return web.Response(text="SYRAX OK")


# ---------- App bootstrap ----------
async def on_startup(app: web.Application):
    await init_db()
    bot: Bot = app["bot"]
    dp: Dispatcher = app["dp"]
    app["polling_task"] = asyncio.create_task(dp.start_polling(bot))


async def on_cleanup(app: web.Application):
    task = app.get("polling_task")
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass
    bot: Bot = app["bot"]
    await bot.session.close()


import asyncio


def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN missing")

    logger.info("ADMIN_IDS loaded: %s", ADMIN_IDS)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp
    app.router.add_get("/postback", postback_handler)
    app.router.add_get("/api/access", access_handler)
    app.router.add_route("OPTIONS", "/api/access", access_handler)
    app.router.add_get("/health", health_handler)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    logger.info("Starting SYRAX bot on port %s", PORT)
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
