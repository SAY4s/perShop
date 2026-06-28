"""
github_client.py
ارتباط با GitHub REST API برای خوندن و نوشتن products.json و آپلود عکس محصولات
بدون نیاز به git نصب‌شده روی سرور - همه چیز از طریق Contents API انجام می‌شه.
"""
import base64
import json
import requests

from config import GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH, PRODUCTS_PATH, ASSETS_PATH

API_BASE = "https://api.github.com"


def _headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _contents_url(path: str) -> str:
    return f"{API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"


def get_file(path: str):
    """
    یک فایل متنی (مثل JSON) رو از ریپو می‌خونه و decode می‌کنه.
    خروجی: (content_str, sha) یا (None, None) اگه فایل وجود نداشت.
    فقط برای فایل‌های متنی استفاده شه؛ برای عکس/فایل باینری از get_file_sha استفاده کن.
    """
    resp = requests.get(_contents_url(path), headers=_headers(), params={"ref": GITHUB_BRANCH})
    if resp.status_code == 404:
        return None, None
    resp.raise_for_status()
    data = resp.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def get_file_sha(path: str):
    """
    فقط sha فایل رو برمی‌گردونه، بدون اینکه محتوا رو decode کنه.
    برای فایل‌های باینری (عکس و...) باید این تابع استفاده شه، نه get_file.
    خروجی: sha (str) یا None اگه فایل وجود نداشت.
    """
    resp = requests.get(_contents_url(path), headers=_headers(), params={"ref": GITHUB_BRANCH})
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()["sha"]


def put_file(path: str, content_bytes: bytes, message: str, sha: str = None):
    """
    یک فایل رو در ریپو می‌سازه یا آپدیت می‌کنه (کامیت جدید).
    اگه فایل از قبل وجود داشته باشه، sha فعلیش باید پاس داده شه تا تعارض پیش نیاد.
    """
    payload = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode("utf-8"),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(_contents_url(path), headers=_headers(), data=json.dumps(payload))
    resp.raise_for_status()
    return resp.json()


def load_products() -> dict:
    """
    products.json رو می‌خونه و به صورت dict پایتونی برمی‌گردونه.
    اگه فایل وجود نداشت، یک ساختار خالی پیش‌فرض برمی‌گردونه.
    """
    content, sha = get_file(PRODUCTS_PATH)
    if content is None:
        return {"last_updated": "", "categories": [], "products": []}, None
    return json.loads(content), sha


def save_products(data: dict, commit_message: str):
    """
    دیکشنری products رو به JSON تبدیل و در ریپو کامیت می‌کنه.
    هر بار قبل از نوشتن، sha تازه گرفته می‌شه تا race condition پیش نیاد.
    """
    import datetime
    data["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"

    # sha تازه رو دوباره می‌گیریم (ممکنه از آخرین بار که load شده تغییر کرده باشه)
    _, fresh_sha = get_file(PRODUCTS_PATH)

    content_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    return put_file(PRODUCTS_PATH, content_bytes, commit_message, sha=fresh_sha)


def upload_image(filename: str, image_bytes: bytes, commit_message: str) -> str:
    """
    یک عکس رو در پوشه assets ریپو آپلود می‌کنه.
    خروجی: مسیر نسبی فایل (برای استفاده در image_url)
    """
    path = f"{ASSETS_PATH}/{filename}"
    # برای عکس جدید معمولاً sha نداریم؛ اگه از قبل بود، فقط sha رو می‌گیریم
    # (نه محتوا - چون عکس باینریه و نمی‌شه با utf-8 decode بشه)
    sha = get_file_sha(path)
    put_file(path, image_bytes, commit_message, sha=sha)
    return path
