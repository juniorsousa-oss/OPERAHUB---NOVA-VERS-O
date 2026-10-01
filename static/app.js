(() => {
  const search = document.getElementById("appSearch");
  const cards = Array.from(document.querySelectorAll(".app-card"));
  const empty = document.getElementById("emptySearch");
  const toast = document.getElementById("toast");
  const mobileMenu = document.getElementById("mobileMenu");
  const sideNav = document.getElementById("sideNav");
  const overlay = document.getElementById("navOverlay");

  let toastTimer = null;

  const showToast = (message) => {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 2200);
  };

  document.querySelectorAll("[data-unconfigured='true']").forEach((el) => {
    el.addEventListener("click", (event) => {
      event.preventDefault();
      showToast("Configure o link deste módulo em Configurações.");
    });
  });

  if (search) {
    search.addEventListener("input", () => {
      const term = search.value.trim().toLowerCase();
      let visible = 0;

      cards.forEach((card) => {
        const haystack = card.dataset.search || "";
        const match = !term || haystack.includes(term);
        card.style.display = match ? "" : "none";
        if (match) visible += 1;
      });

      if (empty) empty.hidden = visible !== 0;
    });
  }

  const closeMenu = () => {
    sideNav?.classList.remove("open");
    overlay?.classList.remove("show");
  };

  mobileMenu?.addEventListener("click", () => {
    sideNav?.classList.toggle("open");
    overlay?.classList.toggle("show");
  });

  overlay?.addEventListener("click", closeMenu);

  window.addEventListener("resize", () => {
    if (window.innerWidth > 860) closeMenu();
  });
})();
