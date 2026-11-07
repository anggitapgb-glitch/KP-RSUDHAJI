/* ==========================================================
   chatbot.js : asisten edukasi (berbasis kata kunci)
   Hanya edukasi umum, TIDAK mendiagnosis.
   Nanti bisa diganti memanggil API (mis. Cloudflare Worker).
   ========================================================== */

// Urutan array = prioritas. Topik darurat harus paling atas.
const BOT_TOPICS = [
  { keys: ["darurat", "nyeri hebat", "sesak", "pingsan", "demam tinggi"],
    answer: "Jika ada nyeri hebat, sesak napas, pingsan, atau gejala berat lainnya, segera menuju IGD atau fasilitas kesehatan terdekat. Asisten ini tidak bisa menangani kondisi darurat." },
  { keys: ["pengganti dokter", "tanpa dokter", "tidak perlu dokter", "diagnosis"],
    answer: "Sistem ini bukan pengganti dokter. Fungsinya membantu Anda memahami hasil lebih awal dan menandai kondisi yang perlu diperiksa lebih lanjut. Keputusan medis tetap ada pada dokter." },
  { keys: ["biaya", "bpjs", "bayar", "mahal", "gratis"],
    answer: "Untuk informasi biaya dan penggunaan BPJS, silakan tanyakan ke loket pendaftaran atau bagian informasi RSUD Haji. Asisten ini tidak punya data tarif." },
  { keys: ["verifikasi", "menunggu", "belum muncul"],
    answer: "Hasil baru tampil setelah diverifikasi dokter/radiolog. Jika statusnya masih \"Menunggu verifikasi\", mohon tunggu atau tanyakan ke petugas radiologi." },
  { keys: ["lebih maju", "lebih cepat"],
    answer: "Usia tulang yang lebih maju dari usia sebenarnya juga perlu dibahas dengan dokter. Penyebabnya beragam dan perlu dinilai bersama data tinggi badan, berat badan, dan riwayat anak." },
  { keys: ["terlambat", "keterlambatan", "stunting", "tertinggal"],
    answer: "Status \"Indikasi Keterlambatan\" berarti usia tulang tertinggal cukup jauh dari usia sebenarnya. Ini hanya tanda awal, bukan diagnosis. Penyebabnya bisa beragam, misalnya gizi atau hormon, dan hanya dokter yang bisa menentukannya. Segera jadwalkan konsultasi ke dokter anak." },
  { keys: ["normal", "sesuai"],
    answer: "Status \"Normal / Sesuai Pertumbuhan\" berarti selisih usia tulang dan usia sebenarnya masih dalam batas yang ditetapkan. Ini bukan jaminan bebas penyakit. Jika ada keluhan, tetap konsultasikan ke dokter." },
  { keys: ["bone age", "usia tulang", "umur tulang"],
    answer: "Usia tulang (bone age) menunjukkan seberapa matang tulang seorang anak, dilihat dari foto X-ray pergelangan tangan. Angkanya dibandingkan dengan usia sebenarnya (usia kronologis) untuk melihat apakah pertumbuhan tulang sesuai." },
  { keys: ["data", "privasi", "aman", "keamanan"],
    answer: "Data pemeriksaan adalah data pribadi yang sensitif. Pada sistem yang sesungguhnya, akses dibatasi dengan login dan data hanya dipakai untuk layanan dan penelitian dengan izin yang sesuai." },
  { keys: ["konsultasi", "dokter", "kapan"],
    answer: "Sebaiknya konsultasi bila hasil bertanda \"Perlu Dipantau\" atau \"Indikasi\", bila anak tampak lebih pendek atau lebih lambat tumbuh dari teman seusianya, atau bila ada keluhan lain." },
  { keys: ["halo", "hai", "pagi", "siang", "sore", "malam"],
    answer: "Halo! Saya asisten edukasi BoneCare. Silakan tanya seputar arti usia tulang atau arti status hasil pemeriksaan." }
];

const BOT_FALLBACK =
  "Maaf, saya belum bisa menjawab itu. Saya hanya membantu penjelasan umum tentang usia tulang dan arti hasil pemeriksaan. Untuk pertanyaan medis pribadi, silakan hubungi dokter atau petugas RSUD Haji.";

function botReply(text) {
  const q = text.toLowerCase();
  for (const t of BOT_TOPICS) {
    if (t.keys.some(k => q.includes(k))) return t.answer;
  }
  return BOT_FALLBACK;
}
