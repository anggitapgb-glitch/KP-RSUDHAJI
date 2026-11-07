/* ==========================================================
   app.js : tampilan & alur aplikasi (prototipe front-end)
   Data disimpan di localStorage browser HANYA untuk demo.
   Nanti diganti ke backend (mis. Cloudflare Workers + D1).
   ========================================================== */

const KEY_REC = "bonecare_records_v1";
const KEY_SES = "bonecare_session_v1";

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const today = () => new Date().toISOString().slice(0, 10);

/* ---------- State ---------- */
let session = null;
try { session = JSON.parse(localStorage.getItem(KEY_SES)); } catch (e) { session = null; }
let records = loadRecords();
let view = null;
let loginRole = "pasien";
let draft = null;
let draftFile = null;
const chatLog = [{ who: "bot", text: "Halo! Saya asisten edukasi BoneCare. Saya bisa menjelaskan arti usia tulang dan arti status hasil pemeriksaan. Saya tidak memberi diagnosis." }];

/* ---------- Data ---------- */
function seedRecords() {
  const mk = (o) => buildRecord({ ...o, ratio: Math.round((0.05 + (o.boneMonths / 216) * 0.9) * 1000) / 1000 });
  return [
    mk({ rm: "RM-001001", nama: "Aisyah Putri", jk: "P", lahir: "2017-03-12", tglFoto: "2026-08-20", boneMonths: 112, verified: true, catatan: "Pertumbuhan tulang sesuai usia. Kontrol rutin." }),
    mk({ rm: "RM-001001", nama: "Aisyah Putri", jk: "P", lahir: "2017-03-12", tglFoto: "2025-09-10", boneMonths: 94, verified: true, catatan: "" }),
    mk({ rm: "RM-001002", nama: "Raka Pratama", jk: "L", lahir: "2018-06-05", tglFoto: "2026-09-30", boneMonths: 66, verified: false }),
    mk({ rm: "RM-001003", nama: "Dimas Saputra", jk: "L", lahir: "2015-01-20", tglFoto: "2026-07-14", boneMonths: 120, verified: true, catatan: "Disarankan pemantauan dan konsultasi dokter anak." })
  ];
}
function loadRecords() {
  try {
    const r = JSON.parse(localStorage.getItem(KEY_REC));
    if (Array.isArray(r) && r.length) return r;
  } catch (e) { /* abaikan */ }
  const s = seedRecords();
  localStorage.setItem(KEY_REC, JSON.stringify(s));
  return s;
}
function saveRecords() { localStorage.setItem(KEY_REC, JSON.stringify(records)); }
const byDateDesc = (a, b) => b.tglFoto.localeCompare(a.tglFoto);

/* ---------- Util UI ---------- */
const ICONS = {
  home: '<path d="M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  check: '<path d="M20 6L9 17l-5-5"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  chat: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
};
const icon = (n) => `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[n]}</svg>`;

let toastTimer;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2600);
}

/* ---------- Komponen: penggaris usia tulang ---------- */
function rulerHTML(r) {
  const MAX = 216; // 18 tahun
  const pct = (m) => Math.max(0, Math.min(100, (m / MAX) * 100));
  const N = CONFIG.NORMAL_RANGE_MONTHS;
  const bandL = pct(Math.max(0, r.chronoMonths - N));
  const bandR = pct(r.chronoMonths + N);
  return `
  <div class="ruler" role="img" aria-label="Usia kronologis ${fmtAge(r.chronoMonths)}, usia tulang ${fmtAge(r.boneMonths)}">
    <div class="ruler-track">
      <div class="ruler-band" style="left:${bandL}%;width:${bandR - bandL}%"></div>
      <div class="pin chrono" style="left:${pct(r.chronoMonths)}%">Kronologis ${fmtAge(r.chronoMonths)}</div>
      <div class="pin bone below ${r.level}" style="left:${pct(r.boneMonths)}%">Usia tulang ${fmtAge(r.boneMonths)}</div>
    </div>
    <div class="ruler-scale"><span>0</span><span>3 th</span><span>6 th</span><span>9 th</span><span>12 th</span><span>15 th</span><span>18 th</span></div>
    <p class="ruler-legend">Pita hijau: rentang sesuai (±${N} bulan dari usia kronologis).</p>
  </div>`;
}

/* ---------- Komponen: kartu hasil ---------- */
function resultCard(r, forPatient = false) {
  const hidden = forPatient && !r.verified;
  const meta = `${esc(r.rm)}, ${r.jk === "L" ? "laki-laki" : "perempuan"}, foto diambil ${fmtDate(r.tglFoto)}`;
  const status = hidden
    ? '<span class="status pending">Menunggu verifikasi dokter</span>'
    : `<span class="status ${r.level}">${esc(r.title)}</span>`;
  const head = `<div class="result-head"><div><h2>${esc(r.nama)}</h2><p class="patient-meta">${meta}</p></div>${status}</div>`;

  if (hidden) {
    return `${head}
      <p style="margin-top:1rem">Hasil sedang ditinjau oleh dokter/radiolog dan akan tampil di sini setelah diverifikasi.</p>
      <div class="disclaimer">${DISCLAIMER}</div>`;
  }
  const d = r.diff;
  return `${head}
    <div class="stats">
      <div class="stat"><span>Usia kronologis</span><strong>${fmtAge(r.chronoMonths)}</strong></div>
      <div class="stat"><span>Usia tulang (bone age)</span><strong>${fmtAge(r.boneMonths)}</strong></div>
      <div class="stat"><span>Selisih</span><strong>${d > 0 ? "+" : ""}${fmtAge(d)}</strong></div>
    </div>
    ${rulerHTML(r)}
    <div class="message-box"><strong>${esc(r.title)}.</strong> ${esc(r.message)}</div>
    <p class="verify-note">${r.verified
      ? "Sudah diverifikasi dokter/radiolog." + (r.catatan ? " Catatan: " + esc(r.catatan) : "")
      : "Belum diverifikasi. Hasil ini hanya terlihat oleh petugas."}</p>
    <div class="disclaimer">${DISCLAIMER}</div>`;
}

/* ==========================================================
   LOGIN
   ========================================================== */
function renderLogin() {
  const demo = { chronoMonths: 108, boneMonths: 84, level: "watch" };
  const isP = loginRole === "pasien";
  $("#app").innerHTML = `
  <div class="login">
    <section class="login-hero">
      <div class="brand"><span class="brand-mark">B</span> BoneCare RSUD Haji</div>
      <div>
        <h1>Pahami hasil X&#8209;ray tulang tangan anak Anda.</h1>
        <p>Lihat perbandingan usia tulang dengan usia sebenarnya, riwayat pemeriksaan, dan tanyakan arti hasil ke asisten edukasi.</p>
        <div class="hero-ruler">${rulerHTML(demo).replace(/<p class="ruler-legend">.*?<\/p>/, "")}</div>
      </div>
      <p style="font-size:.8rem;margin:0">Alat bantu skrining awal. Bukan pengganti dokter.</p>
    </section>
    <section class="login-form-wrap">
      <form class="login-card" id="login-form" novalidate>
        <h2>Masuk</h2>
        <p class="sub">Pilih peran Anda untuk melanjutkan.</p>
        <div class="seg" role="group" aria-label="Peran">
          <button type="button" data-role="pasien" aria-pressed="${isP}">Pasien</button>
          <button type="button" data-role="petugas" aria-pressed="${!isP}">Petugas radiologi</button>
        </div>
        ${isP ? `
          <div class="field"><label for="rm">No. rekam medis</label><input id="rm" autocomplete="off" placeholder="RM-001001"></div>
          <div class="field"><label for="dob">Tanggal lahir pasien</label><input id="dob" type="date"></div>`
        : `
          <div class="field"><label for="staff">Nama petugas</label><input id="staff" autocomplete="off" placeholder="Nama lengkap"></div>`}
        <div class="error-text" id="login-error" role="alert"></div>
        <button class="btn block" type="submit">Masuk</button>
        <p class="demo-note">${isP
          ? "Mode demo. Coba No. RM <b>RM-001001</b> dengan tanggal lahir <b>12-03-2017</b>. Atau <b>RM-001002</b> / <b>05-06-2018</b> untuk melihat status menunggu verifikasi."
          : "Mode demo. Isi nama apa saja untuk masuk sebagai petugas."}</p>
      </form>
    </section>
  </div>`;

  document.querySelectorAll(".seg button").forEach((b) =>
    b.addEventListener("click", () => { loginRole = b.dataset.role; renderLogin(); }));
  $("#login-form").addEventListener("submit", onLogin);
}

function onLogin(e) {
  e.preventDefault();
  const err = $("#login-error");
  if (loginRole === "pasien") {
    const rm = $("#rm").value.trim().toUpperCase();
    const dob = $("#dob").value;
    const rec = records.find((r) => r.rm.toUpperCase() === rm && r.lahir === dob);
    if (!rm || !dob) { err.textContent = "Isi No. rekam medis dan tanggal lahir."; return; }
    if (!rec) { err.textContent = "No. rekam medis atau tanggal lahir tidak cocok. Periksa lagi."; return; }
    session = { role: "pasien", name: rec.nama, rm: rec.rm };
  } else {
    const name = $("#staff").value.trim();
    if (!name) { err.textContent = "Isi nama petugas."; return; }
    session = { role: "petugas", name };
  }
  localStorage.setItem(KEY_SES, JSON.stringify(session));
  view = null;
  renderShell();
}

function logout() {
  session = null; view = null; draft = null; draftFile = null;
  localStorage.removeItem(KEY_SES);
  renderLogin();
}

/* ==========================================================
   SHELL + NAVIGASI
   ========================================================== */
function navItems() {
  const pending = records.filter((r) => !r.verified).length;
  return session.role === "pasien"
    ? [
        { id: "home", label: "Beranda", ico: "home" },
        { id: "history", label: "Riwayat", ico: "clock" },
        { id: "chat", label: "Asisten", ico: "chat" }
      ]
    : [
        { id: "new", label: "Pemeriksaan baru", ico: "plus" },
        { id: "queue", label: "Antrean verifikasi", ico: "check", badge: pending },
        { id: "history", label: "Semua riwayat", ico: "clock" },
        { id: "chat", label: "Asisten", ico: "chat" }
      ];
}

function go(v) { view = v; renderShell(); window.scrollTo(0, 0); }

function renderShell() {
  const nav = navItems();
  if (!view || !nav.some((n) => n.id === view)) view = nav[0].id;

  $("#app").innerHTML = `
  <div class="shell">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">B</span><span>BoneCare<small>RSUD Haji</small></span></div>
      <nav class="nav" aria-label="Menu utama">
        ${nav.map((n) => `<button data-view="${n.id}" ${n.id === view ? 'aria-current="page"' : ""}>${icon(n.ico)}<span>${n.label}</span>${n.badge ? `<span class="badge">${n.badge}</span>` : ""}</button>`).join("")}
      </nav>
      <div class="sidebar-foot">
        <strong>${esc(session.name)}</strong>${session.role === "pasien" ? "Pasien" : "Petugas radiologi"}
        <br><button id="logout">Keluar</button>
      </div>
    </aside>
    <main id="main"></main>
  </div>`;

  document.querySelectorAll(".nav button").forEach((b) => b.addEventListener("click", () => go(b.dataset.view)));
  $("#logout").addEventListener("click", logout);

  const views = { home: viewHome, history: viewHistory, chat: viewChat, new: viewNew, queue: viewQueue };
  views[view]();
}

/* ==========================================================
   VIEW: PASIEN - BERANDA
   ========================================================== */
function myRecords() {
  return records.filter((r) => r.rm === session.rm).sort(byDateDesc);
}

function viewHome() {
  const mine = myRecords();
  const latestVerified = mine.find((r) => r.verified);
  const pending = mine.filter((r) => !r.verified).length;
  const first = session.name.split(" ")[0];

  $("#main").innerHTML = `
    <div class="page-head">
      <h1>Halo, ${esc(first)}</h1>
      <p>${latestVerified ? "Ini hasil pemeriksaan terbaru yang sudah diverifikasi dokter." : "Belum ada hasil yang bisa ditampilkan."}</p>
    </div>
    ${latestVerified
      ? `<section class="panel">${resultCard(latestVerified, true)}</section>`
      : `<section class="panel empty"><strong>Belum ada hasil terverifikasi</strong>Hasil akan muncul di sini setelah dokter/radiolog selesai memeriksa.</section>`}
    ${pending ? `<section class="panel"><span class="status pending">Menunggu verifikasi</span> <span style="margin-left:.4rem">${pending} pemeriksaan sedang ditinjau dokter.</span></section>` : ""}
    <section class="panel">
      <h3>Ada pertanyaan tentang hasil Anda?</h3>
      <p style="color:var(--muted);margin:.3rem 0 .9rem">Asisten edukasi bisa menjelaskan arti usia tulang dan arti status hasil.</p>
      <button class="btn secondary" onclick="go('chat')">Tanya asisten</button>
    </section>`;
}

/* ==========================================================
   VIEW: RIWAYAT (pasien: milik sendiri, petugas: semua)
   ========================================================== */
function viewHistory() {
  const isP = session.role === "pasien";
  const list = (isP ? myRecords() : [...records].sort(byDateDesc));

  const rows = list.map((r) => {
    const hide = isP && !r.verified;
    return `<tr>
      <td>${fmtDate(r.tglFoto)}</td>
      ${isP ? "" : `<td>${esc(r.nama)}<br><small style="color:var(--muted)">${esc(r.rm)}</small></td>`}
      <td>${fmtAge(r.chronoMonths)}</td>
      <td>${hide ? "-" : fmtAge(r.boneMonths)}</td>
      <td>${hide || (!isP && !r.verified)
          ? `<span class="status pending">${hide ? "Menunggu verifikasi" : "Belum diverifikasi"}</span>`
          : `<span class="status ${r.level}">${esc(r.title)}</span>`}</td>
      <td><button class="btn secondary small" onclick="openRecord('${r.id}')">Lihat</button></td>
    </tr>`;
  }).join("");

  $("#main").innerHTML = `
    <div class="page-head">
      <h1>${isP ? "Riwayat pemeriksaan" : "Semua riwayat"}</h1>
      <p>${isP ? "Semua hasil X-ray Anda, dari yang terbaru." : "Seluruh pemeriksaan yang tersimpan di sistem."}</p>
    </div>
    <section class="panel">
      ${list.length ? `<div class="table-wrap"><table>
        <thead><tr><th>Tanggal foto</th>${isP ? "" : "<th>Pasien</th>"}<th>Usia kronologis</th><th>Usia tulang</th><th>Status</th><th></th></tr></thead>
        <tbody>${rows}</tbody></table></div>`
      : `<div class="empty"><strong>Belum ada riwayat</strong>Pemeriksaan akan tercatat di sini.</div>`}
    </section>`;
}

/* ---------- Modal detail / verifikasi ---------- */
function openRecord(id) {
  const r = records.find((x) => x.id === id);
  if (!r) return;
  const isP = session.role === "pasien";
  const canVerify = !isP && !r.verified;

  const bg = document.createElement("div");
  bg.className = "modal-bg";
  bg.innerHTML = `<div class="modal" role="dialog" aria-modal="true">
    ${resultCard(r, isP)}
    ${canVerify ? `<div class="field" style="margin-top:1rem"><label for="note">Catatan dokter/radiolog (opsional)</label><input id="note" placeholder="Contoh: sesuai usia, kontrol rutin"></div>` : ""}
    <div class="modal-actions">
      <button class="btn secondary" id="m-close">Tutup</button>
      ${canVerify ? `<button class="btn" id="m-verify">Verifikasi dan tampilkan ke pasien</button>` : ""}
    </div></div>`;
  document.body.appendChild(bg);

  const close = () => { bg.remove(); document.removeEventListener("keydown", onKey); };
  const onKey = (e) => { if (e.key === "Escape") close(); };
  document.addEventListener("keydown", onKey);
  bg.addEventListener("click", (e) => { if (e.target === bg) close(); });
  $("#m-close").addEventListener("click", close);
  if (canVerify) {
    $("#m-verify").addEventListener("click", () => {
      r.verified = true;
      r.catatan = $("#note").value.trim();
      saveRecords(); close();
      toast("Diverifikasi. Hasil sekarang tampil di akun pasien.");
      renderShell();
    });
  }
  (canVerify ? $("#note") : $("#m-close")).focus();
}

/* ==========================================================
   VIEW: PETUGAS - PEMERIKSAAN BARU
   ========================================================== */
function viewNew() {
  $("#main").innerHTML = `
    <div class="page-head">
      <h1>Pemeriksaan baru</h1>
      <p>Unggah citra X-ray pergelangan tangan dan isi data pasien. Hasil masuk antrean verifikasi dulu sebelum bisa dilihat pasien.</p>
    </div>
    <form id="exam-form" class="panel" novalidate>
      <div class="row">
        <div class="field"><label for="f-nama">Nama pasien</label><input id="f-nama" autocomplete="off"></div>
        <div class="field"><label for="f-rm">No. rekam medis</label><input id="f-rm" placeholder="RM-001004" autocomplete="off"></div>
      </div>
      <div class="row">
        <div class="field"><label for="f-jk">Jenis kelamin</label>
          <select id="f-jk"><option value="L">Laki-laki</option><option value="P">Perempuan</option></select></div>
        <div class="field"><label for="f-lahir">Tanggal lahir</label><input id="f-lahir" type="date" max="${today()}"></div>
      </div>
      <div class="row">
        <div class="field"><label for="f-foto">Tanggal pengambilan foto X-ray</label><input id="f-foto" type="date" value="${today()}" max="${today()}"></div>
        <div class="field"><label for="f-bone">Usia tulang simulasi (bulan)</label><input id="f-bone" type="number" min="0" max="240" placeholder="Opsional">
          <span class="hint">Khusus demo. Kosongkan agar dibuat otomatis. Nanti diganti hasil analisis citra.</span></div>
      </div>
      <div class="field">
        <label for="file">Citra X-ray</label>
        <label class="dropzone" id="dz"><input type="file" id="file" accept="image/*"><span id="dz-text">Klik atau seret citra X-ray ke sini<br><small>Format JPG atau PNG</small></span></label>
      </div>
      <div class="error-text" id="exam-error" role="alert"></div>
      <button class="btn" type="submit">Analisis citra</button>
    </form>
    <div id="draft-result"></div>`;

  const dz = $("#dz"), fileInput = $("#file");
  const setFile = (f) => {
    if (!f || !f.type.startsWith("image/")) { $("#exam-error").textContent = "File harus berupa gambar (JPG atau PNG)."; return; }
    draftFile = f;
    $("#exam-error").textContent = "";
    $("#dz-text").innerHTML = `<img alt="Pratinjau citra X-ray" src="${URL.createObjectURL(f)}"><br><small>${esc(f.name)}</small>`;
  };
  fileInput.addEventListener("change", () => setFile(fileInput.files[0]));
  ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("drag"); }));
  ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("drag"); }));
  dz.addEventListener("drop", (e) => setFile(e.dataTransfer.files[0]));

  $("#exam-form").addEventListener("submit", analyze);
}

function analyze(e) {
  e.preventDefault();
  const err = $("#exam-error");
  const v = (id) => $(id).value.trim();
  const nama = v("#f-nama"), rm = v("#f-rm").toUpperCase(), lahir = v("#f-lahir"), foto = v("#f-foto");

  if (!nama || !rm || !lahir || !foto) { err.textContent = "Lengkapi nama, No. RM, tanggal lahir, dan tanggal foto."; return; }
  if (!draftFile) { err.textContent = "Pilih citra X-ray terlebih dahulu."; return; }
  const chrono = monthsBetween(lahir, foto);
  if (chrono < 0) { err.textContent = "Tanggal foto tidak boleh sebelum tanggal lahir."; return; }
  err.textContent = "";

  const sim = simulateAnalysis(draftFile.name, chrono, v("#f-bone"));
  draft = buildRecord({ rm, nama, jk: $("#f-jk").value, lahir, tglFoto: foto, boneMonths: sim.boneMonths, ratio: sim.ratio });

  $("#draft-result").innerHTML = `
    <section class="panel" style="margin-top:1rem">
      <p class="hint" style="margin-bottom:.8rem"><span class="status pending">Hasil simulasi</span> Rasio luas osifikasi karpal (dummy): ${draft.ratio}</p>
      ${resultCard(draft, false)}
      <div class="modal-actions"><button class="btn" id="save-draft">Simpan dan kirim ke verifikasi</button></div>
    </section>`;
  $("#save-draft").addEventListener("click", saveDraft);
  $("#draft-result").scrollIntoView({ behavior: "smooth", block: "start" });
}

function saveDraft() {
  if (!draft) return;
  records.unshift(draft);
  saveRecords();
  draft = null; draftFile = null;
  toast("Tersimpan. Menunggu verifikasi dokter/radiolog.");
  go("queue");
}

/* ==========================================================
   VIEW: PETUGAS - ANTREAN VERIFIKASI
   ========================================================== */
function viewQueue() {
  const list = records.filter((r) => !r.verified).sort(byDateDesc);
  $("#main").innerHTML = `
    <div class="page-head">
      <h1>Antrean verifikasi</h1>
      <p>Tinjau hasil analisis sebelum ditampilkan ke pasien.</p>
    </div>
    <section class="panel">
      ${list.length ? `<div class="table-wrap"><table>
        <thead><tr><th>Tanggal foto</th><th>Pasien</th><th>Hasil sistem</th><th></th></tr></thead>
        <tbody>${list.map((r) => `<tr>
          <td>${fmtDate(r.tglFoto)}</td>
          <td>${esc(r.nama)}<br><small style="color:var(--muted)">${esc(r.rm)}</small></td>
          <td><span class="status ${r.level}">${esc(r.title)}</span></td>
          <td><button class="btn small" onclick="openRecord('${r.id}')">Tinjau</button></td></tr>`).join("")}
        </tbody></table></div>`
      : `<div class="empty"><strong>Antrean kosong</strong>Semua hasil sudah diverifikasi.</div>`}
    </section>`;
}

/* ==========================================================
   VIEW: CHAT ASISTEN
   ========================================================== */
const CHIPS = ["Apa itu usia tulang?", "Apa arti hasil normal?", "Apa arti indikasi keterlambatan?", "Kapan harus ke dokter?", "Apakah ini pengganti dokter?"];

function bubble(who, text) {
  const d = document.createElement("div");
  d.className = "bubble " + who;
  d.textContent = text;
  return d;
}

function viewChat() {
  $("#main").innerHTML = `
    <div class="page-head">
      <h1>Asisten edukasi</h1>
      <p>Penjelasan umum tentang usia tulang dan hasil pemeriksaan.</p>
    </div>
    <section class="panel chat">
      <div class="chat-log" id="log" aria-live="polite"></div>
      <div class="chips">${CHIPS.map((c) => `<button class="chip" type="button">${esc(c)}</button>`).join("")}</div>
      <form class="chat-form" id="chat-form">
        <input id="chat-input" placeholder="Tulis pertanyaan Anda" autocomplete="off" aria-label="Pertanyaan">
        <button class="btn" type="submit">Kirim</button>
      </form>
      <p class="chat-foot">${DISCLAIMER} Untuk kondisi darurat, segera ke IGD.</p>
    </section>`;

  const log = $("#log");
  chatLog.forEach((m) => log.appendChild(bubble(m.who, m.text)));
  log.scrollTop = log.scrollHeight;

  const send = (text) => {
    text = text.trim();
    if (!text) return;
    chatLog.push({ who: "me", text });
    log.appendChild(bubble("me", text));
    log.scrollTop = log.scrollHeight;
    setTimeout(() => {
      const ans = botReply(text);
      chatLog.push({ who: "bot", text: ans });
      log.appendChild(bubble("bot", ans));
      log.scrollTop = log.scrollHeight;
    }, 450);
  };

  $("#chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const inp = $("#chat-input");
    send(inp.value);
    inp.value = "";
  });
  document.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => send(c.textContent)));
}

/* ---------- Mulai ---------- */
if (session) renderShell(); else renderLogin();
