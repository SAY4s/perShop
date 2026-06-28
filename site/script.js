// ===== تنظیمات =====
const BOT_USERNAME = "perShop_bot"; // یوزرنیم بات بدون @ - بعد از ساخت بات این رو عوض کن
const DATA_URL = "./data/products.json";
const NEW_PRODUCT_DAYS = 3; // محصولاتی که در این بازه ثبت شدن، برچسب «تازه» می‌گیرن

// ===== State =====
let allProducts = [];
let activeCategory = "all";

const grid = document.getElementById("productGrid");
const tabsContainer = document.getElementById("categoryTabs");
const emptyState = document.getElementById("emptyState");

// ===== بارگذاری دیتا =====
async function loadProducts() {
  try {
    const res = await fetch(`${DATA_URL}?v=${Date.now()}`); // جلوگیری از کش گیت‌هاب پیجز
    if (!res.ok) throw new Error("network error");
    const data = await res.json();
    allProducts = (data.products || []).filter(p => p.is_active !== false);
    buildCategoryTabs(data.categories || []);
    renderGrid();
  } catch (err) {
    console.error("خطا در بارگذاری محصولات:", err);
    emptyState.hidden = false;
    emptyState.textContent = "مشکلی در بارگذاری فروشگاه پیش اومد. کمی بعد دوباره سر بزن.";
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
    activeCategory = value;
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    btn.classList.add("active");
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

function renderGrid() {
  const filtered = activeCategory === "all"
    ? allProducts
    : allProducts.filter(p => p.category === activeCategory);

  grid.innerHTML = "";

  if (filtered.length === 0) {
    emptyState.hidden = false;
    emptyState.textContent = "محصولی در این دسته پیدا نشد.";
    return;
  }
  emptyState.hidden = true;

  filtered.forEach(product => grid.appendChild(buildCard(product)));
}

function buildCard(product) {
  const card = document.createElement("article");
  card.className = "product-card";
  card.addEventListener("click", () => openModal(product));

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

// ===== Modal =====
const modal = document.getElementById("productModal");
const modalImage = document.getElementById("modalImage");
const modalStamp = document.getElementById("modalStamp");
const modalCategory = document.getElementById("modalCategory");
const modalTitle = document.getElementById("modalTitle");
const modalDescription = document.getElementById("modalDescription");
const modalPrice = document.getElementById("modalPrice");
const modalBuyBtn = document.getElementById("modalBuyBtn");
const modalOutOfStock = document.getElementById("modalOutOfStock");

function openModal(product) {
  modalImage.src = product.image_url;
  modalImage.alt = product.title;
  modalStamp.hidden = !isNewProduct(product);
  modalCategory.textContent = product.category || "";
  modalTitle.textContent = product.title;
  modalDescription.textContent = product.description || "";
  modalPrice.textContent = formatPrice(product.price);

  const outOfStock = !product.in_stock || product.stock_count <= 0;
  modalOutOfStock.hidden = !outOfStock;

  if (outOfStock) {
    modalBuyBtn.classList.add("disabled");
    modalBuyBtn.removeAttribute("href");
    modalBuyBtn.textContent = "فعلاً ناموجود";
  } else {
    modalBuyBtn.classList.remove("disabled");
    modalBuyBtn.href = `https://t.me/${BOT_USERNAME}?start=order_${product.id}`;
    modalBuyBtn.textContent = "سفارش از طریق تلگرام";
  }

  modal.hidden = false;
  document.body.style.overflow = "hidden";
}

function closeModal() {
  modal.hidden = true;
  document.body.style.overflow = "";
}

document.querySelectorAll("[data-close]").forEach(el => el.addEventListener("click", closeModal));
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && !modal.hidden) closeModal();
});

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
