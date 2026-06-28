import os
from dotenv import load_dotenv

load_dotenv()

# توکن بات تلگرام - از @BotFather بگیر
BOT_TOKEN = os.getenv("BOT_TOKEN", "8715972406:AAEvPJXG6cWS1H0kcQULeurdJNeCZuu9uXo")

# لیست آیدی عددی ادمین‌ها (با گرفتن آیدی از @userinfobot)
# مثال: "111111,222222"
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "7633207763").split(",") if x.strip()]

# توکن GitHub با اسکوپ repo (Settings > Developer settings > Personal access tokens)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# صاحب ریپو و نام ریپو، مثل: SAY4s/perShop
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

# مسیر فایل دیتا و پوشه عکس‌ها داخل ریپو (نسبت به ریشه ریپو)
PRODUCTS_PATH = os.getenv("PRODUCTS_PATH", "site/data/products.json")
ASSETS_PATH = os.getenv("ASSETS_PATH", "site/assets")

# یوزرنیم بات بدون @ - برای ساخت دیپ‌لینک سفارش در سایت
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

# آیدی عددی (یا یوزرنیم) کانال/چت لاگ تغییرات (اختیاری)
LOG_CHAT_ID = os.getenv("LOG_CHAT_ID", "")


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
