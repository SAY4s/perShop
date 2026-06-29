// ===== تنظیمات =====
const BOT_USERNAME = "perShop_bot"; // یوزرنیم بات بدون @ - بعد از ساخت بات این رو عوض کن
const DATA_URL = "./data/products.json";
const NEW_PRODUCT_DAYS = 3; // محصولاتی که در این بازه ثبت شدن، برچسب «تازه» می‌گیرن

// ===== Telegram Mini App init =====
const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
if (tg) {
  document.body.classList.add("in-telegram");
  try {
    tg.ready();
    tg.expand();
  } catch (e) {
    console.warn("Telegram WebApp init warning:", e);
  }
}

// ===== تم تاریک/روشن =====
const themeToggleBtn = document.getElementById("themeToggle");

function applyTheme(theme) {
  if (theme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
    themeToggleBtn.textContent = "☀️";
  } else {
    document.documentElement.removeAttribute("data-theme");
    themeToggleBtn.textContent = "🌙";
  }
}

function detectInitialTheme() {
  // اول اگه کاربر قبلاً دستی انتخاب کرده، همونو رعایت کن
  const saved = sessionStorage.getItem("perShop_theme");
  if (saved) return saved;
  // وگرنه از تم فعلی تلگرام پیروی کن
  if (tg && tg.colorScheme === "dark") return "dark";
  if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark";
  return "light";
}

applyTheme(detectInitialTheme());

themeToggleBtn.addEventListener("click", () => {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  const next = isDark ? "light" : "dark";
  applyTheme(next);
  sessionStorage.setItem("perShop_theme", next);
  hapticTap();
});

// ===== State =====
let allProducts = [];
let activeCategory = "all";
let searchTerm = "";
let sortMode = "default";

const grid = document.getElementById("productGrid");
const skeletonGrid = document.getElementById("skeletonGrid");
const tabsContainer = document.getElementById("categoryTabs");
const emptyState = document.getElementById("emptyState");
const searchInput = document.getElementById("searchInput");
const sortSelect = document.getElementById("sortSelect");

// ===== بارگذاری دیتا =====
async function loadProducts() {
  skeletonGrid.classList.add("visible");
  try {
    const res = await fetch(`${DATA_URL}?v=${Date.now()}`); // جلوگیری از کش گیت‌هاب پیجز
    if (!res.ok) throw new Error("network error");
    const data = await res.json();
    allProducts = (data.products || []).filter(p => p.is_active !== false);
    buildCategoryTabs(data.categories || []);
    renderGrid();
    openProductFromUrlIfAny();
  } catch (err) {
    console.error("خطا در بارگذاری محصولات:", err);
    emptyState.hidden = false;
    emptyState.textContent = "مشکلی در بارگذاری فروشگاه پیش اومد. کمی بعد دوباره سر بزن.";
  } finally {
    skeletonGrid.classList.remove("visible");
  }
}

function buildCategoryTabs(categories) {
  tabsContainer.innerHTML = "";
  const allTab = makeTab("همه", "all");
  tabsContainer.appendChild(allTab);
  categories.forEach(cat => tabsContainer.appendChild(makeTab(cat, cat)));
}

function makeTab(label, value) {
  const btn = document.createElement("button");
  btn.className = "tab" + (value === activeCategory ? " active" : "");
  btn.textContent = label;
  btn.dataset.category = value;
  btn.addEventListener("click", () => {
    if (value === activeCategory) return;
    activeCategory = value;
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    btn.classList.add("active");
    hapticTap();
    renderGrid();
  });
  return btn;
}

function isNewProduct(product) {
  if (!product.created_at) return false;
  const created = new Date(product.created_at);
  const diffDays = (Date.now() - created.getTime()) / (1000 * 60 * 60 * 24);
  return diffDays <= NEW_PRODUCT_DAYS;
}

// ===== جستجو =====
let searchDebounceTimer = null;
searchInput.addEventListener("input", () => {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    searchTerm = searchInput.value.trim().toLowerCase();
    renderGrid();
  }, 180);
});

// ===== مرتب‌سازی =====
sortSelect.addEventListener("change", () => {
  sortMode = sortSelect.value;
  hapticTap();
  renderGrid();
});

function applySort(list) {
  const arr = [...list];
  if (sortMode === "price_asc") arr.sort((a, b) => (a.price || 0) - (b.price || 0));
  else if (sortMode === "price_desc") arr.sort((a, b) => (b.price || 0) - (a.price || 0));
  else arr.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
  return arr;
}

function renderGrid() {
  let filtered = activeCategory === "all"
    ? allProducts
    : allProducts.filter(p => p.category === activeCategory);

  if (searchTerm) {
    filtered = filtered.filter(p =>
      (p.title || "").toLowerCase().includes(searchTerm) ||
      (p.description || "").toLowerCase().includes(searchTerm)
    );
  }

  filtered = applySort(filtered);

  grid.innerHTML = "";

  if (filtered.length === 0) {
    emptyState.hidden = false;
    emptyState.textContent = searchTerm ? "چیزی با این عبارت پیدا نشد." : "محصولی در این دسته پیدا نشد.";
    return;
  }
  emptyState.hidden = true;

  filtered.forEach((product, i) => {
    const card = buildCard(product);
    card.style.animationDelay = `${Math.min(i, 8) * 45}ms`;
    grid.appendChild(card);
  });
}

function buildCard(product) {
  const card = document.createElement("article");
  card.className = "product-card";
  card.addEventListener("click", () => openSheet(product));

  const outOfStock = !product.in_stock || product.stock_count <= 0;

  card.innerHTML = `
    <div class="card-image-wrap">
      <img src="${product.image_url}" alt="${escapeHtml(product.title)}" loading="lazy">
      ${isNewProduct(product) ? '<span class="stamp">تازه</span>' : ""}
      ${outOfStock ? '<div class="out-of-stock-badge">ناموجود</div>' : ""}
    </div>
    <div class="card-body">
      <span class="card-category">${escapeHtml(product.category || "")}</span>
      <h3 class="card-title">${escapeHtml(product.title)}</h3>
      <div class="card-footer">
        <span class="price">${formatPrice(product.price)}</span>
        <span class="stock-pill ${outOfStock ? "out" : ""}">${outOfStock ? "ناموجود" : "موجود"}</span>
      </div>
    </div>
  `;
  return card;
}

// ===== Bottom Sheet =====
const sheetOverlay = document.getElementById("sheetOverlay");
const sheet = document.getElementById("productSheet");
const sheetImage = document.getElementById("sheetImage");
const sheetStamp = document.getElementById("sheetStamp");
const sheetCategory = document.getElementById("sheetCategory");
const sheetTitle = document.getElementById("sheetTitle");
const sheetDescription = document.getElementById("sheetDescription");
const sheetPrice = document.getElementById("sheetPrice");
const sheetBuyBtn = document.getElementById("sheetBuyBtn");
const sheetOutOfStock = document.getElementById("sheetOutOfStock");

let currentOrderUrl = null;

function openSheet(product, fromUrl = false) {
  if (!fromUrl) hapticTap();
  sheetImage.src = product.image_url;
  sheetImage.alt = product.title;
  sheetStamp.hidden = !isNewProduct(product);
  sheetCategory.textContent = product.category || "";
  sheetTitle.textContent = product.title;
  sheetDescription.textContent = product.description || "";
  sheetPrice.textContent = formatPrice(product.price);

  const outOfStock = !product.in_stock || product.stock_count <= 0;
  sheetOutOfStock.hidden = !outOfStock;

  if (outOfStock) {
    sheetBuyBtn.classList.add("disabled");
    sheetBuyBtn.textContent = "فعلاً ناموجود";
    currentOrderUrl = null;
  } else {
    sheetBuyBtn.classList.remove("disabled");
    sheetBuyBtn.textContent = "سفارش از طریق تلگرام";
    currentOrderUrl = `https://t.me/${BOT_USERNAME}?start=order_${product.id}`;
  }

  // برای اشتراک‌گذاری مستقیم لینک همین محصول، آیدی رو در URL می‌گذاریم
  history.replaceState(null, "", `?product=${product.id}`);

  sheetOverlay.hidden = false;
  sheet.hidden = false;
  document.body.style.overflow = "hidden";
  requestAnimationFrame(() => {
    sheetOverlay.classList.add("visible");
    sheet.classList.add("visible");
  });
}

function closeSheet() {
  sheetOverlay.classList.remove("visible");
  sheet.classList.remove("visible");
  document.body.style.overflow = "";
  history.replaceState(null, "", location.pathname);
  setTimeout(() => {
    sheetOverlay.hidden = true;
    sheet.hidden = true;
  }, 320);
}

// اگه لینک با ?product=ID باز شده باشه، خودکار همون محصول رو نشون بده
function openProductFromUrlIfAny() {
  const params = new URLSearchParams(location.search);
  const productId = params.get("product");
  if (!productId) return;
  const product = allProducts.find(p => p.id === productId);
  if (product) openSheet(product, true);
}

sheetBuyBtn.addEventListener("click", () => {
  if (!currentOrderUrl) return;
  hapticTap();
  // داخل Mini App از openTelegramLink استفاده می‌کنیم تا مستقیم به چت بات برسه
  if (tg && tg.openTelegramLink) {
    tg.openTelegramLink(currentOrderUrl);
  } else {
    window.open(currentOrderUrl, "_blank");
  }
});

document.querySelectorAll("[data-close]").forEach(el => el.addEventListener("click", closeSheet));
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && !sheet.hidden) closeSheet();
});

function hapticTap() {
  if (tg && tg.HapticFeedback) {
    try { tg.HapticFeedback.impactOccurred("light"); } catch (e) { /* noop */ }
  }
}

// ===== کمکی =====
function formatPrice(price) {
  return Number(price || 0).toLocaleString("fa-IR");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// ===== شروع =====
loadProducts();
