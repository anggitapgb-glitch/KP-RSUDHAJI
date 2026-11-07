(() => {
  "use strict";

  const track = document.getElementById("slides");

  const dots = Array.from(
    document.querySelectorAll("[data-slide]")
  );

  const loginButtons = Array.from(
    document.querySelectorAll("[data-go-login]")
  );

  let scrollTimer = null;

  /*
   * Memperbarui indikator titik sesuai slide aktif.
   */
  function setActiveSlide(index) {
    if (!dots.length) return;

    const safeIndex = Math.max(
      0,
      Math.min(index, dots.length - 1)
    );

    dots.forEach((dot, dotIndex) => {
      const active = dotIndex === safeIndex;

      dot.classList.toggle("is-active", active);
      dot.setAttribute("aria-pressed", String(active));
    });
  }

  /*
   * Berpindah ke slide tertentu.
   */
  function goToSlide(index) {
    if (!track || !dots.length) return;

    const safeIndex = Math.max(
      0,
      Math.min(index, dots.length - 1)
    );

    track.scrollTo({
      left: safeIndex * track.clientWidth,
      behavior: "smooth"
    });

    setActiveSlide(safeIndex);
  }

  /*
   * Navigasi menggunakan titik indikator.
   */
  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      const index = Number(dot.dataset.slide);

      if (Number.isInteger(index)) {
        goToSlide(index);
      }
    });
  });

  /*
   * Memperbarui titik saat pengguna swipe.
   */
  if (track) {
    track.addEventListener(
      "scroll",
      () => {
        window.clearTimeout(scrollTimer);

        scrollTimer = window.setTimeout(() => {
          const index = Math.round(
            track.scrollLeft /
            Math.max(track.clientWidth, 1)
          );

          setActiveSlide(index);
        }, 60);
      },
      { passive: true }
    );

    /*
     * Navigasi keyboard.
     */
    track.addEventListener("keydown", (event) => {
      const index = Math.round(
        track.scrollLeft /
        Math.max(track.clientWidth, 1)
      );

      if (event.key === "ArrowRight") {
        event.preventDefault();
        goToSlide(index + 1);
      }

      if (event.key === "ArrowLeft") {
        event.preventDefault();
        goToSlide(index - 1);
      }
    });
  }

  /*
   * Fungsi untuk membuka halaman login.
   */
  function openLogin() {
    // Kondisi 1: dipanggil dari index.html langsung.
    if (typeof window.openOssiaPage === "function") {
      window.openOssiaPage("login.html");
      return;
    }

    // Kondisi 2: landing.html berada di dalam iframe index.html.
    try {
      if (
        window.parent !== window &&
        typeof window.parent.openOssiaPage === "function"
      ) {
        window.parent.openOssiaPage("login.html");
        return;
      }
    } catch (error) {
      console.warn(
        "Fungsi navigasi induk tidak dapat diakses.",
        error
      );
    }

    // Kondisi 3: landing.html dibuka secara langsung.
    window.location.assign(
      new URL("./login.html", document.baseURI).href
    );
  }

  /*
   * Tombol Mulai Sekarang di semua slide.
   */
  loginButtons.forEach((button) => {
    button.addEventListener("click", openLogin);
  });

  /*
   * Atur indikator awal.
   */
  window.addEventListener("pageshow", () => {
    if (track && track.scrollLeft === 0) {
      setActiveSlide(0);
    }
  });

  setActiveSlide(0);
})();