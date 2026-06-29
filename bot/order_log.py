"""
order_log.py
هر سفارشی که از طریق بات ثبت می‌شه (نه فقط پیام به ادمین)، اینجا هم
به‌صورت یک خط JSON در فایل orders_log.jsonl ذخیره می‌شه. این یک آرشیو
محلی و ساده‌ست تا بشه بعداً گزارش گرفت یا تعداد سفارش‌ها رو شمرد،
بدون نیاز به دیتابیس واقعی.
"""
import json
import os
import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), "orders_log.jsonl")


def log_order(product_id: str, product_title: str, price: int, customer_id: int, customer_tag: str, note: str):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "product_id": product_id,
        "product_title": product_title,
        "price": price,
        "customer_id": customer_id,
        "customer_tag": customer_tag,
        "note": note,
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        # لاگ کردن سفارش هیچ‌وقت نباید باعث شکست خود فلوی سفارش بشه
        print(f"⚠️ خطا در ذخیره لاگ سفارش: {e}")


def count_orders_today() -> int:
    if not os.path.exists(LOG_PATH):
        return 0
    today = datetime.datetime.utcnow().date().isoformat()
    count = 0
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("timestamp", "").startswith(today):
                    count += 1
            except json.JSONDecodeError:
                continue
    return count


def count_orders_total() -> int:
    if not os.path.exists(LOG_PATH):
        return 0
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)
