#!/usr/bin/env python3
"""
来财AI客服 - 网页版 v2.0
优化点：
1. 💬 快捷回复按钮（点击即发）
2. 🌙 暗色主题切换
3. 📊 经营驾驶舱可视化卡片
4. 💡 引导提示（空状态）
5. 📱 移动端适配优化
6. 🔔 消息状态（发送中/已发送）
"""

import sys, os, webbrowser, time, threading
from werkzeug.serving import make_server
from flask import Flask, render_template_string, request, jsonify
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, APP_DIR)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# ====== 快捷按钮配置 ======
QUICK_REPLIES = {
    "常用": [
        {"label": "🔍 查价格", "text": "60s天丝多少钱"},
        {"label": "📦 查库存", "text": "60s天丝有货吗"},
        {"label": "🛒 我要下单", "text": "我要订一批货"},
        {"label": "📋 我的订单", "text": "我的订单"},
    ],
    "经营": [
        {"label": "📊 经营日报", "text": "今日经营情况"},
        {"label": "🚚 物流查询", "text": "DD-20250501-001物流"},
        {"label": "🏭 生产进度", "text": "DD-20250501-001进度"},
        {"label": "📦 库存预警", "text": "库存需要补货吗"},
    ],
    "帮助": [
        {"label": "📖 使用帮助", "text": "帮助"},
        {"label": "👑 VIP申请", "text": "VIP申请"},
        {"label": "🌟 爆款推荐", "text": "有什么爆款推荐"},
    ]
}

# ====== HTML模板 v2 ======
HTML_V2 = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>来财AI客服 v2.0</title>
<style>
  :root {
    --bg-primary: #f0f2f5;
    --bg-header: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    --bg-card: #ffffff;
    --bg-input: #ffffff;
    --text-primary: #1a1a2e;
    --text-secondary: #666;
    --text-muted: #999;
    --accent: #1890ff;
    --accent-hover: #1677ff;
    --border: #eee;
    --shadow: 0 1px 3px rgba(0,0,0,0.1);
    --radius: 12px;
    --user-bubble: #1890ff;
    --bot-bubble: #ffffff;
    --user-text: #ffffff;
    --bot-text: #333;
  }

  .dark {
    --bg-primary: #1a1a2e;
    --bg-header: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
    --bg-card: #252542;
    --bg-input: #2a2a4a;
    --text-primary: #f0f0f0;
    --text-secondary: #aaa;
    --text-muted: #777;
    --border: #3a3a5a;
    --shadow: 0 1px 3px rgba(0,0,0,0.3);
    --user-bubble: #3a8aff;
    --bot-bubble: #2a2a4a;
    --bot-text: #e0e0e0;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Microsoft YaHei", sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    height: 100vh;
    display: flex;
    flex-direction: column;
    transition: background 0.3s, color 0.3s;
  }

  /* === 顶部 === */
  .header {
    background: var(--bg-header);
    color: white;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }
  .header h1 { font-size: 17px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
  .header .subtitle { font-size: 11px; opacity: 0.65; }
  .header-right { display: flex; align-items: center; gap: 12px; }
  .status-dot { width: 8px; height: 8px; background: #4ade80; border-radius: 50%; display: inline-block; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  .theme-toggle {
    background: rgba(255,255,255,0.15);
    border: none;
    color: white;
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 12px;
    cursor: pointer;
    transition: background 0.2s;
  }
  .theme-toggle:hover { background: rgba(255,255,255,0.25); }

  /* === 快捷按钮 === */
  .quick-bar {
    background: var(--bg-card);
    border-bottom: 1px solid var(--border);
    padding: 10px 12px;
    overflow-x: auto;
    flex-shrink: 0;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .quick-bar::-webkit-scrollbar { display: none; }
  .quick-group { display: inline-flex; align-items: center; gap: 6px; margin-right: 12px; }
  .quick-group-label { font-size: 10px; color: var(--text-muted); margin-right: 2px; }
  .quick-btn {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    padding: 5px 12px;
    border-radius: 16px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
  }
  .quick-btn:hover, .quick-btn:active {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
    transform: scale(0.97);
  }

  /* === 聊天区 === */
  .chat-container {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    scroll-behavior: smooth;
  }
  .message {
    max-width: 78%;
    padding: 9px 13px;
    border-radius: var(--radius);
    font-size: 14px;
    line-height: 1.65;
    white-space: pre-wrap;
    word-break: break-word;
    animation: fadeIn 0.2s ease;
    position: relative;
  }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
  .message.user {
    align-self: flex-end;
    background: var(--user-bubble);
    color: var(--user-text);
    border-bottom-right-radius: 4px;
  }
  .message.bot {
    align-self: flex-start;
    background: var(--bot-bubble);
    color: var(--bot-text);
    border-bottom-left-radius: 4px;
    box-shadow: var(--shadow);
  }
  .message.system {
    align-self: center;
    background: #fffbe6;
    color: #ad6800;
    font-size: 12px;
    text-align: center;
    max-width: 90%;
    border-radius: 8px;
  }
  .msg-status {
    font-size: 10px;
    opacity: 0.6;
    margin-top: 2px;
    text-align: right;
  }

  /* === 空状态引导 === */
  .empty-state {
    text-align: center;
    padding: 50px 20px;
    color: var(--text-muted);
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .empty-state .emoji { font-size: 48px; margin-bottom: 16px; }
  .empty-state h3 { color: var(--text-secondary); margin-bottom: 8px; font-size: 16px; }
  .empty-state p { font-size: 13px; line-height: 1.7; }

  /* === 底部输入 === */
  .input-area {
    background: var(--bg-card);
    border-top: 1px solid var(--border);
    padding: 10px 14px;
    display: flex;
    gap: 8px;
    align-items: flex-end;
    flex-shrink: 0;
  }
  .input-area textarea {
    flex: 1;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 9px 11px;
    font-size: 14px;
    resize: none;
    outline: none;
    min-height: 42px;
    max-height: 110px;
    font-family: inherit;
    background: var(--bg-input);
    color: var(--text-primary);
    transition: border-color 0.2s;
  }
  .input-area textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(24,144,255,0.15);
  }
  .send-btn {
    background: var(--accent);
    color: white;
    border: none;
    padding: 9px 18px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background 0.2s, transform 0.1s;
  }
  .send-btn:hover { background: var(--accent-hover); }
  .send-btn:active { transform: scale(0.97); }
  .send-btn:disabled { background: #d9d9d9; cursor: not-allowed; transform: none; }

  /* === 加载动画 === */
  .loading { display: flex; gap: 4px; align-items: center; padding: 10px 14px; }
  .loading span { width: 6px; height: 6px; background: var(--text-muted); border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
  .loading span:nth-child(1){ animation-delay: -0.32s; }
  .loading span:nth-child(2){ animation-delay: -0.16s; }
  @keyframes bounce { 0%,80%,100%{transform:scale(0)} 40%{transform:scale(1)} }

  /* === 仪表盘卡片 === */
  .dashboard-card {
    background: var(--bot-bubble);
    border-radius: var(--radius);
    padding: 12px;
    margin: 4px 0;
    box-shadow: var(--shadow);
  }
  .dashboard-card h4 { font-size: 13px; color: var(--accent); margin-bottom: 8px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
  .dashboard-card .stat-row { display: flex; justify-content: space-between; padding: 3px 0; font-size: 13px; }
  .dashboard-card .stat-label { color: var(--text-secondary); }
  .dashboard-card .stat-value { font-weight: 600; }
  .trend-up { color: #52c41a; }
  .trend-down { color: #ff4d4f; }
  .trend-flat { color: var(--text-muted); }

  /* === 响应式 === */
  @media (max-width: 480px) {
    .header h1 { font-size: 15px; }
    .message { max-width: 85%; }
    .quick-bar { padding: 8px 10px; }
    .header .subtitle { display: none; }
  }
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>🧵 来财AI客服 <span style="font-size:11px;opacity:0.6">v2.0</span></h1>
    <div class="subtitle">叠石桥面料行业智能助手</div>
  </div>
  <div class="header-right">
    <span class="status-dot"></span>
    <button class="theme-toggle" onclick="toggleTheme()" id="themeBtn">🌙 深色</button>
  </div>
</div>

<!-- 快捷按钮栏 -->
<div class="quick-bar" id="quickBar">
</div>

<!-- 聊天区 -->
<div class="chat-container" id="chatContainer">
  <div class="empty-state" id="emptyState">
    <div class="emoji">🧵</div>
    <h3>来财AI客服 v2.0</h3>
    <p>我可以帮您查产品、查库存、下订单<br>经营分析、订单跟进...随时找我！</p>
  </div>
</div>

<!-- 输入区 -->
<div class="input-area">
  <textarea id="msgInput" placeholder="输入消息，Enter 发送..." rows="1" onkeydown="handleKey(event)"></textarea>
  <button class="send-btn" id="sendBtn" onclick="sendMsg()">发送</button>
</div>

<script>
// ====== 主题切换 ======
function toggleTheme() {
  document.body.classList.toggle('dark');
  const btn = document.getElementById('themeBtn');
  btn.textContent = document.body.classList.contains('dark') ? '☀️ 浅色' : '🌙 深色';
  localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
}
(function(){
  if(localStorage.getItem('theme')==='dark'){
    document.body.classList.add('dark');
    document.getElementById('themeBtn').textContent='☀️ 浅色';
  }
})();

// ====== 快捷按钮 ======
const quickReplies = {{ quick_replies | tojson }};
(function buildQuickBar(){
  const bar = document.getElementById('quickBar');
  for(const [group, btns] of Object.entries(quickReplies)){
    const gDiv = document.createElement('div');
    gDiv.className = 'quick-group';
    gDiv.innerHTML = `<span class="quick-group-label">${group}</span>`;
    btns.forEach(b => {
      const btn = document.createElement('button');
      btn.className = 'quick-btn';
      btn.textContent = b.label;
      btn.onclick = () => send(b.text);
      gDiv.appendChild(btn);
    });
    bar.appendChild(gDiv);
  }
})();

// ====== 聊天 ======
let loadingDiv = null;
let msgCount = 0;

function scrollBottom(){
  const c = document.getElementById('chatContainer');
  c.scrollTop = c.scrollHeight;
}

function hideEmpty(){
  const e = document.getElementById('emptyState');
  if(e) e.remove();
}

function addMsg(text, type, status){
  hideEmpty();
  const container = document.getElementById('chatContainer');
  const div = document.createElement('div');
  div.className = 'message ' + type;
  // 支持简单的仪表盘卡片渲染
  if(text.includes('━━━') && type==='bot'){
    div.innerHTML = formatDashboard(text);
  } else {
    div.innerHTML = text.replace(/\n/g, '<br>');
  }
  if(status){
    const s = document.createElement('div');
    s.className = 'msg-status';
    s.textContent = status;
    div.appendChild(s);
  }
  container.appendChild(div);
  scrollBottom();
}

function formatDashboard(text){
  // 简单处理仪表盘卡片格式
  return text.replace(/━━━━━━━━━━━━━━/g, '<div style="border-top:1px solid var(--border);margin:6px 0"></div>')
    .replace(/📈|📉|➡️|🔥|⚫|⚠️|🚚|⏰|🔬/g, m => `<span style="font-size:13px">${m}</span>`);
}

function addLoading(){
  const container = document.getElementById('chatContainer');
  hideEmpty();
  loadingDiv = document.createElement('div');
  loadingDiv.className = 'message bot loading';
  loadingDiv.innerHTML = '<span></span><span></span><span></span>';
  container.appendChild(loadingDiv);
  scrollBottom();
}

function removeLoading(){
  if(loadingDiv){ loadingDiv.remove(); loadingDiv=null; }
}

async function send(text){
  const input = document.getElementById('msgInput');
  if(!text) text = input.value.trim();
  if(!text) return;
  addMsg(text, 'user', '发送中...');
  input.value = '';
  const btn = document.getElementById('sendBtn');
  btn.disabled = true;
  addLoading();
  try{
    const resp = await fetch('/api/chat', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({message: text, session_id: '{{ session_id }}'})
    });
    const data = await resp.json();
    removeLoading();
    addMsg(data.reply || '（无响应）', 'bot');
  } catch(e){
    removeLoading();
    addMsg('⚠️ 网络错误，请检查服务器是否运行中', 'bot');
  }
  btn.disabled = false;
  input.focus();
}

function sendMsg(){ send(''); }

function handleKey(e){
  if(e.key==='Enter' && !e.shiftKey){
    e.preventDefault();
    sendMsg();
  }
}
</script>
</body>
</html>
'''

# ====== API路由 ======
@app.route('/')
def index():
    session_id = request.cookies.get('session_id', '')
    if not session_id:
        session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:16]
    return render_template_string(HTML_V2,
        quick_replies=QUICK_REPLIES,
        session_id=session_id)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    msg = data.get('message', '').strip()
    session_id = data.get('session_id', 'default')
    if not msg:
        return jsonify({'reply': '请输入内容'})
    try:
        # 优先使用 v2 引擎
        try:
            from agent_v2 import process as process_v2
            reply = process_v2(msg, session_id)
        except ImportError:
            from agent_extended import process
            reply = process(msg)
    except Exception as e:
        reply = f"⚠️ 系统错误：{e}"
    return jsonify({'reply': reply})

# ====== 启动 ======
def open_browser():
    time.sleep(1.2)
    webbrowser.open('http://localhost:5188')

if __name__ == '__main__':
    PORT = 5188
    print("=" * 44)
    print("  🧵 来财AI客服 v2.0 - 网页版")
    print("=" * 44)
    print(f"  启动中... http://localhost:{PORT}")
    print("  快捷按钮 | 暗色主题 | 仪表盘展示")
    print("  按 Ctrl+C 停止服务器")
    print("=" * 44)
    threading.Thread(target=open_browser, daemon=True).start()
    server = make_server('127.0.0.1', PORT, app)
    server.serve_forever()
