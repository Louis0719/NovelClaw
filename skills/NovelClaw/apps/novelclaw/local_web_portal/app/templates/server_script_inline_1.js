
  (function () {
    var started = false;

    function readPayload(response) {
      var contentType = response.headers.get('content-type') || '';
      if (contentType.indexOf('application/json') !== -1) {
        return response.json();
      }
      return response.text().then(function (raw) {
        return { ok: response.ok, error: raw || response.statusText || 'Request failed' };
      });
    }

    function installFallbackIdeaLive(root) {
      if (!root || root.dataset.ideaFallbackBound === '1') return false;
      var form = root.querySelector('[data-idea-reply-form]');
      var feed = root.querySelector('[data-idea-feed]');
      var statusNode = root.querySelector('[data-idea-status]');
      var textarea = form ? form.querySelector('textarea[name= reply]') : null;
      var submitBtn = form ? form.querySelector('button[type=submit]') : null;
      if (!form || !feed || !textarea || !submitBtn) return false;
      root.dataset.ideaFallbackBound = '1';

      function setStatus(kind, message) {
        if (!statusNode) return;
        if (!message) {
          statusNode.hidden = true;
          statusNode.textContent = '';
          statusNode.className = 'console-alert';
          return;
        }
        statusNode.hidden = false;
        statusNode.className = 'console-alert ' + (kind === 'error' ? 'error' : 'ok');
        statusNode.textContent = message;
      }

      function setBusy(isBusy) {
        textarea.disabled = isBusy;
        submitBtn.disabled = isBusy;
      }

      function appendPending() {
        if (feed.querySelector('[data-pending-row=1]')) return;
        feed.insertAdjacentHTML('beforeend', '<div class=chat-row assistant is-pending data-pending-row=1><div class=avatar-circle>WC</div><div class=assistant-panel><div class=assistant-section><div class=assistant-title>' + (root.dataset.labelAnalysisTitle || 'NovelClaw analysis') + '</div><div class=assistant-text typing-dots>' + (root.dataset.labelThinking || 'Thinking') + '</div></div></div></div>');
        feed.scrollTop = feed.scrollHeight;
      }

      function pollState() {
        var sessionId = root.dataset.sessionId || '';
        if (!sessionId) return;
        var timer = window.setInterval(function () {
          fetch(window.__appPath('/api/idea-copilot/' + sessionId + '/state?_=' + Date.now()), { headers: { Accept: 'application/json' }, cache: 'no-store' })
            .then(readPayload)
            .then(function (data) {
              if (!data || !data.ok) return;
              if (data.final_job_id) {
                window.clearInterval(timer);
                window.location.href = window.__appPath('/console/chat?session_id=' + encodeURIComponent(sessionId));
                return;
              }
              if (data.reply_pending) {
                appendPending();
                setStatus('ok', root.dataset.labelContinuing || 'NovelClaw is continuing...');
                return;
              }
              window.clearInterval(timer);
              window.location.href = window.__appPath('/console/chat?session_id=' + encodeURIComponent(sessionId));
            })
            .catch(function () {});
        }, 900);
      }

      form.addEventListener('submit', function (event) {
        event.preventDefault();
        var reply = String(textarea.value || '').trim();
        if (!reply) {
          setStatus('error', 'Reply cannot be empty');
          return;
        }
        var payload = new FormData(form);
        setBusy(true);
        setStatus('ok', '');
        feed.insertAdjacentHTML('beforeend', '<div class=chat-row user><div class=user-bubble></div><div class=user-tag>' + (root.dataset.labelYou || 'You') + '</div></div>');
        var bubble = feed.lastElementChild && feed.lastElementChild.querySelector('.user-bubble');
        if (bubble) bubble.textContent = reply;
        textarea.value = '';
        appendPending();
        fetch(form.action, {
          method: 'POST',
          body: payload,
          headers: { 'X-Requested-With': 'fetch', 'Accept': 'application/json' }
        })
          .then(readPayload)
          .then(function (data) {
            if (!data || !data.ok) throw new Error((data && (data.error || data.detail)) || 'Submit failed');
            setStatus('ok', root.dataset.labelContinuing || 'NovelClaw is continuing...');
            pollState();
          })
          .catch(function (error) {
            setBusy(false);
            setStatus('error', error && error.message ? error.message : 'Request failed');
          });
      });

      if (root.dataset.replyPending === 'true') {
        setBusy(true);
        appendPending();
        setStatus('ok', root.dataset.labelContinuing || 'NovelClaw is continuing...');
        pollState();
      }
      return true;
    }

    function start() {
      if (started) return true;
      
      var root = document.querySelector('[data-idea-copilot-root][data-layout=dashboard]');
      if (root && typeof window.initIdeaCopilotLive === 'function') {
        window.initIdeaCopilotLive(root);
        started = true;
        return true;
      }
      if (root && installFallbackIdeaLive(root)) {
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

