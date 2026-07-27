
function toggleBriefEdit(btn) {
  var form = document.getElementById('brief-edit-form');
  if (!form) return;
  var isOpen = form.classList.contains('is-open');
  form.classList.toggle('is-open', !isOpen);
  if (!isOpen) {
    var ta = document.getElementById('brief-edit-text');
    var current = document.querySelector('[data-refined-idea]');
    if (ta && current) ta.value = current.textContent.trim();
    if (ta) ta.focus();
  }
}
async function saveBrief(sessionId) {
  var ta = document.getElementById('brief-edit-text');
  var status = document.getElementById('brief-edit-status');
  if (!ta) return;
  var val = ta.value.trim();
  if (!val) { if (status) { status.textContent = '内容不能为空'; status.className = 'inline-status err'; } return; }
  if (status) { status.textContent = '保存中...'; status.className = 'inline-status'; }
  try {
    var resp = await fetch(window.__appPath('/api/idea-copilot/' + sessionId + '/brief'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ brief: val })
    });
    var data = await resp.json();
    if (!resp.ok || !data.ok) throw new Error(data.detail || data.error || 'Save failed');
    document.querySelectorAll('[data-refined-idea]').forEach(function(el) { el.textContent = data.refined_idea; });
    if (status) { status.textContent = '已保存'; status.className = 'inline-status ok'; }
    setTimeout(function() { var f = document.getElementById('brief-edit-form'); if (f) f.classList.remove('is-open'); }, 900);
  } catch (e) {
    if (status) { status.textContent = e.message || 'Error'; status.className = 'inline-status err'; }
  }
}
