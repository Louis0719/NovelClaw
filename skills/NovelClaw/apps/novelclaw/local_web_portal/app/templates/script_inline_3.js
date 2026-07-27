
    window.__APP_BASE_PATH__ = "";
    window.__appPath = function (path) {
      var base = String(window.__APP_BASE_PATH__ || "");
      var raw = String(path || "");
      if (!raw) return base || "";
      if (/^[a-z]+:\/\//i.test(raw)) return raw;
      if (!raw.startsWith("/")) raw = "/" + raw;
      if (base && (raw === base || raw.startsWith(base + "/"))) return raw;
      return (base || "") + raw;
    };
  