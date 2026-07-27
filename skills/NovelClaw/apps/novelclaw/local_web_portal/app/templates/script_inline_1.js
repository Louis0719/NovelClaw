
  (function () {
    var started = false;
    function start() {
      if (started) return true;
      
      var root = document.querySelector('[data-idea-copilot-root][data-layout="dashboard"]');
      if (root && typeof window.initIdeaCopilotLive === 'function') {
        window.initIdeaCopilotLive(root);
        started = true;
        return true;
      }
      
      
      return false;
    }

    if (start()) return;
    var tries = 0;
    var timer = window.setInterval(function () {
      tries += 1;
      if (start() || tries >= 20) {
        window.clearInterval(timer);
      }
    }, 250);
    window.addEventListener('load', start, { once: true });
    document.addEventListener('DOMContentLoaded', start, { once: true });
  })();
