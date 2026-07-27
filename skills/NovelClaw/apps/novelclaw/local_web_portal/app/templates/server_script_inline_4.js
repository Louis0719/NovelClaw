
    (function () {
      const key = "novelclaw.sidebar.collapsed";
      const body = document.body;
      const button = document.querySelector("[data-sidebar-toggle]");
      if (!button || !body.classList.contains("console-body")) return;
      function apply(collapsed) {
        body.classList.toggle("sidebar-collapsed", collapsed);
        button.setAttribute("aria-pressed", collapsed ? "true" : "false");
      }
      apply(window.localStorage.getItem(key) === "1");
      button.addEventListener("click", function () {
        const next = !body.classList.contains("sidebar-collapsed");
        apply(next);
        window.localStorage.setItem(key, next ? "1" : "0");
      });
    })();
  
