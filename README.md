# SYRAX Signal Bot

## Railway deploy

1. GitHub da yangi **private** repo: `syrax-bot`
2. Shu papkadagi fayllarni yuklang: `main.py`, `requirements.txt`, `.env.example`
3. [railway.app](https://railway.app) → New Project → Deploy from GitHub → `syrax-bot`
4. Variables qo‘shing:
   - `BOT_TOKEN` = yangi token (BotFather)
   - `CHANNEL_ID` = `@syraxapp`
   - `CHANNEL_URL` = `https://t.me/syraxapp`
   - `SUPPORT_URL` = `https://t.me/syrax_admin`
   - `MINIAPP_URL` = `https://syrax-app.github.io/SYRAX-MINI-APP/`
   - `PARTNER_LINK` = `https://shorturl.at/eqDTy`
   - `PROMO_CODE` = `SYRAX`
   - `ADMIN_IDS` = sizning Telegram ID (raqam)
5. Settings → Networking → **Generate Domain**
6. Domain masalan: `https://syrax-bot-production-xxxx.up.railway.app`
7. 1WIN postback:

**Registratsiya:**
```
https://YOUR-RAILWAY-DOMAIN/postback?event=reg&sub1={sub1}&user_id={user_id}
```

**Birinchi depozit:**
```
https://YOUR-RAILWAY-DOMAIN/postback?event=ftd&sub1={sub1}&user_id={user_id}&amount={amount}
```

**Barcha depozitlar:**
```
https://YOUR-RAILWAY-DOMAIN/postback?event=dep&sub1={sub1}&user_id={user_id}&amount={amount}
```

## Admin buyruqlar
- `/setreg 123456` — reg belgilash
- `/setdep 123456` — depozit + faollashtirish
- `/setbalance 123456 0` — balans 0 (signallarni to‘xtatish)
- `/setbalance 123456 1` — qayta yoqish

## Oqim
Start → til → kanal obunasi → menyu → Signal → 1WIN reg (SYRAX) → depozit → Mini App
