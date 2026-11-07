/* ==========================================================
   logic.js : perhitungan usia & aturan skrining (rule-based)
   ========================================================== */

// PENTING: ambang batas ini HARUS dikonfirmasi bersama dokter radiologi / dokter anak.
const CONFIG = {
  NORMAL_RANGE_MONTHS: 12,    // |bone age - usia kronologis| <= 12 bulan = sesuai pertumbuhan
  DELAY_THRESHOLD_MONTHS: 24  // bone age tertinggal > 24 bulan = indikasi keterlambatan
};

const DISCLAIMER =
  "Hasil ini adalah alat bantu skrining awal, bukan diagnosis dan bukan pengganti pemeriksaan dokter.";

/** Selisih bulan penuh antara dua tanggal (format YYYY-MM-DD). */
function monthsBetween(fromStr, toStr) {
  const a = new Date(fromStr), b = new Date(toStr);
  let m = (b.getFullYear() - a.getFullYear()) * 12 + (b.getMonth() - a.getMonth());
  if (b.getDate() < a.getDate()) m--;
  return m;
}

/** 113 -> "9 th 5 bln" */
function fmtAge(months) {
  const neg = months < 0;
  const m = Math.abs(months);
  const y = Math.floor(m / 12), r = m % 12;
  const parts = [];
  if (y) parts.push(`${y} th`);
  if (r || !y) parts.push(`${r} bln`);
  return (neg ? "-" : "") + parts.join(" ");
}

/** 2026-08-20 -> 20 Agu 2026 */
function fmtDate(str) {
  return new Date(str).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
}

/** Aturan peringatan. level: normal | watch | alert */
function classify(chronoMonths, boneMonths) {
  const diff = boneMonths - chronoMonths;
  const { NORMAL_RANGE_MONTHS: N, DELAY_THRESHOLD_MONTHS: D } = CONFIG;

  if (Math.abs(diff) <= N) {
    return { level: "normal", diff, title: "Normal / Sesuai Pertumbuhan",
      message: "Usia tulang berada dalam rentang yang sesuai dengan usia kronologis." };
  }
  if (diff < -D) {
    return { level: "alert", diff, title: "Indikasi Keterlambatan Pertumbuhan",
      message: "Usia tulang tertinggal jauh dari usia kronologis. Disarankan konsultasi ke dokter anak atau dokter spesialis terkait." };
  }
  if (diff < -N) {
    return { level: "watch", diff, title: "Perlu Dipantau",
      message: "Usia tulang sedikit tertinggal dari usia kronologis. Disarankan membahasnya dengan dokter." };
  }
  return { level: "watch", diff, title: "Usia Tulang Lebih Maju",
    message: "Usia tulang lebih maju dari usia kronologis. Disarankan membahasnya dengan dokter." };
}

/* ----------------------------------------------------------
   MODUL ANALISIS CITRA (SIMULASI)
   Nanti ganti fungsi ini dengan hasil analisis rasio luas
   osifikasi tulang karpal yang sebenarnya (model / backend).
   ---------------------------------------------------------- */
function hashString(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
}

function simulateAnalysis(fileName, chronoMonths, overrideBone) {
  let bone;
  if (overrideBone !== null && overrideBone !== "" && !isNaN(overrideBone)) {
    bone = Math.max(0, Math.round(Number(overrideBone)));
  } else {
    const offset = (hashString(fileName) % 45) - 30; // -30 .. +14 bulan (dummy)
    bone = Math.max(0, chronoMonths + offset);
  }
  // rasio luas osifikasi karpal (dummy, hanya untuk tampilan)
  const ratio = Math.min(0.95, 0.05 + (bone / 216) * 0.9);
  return { boneMonths: bone, ratio: Math.round(ratio * 1000) / 1000 };
}

/** Bentuk 1 record lengkap dari input + hasil analisis. */
function buildRecord({ rm, nama, jk, lahir, tglFoto, boneMonths, ratio, verified = false, catatan = "" }) {
  const chronoMonths = monthsBetween(lahir, tglFoto);
  const c = classify(chronoMonths, boneMonths);
  return {
    id: "ex-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    rm, nama, jk, lahir, tglFoto, chronoMonths, boneMonths, ratio,
    diff: c.diff, level: c.level, title: c.title, message: c.message,
    verified, catatan, createdAt: new Date().toISOString()
  };
}
