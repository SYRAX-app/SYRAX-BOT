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

BOT_TOKEN = os.getenv("BOT_TOKEN", "8703941609:AAHRtPI8ZIXpvr_Byr9xMW4EbPpm4h0ZLJ4")
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
            "👋 <b>Syrax Signals</b> ga xush kelibsiz!\n\n"
            "🚀 Ushbu bot mashhur o‘yinlardan imkoniyatlarni ishlatish va "
            "maksimal foyda olish uchun yaratilgan.\n\n"
            "🎯 Asos — kuchli tahlil tizimi: ma’lumotlarni qayta ishlaydi va "
            "yuqori aniqlikdagi signallar beradi.\n\n"
            "🔥 O‘yinni boshlang va bashoratlarimizdan foydalaning!"
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
            "📋 <b>Ro‘yxatdan o‘tish</b>\n\n"
            "1️⃣ Saytda ro‘yxatdan o‘tish uchun <b>1WIN</b> tugmasini bosing.\n"
            "2️⃣ Ro‘yxatdan o‘tishda promo kodni kiriting: <b>{promo}</b>\n"
            "3️⃣ Ro‘yxatdan so‘ng bot akkauntingizni avtomatik tekshiradi.\n"
            "Agar xabar kelmasa — «ID ni tekshirish» tugmasini bosing va ID yuboring.\n\n"
            "Muammo bo‘lsa: {support}\n\n"
            "4️⃣ <b>Muhim:</b> agar hisobingiz bo‘lsa, yangi email bilan yangi hisob oching. "
            "Telefon ixtiyoriy; eng muhimi — email."
        ),
        "reg_ok": (
            "✅ <b>Siz muvaffaqiyatli ro‘yxatdan o‘tdingiz!</b> 🎉\n\n"
            "Endi signallarga kirish uchun o‘yin hisobingiz balansini to‘ldiring. 💳"
        ),
        "dep_need": (
            "💳 Belgilarga kirish uchun birinchi depozitni amalga oshiring.\n\n"
            "♦ Depozit miqdori status va signal sifatiga bog‘liq bo‘lishi mumkin.\n"
            "♦ Mablag‘ hisobingizga tushadi — o‘yin va g‘alaba uchun ishlatasiz.\n\n"
            "Depozitdan so‘ng «Depozitni tekshirish» ni bosing."
        ),
        "dep_ok": (
            "🎉 Hisob faollashtirildi!\n\n"
            "Endi signallarni ochishingiz mumkin:"
        ),
        "balance_zero": (
            "⚠️ Balansingiz 0 ga tushgan ko‘rinadi.\n"
            "Signallar ishlashi uchun hisobni to‘ldiring (depozit)."
        ),
        "account": (
            "🆔 <b>Hisobingiz</b>\n\n"
            "Telegram ID: <code>{tg_id}</code>\n"
            "Til: {lang}\n"
            "Obuna: {sub}\n"
            "1WIN reg: {reg}\n"
            "Depozit: {dep}\n"
            "Status: {status}"
        ),
        "guide": (
            "📖 <b>Qanday ishlaydi</b>\n\n"
            "🟢 1. O‘yinni tanlang (mini-app ichida).\n"
            "🟢 2. Botdan signal oling va shu asosda tikish qiling.\n"
            "🟢 3. Signal ishlamasa — keyingi signalga tikishni ehtiyot bilan boshqaring.\n\n"
            "⚠️ Tikishni ikki baravar oshirishni doim ishlatmang.\n\n"
            "Bugun sinab ko‘ring — kapitalni oshirish imkoniyatini ko‘ring! 🚀"
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
    "kk": {
        "choose_lang": "🌐 Тілді таңдаңыз:",
        "need_sub": "📢 Ботты қолдану үшін арнаға жазылыңыз:",
        "check_sub": "✅ Жазылымды тексеру",
        "not_sub": "❌ Сіз әлі жазылмағансыз.",
        "welcome": "👋 <b>Syrax Signals</b> қош келдіңіз!",
        "btn_guide": "📖 Нұсқаулық",
        "btn_signal": "❗ Сигнал алу ❗",
        "btn_account": "🆔 Аккаунтым",
        "btn_lang": "🌐 Тіл",
        "btn_video": "🎬 Видео",
        "btn_support": "🆘 Қолдау",
        "btn_1win": "💻 1WIN",
        "btn_link_fail": "⚠️ Сілтеме ашылмайды",
        "btn_cancel": "❌ Болдырмау",
        "btn_check_id": "🔍 ID тексеру",
        "btn_deposit_how": "💰 Қалай толтыру?",
        "btn_check_dep": "🔍 Депозитті тексеру",
        "btn_open_app": "🎮 Сигналдарды ашу",
        "btn_main": "⬅️ Басты мәзір",
        "reg_text": "📋 <b>Тіркелу</b>\n\n1️⃣ 1WIN басыңыз\n2️⃣ Промо: <b>{promo}</b>\n\n{support}",
        "reg_ok": "✅ Тіркелдіңіз! Депозит жасаңыз. 💳",
        "dep_need": "💳 Бірінші депозит қажет.",
        "dep_ok": "🎉 Белсенді!",
        "balance_zero": "⚠️ Баланс 0. Толтырыңыз.",
        "account": "🆔 <code>{tg_id}</code>\n{lang}\n{reg}\n{dep}\n{status}",
        "guide": "📖 Ойын таңда → сигнал ал → абайлап ойын.",
        "video": "🎬 Жақында\n{support}",
        "send_id": "ID жіберіңіз:",
        "id_saved": "✅ Қабылданды.",
        "link_fail_help": "⚠️ VPN қолданып көріңіз\n{support}",
        "yes": "✅",
        "no": "❌",
        "status_active": "🟢 Белсенді",
        "status_wait_dep": "🟡 Депозит күтілуде",
        "status_wait_reg": "🟠 Тіркелу керек",
        "status_sub": "🔴 Алдымен жазылыңыз",
    },
}

LANG_NAMES = {
    "uz": "🇺🇿 O‘zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "tr": "🇹🇷 Türkçe",
    "ar": "🇸🇦 العربية",
    "hi": "🇮🇳 हिन्दी",
    "kk": "🇰🇿 Қазақша",
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
        status = t(lang, "balance_zero")
    else:
        status = t(lang, "status_active")

    text = t(
        lang,
        "account",
        tg_id=cq.from_user.id,
        lang=LANG_NAMES.get(lang, lang),
        sub=t(lang, "yes") if (user["subscribed"] or sub) else t(lang, "no"),
        reg=t(lang, "yes") if user["registered"] else t(lang, "no"),
        dep=t(lang, "yes") if user["deposited"] else t(lang, "no"),
        status=status,
    )
    await cq.message.edit_text(text, reply_markup=kb_back(lang))
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


@router.message(F.text)
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


# Admin: /setreg /setdep /setbalance
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
    await message.answer(f"registered=1 for {tid}")


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
    await message.answer(f"deposited=1 for {tid}")


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

        elif event in ("ftd", "first_deposit", "firstdep", "dep", "deposit"):
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

    return web.Response(text="OK")


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

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp
    app.router.add_get("/postback", postback_handler)
    app.router.add_get("/health", health_handler)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    logger.info("Starting SYRAX bot on port %s", PORT)
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
