"""
orders_store.py
سیستم کامل مدیریت سفارش‌ها با وضعیت، ذخیره‌شده در فایل محلی orders.json
(نه روی گیت‌هاب - چون دیتای مشتری نباید عمومی باشه).

وضعیت‌های ممکن یک سفارش:
    incomplete  - مشتری وارد فلوی سفارش شده ولی هنوز توضیح/تماس نفرستاده
    pending     - مشتری توضیح فرستاده، منتظر تأیید یا رد ادمینه
    confirmed   - ادمین سفارش رو نهایی کرده
    cancelled   - مشتری خودش لغو کرده، ادمین رد کرده، یا به‌خاطر بی‌پاسخی منقضی شده
"""
import json
import os
import datetime
import threading

ORDERS_PATH = os.path.join(os.path.dirname(__file__), "orders.json")
_lock = threading.Lock()

# بعد از این مدت (دقیقه) بدون پاسخ مشتری، سفارش خودکار «منصرف‌شده» علامت می‌خوره
ABANDON_TIMEOUT_MINUTES = 30


def _now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def _load():
    if not os.path.exists(ORDERS_PATH):
        return []
    try:
        with open(ORDERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save(orders: list):
    with open(ORDERS_PATH, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)


def _generate_order_id(orders: list) -> str:
    max_num = 0
    for o in orders:
        oid = o.get("order_id", "")
        if oid.startswith("o_"):
            try:
                max_num = max(max_num, int(oid.split("_")[1]))
            except (IndexError, ValueError):
                continue
    return f"o_{max_num + 1:04d}"


def create_incomplete_order(product_id: str, product_title: str, price: int,
                             customer_id: int, customer_tag: str) -> str:
    """
    وقتی مشتری وارد فلوی سفارش می‌شه (قبل از فرستادن توضیح)، یک رکورد
    اولیه با وضعیت incomplete ساخته می‌شه. خروجی: order_id
    """
    with _lock:
        orders = _load()
        order_id = _generate_order_id(orders)
        orders.append({
            "order_id": order_id,
            "product_id": product_id,
            "product_title": product_title,
            "price": price,
            "customer_id": customer_id,
            "customer_tag": customer_tag,
            "note": "",
            "status": "incomplete",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        })
        _save(orders)
        return order_id


def mark_pending(order_id: str, note: str):
    """ وقتی مشتری توضیح/تماس می‌فرسته، سفارش از incomplete به pending می‌ره. """
    with _lock:
        orders = _load()
        for o in orders:
            if o["order_id"] == order_id:
                o["note"] = note
                o["status"] = "pending"
                o["updated_at"] = _now_iso()
                _save(orders)
                return o
        return None


def set_status(order_id: str, status: str):
    with _lock:
        orders = _load()
        for o in orders:
            if o["order_id"] == order_id:
                o["status"] = status
                o["updated_at"] = _now_iso()
                _save(orders)
                return o
        return None


def get_order(order_id: str):
    orders = _load()
    for o in orders:
        if o["order_id"] == order_id:
            return o
    return None


def get_latest_incomplete_order(customer_id: int):
    """ آخرین سفارش incomplete یک مشتری رو پیدا می‌کنه (برای ادامه‌ی فلوی فعلی). """
    orders = [o for o in _load() if o["customer_id"] == customer_id and o["status"] == "incomplete"]
    if not orders:
        return None
    return sorted(orders, key=lambda o: o["created_at"])[-1]


def get_orders_by_customer(customer_id: int) -> list:
    orders = [o for o in _load() if o["customer_id"] == customer_id]
    return sorted(orders, key=lambda o: o["created_at"], reverse=True)


def get_orders_by_status(status: str) -> list:
    orders = [o for o in _load() if o["status"] == status]
    return sorted(orders, key=lambda o: o["created_at"])


def count_orders_today() -> int:
    today = datetime.datetime.utcnow().date().isoformat()
    return sum(1 for o in _load() if o.get("created_at", "").startswith(today))


def count_orders_total() -> int:
    return len(_load())


def count_by_status(status: str) -> int:
    return sum(1 for o in _load() if o.get("status") == status)


def expire_abandoned_orders() -> list:
    """
    سفارش‌های incomplete یا pending که بیشتر از ABANDON_TIMEOUT_MINUTES
    بدون آپدیت موندن رو خودکار cancelled می‌کنه. خروجی: لیست سفارش‌های منقضی‌شده.
    """
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=ABANDON_TIMEOUT_MINUTES)
    expired = []
    with _lock:
        orders = _load()
        changed = False
        for o in orders:
            if o["status"] in ("incomplete", "pending"):
                try:
                    updated = datetime.datetime.fromisoformat(o["updated_at"].replace("Z", ""))
                except ValueError:
                    continue
                if updated < cutoff:
                    o["status"] = "cancelled"
                    o["updated_at"] = _now_iso()
                    o["cancel_reason"] = "timeout"
                    changed = True
                    expired.append(o)
        if changed:
            _save(orders)
    return expired
