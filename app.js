const PAGE_FILES = {
  landing: "pages/landing.html",
  login: "pages/login.html",
  home: "pages/home.html",
  dashboard: "pages/home.html",
  riwayat: "pages/riwayat.html",
  chat: "pages/chat.html",
  chatbot: "pages/chat.html",
  me: "pages/me.html"
};

let currentPage = "landing";
let activePageScript = null;
let activePageStyle = null;

window.showOssiaToast = function (message) {
  let toast = document.getElementById("ossia-global-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "ossia-global-toast";
    toast.className = "toast";
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(window.__ossiaToastTimer);
  window.__ossiaToastTimer = setTimeout(() => toast.classList.remove("show"), 2500);
};

function clearPageAssets() {
  if (activePageScript) {
    activePageScript.remove();
    activePageScript = null;
  }
  if (activePageStyle) {
    activePageStyle.remove();
    activePageStyle = null;
  }
}

function loadPageAssets(page) {
  clearPageAssets();
  const key = page === "dashboard" ? "home" : page;
  if (key !== "home" && key !== "riwayat") return;

  const css = document.createElement("link");
  css.rel = "stylesheet";
  css.href = `css/${key}.css`;
  css.dataset.ossiaPageStyle = key;
  document.head.appendChild(css);
  activePageStyle = css;

  const script = document.createElement("script");
  script.src = `js/${key}.js`;
  script.dataset.ossiaPageScript = key;
  script.onload = () => {
    if (key === "home" && typeof window.initHomeUI === "function") window.initHomeUI();
    if (key === "riwayat" && typeof window.initRiwayatUI === "function") window.initRiwayatUI();
  };
  script.onerror = () => console.error(`Gagal memuat js/${key}.js`);
  document.body.appendChild(script);
  activePageScript = script;
}

function addMobileNavigation(page) {
  document.querySelector(".mobile-nav")?.remove();
  if (page === "landing" || page === "login") return;

  const active = page === "dashboard" ? "home" : page === "chatbot" ? "chat" : page;
  const nav = document.createElement("nav");
  nav.className = "mobile-nav";
  nav.setAttribute("aria-label", "Navigasi utama");
  const items = [
    ["home", "⌂", "Home"],
    ["riwayat", "▤", "Riwayat"],
    ["chat", "▢", "Chat"],
    ["me", "♙", "Me"]
  ];
  nav.innerHTML = items.map(([id, icon, label]) =>
    `<button type="button" class="${active === id ? "active" : ""}" data-app-page="${id}">
      <span aria-hidden="true">${icon}</span><span>${label}</span>
    </button>`
  ).join("");
  document.body.appendChild(nav);
}

async function bukaHalaman(target) {
  const page = PAGE_FILES[target] ? target : "landing";
  const app = document.getElementById("app-view");
  if (!app) return;
  app.innerHTML = '<div class="loading-screen">Memuat halaman...</div>';

  try {
    const response = await fetch(PAGE_FILES[page]);
    if (!response.ok) throw new Error(`Tidak bisa memuat ${PAGE_FILES[page]}`);
    app.innerHTML = await response.text();
    currentPage = page;

    const titles = {
      landing: "Landing Page", login: "Masuk", home: "Home",
      dashboard: "Home", riwayat: "Riwayat", chat: "Chat",
      chatbot: "Chat", me: "Profil"
    };
    document.title = `OSSIA | ${titles[page] || "Skrining Usia Tulang"}`;
    addMobileNavigation(page);
    loadPageAssets(page);
    window.scrollTo(0, 0);

    if ((page === "chat" || page === "chatbot") && typeof window.initChatbot === "function") {
      window.initChatbot();
    }
    if (typeof window.initLogic === "function") window.initLogic(page);
  } catch (error) {
    app.innerHTML = `<section class="error-page">
      <h2>Halaman tidak dapat dimuat</h2>
      <p>${error.message}</p>
      <p>Jalankan proyek dengan Live Server, bukan membuka index.html langsung.</p>
    </section>`;
    console.error(error);
  }
}
window.bukaHalaman = bukaHalaman;

document.addEventListener("click", event => {
  const navButton = event.target.closest("[data-app-page]");
  if (navButton) {
    bukaHalaman(navButton.dataset.appPage);
    return;
  }
  const link = event.target.closest("[data-page]");
  if (link) {
    event.preventDefault();
    bukaHalaman(link.dataset.page);
  }
});

document.addEventListener("DOMContentLoaded", () => bukaHalaman("landing"));
