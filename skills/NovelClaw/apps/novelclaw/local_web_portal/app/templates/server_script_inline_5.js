
    (function () {
      const roots = Array.from(document.querySelectorAll(".console-sidebar .console-nav-label, .console-sidebar .console-nav-item span:last-child, .console-sidebar .console-nav-drawer-summary > span:first-child"));
      if (!roots.length) return;
      const storageKey = "novelclaw.custom_sidebar_labels";
      const isZh = String(document.documentElement.lang || "").toLowerCase().startsWith("zh");
      let saved = {};
      try {
        saved = JSON.parse(window.localStorage.getItem(storageKey) || "{}") || {};
      } catch (_) {
        saved = {};
      }

      function labelKey(node, index) {
        if (node.dataset.userLabelKey) return node.dataset.userLabelKey;
        const link = node.closest(".console-nav-item");
        if (link && link.getAttribute("href")) return `href:${link.getAttribute("href")}`;
        return `text:${index}`;
      }

      function helpText(name) {
        return isZh ? `淇敼鏍囩锛?{name}\n鐣欑┖鎭㈠榛樿` : `Rename label: ${name}\nLeave empty to reset`;
      }

      function applyLabels() {
        roots.forEach((node, index) => {
          const key = labelKey(node, index);
          const fallback = node.dataset.userLabelDefault || node.textContent.trim();
          if (!node.dataset.userLabelDefault) node.dataset.userLabelDefault = fallback;
          const custom = typeof saved[key] === "string" ? saved[key].trim() : "";
          node.textContent = custom || fallback;
          node.title = isZh ? "鍙屽嚮鍗冲彲鏀瑰悕锛岀暀绌烘仮澶嶉粯璁? : "Double-click to rename. Leave empty to reset.";
        });
      }

      function rename(node, index) {
        const key = labelKey(node, index);
        const fallback = node.dataset.userLabelDefault || node.textContent.trim();
        const current = (typeof saved[key] === "string" ? saved[key].trim() : "") || fallback;
        const next = window.prompt(helpText(fallback), current);
        if (next === null) return;
        const cleaned = String(next).trim();
        if (cleaned) saved[key] = cleaned;
        else delete saved[key];
        window.localStorage.setItem(storageKey, JSON.stringify(saved));
        applyLabels();
      }

      roots.forEach((node, index) => {
        node.addEventListener("dblclick", function (event) {
          event.preventDefault();
          event.stopPropagation();
          rename(node, index);
        });
      });

      applyLabels();
    })();
  
