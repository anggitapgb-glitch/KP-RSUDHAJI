(function () {
  function initHomeUI() {
    const input = document.getElementById("homeXrayFile");
    const dropzone = document.getElementById("homeDropzone");
    const preview = document.getElementById("homeFilePreview");
    const previewImage = document.getElementById("homePreviewImage");
    const fileName = document.getElementById("homeFileName");
    const fileSize = document.getElementById("homeFileSize");
    const title = document.getElementById("homeUploadTitle");
    const hint = document.getElementById("homeUploadHint");
    const testButton = document.getElementById("homeTestUpload");
    const message = document.getElementById("homeUploadMessage");
    if (!input || input.dataset.bound === "1") return;
    input.dataset.bound = "1";
    let selectedFile = null;
    let objectUrl = null;

    const notify = text => {
      if (window.showOssiaToast) window.showOssiaToast(text);
      else {
        let toast = document.querySelector(".om-toast");
        if (!toast) {
          toast = document.createElement("div");
          toast.className = "om-toast";
          document.body.appendChild(toast);
        }
        toast.textContent = text;
        toast.classList.add("show");
        clearTimeout(window.__omToastTimer);
        window.__omToastTimer = setTimeout(() => toast.classList.remove("show"), 2400);
      }
    };
    const formatSize = bytes => bytes < 1048576 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1048576).toFixed(1)} MB`;

    function resetFile() {
      selectedFile = null;
      input.value = "";
      preview.hidden = true;
      previewImage.removeAttribute("src");
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = null;
      title.textContent = "Pilih atau seret file X-ray";
      hint.textContent = "PNG atau JPG dari perangkatmu";
      testButton.disabled = true;
      message.textContent = "Pilih citra X-ray untuk memulai pemeriksaan.";
    }
    
    function handleFile(file) {
      if (!file) return;
      if (!["image/png", "image/jpeg"].includes(file.type)) {
        notify("Format file belum didukung. Pilih PNG atau JPG.");
        input.value = "";
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        notify("Ukuran file maksimal 10 MB.");
        input.value = "";
        return;
      }
      selectedFile = file;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = URL.createObjectURL(file);
      previewImage.src = objectUrl;
      fileName.textContent = file.name;
      fileSize.textContent = formatSize(file.size);
      preview.hidden = false;
      title.textContent = "File berhasil dipilih";
      hint.textContent = "Pratinjau siap diperiksa";
      testButton.disabled = false;
      message.textContent = "File X-ray berhasil dipilih dan siap diproses.";
    }

    input.addEventListener("change", () => {
      if (input.files && input.files[0]) {
        handleFile(input.files[0]);
      }
    });

    ["dragenter", "dragover"].forEach(name => dropzone?.addEventListener(name, e => {
      e.preventDefault(); dropzone.classList.add("dragging");
    }));
    
    ["dragleave", "drop"].forEach(name => dropzone?.addEventListener(name, e => {
      e.preventDefault(); dropzone.classList.remove("dragging");
    }));
    
    dropzone?.addEventListener("drop", e => {
      if (e.dataTransfer && e.dataTransfer.files[0]) {
        handleFile(e.dataTransfer.files[0]);
      }
    });
    
    document.getElementById("homeRemoveFile")?.addEventListener("click", resetFile);
    
    // ========================================
    // INTEGRASI BACKEND OSSIA - FLASK
    // ========================================
    testButton.addEventListener("click", async () => {
      if (!selectedFile) return;

      const formData = new FormData();
      formData.append("image", selectedFile);

      testButton.disabled = true;
      message.textContent = "Sedang memproses citra X-ray...";

      try {
        const response = await fetch("/api/analyze", {
          method: "POST",
          body: formData
        });

        const result = await response.json();

        if (!response.ok || result.ok !== true) {
          throw new Error(result.error || "Pemrosesan citra gagal.");
        }

        // Tampilkan teks ringkas hasil estimasi & kriteria klinis di bawah tombol
        message.textContent = 
          `Selesai! Estimasi: ${result.estimasi_tahun} Tahun (${result.estimasi_bulan} bln). ` +
          `Status: ${result.kriteria}.`;
        
        notify("Citra X-ray berhasil diproses dan diestimasi!");

        // --- PAKSA KOTAK RINGKASAN DI HOME BERUBAH SECARA DINAMIS ---
        const ringkasanCard = document.querySelector(".om-empty-results")?.closest(".om-card") || document.querySelector("div.om-section .om-card");
        if (ringkasanCard) {
            ringkasanCard.innerHTML = `
                <div style="padding: 6px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-size:11px; font-weight:700; color:#0a4f2b; background:#e5f5ec; padding:2px 8px; border-radius:6px;">BARU SAJA</span>
                        <span style="font-size:11px; color:#718279;">${selectedFile.name}</span>
                    </div>
                    <h4 style="font-size:1rem; color:#0a4f2b; margin:6px 0;">Estimasi Usia: ${result.estimasi_tahun} Tahun (${result.estimasi_bulan} bln)</h4>
                    <p style="font-size:0.8rem; color:#2c3e35; margin:4px 0;"><strong>Status Klinis:</strong> ${result.kriteria}</p>
                    <p style="font-size:0.75rem; color:#718279; margin:8px 0 0 0; line-height:1.4;"><em>${result.explanation}</em></p>
                </div>
            `;
        }

        // Simpan ke localStorage agar otomatis masuk ke halaman Riwayat
        try {
            let history = JSON.parse(localStorage.getItem("ossia_exam_history") || "[]");
            
            const newRecord = {
                id: "EX-" + Math.floor(Math.random() * 10000),
                dateISO: new Date().toISOString(),
                filename: selectedFile.name,
                threshold: result.threshold,
                foregroundRatio: result.foreground_ratio,
                status: result.kriteria, 
                explanation: result.explanation,
                estimasiTahun: result.estimasi_tahun,
                estimasiBulan: result.estimasi_bulan
            };
            
            history.unshift(newRecord);
            localStorage.setItem("ossia_exam_history", JSON.stringify(history));
        } catch (e) {
            console.log("Gagal menyimpan ke riwayat: ", e);
        }

      } catch (error) {
        console.error("OSSIA API Error:", error);
        message.textContent = `Gagal memproses X-ray: ${error.message}`;
        notify("Pemrosesan gagal. Periksa backend OSSIA.");
      } finally {
        testButton.disabled = !selectedFile;
      }
    });

    document.getElementById("homeNotifications")?.addEventListener("click", () => notify("Belum ada notifikasi baru."));
    document.getElementById("homeShowDetail")?.addEventListener("click", e => {
      const button = e.currentTarget;
      const panel = document.getElementById("homeResultExplanation");
      const open = button.getAttribute("aria-expanded") !== "true";
      button.setAttribute("aria-expanded", String(open));
      panel.hidden = !open;
    });
  }

  window.initHomeUI = initHomeUI;
  if (document.readyState !== "loading") initHomeUI();
  else document.addEventListener("DOMContentLoaded", initHomeUI);
})();