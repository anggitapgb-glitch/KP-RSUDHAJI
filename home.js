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

    input.addEventListener("change", () => handleFile(input.files[0]));
    ["dragenter", "dragover"].forEach(name => dropzone?.addEventListener(name, e => {
      e.preventDefault(); dropzone.classList.add("dragging");
    }));
    ["dragleave", "drop"].forEach(name => dropzone?.addEventListener(name, e => {
      e.preventDefault(); dropzone.classList.remove("dragging");
    }));
    dropzone?.addEventListener("drop", e => handleFile(e.dataTransfer.files[0]));
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
        // Mengirim citra ke backend OSSIA
        const response = await fetch("/api/analyze", {
          method: "POST",
          body: formData
        });

        // Membaca respons dari Flask
        const result = await response.json();

        if (!response.ok || result.ok !== true) {
          throw new Error(
            result.error || "Pemrosesan citra gagal."
          );
        }

        // Mengambil hasil preprocessing Otsu
        const threshold = result.threshold ?? "-";
        const status = result.status || "Perlu verifikasi";

        // Menampilkan informasi teknis di Home
        message.textContent =
          `Pemrosesan citra selesai. ` +
          `Threshold Otsu: ${threshold}. ` +
          `Status teknis: ${status}. ` +
          `Hasil ini bukan penilaian klinis.`;

        notify("Citra X-ray berhasil diproses oleh OSSIA!");

        console.log("Hasil preprocessing OSSIA:", {
          threshold,
          foreground_ratio: result.foreground_ratio,
          status
        });

      } catch (error) {
        console.error("OSSIA API Error:", error);

        message.textContent =
          `Gagal memproses X-ray: ${error.message}`;

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
