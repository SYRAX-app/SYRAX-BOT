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

import asyncpg
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
    InputMediaPhoto,
    InputMediaVideo,
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
PARTNER_LINK = os.getenv("PARTNER_LINK", "https://one-vv8433.com/casino/list?open=register&p=qhz7")
PROMO_CODE = os.getenv("PROMO_CODE", "SYRAX")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
DATABASE_URL = os.getenv("DATABASE_URL", "")
PORT = int(os.getenv("PORT", "8000"))

PHOTO_REG = os.getenv("PHOTO_REG", "AgACAgIAAxkBAAOQan7S59dyH9uSQ8dNafHukXJYNbgAAsEdaxtGpfhLJZ0t9di1N4UBAAMCAAN3AAM9BA")
PHOTO_START = os.getenv("PHOTO_START", "AgACAgIAAxkBAAOSan7TKTEsi5cWuY2LOUT_p8YVkMgAAtQaaxtsDPhLHi7Ekf2ZVkIBAAMCAAN3AAM9BA")
PHOTO_DEP = os.getenv("PHOTO_DEP", "AgACAgIAAxkBAAOUan7TaPFSyk7enNDnsKoPjqxtFXwAAtcaaxtsDPhLMX3KGxZQ0P0BAAMCAAN3AAM9BA")
PHOTO_GUIDE = os.getenv("PHOTO_GUIDE", "AgACAgIAAxkBAAOpan7bslDJqQl3Lm3wd6oPqPcqdp0AAvsaaxtsDPhLAhG_beLFlwEBAAMCAAN5AAM9BA")
VIDEO_GUIDE = os.getenv("VIDEO_GUIDE", "BAACAgIAAxkBAAIBW2p_AiZiNrOO_bFI2U_Xw6FX9-8UAALQrwACbAz4S3SEiM7ti6HQPQQ")

# ---------- Translations (7 langs) ----------
T = {
    "uz": {
        "choose_lang": "🌐 Tilni tanlang / Choose language:",
        "need_sub": "📢 Botdan foydalanish uchun kanalga obuna bo‘ling:",
        "check_sub": "✅ Obunani tekshirish",
        "not_sub": "❌ Siz hali obuna bo‘lmadingiz. Avval kanalga qo‘shiling.",
        "welcome": (
            "👋🏻 <b>{name}</b> 🔸SYRAX - SIGNAL BOT🔸 ga xush kelibsiz!\n\n"
            "🚀 Ushbu bot mashhur o‘yinlardan imkoniyatlarni foydalanishingiz "
            "va maksimal foyda olishingiz uchun yaratilgan.\n\n"
            "🧠 Bot <b>maxsus tizimli AI</b> asosida — "
            "1WIN / Spribe o‘yinlar provayderi API ma’lumotlarini olib "
            "real vaqtda sinxronlashadi.\n"
            "💰 Foydalanuvchilar kuniga <b>15–25%</b> daromad olishmoqda!\n"
            "📈 Bashorat aniqligi: <b>~82-95%</b> (va u doimiy ravishda yaxshilanmoqda).\n\n"
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
            "💸 <b>4.</b> Muhim: agar sizda hisob bo‘lsa, yangi elektron pochta "
            "bilan yangi hisob yarating.\n"
            "Telefon raqami ixtiyoriy; eng muhimi — elektron pochtangiz.\n\n"
            "✅ To‘g‘ri ro‘yxatdan o‘tganingizdan so‘ng botga <b>Tasdiqlandi</b> "
            "degan avtomatik xabar keladi va keyin signal menyusi ochiladi.\n\n"
            "🧑🏻‍💻 Agar muammo bo‘lsa: @syrax_admin"
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
            "💵 <b>Daromad olish uchun ushbu oddiy ko‘rsatmalarga rioya qiling:</b>\n\n"
            "🟢 1. Daromad olishni xohlagan o‘yinni tanlang.\n\n"
            "🟢 2. Botdan signal so‘rang va ushbu signal asosida tanlangan "
            "o‘yinda pul tikish qiling.\n\n"
            "🟢 3. Agar signal muvaffaqiyatsiz bo‘lsa, keyingi signalga "
            "yo‘qotishni qoplash uchun pul tikish miqdorini ikki baravar oshiring (X²).\n\n"
            "⚠️ Muhim: tikishni ikki baravar oshirishni ehtiyotkorlik bilan amalga oshiring. "
            "O‘ta xavflardan qochish uchun ushbu strategiyani doimiy ravishda ishlatmang.\n\n"
            "Bugun sinab ko‘ring va bizning botimiz bilan qanday qilib "
            "kapitalingizni oshirish mumkinligini o‘zingiz ko‘ring! 🚀"
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
            "👋🏻 <b>{name}</b>, добро пожаловать в 🔸SYRAX - SIGNAL BOT🔸!\n\n"
            "🚀 Бот создан, чтобы вы могли использовать возможности популярных игр "
            "и получать максимальную прибыль.\n\n"
            "🧠 Бот работает на базе <b>специальной AI-системы</b> — "
            "берёт данные API провайдера 1WIN / Spribe и синхронизирует в реальном времени.\n"
            "💰 Пользователи зарабатывают <b>15–25%</b> в день!\n"
            "📈 Точность прогнозов: <b>~82-95%</b> (постоянно улучшается).\n\n"
            "🔥 Начните игру и используйте наши сигналы!"
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
            "💸 <b>1.</b> Нажмите кнопку <b>1WIN</b> для регистрации на сайте.\n\n"
            "💸 <b>2.</b> При регистрации введите промокод: <b>{promo}</b>\n\n"
            "💸 <b>3.</b> После регистрации бот автоматически проверит аккаунт "
            "и отправит сообщение.\n"
            "Если сообщения нет — нажмите «Проверить ID» и отправьте ID.\n\n"
            "💸 <b>4.</b> Важно: если у вас уже есть аккаунт, создайте новый "
            "на новую электронную почту.\n"
            "Номер телефона необязателен; главное — email.\n\n"
            "✅ После правильной регистрации бот отправит сообщение "
            "<b>Подтверждено</b> и откроется меню сигналов.\n\n"
            "🧑🏻‍💻 Если проблема: @syrax_admin"
        ),
        "reg_ok": (
            "✅ <b>Регистрация успешна!</b> 🎉\n\n"
            "Для доступа к сигналам пополните баланс игрового счёта. 💳"
        ),
        "dep_need": (
            "🌐 <b>Для доступа к сигналам нужен первый депозит.</b>\n\n"
            "✦ Сумма депозита влияет на LVL (уровень), статус и вероятность успеха сигналов. "
            "Чем больше депозит — тем выше уровень и точнее сигналы.\n\n"
            "✦ Средства зачисляются на ВАШ счёт — используйте для игры и прибыли.\n\n"
            "● После депозита нажмите «🔍 Проверить депозит»."
        ),
        "dep_ok": "🎉 Аккаунт активирован!\n\nМожно открыть сигналы:",
        "balance_zero": (
            "⚠️ <b>Баланс равен 0.</b>\n\n"
            "Поэтому сигналы недоступны.\n"
            "Пополните счёт 1WIN, чтобы продолжить."
        ),
        "account": (
            "👤 <b>Профиль</b>\n"
            "————————————\n"
            "🆔 ID: <code>{tg_id}</code>\n"
            "💰 Депозит: {dep_label}\n"
            "🏅 Уровень: {level_name}\n"
            "🎯 Точность сигнала: ~{accuracy}%\n"
            "📊 До следующего уровня: {next_need}\n"
            "{progress_bar} {progress_pct}%\n"
            "————————————\n"
            "🌐 Язык: {lang}\n"
            "📢 Подписка: {sub}\n"
            "✅ Reg: {reg}\n"
            "📌 Статус: {status}"
        ),
        "guide": (
            "💵 <b>Чтобы зарабатывать, следуйте этим простым шагам:</b>\n\n"
            "🟢 1. Выберите игру, в которой хотите заработать.\n\n"
            "🟢 2. Запросите сигнал у бота и сделайте ставку по этому сигналу.\n\n"
            "🟢 3. Если сигнал не сработал — удвойте следующую ставку (X²), "
            "чтобы отыграть проигрыш.\n\n"
            "⚠️ Важно: удваивайте ставку осторожно. "
            "Не используйте эту стратегию постоянно, чтобы избежать лишнего риска.\n\n"
            "Попробуйте сегодня и убедитесь, как можно увеличить капитал с нашим ботом! 🚀"
        ),
        "video": "🎬 Видеоинструкция скоро.\nПоддержка: {support}",
        "send_id": "Отправьте ID (Telegram или 1WIN):",
        "id_saved": "✅ Принято. Ожидаем подтверждение / postback.",
        "link_fail_help": (
            "⚠️ Если ссылка не открывается:\n"
            "• Включите VPN\n"
            "• Попробуйте другой браузер / Chrome\n"
            "• Напишите в поддержку: {support}"
        ),
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
            "👋🏻 <b>{name}</b>, welcome to 🔸SYRAX - SIGNAL BOT🔸!\n\n"
            "🚀 This bot is built so you can use opportunities from popular games "
            "and get maximum profit.\n\n"
            "🧠 Powered by a <b>special AI system</b> — "
            "it takes 1WIN / Spribe provider API data and syncs in real time.\n"
            "💰 Users earn <b>15–25%</b> per day!\n"
            "📈 Prediction accuracy: <b>~82-95%</b> (constantly improving).\n\n"
            "🔥 Start playing and use our signals!"
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
            "💸 <b>1.</b> Tap <b>1WIN</b> to register on the site.\n\n"
            "💸 <b>2.</b> Enter promo code during registration: <b>{promo}</b>\n\n"
            "💸 <b>3.</b> After registration the bot will automatically verify your account "
            "and send a message.\n"
            "If no message — tap «Check ID» and send your ID.\n\n"
            "💸 <b>4.</b> Important: if you already have an account, create a new one "
            "with a new email.\n"
            "Phone number is optional; email is the main thing.\n\n"
            "✅ After correct registration the bot will send <b>Confirmed</b> "
            "and the signal menu will open.\n\n"
            "🧑🏻‍💻 If you have issues: @syrax_admin"
        ),
        "reg_ok": (
            "✅ <b>Registered successfully!</b> 🎉\n\n"
            "Deposit to your game account to unlock signals. 💳"
        ),
        "dep_need": (
            "🌐 <b>First deposit is required to access signals.</b>\n\n"
            "✦ Deposit amount affects LVL (level), status and signal success rate. "
            "The larger the deposit — the higher your level and the better the signals.\n\n"
            "✦ Funds go to YOUR account — use them to play and win.\n\n"
            "● After deposit tap «🔍 Check deposit»."
        ),
        "dep_ok": "🎉 Account activated!\n\nYou can open signals:",
        "balance_zero": (
            "⚠️ <b>Your balance is 0.</b>\n\n"
            "Signals are unavailable.\n"
            "Top up your 1WIN account to continue."
        ),
        "account": (
            "👤 <b>Profile</b>\n"
            "————————————\n"
            "🆔 ID: <code>{tg_id}</code>\n"
            "💰 Deposit: {dep_label}\n"
            "🏅 Level: {level_name}\n"
            "🎯 Signal accuracy: ~{accuracy}%\n"
            "📊 To next level: {next_need}\n"
            "{progress_bar} {progress_pct}%\n"
            "————————————\n"
            "🌐 Lang: {lang}\n"
            "📢 Sub: {sub}\n"
            "✅ Reg: {reg}\n"
            "📌 Status: {status}"
        ),
        "guide": (
            "💵 <b>Follow these simple steps to earn:</b>\n\n"
            "🟢 1. Choose the game you want to earn from.\n\n"
            "🟢 2. Request a signal from the bot and place a bet based on it.\n\n"
            "🟢 3. If the signal fails — double the next bet (X²) to recover the loss.\n\n"
            "⚠️ Important: double bets carefully. "
            "Do not use this strategy all the time to avoid high risk.\n\n"
            "Try today and see how you can grow your capital with our bot! 🚀"
        ),
        "video": "🎬 Video guide coming soon.\nSupport: {support}",
        "send_id": "Send your ID (Telegram or 1WIN):",
        "id_saved": "✅ Received. Waiting for confirmation / postback.",
        "link_fail_help": (
            "⚠️ If the link does not open:\n"
            "• Turn on VPN\n"
            "• Try another browser / Chrome\n"
            "• Contact support: {support}"
        ),
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
        "welcome": (
            "👋🏻 <b>{name}</b>, 🔸SYRAX - SIGNAL BOT🔸'a hoş geldiniz!\n\n"
            "🚀 Bu bot popüler oyunlardan fırsatları kullanmanız "
            "ve maksimum kâr elde etmeniz için oluşturuldu.\n\n"
            "🧠 Özel <b>AI sistemi</b> ile çalışır — "
            "1WIN / Spribe API verilerini alıp gerçek zamanlı senkronize eder.\n"
            "💰 Kullanıcılar günde <b>%15–25</b> kazanıyor!\n"
            "📈 Tahmin doğruluğu: <b>~%82-95</b> (sürekli iyileşiyor).\n\n"
            "🔥 Oyuna başlayın ve sinyallerimizi kullanın!"
        ),
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
        "reg_text": (
            "💸 <b>1.</b> Kayıt için <b>1WIN</b> düğmesine basın.\n\n"
            "💸 <b>2.</b> Kayıt sırasında promosyon kodunu girin: <b>{promo}</b>\n\n"
            "💸 <b>3.</b> Kayıttan sonra bot hesabınızı otomatik kontrol eder "
            "ve mesaj gönderir.\n"
            "Mesaj gelmezse — «ID kontrol»e basın ve ID gönderin.\n\n"
            "💸 <b>4.</b> Önemli: hesabınız varsa yeni e-posta ile yeni hesap oluşturun.\n"
            "Telefon isteğe bağlı; asıl önemli olan e-posta.\n\n"
            "✅ Doğru kayıttan sonra bot <b>Onaylandı</b> mesajı gönderir "
            "ve sinyal menüsü açılır.\n\n"
            "🧑🏻‍💻 Sorun olursa: @syrax_admin"
        ),
        "reg_ok": "✅ <b>Kayıt başarılı!</b> 🎉\n\nSinyaller için bakiye yükleyin. 💳",
        "dep_need": (
            "🌐 <b>Sinyallere erişim için ilk yatırım gerekli.</b>\n\n"
            "✦ Yatırım tutarı LVL, durum ve sinyal başarı oranını etkiler.\n\n"
            "● Yatırımdan sonra «🔍 Yatırımı kontrol et»e basın."
        ),
        "dep_ok": "🎉 Hesap aktif!\n\nSinyalleri açabilirsiniz:",
        "balance_zero": "⚠️ <b>Bakiye 0.</b>\n\nSinyaller kapalı. 1WIN hesabını doldurun.",
        "account": (
            "👤 <b>Profil</b>\n"
            "————————————\n"
            "🆔 ID: <code>{tg_id}</code>\n"
            "💰 Yatırım: {dep_label}\n"
            "🏅 Seviye: {level_name}\n"
            "🎯 Sinyal doğruluğu: ~{accuracy}%\n"
            "📊 Sonraki seviyeye: {next_need}\n"
            "{progress_bar} {progress_pct}%\n"
            "————————————\n"
            "🌐 Dil: {lang} | 📢 Abone: {sub}\n"
            "✅ Reg: {reg} | 📌 Durum: {status}"
        ),
        "guide": (
            "💵 <b>Kazanmak için şu adımları izleyin:</b>\n\n"
            "🟢 1. Kazanmak istediğiniz oyunu seçin.\n\n"
            "🟢 2. Bottan sinyal isteyin ve bu sinyale göre bahis yapın.\n\n"
            "🟢 3. Sinyal tutmazsa — kaybı kapatmak için bir sonraki bahsi ikiye katlayın (X²).\n\n"
            "⚠️ Önemli: ikiye katlamayı dikkatli kullanın. Sürekli kullanmayın.\n\n"
            "Bugün deneyin ve botla sermayenizi nasıl artırabileceğinizi görün! 🚀"
        ),
        "video": "🎬 Video yakında.\nDestek: {support}",
        "send_id": "ID gönderin (Telegram veya 1WIN):",
        "id_saved": "✅ Alındı. Onay bekleniyor.",
        "link_fail_help": "⚠️ Link açılmazsa:\n• VPN açın\n• Başka tarayıcı deneyin\n• Destek: {support}",
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


# ---------- Database ----------
class Database:
    _instance = None
    _pool = None

    async def initialize(self):
        """Initialize connection pool"""
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        self._pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        logger.info("PostgreSQL connection pool created")
        await self.init_db()
        return self._pool

    async def get_pool(self):
        if self._pool is None:
            await self.initialize()
        return self._pool

    async def init_db(self):
        """Create users table if not exists"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    tg_id BIGINT PRIMARY KEY,
                    lang TEXT DEFAULT 'uz',
                    subscribed INTEGER DEFAULT 0,
                    registered INTEGER DEFAULT 0,
                    deposited INTEGER DEFAULT 0,
                    balance_ok INTEGER DEFAULT 1,
                    win_user_id TEXT,
                    waiting_id INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Database initialized (users table created if not exists)")


db = Database()


async def init_db():
    """Initialize database (kept for backward compatibility)"""
    await db.init_db()


async def get_user(tg_id: int) -> dict:
    """Get user by tg_id, create if not exists"""
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE tg_id = $1", tg_id)
        if row:
            return dict(row)
        
        await conn.execute(
            "INSERT INTO users (tg_id) VALUES ($1)",
            tg_id
        )
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
    """Update user fields dynamically"""
    if not fields:
        return
    
    columns = []
    values = []
    for key, val in fields.items():
        columns.append(f"{key} = ${len(values) + 1}")
        values.append(val)
    
    values.append(tg_id)
    query = f"UPDATE users SET {', '.join(columns)} WHERE tg_id = ${len(values)}"
    
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        await conn.execute(query, *values)


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


def kb_account(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Yangilash", callback_data="account"),
                InlineKeyboardButton(text="📊 Darajalar", callback_data="levels"),
            ],
            [InlineKeyboardButton(text=t(lang, "btn_main"), callback_data="main")],
        ]
    )


def kb_levels(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Profil", callback_data="account")],
            [InlineKeyboardButton(text=t(lang, "btn_main"), callback_data="main")],
        ]
    )


def kb_deposit_check(lang: str, tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Depozitni tekshirish", callback_data="check_dep"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main"),
            ],
            [InlineKeyboardButton(text=t(lang, "btn_1win"), url=partner_url(tg_id))],
        ]
    )


def kb_guide(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_signal"), callback_data="signal")],
            [InlineKeyboardButton(text=t(lang, "btn_main"), callback_data="main")],
        ]
    )


LEVELS_TEXT = (
    "📊 <b>Darajalar va signal aniqligi:</b>\n"
    "————————————\n"
    "🟢 <b>Boshlovchi</b> — so‘m0 | ~82.3%\n"
    "🔵 <b>O‘yinchi</b> — so‘m133 333 | ~85.7%\n"
    "🟣 <b>Tajribali</b> — so‘m666 666 | ~89.1%\n"
    "🟠 <b>Professional</b> — so‘m1 333 333 | ~92.4%\n"
    "🔴 <b>Afsona</b> — so‘m6 666 666 | ~95.9%"
)

DEP_NEED_FULL = (
    "🌐 <b>Signallarga kirish uchun birinchi depozitni amalga oshirishingiz kerak.</b>\n\n"
    "✦ Depozit miqdori botdagi LVL (daraja), status va signal muvaffaqiyati "
    "ehtimoliga bog‘liq.\n\n"
    "✦ Mablag‘lar HISOBINGIZGA kiritiladi.\n\n"
    "● Depozitdan so‘ng «🔍 Depozitni tekshirish» tugmasini bosing."
)


def welcome_text(lang: str, name: str) -> str:
    try:
        return t(lang, "welcome", name=name or "User")
    except Exception:
        return t("en", "welcome", name=name or "User")


async def safe_screen(cq: CallbackQuery, text: str, reply_markup=None, photo=None, video=None):
    """Menyular orasida SILLIQ o'tish uchun: iloji boricha mavjud xabarni EDIT qiladi
    (o'chirib-qayta yubormaydi). Faqat matn<->media turi almashganda (Telegram texnik
    cheklovi tufayli edit qilib bo'lmaydi) eski xabar o'chirilib, yangisi yuboriladi."""
    chat_id = cq.message.chat.id
    bot = cq.bot
    old_is_media = bool(cq.message.photo or cq.message.video)

    # Yangi ekran rasm yoki video bo'lsa
    if photo or video:
        caption = (text or "")[:1024] or None
        if old_is_media:
            # eski xabar ham rasm/video edi - media'ni joyida EDIT qilamiz (flash bo'lmaydi)
            try:
                if photo:
                    media = InputMediaPhoto(media=photo, caption=caption)
                else:
                    media = InputMediaVideo(media=video, caption=caption)
                await cq.message.edit_media(media=media, reply_markup=reply_markup)
                return
            except Exception:
                pass
        # eski xabar matn edi - media qo'shib bo'lmaydi (Telegram cheklovi), shu sabab qayta yuboramiz
        try:
            await cq.message.delete()
        except Exception:
            pass
        if photo:
            await bot.send_photo(chat_id, photo=photo, caption=caption, reply_markup=reply_markup, protect_content=True)
        else:
            await bot.send_video(chat_id, video=video, caption=caption, reply_markup=reply_markup, protect_content=True)
        return

    # Yangi ekran oddiy matn
    if old_is_media:
        # eski xabar rasm/video edi - matnga o'zgartirib bo'lmaydi (Telegram cheklovi), qayta yuboramiz
        try:
            await cq.message.delete()
        except Exception:
            pass
        await bot.send_message(chat_id, text, reply_markup=reply_markup, protect_content=True)
        return

    # matn -> matn: joyida EDIT qilamiz (asosiy holat, flash bo'lmaydi)
    try:
        await cq.message.edit_text(text, reply_markup=reply_markup)
        return
    except Exception:
        pass

    try:
        await cq.message.delete()
    except Exception:
        pass
    await bot.send_message(chat_id, text, reply_markup=reply_markup, protect_content=True)


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
    await message.answer(t(user["lang"], "choose_lang"), reply_markup=kb_langs())


@router.callback_query(F.data.startswith("lang:"))
async def on_lang(cq: CallbackQuery, bot: Bot):
    lang = cq.data.split(":")[1]
    if lang not in T:
        lang = "uz"
    await update_user(cq.from_user.id, lang=lang)
    name = cq.from_user.first_name or "User"
    sub = await is_subscribed(bot, cq.from_user.id)
    if sub:
        await update_user(cq.from_user.id, subscribed=1)
        await safe_screen(cq, welcome_text(lang, name), kb_main(lang), PHOTO_START)
    else:
        await safe_screen(cq, t(lang, "need_sub"), kb_sub(lang))
    await cq.answer()


@router.callback_query(F.data == "check_sub")
async def on_check_sub(cq: CallbackQuery, bot: Bot):
    user = await get_user(cq.from_user.id)
    lang = user.get("lang") or "uz"
    name = cq.from_user.first_name or "User"
    sub = await is_subscribed(bot, cq.from_user.id)
    if sub:
        await update_user(cq.from_user.id, subscribed=1)
        await safe_screen(cq, welcome_text(lang, name), kb_main(lang), PHOTO_START)
        await cq.answer("✅")
    else:
        await cq.answer(t(lang, "not_sub"), show_alert=True)


@router.callback_query(F.data == "main")
async def on_main(cq: CallbackQuery, bot: Bot):
    user = await get_user(cq.from_user.id)
    lang = user.get("lang") or "uz"
    name = cq.from_user.first_name or "User"
    sub = await is_subscribed(bot, cq.from_user.id)
    if not sub:
        await safe_screen(cq, t(lang, "need_sub"), kb_sub(lang))
    else:
        await safe_screen(cq, welcome_text(lang, name), kb_main(lang), PHOTO_START)
    await cq.answer()


@router.callback_query(F.data == "set_lang")
async def on_set_lang(cq: CallbackQuery):
    await safe_screen(cq, t("uz", "choose_lang"), kb_langs())
    await cq.answer()


@router.callback_query(F.data == "guide")
async def on_guide(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    lang = user.get("lang") or "uz"
    await safe_screen(cq, t(lang, "guide"), kb_guide(lang), PHOTO_GUIDE)
    await cq.answer()


@router.callback_query(F.data == "video")
async def on_video(cq: CallbackQuery):
    """Video qo'llanma — menyular kabi silliq (edit) ochiladi."""
    user = await get_user(cq.from_user.id)
    lang = user.get("lang") or "uz"
    try:
        await safe_screen(cq, "", kb_back(lang), video=VIDEO_GUIDE)
    except Exception as e:
        logger.warning("video send failed: %s", e)
        await safe_screen(cq, t(lang, "video", support=SUPPORT_URL), kb_back(lang))
    await cq.answer()


def _level_info(deposited: int, balance_ok: int) -> dict:
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
    try:
        user = await get_user(cq.from_user.id)
        lang = user.get("lang") or "uz"
        sub = await is_subscribed(bot, cq.from_user.id)
        if sub and not user.get("subscribed"):
            await update_user(cq.from_user.id, subscribed=1)
            user["subscribed"] = 1
        if not user.get("subscribed") and not sub:
            status = t(lang, "status_sub")
        elif not user.get("registered"):
            status = t(lang, "status_wait_reg")
        elif not user.get("deposited"):
            status = t(lang, "status_wait_dep")
        elif not user.get("balance_ok", 1):
            status = "⚠️ Balans 0"
        else:
            status = t(lang, "status_active")
        lvl = _level_info(int(user.get("deposited") or 0), int(user.get("balance_ok", 1)))
        text = (
            f"👤 <b>Profil</b>\n————————————\n"
            f"🆔 ID: <code>{cq.from_user.id}</code>\n"
            f"💰 Depozit: {lvl['dep_label']}\n"
            f"🏅 Daraja: {lvl['level_name']}\n"
            f"🎯 Signal aniqligi: ~{lvl['accuracy']}%\n"
            f"📊 Keyingi darajagacha: {lvl['next_need']}\n"
            f"{lvl['progress_bar']} {lvl['progress_pct']}%\n"
            f"————————————\n"
            f"🌐 Til: {LANG_NAMES.get(lang, lang)}\n"
            f"📢 Obuna: {t(lang, 'yes') if (user.get('subscribed') or sub) else t(lang, 'no')}\n"
            f"✅ Reg: {t(lang, 'yes') if user.get('registered') else t(lang, 'no')}\n"
            f"📌 Status: {status}"
        )
        await safe_screen(cq, text, kb_account(lang))
    except Exception as e:
        logger.exception("account: %s", e)
        await safe_screen(cq, f"👤 ID: <code>{cq.from_user.id}</code>", kb_back("uz"))
    await cq.answer()


@router.callback_query(F.data == "levels")
async def on_levels(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    lang = user.get("lang") or "uz"
    await safe_screen(cq, LEVELS_TEXT, kb_levels(lang))
    await cq.answer()


@router.callback_query(F.data == "signal")
async def on_signal(cq: CallbackQuery, bot: Bot):
    user = await get_user(cq.from_user.id)
    lang = user.get("lang") or "uz"
    tg_id = cq.from_user.id
    sub = await is_subscribed(bot, tg_id)
    if not sub:
        await safe_screen(cq, t(lang, "need_sub"), kb_sub(lang))
        await cq.answer()
        return
    if not user.get("registered"):
        await safe_screen(
            cq,
            t(lang, "reg_text", promo=PROMO_CODE, support=SUPPORT_URL),
            kb_reg(lang, tg_id),
            PHOTO_REG,
        )
        await cq.answer()
        return
    if not user.get("deposited"):
        await safe_screen(cq, DEP_NEED_FULL, kb_deposit_check(lang, tg_id), PHOTO_DEP)
        await cq.answer()
        return
    if not user.get("balance_ok", 1):
        await safe_screen(cq, t(lang, "balance_zero"), kb_deposit(lang, tg_id), PHOTO_DEP)
        await cq.answer()
        return
    await safe_screen(cq, t(lang, "dep_ok"), kb_open_app(lang))
    await cq.answer()


@router.callback_query(F.data == "link_fail")
async def on_link_fail(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    lang = user.get("lang") or "uz"
    await safe_screen(cq, t(lang, "link_fail_help", support=SUPPORT_URL), kb_reg(lang, cq.from_user.id))
    await cq.answer()


@router.callback_query(F.data == "check_id")
async def on_check_id(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    lang = user.get("lang") or "uz"
    await update_user(cq.from_user.id, waiting_id=1)
    await safe_screen(cq, t(lang, "send_id"), kb_back(lang))
    await cq.answer()


@router.callback_query(F.data == "dep_how")
async def on_dep_how(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    lang = user.get("lang") or "uz"
    await safe_screen(cq, DEP_NEED_FULL, kb_deposit_check(lang, cq.from_user.id), PHOTO_DEP)
    await cq.answer()


@router.callback_query(F.data == "check_dep")
async def on_check_dep(cq: CallbackQuery):
    user = await get_user(cq.from_user.id)
    lang = user.get("lang") or "uz"
    tg_id = cq.from_user.id
    user = await get_user(tg_id)
    if user.get("deposited"):
        await safe_screen(cq, t(lang, "dep_ok"), kb_open_app(lang))
    else:
        await safe_screen(cq, DEP_NEED_FULL, kb_deposit_check(lang, tg_id), PHOTO_DEP)
    await cq.answer()


@router.message(F.photo | F.video | F.animation | F.document | F.video_note)
async def on_media_file_id(message: Message):
    """Admin rasm/video yuborsa file_id qaytaradi."""
    if message.from_user.id not in ADMIN_IDS:
        return
    if message.photo:
        kind, fid = "photo", message.photo[-1].file_id
    elif message.video:
        kind, fid = "video", message.video.file_id
    elif message.animation:
        kind, fid = "animation", message.animation.file_id
    elif message.video_note:
        kind, fid = "video_note", message.video_note.file_id
    elif message.document:
        kind, fid = "document", message.document.file_id
    else:
        return
    await message.answer(f"✅ <b>{kind} file_id:</b>\n<code>{fid}</code>")


@router.message(F.text & ~F.text.startswith("/"))
async def on_text(message: Message):
    user = await get_user(message.from_user.id)
    lang = user.get("lang") or "uz"
    if user.get("waiting_id"):
        await update_user(message.from_user.id, waiting_id=0, win_user_id=message.text.strip()[:64])
        await message.answer(t(lang, "id_saved"), reply_markup=kb_main(lang))
        return
    name = message.from_user.first_name or "User"
    try:
        await message.answer_photo(
            PHOTO_START,
            caption=welcome_text(lang, name)[:1024],
            reply_markup=kb_main(lang),
            protect_content=True,
        )
    except Exception:
        await message.answer(welcome_text(lang, name), reply_markup=kb_main(lang), protect_content=True)


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
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM users")
            regs = await conn.fetchval("SELECT COUNT(*) FROM users WHERE registered=1")
            deps = await conn.fetchval("SELECT COUNT(*) FROM users WHERE deposited=1")
            subs = await conn.fetchval("SELECT COUNT(*) FROM users WHERE subscribed=1")
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
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM users")
        regs = await conn.fetchval("SELECT COUNT(*) FROM users WHERE registered=1")
        deps = await conn.fetchval("SELECT COUNT(*) FROM users WHERE deposited=1")
        subs = await conn.fetchval("SELECT COUNT(*) FROM users WHERE subscribed=1")
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
                    protect_content=True,
                )
            except Exception as e:
                logger.warning("notify reg failed: %s", e)

        elif event in ("ftd", "first_deposit", "firstdep"):
            await update_user(tg_id, registered=1, deposited=1, balance_ok=1, win_user_id=user_id_1win or None)
            try:
                bot: Bot = request.app["bot"]
                user = await get_user(tg_id)
                await bot.send_message(
                    tg_id,
                    t(user["lang"], "dep_ok"),
                    reply_markup=kb_open_app(user["lang"]),
                    protect_content=True,
                )
            except Exception as e:
                logger.warning("notify ftd failed: %s", e)

        elif event in ("dep", "deposit"):
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
                        protect_content=True,
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
    await db.initialize()
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
    if db._pool:
        await db._pool.close()
        logger.info("PostgreSQL connection pool closed")


import asyncio


def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN missing")
    
    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL environment variable is required for PostgreSQL")

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