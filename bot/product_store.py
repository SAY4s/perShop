"""
product_store.py
منطق CRUD روی لیست محصولات (مستقل از تلگرام و گیت‌هاب).
"""
from github_client import load_products, save_products


def generate_id(products: list) -> str:
    """ یک آیدی یکتای جدید مثل p_0001, p_0002 می‌سازه """
    max_num = 0
    for p in products:
        pid = p.get("id", "")
        if pid.startswith("p_"):
            try:
                num = int(pid.split("_")[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue
    return f"p_{max_num + 1:04d}"


def add_product(title, description, price, category, image_url, stock_count, commit_actor="admin"):
    data, _ = load_products()
    new_id = generate_id(data["products"])

    if category and category not in data.get("categories", []):
        data.setdefault("categories", []).append(category)

    product = {
        "id": new_id,
        "title": title,
        "description": description,
        "price": price,
        "currency": "IRT",
        "category": category,
        "image_url": image_url,
        "in_stock": stock_count > 0,
        "stock_count": stock_count,
        "created_at": "",
        "is_active": True,
    }
    import datetime
    product["created_at"] = datetime.datetime.utcnow().isoformat() + "Z"

    data["products"].append(product)
    save_products(data, f"chore: add product {new_id} by {commit_actor}")
    return product


def get_product(product_id: str):
    data, _ = load_products()
    for p in data["products"]:
        if p["id"] == product_id:
            return p
    return None


def list_products(only_active=False):
    data, _ = load_products()
    products = data["products"]
    if only_active:
        products = [p for p in products if p.get("is_active", True)]
    return products


def update_product_field(product_id: str, field: str, value, commit_actor="admin"):
    data, _ = load_products()
    for p in data["products"]:
        if p["id"] == product_id:
            p[field] = value
            if field == "stock_count":
                p["in_stock"] = value > 0
            save_products(data, f"chore: update {field} of {product_id} by {commit_actor}")
            return p
    return None


def deactivate_product(product_id: str, commit_actor="admin"):
    return update_product_field(product_id, "is_active", False, commit_actor)


def delete_product(product_id: str, commit_actor="admin"):
    data, _ = load_products()
    before = len(data["products"])
    data["products"] = [p for p in data["products"] if p["id"] != product_id]
    if len(data["products"]) == before:
        return False
    save_products(data, f"chore: delete product {product_id} by {commit_actor}")
    return True
