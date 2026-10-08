(() => {
  const search = document.getElementById("appSearch");
  const cards = Array.from(document.querySelectorAll(".app-card"));
  const empty = document.getElementById("emptySearch");
  const toast = document.getElementById("toast");
  const mobileMenu = document.getElementById("mobileMenu");
  const sideNav = document.getElementById("sideNav");
  const overlay = document.getElementById("navOverlay");

  let toastTimer = null;

  const flashToasts = Array.from(
    document.querySelectorAll(".toast-flash.show")
  );

  flashToasts.forEach((flashToast) => {
    window.setTimeout(() => {
      flashToast.classList.remove("show");
      window.setTimeout(() => flashToast.remove(), 280);
    }, 3200);
  });

  const successFlashes = Array.from(
    document.querySelectorAll(".flash.success")
  );

  successFlashes.forEach((flashMessage) => {
    window.setTimeout(() => {
      flashMessage.style.transition = "opacity .25s ease, transform .25s ease";
      flashMessage.style.opacity = "0";
      flashMessage.style.transform = "translateY(-4px)";
      window.setTimeout(() => flashMessage.remove(), 280);
    }, 3600);
  });

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

  // O sino abre uma central acessível; nenhum aviso fictício é criado.
  // As informações da aba Sistema são derivadas dos aplicativos do tenant ativo.
  const notificationTrigger = document.getElementById("notificationsTrigger");
  const notificationPanel = document.getElementById("notificationsPanel");
  const notificationClose = document.getElementById("notificationsClose");
  const notificationTabs = Array.from(document.querySelectorAll("[data-notification-tab]"));
  const notificationPanels = Array.from(document.querySelectorAll("[data-notification-panel]"));

  if (notificationTrigger && notificationPanel) {
    const updateSystemSummary = () => {
      const registered = document.getElementById("notificationsAppsTotal");
      const configured = document.getElementById("notificationsAppsConfigured");
      const maintenance = document.getElementById("notificationsAppsMaintenance");
      if (registered) registered.textContent = String(cards.length);
      if (configured) configured.textContent = String(cards.filter((card) => !card.classList.contains("app-disabled")).length);
      if (maintenance) maintenance.textContent = String(cards.filter((card) => card.querySelector(".status-maintenance")).length);
    };

    const positionNotifications = () => {
      if (notificationPanel.hidden) return;
      const trigger = notificationTrigger.getBoundingClientRect();
      const width = notificationPanel.offsetWidth;
      const left = Math.max(12, Math.min(trigger.right - width, window.innerWidth - width - 12));
      const top = Math.max(8, Math.min(trigger.bottom + 10, window.innerHeight - 130));
      notificationPanel.style.left = left + "px";
      notificationPanel.style.top = top + "px";
      notificationPanel.style.maxHeight = Math.max(100, window.innerHeight - top - 12) + "px";
    };

    const selectNotificationsTab = (category, focusTab = false) => {
      let selected = null;
      notificationTabs.forEach((tab) => {
        const active = tab.dataset.notificationTab === category;
        tab.setAttribute("aria-selected", String(active));
        tab.tabIndex = active ? 0 : -1;
        if (active) selected = tab;
      });
      notificationPanels.forEach((panel) => {
        panel.hidden = panel.dataset.notificationPanel !== category;
      });
      if (focusTab && selected) selected.focus();
    };

    const closeNotifications = (returnFocus = false) => {
      if (notificationPanel.hidden) return;
      notificationPanel.hidden = true;
      notificationTrigger.setAttribute("aria-expanded", "false");
      notificationTrigger.setAttribute("aria-label", "Abrir central de notificações");
      if (returnFocus) notificationTrigger.focus();
    };

    const openNotifications = () => {
      closeMenu();
      updateSystemSummary();
      notificationPanel.hidden = false;
      notificationTrigger.setAttribute("aria-expanded", "true");
      notificationTrigger.setAttribute("aria-label", "Fechar central de notificações");
      positionNotifications();
      notificationPanel.focus({ preventScroll: true });
    };

    notificationTrigger.addEventListener("click", () => {
      if (notificationPanel.hidden) openNotifications();
      else closeNotifications(true);
    });
    notificationClose?.addEventListener("click", () => closeNotifications(true));

    document.querySelectorAll("[data-open-notifications]").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        openNotifications();
      });
    });

    notificationTabs.forEach((tab, index) => {
      tab.addEventListener("click", () => selectNotificationsTab(tab.dataset.notificationTab));
      tab.addEventListener("keydown", (event) => {
        if (!["ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        let next = index;
        if (event.key === "ArrowRight") next = (index + 1) % notificationTabs.length;
        if (event.key === "ArrowLeft") next = (index - 1 + notificationTabs.length) % notificationTabs.length;
        if (event.key === "Home") next = 0;
        if (event.key === "End") next = notificationTabs.length - 1;
        selectNotificationsTab(notificationTabs[next].dataset.notificationTab, true);
      });
    });

    document.addEventListener("pointerdown", (event) => {
      if (notificationPanel.hidden) return;
      if (!notificationPanel.contains(event.target) && !notificationTrigger.contains(event.target)) closeNotifications();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !notificationPanel.hidden) {
        event.preventDefault();
        closeNotifications(true);
      }
    });
    window.addEventListener("resize", positionNotifications);
    document.addEventListener("scroll", positionNotifications, true);
  }
})();
