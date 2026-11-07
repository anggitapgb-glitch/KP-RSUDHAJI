(function () {
  "use strict";
  const HISTORY_KEY = "ossia_exam_history";
  let activeFilter = "all";

  function recordsFromStorage() {
    try {
      const value = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
      return Array.isArray(value) ? value : [];
    } catch (_) { return []; }
  }
  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, ch => ({
      "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
    }[ch]));
  }
  function statusClass(status) {
    return status === "Perlu peninjauan" ? "attention" :
      status === "Normal" ? "normal" : "review";
  }
  function initRiwayatUI() {
    const list = document.getElementById("historyList");
    const search = document.getElementById("historySearch");
    if (!list || !search || search.dataset.bound === "1") return;
    search.dataset.bound = "1";
    const clear = document.getElementById("historyClear");
    const dialog = document.getElementById("historyDetailDialog");
    const detailContent = document.getElementById("historyDetailContent");

    function dateText(record) {
      const d = new Date(record.dateISO || record.date || Date.now());
      return Number.isNaN(d.getTime()) ? "Tanggal tidak tersedia" :
        d.toLocaleString("id-ID", {day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"});
    }
    function emptyText(query) {
      if (query) return ["Tidak ada hasil yang cocok", "Coba kata kunci lain atau hapus pencarian."];
      if (activeFilter === "normal") return ["Belum ada data Normal", "Segmentasi Otsu tidak menetapkan status klinis normal."];
      if (activeFilter === "attention") return ["Belum ada hasil yang perlu peninjauan", "Hasil yang memerlukan pemeriksaan visual akan muncul di sini."];
      return ["Belum ada riwayat pemeriksaan", "Unggah dan proses citra X-ray dari Home untuk menyimpan hasil."];
    }
    function card(r) {
      const status = esc(r.status || "Perlu verifikasi");
      const id = esc(r.id || "OSSIA");
      const name = esc(r.filename || "Citra X-ray");
      const thumb = r.overlay
        ? `<img class="om-xray-thumb-img" src="${r.overlay}" alt="Overlay segmentasi X-ray">`
        : `<div class="om-xray-thumb" aria-hidden="true">▧</div>`;
      const threshold = r.threshold == null ? "—" : Number(r.threshold).toFixed(1);
      const area = r.foregroundRatio == null ? "—" : `${(Number(r.foregroundRatio) * 100).toFixed(1)}%`;
      return `<article class="om-history-card">
        <div class="om-history-top">
          <div class="om-history-date">${thumb}<div><strong>${name}</strong><small>${dateText(r)} · ID: ${id}</small></div></div>
          <span class="om-status ${statusClass(r.status)}">${status}</span>
        </div>
        <div class="om-history-metrics">
          <div><span>Ambang Otsu</span><strong>${threshold}</strong></div>
          <div><span>Area mask</span><strong>${area}</strong></div>
        </div>
        <div class="om-history-bottom"><p>Estimasi usia tulang: <strong>Belum tersedia</strong></p>
          <button class="om-detail-button" type="button" data-detail-id="${id}">Detail hasil →</button>
        </div>
      </article>`;
    }
    function showDetail(id) {
      const r = recordsFromStorage().find(item => String(item.id) === String(id));
      if (!r || !detailContent) return;
      const overlay = r.overlay ? `<img src="${r.overlay}" alt="Overlay hasil segmentasi" style="width:100%;border-radius:12px;margin:12px 0">` : "";
      const mask = r.mask ? `<details><summary>Lihat mask segmentasi</summary><img src="${r.mask}" alt="Mask biner" style="width:100%;border-radius:12px;margin-top:8px"></details>` : "";
      const threshold = r.threshold == null ? "—" : Number(r.threshold).toFixed(1);
      const area = r.foregroundRatio == null ? "—" : `${(Number(r.foregroundRatio)*100).toFixed(1)}%`;
      detailContent.innerHTML = `
        <p class="om-eyebrow">DETAIL PEMROSESAN CITRA</p>
        <h2>${esc(r.filename || "Citra X-ray")}</h2>
        <p>ID pemeriksaan: ${esc(r.id || "OSSIA")}<br>${dateText(r)}</p>
        <span class="om-status ${statusClass(r.status)}">${esc(r.status || "Perlu verifikasi")}</span>
        ${overlay}${mask}
        <div class="om-detail-grid">
          <div><span>Ambang Otsu</span><strong>${threshold}</strong></div>
          <div><span>Area mask</span><strong>${area}</strong></div>
        </div>
        <div class="om-detail-explanation"><strong>Penjelasan</strong><p>${esc(r.explanation || "Hasil segmentasi perlu diperiksa secara visual.")}</p></div>
        <p>${esc(r.limitation || "Hasil ini bukan estimasi usia tulang atau diagnosis klinis.")}</p>
        <p><strong>Catatan:</strong> hasil Otsu merupakan segmentasi berbasis intensitas, bukan penilaian klinis.</p>`;
      if (dialog && typeof dialog.showModal === "function") dialog.showModal();
      else detailContent.scrollIntoView({behavior:"smooth"});
    }
    function render() {
      const records = recordsFromStorage();
      const query = search.value.trim().toLowerCase();
      const filtered = records.filter(r => {
        const s = String(r.status || "").toLowerCase();
        const matchesFilter = activeFilter === "all" ||
          (activeFilter === "normal" && s === "normal") ||
          (activeFilter === "attention" && s === "perlu peninjauan");
        const searchFields = [r.filename, r.id, r.status, dateText(r)];
        return matchesFilter && (!query || searchFields.some(v => String(v || "").toLowerCase().includes(query)));
      });
      const total = document.getElementById("historyTotal");
      const attention = document.getElementById("historyAttention");
      if (total) total.textContent = String(records.length);
      if (attention) attention.textContent = String(records.filter(r => r.status === "Perlu peninjauan").length);
      if (filtered.length) list.innerHTML = filtered.map(card).join("");
      else {
        const [title, body] = emptyText(query);
        list.innerHTML = `<div class="om-empty-state"><strong>${title}</strong><span>${body}</span></div>`;
      }
      list.querySelectorAll("[data-detail-id]").forEach(b => b.addEventListener("click", () => showDetail(b.dataset.detailId)));
      if (clear) clear.hidden = !search.value;
      document.querySelectorAll("[data-history-filter]").forEach(b => {
        const selected = b.dataset.historyFilter === activeFilter;
        b.classList.toggle("selected", selected);
        b.setAttribute("aria-pressed", String(selected));
      });
    }
    search.addEventListener("input", render);
    clear?.addEventListener("click", () => { search.value = ""; render(); search.focus(); });
    document.querySelectorAll("[data-history-filter]").forEach(b => b.addEventListener("click", () => {
      activeFilter = b.dataset.historyFilter || "all"; render();
    }));
    document.getElementById("historyNotifications")?.addEventListener("click", () => {
      if (typeof window.showOssiaToast === "function") window.showOssiaToast("Belum ada notifikasi baru.");
    });
    render();
  }
  window.initRiwayatUI = initRiwayatUI;
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initRiwayatUI);
  else initRiwayatUI();
})();