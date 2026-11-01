(() => {
  const narrow = window.matchMedia("(max-width: 1000px)");
  const workspace = document.querySelector(".workspace");
  const sidebar = document.getElementById("sidebar");
  const toggle = document.getElementById("sidebarToggle");
  const close = document.getElementById("sidebarClose");
  const header = document.querySelector(".mobile-header");
  const content = document.querySelector(".content-pane");
  let open = false;

  function setOpen(value) {
    open = narrow.matches && value;
    const hadSidebarFocus = sidebar.contains(document.activeElement);
    workspace.classList.toggle("sidebar-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    header.inert = open;
    content.inert = open;
    sidebar.inert = narrow.matches && !open;
    if (open) {
      sidebar.removeAttribute("aria-hidden");
      sidebar.setAttribute("role", "dialog");
      sidebar.setAttribute("aria-modal", "true");
      close.focus({ preventScroll: true });
    } else {
      sidebar.removeAttribute("role");
      sidebar.removeAttribute("aria-modal");
      if (narrow.matches && hadSidebarFocus) toggle.focus({ preventScroll: true });
      else if (!narrow.matches && document.activeElement === close) document.getElementById("homeButton").focus({ preventScroll: true });
      if (narrow.matches) sidebar.setAttribute("aria-hidden", "true");
      else sidebar.removeAttribute("aria-hidden");
    }
  }

  toggle.addEventListener("click", () => setOpen(!open));
  close.addEventListener("click", () => setOpen(false));
  document.getElementById("sidebarBackdrop").addEventListener("click", () => setOpen(false));
  document.addEventListener("manager:navigated", () => { if (open) setOpen(false); });
  narrow.addEventListener("change", () => setOpen(false));
  document.addEventListener("keydown", (event) => {
    if (!open || document.querySelector("dialog[open]")) return;
    if (event.key === "Escape") {
      event.preventDefault();
      event.stopImmediatePropagation();
      setOpen(false);
    } else if (event.key === "Tab") {
      const items = [...sidebar.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled), [tabindex="0"]')]
        .filter(item => item.tabIndex >= 0 && item.getClientRects().length);
      const first = items[0], last = items.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus();
      }
    }
  }, true);
  setOpen(false);
})();
