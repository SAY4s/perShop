# perShop 🛍

فروشگاه استاتیک با مدیریت محصولات از طریق بات تلگرام، با نمایش به‌صورت Mini App داخل تلگرام.
A static storefront managed entirely through a Telegram bot, also viewable as a Telegram Mini App.

**[فارسی](#فارسی) | [English](#english)**

---

## فارسی

### معرفی
perShop یک فروشگاه دوبخشی‌ست:
1. **بات تلگرام (ادمین‌پنل)** — ادمین از طریق دستورات بات محصول اضافه/ویرایش/حذف می‌کنه.
2. **سایت استاتیک (ویترین مشتری)** — روی GitHub Pages میزبانی می‌شه و هم به‌صورت وب‌سایت معمولی، هم به‌صورت Mini App داخل تلگرام قابل مشاهده‌ست.

منبع حقیقت (source of truth) یک فایل `products.json` داخل ریپوی گیت‌هابه. بات از طریق GitHub REST API مستقیم این فایل رو می‌خونه/می‌نویسه — بدون نیاز به دیتابیس یا سرور جداگانه.

### ساختار پروژه
```
perShop/
├── bot/          ← بات تلگرام (ادمین‌پنل)
│   ├── main.py
│   ├── config.py
│   ├── github_client.py
│   ├── product_store.py
│   ├── order_log.py
│   └── handlers/
└── site/         ← سایت استاتیک (روی GitHub Pages میزبانی می‌شه)
    ├── index.html
    ├── style.css
    ├── script.js
    └── data/products.json
```

### مرحله ۱: ساخت ریپوی گیت‌هاب
1. یک ریپو جدید بساز، مثلاً `SAY4s/perShop`.
2. کل پوشه‌ی `perShop/` رو داخلش push کن (هم `bot/` هم `site/`).
3. در تنظیمات ریپو → **Settings → Pages** → سورس رو روی شاخه‌ی `main` و پوشه‌ی `/site` بگذار (یا اگه گیت‌هاب اجازه نداد پوشه‌ی فرعی رو انتخاب کنی، محتوای `site/` رو به یک ریپوی جدا یا شاخه‌ی `gh-pages` منتقل کن).

### مرحله ۲: ساخت بات تلگرام
1. به [@BotFather](https://t.me/BotFather) پیام بده، با `/newbot` یک بات بساز و توکن رو کپی کن.
2. یوزرنیم بات (مثلاً `perShop_bot`) رو در دو جا بگذار:
   - `bot/.env` → `BOT_USERNAME`
   - `site/script.js` → متغیر `BOT_USERNAME` در بالای فایل
3. آدرس GitHub Pages سایتت رو در `bot/.env` بگذار:
   - `SITE_URL=https://SAY4s.github.io/perShop`

### مرحله ۳: ساخت GitHub Token
1. GitHub → **Settings → Developer settings → Personal access tokens**
2. **اگه از نوع Fine-grained استفاده می‌کنی** (پیشنهادی): زیر *Repository access* فقط ریپوی perShop رو انتخاب کن، و زیر *Repository permissions* پرمیژن **Contents** رو روی **Read and write** بگذار. بدون این تنظیم، بات با خطای 403 یا سکوت کامل گیر می‌کنه.
3. **اگه از نوع Classic استفاده می‌کنی**: اسکوپ `repo` رو فعال کن.
4. توکن رو در `bot/.env` بگذار: `GITHUB_TOKEN=...`

> ⚠️ توکن گیت‌هاب رو هیچ‌وقت در چت، کامیت، یا جای عمومی قرار نده. اگه به‌اشتباه جایی پیست شد، فوراً Revoke/Delete کن و یکی جدید بساز.

### مرحله ۴: گرفتن آیدی عددی ادمین
1. به [@userinfobot](https://t.me/userinfobot) پیام بده تا آیدی عددیت رو بگیری.
2. در `bot/.env`: `ADMIN_IDS=123456789` (برای چند ادمین با کاما جدا کن)

### مرحله ۵: تکمیل فایل `.env`
فایل `bot/.env.example` رو کپی کن به `bot/.env` و مقادیر واقعی رو بگذار:
```
BOT_TOKEN=...
ADMIN_IDS=...
GITHUB_TOKEN=...
GITHUB_OWNER=SAY4s
GITHUB_REPO=perShop
GITHUB_BRANCH=main
PRODUCTS_PATH=site/data/products.json
ASSETS_PATH=site/assets
BOT_USERNAME=perShop_bot
SITE_URL=https://SAY4s.github.io/perShop
```

### مرحله ۶: اجرای بات
روی سرور یا کامپیوتر همیشه‌روشن:
```bash
cd bot
pip install -r requirements.txt
python main.py
```

### مرحله ۷: تست
1. به ادمین‌پنل بات `/add` بزن و یک محصول بساز (عنوان، توضیح، قیمت، دسته، موجودی، عکس).
2. چک کن که در ریپوی گیت‌هاب کامیت جدید زده شده (در `site/data/products.json` و `site/assets/`).
3. آدرس GitHub Pages رو باز کن — محصول باید دیده شه (ممکنه چند دقیقه طول بکشه تا کش Pages آپدیت شه).
4. روی دکمه‌ی «سفارش از طریق تلگرام» کلیک کن — باید با دیپ‌لینک به بات بری و فلوی سفارش شروع شه.
5. توی تلگرام `/start` رو بزن — باید دکمه‌ی «🛍 باز کردن فروشگاه» رو ببینی که Mini App رو باز می‌کنه.

### دستورات ادمین در بات
| دستور | کار |
|---|---|
| `/add` | افزودن محصول جدید (فلوی مرحله‌ای) |
| `/list` | لیست محصولات با دکمه‌های ویرایش/حذف |
| `/stats` | آمار فروشگاه (تعداد محصولات، ارزش موجودی، سفارش‌های امروز/کل) |
| `/shop` | باز کردن فروشگاه به‌صورت Mini App (برای تست) |
| `/help` | راهنما |

### ✨ ویژگی‌های سایت
- 🔍 **جستجو** — سرچ‌باکس بالای گرید، روی عنوان و توضیحات محصول فیلتر می‌کنه.
- ↕️ **مرتب‌سازی** — جدیدترین / ارزان‌ترین / گران‌ترین.
- 🌙 **حالت تاریک** — دکمه‌ی دستی + تشخیص خودکار از تم تلگرام/سیستم.
- 🔗 **لینک مستقیم محصول** — آدرس صفحه به `?product=<id>` تغییر می‌کنه؛ قابل اشتراک‌گذاری مستقیم.
- 🏷 **برچسب «تازه»** — محصولات ثبت‌شده در ۳ روز اخیر برچسب می‌خورن.
- 📱 **سازگار با Telegram Mini App** — هاپتیک فیدبک، باز شدن تمام‌صفحه، دکمه‌ی سفارش که مستقیم به چت بات می‌ره.

### 🧾 آرشیو سفارش‌ها
هر سفارشی که از طریق بات ثبت می‌شه (نه فقط پیامی که برای ادمین می‌ره)، در فایل `bot/orders_log.jsonl` هم به‌صورت یک خط JSON ذخیره می‌شه. این فایل عمداً در `.gitignore` قرار گرفته و **روی گیت‌هاب پوش نمی‌شه** (چون دیتای سفارش نباید عمومی باشه). از همین فایل، `/stats` تعداد سفارش امروز و کل رو می‌خونه.

### 📱 Mini App (باز شدن سایت داخل تلگرام)
وقتی بات اجرا می‌شه، خودش یک دکمه‌ی ثابت 🛍 کنار باکس پیام (Menu Button) نصب می‌کنه که با کلیک، همین سایت رو **بدون خروج از تلگرام** باز می‌کنه. علاوه بر اون، `/start` و `/shop` هم دکمه‌ی مشابه نشون می‌دن.

نکات لازم برای این‌که Mini App درست کار کنه:
- آدرس `SITE_URL` باید HTTPS باشه (GitHub Pages به‌صورت پیش‌فرض HTTPS می‌ده).
- اگه `SITE_URL` خالی باشه، دکمه‌ی منو نصب نمی‌شه ولی بقیه‌ی بات عادی کار می‌کنه.
- سایت با `Telegram.WebApp` API سازگاره (تشخیص خودکار محیط؛ خارج از تلگرام هم بدون مشکل کار می‌کنه).

دکمه‌ی منو رو می‌شه دستی هم از BotFather تنظیم کرد (اختیاری): `/mybots` → انتخاب بات → `Bot Settings` → `Menu Button`.

### نکات مهم
- هر تغییر ادمین یک کامیت جدید روی گیت‌هاب می‌زنه؛ سایت با تأخیر کوتاهی (به‌خاطر کش GitHub Pages) آپدیت می‌شه.
- اگه چند ادمین هم‌زمان کار کنن، کد هر بار قبل از نوشتن SHA تازه می‌گیره تا تعارض پیش نیاد.
- مدل فعلی خرید «هماهنگی دستی»ست: مشتری از سایت/Mini App به بات می‌ره، توضیح می‌ده، بات به ادمین‌ها فوروارد می‌کنه و خرید نهایی دستی پیگیری می‌شه.

### 🚧 ایده‌های توسعه‌ی بعدی
- سبد خرید واقعی (چند محصول در یک سفارش)
- درگاه پرداخت آنلاین (زرین‌پال و مشابه) — نیاز به یک بک‌اند واسط کوچک دارد
- چند سطح دسترسی ادمین (فروش / مدیریت کامل)
- گالری چند عکسی برای هر محصول
- اعلام «موجود شد» برای محصولات ناموجود

---

## English

### Overview
perShop is a two-part shop system:
1. **Telegram bot (admin panel)** — admins add/edit/delete products via bot commands.
2. **Static storefront** — hosted on GitHub Pages, viewable both as a regular website and as a Telegram Mini App inside the bot.

The single source of truth is a `products.json` file inside the GitHub repo. The bot reads/writes this file directly through the GitHub REST API — no database or separate server needed.

### Project structure
```
perShop/
├── bot/          ← Telegram bot (admin panel)
│   ├── main.py
│   ├── config.py
│   ├── github_client.py
│   ├── product_store.py
│   ├── order_log.py
│   └── handlers/
└── site/         ← Static storefront (hosted on GitHub Pages)
    ├── index.html
    ├── style.css
    ├── script.js
    └── data/products.json
```

### Step 1: Create the GitHub repo
1. Create a new repo, e.g. `SAY4s/perShop`.
2. Push the whole `perShop/` folder into it (both `bot/` and `site/`).
3. In repo settings → **Settings → Pages**, set the source to branch `main`, folder `/site` (if GitHub doesn't let you pick a subfolder, move `site/` content to its own repo or a `gh-pages` branch instead).

### Step 2: Create the Telegram bot
1. Message [@BotFather](https://t.me/BotFather), run `/newbot`, and copy the token.
2. Set the bot's username (e.g. `perShop_bot`) in two places:
   - `bot/.env` → `BOT_USERNAME`
   - `site/script.js` → the `BOT_USERNAME` constant near the top
3. Put your GitHub Pages URL in `bot/.env`:
   - `SITE_URL=https://SAY4s.github.io/perShop`

### Step 3: Create a GitHub Token
1. GitHub → **Settings → Developer settings → Personal access tokens**
2. **If using a Fine-grained token** (recommended): under *Repository access*, select only the perShop repo, and under *Repository permissions* set **Contents** to **Read and write**. Without this, the bot will fail silently or with a 403 error.
3. **If using a Classic token**: enable the `repo` scope.
4. Put it in `bot/.env`: `GITHUB_TOKEN=...`

> ⚠️ Never paste your GitHub token into chat, commits, or anywhere public. If it's ever exposed, revoke it immediately and generate a new one.

### Step 4: Get your numeric admin ID
1. Message [@userinfobot](https://t.me/userinfobot) to get your numeric Telegram ID.
2. In `bot/.env`: `ADMIN_IDS=123456789` (comma-separate for multiple admins)

### Step 5: Fill in `.env`
Copy `bot/.env.example` to `bot/.env` and fill in real values:
```
BOT_TOKEN=...
ADMIN_IDS=...
GITHUB_TOKEN=...
GITHUB_OWNER=SAY4s
GITHUB_REPO=perShop
GITHUB_BRANCH=main
PRODUCTS_PATH=site/data/products.json
ASSETS_PATH=site/assets
BOT_USERNAME=perShop_bot
SITE_URL=https://SAY4s.github.io/perShop
```

### Step 6: Run the bot
On an always-on server or computer:
```bash
cd bot
pip install -r requirements.txt
python main.py
```

### Step 7: Test it
1. In the bot, run `/add` and create a product (title, description, price, category, stock, photo).
2. Confirm a new commit appeared in the GitHub repo (`site/data/products.json` and `site/assets/`).
3. Open the GitHub Pages URL — the product should appear (may take a few minutes due to Pages caching).
4. Click "Order via Telegram" — it should deep-link into the bot and start the order flow.
5. In Telegram, send `/start` — you should see a "🛍 Open Shop" button that launches the Mini App.

### Bot admin commands
| Command | Action |
|---|---|
| `/add` | Add a new product (step-by-step flow) |
| `/list` | List products with edit/delete buttons |
| `/stats` | Shop stats (product counts, stock value, today's/total orders) |
| `/shop` | Open the shop as a Mini App (for testing) |
| `/help` | Help |

### ✨ Site features
- 🔍 **Search** — filters by product title/description.
- ↕️ **Sorting** — newest / cheapest / most expensive.
- 🌙 **Dark mode** — manual toggle, plus auto-detection from Telegram/system theme.
- 🔗 **Direct product links** — opening a product updates the URL to `?product=<id>`, shareable directly.
- 🏷 **"New" badge** — products added within the last 3 days get tagged.
- 📱 **Telegram Mini App ready** — haptic feedback, full-screen expand, order button that opens the bot chat directly.

### 🧾 Order archive
Every order placed through the bot (not just the message forwarded to admins) is also appended as a JSON line to `bot/orders_log.jsonl`. This file is intentionally listed in `.gitignore` and **never pushed to GitHub** (customer data shouldn't be public). `/stats` reads today's/total order counts from this file.

### 📱 Mini App (opening the site inside Telegram)
When the bot starts, it automatically installs a persistent 🛍 menu button next to the message box that opens this same site **without leaving Telegram**. `/start` and `/shop` also show the same button.

Requirements for the Mini App to work correctly:
- `SITE_URL` must be HTTPS (GitHub Pages provides this by default).
- If `SITE_URL` is left empty, the menu button simply won't be installed; the rest of the bot still works normally.
- The site uses the `Telegram.WebApp` API (auto-detected; works fine outside Telegram too).

You can also set the menu button manually via BotFather (optional): `/mybots` → select bot → `Bot Settings` → `Menu Button`.

### Important notes
- Every admin change creates a new GitHub commit; the site updates with a short delay due to GitHub Pages caching.
- If multiple admins act at once, the code re-fetches the file's SHA right before each write to avoid conflicts.
- The current ordering model is "manual coordination": the customer goes from the site/Mini App into the bot, leaves a note, the bot forwards it to admins, and the sale is finalized manually.

### 🚧 Future ideas
- A real shopping cart (multiple products per order)
- Online payment gateway (e.g. ZarinPal) — would need a small backend webhook
- Multi-tier admin permissions (sales vs. full management)
- Multi-image gallery per product
- "Notify me when back in stock" for out-of-stock items
