#!/usr/bin/env python3
"""
来财AI客服 - 网页版启动器
客户双击此文件即可运行，打开浏览器访问 http://localhost:5188
"""
import sys, os, webbrowser, time, threading
from werkzeug.serving import make_server
from flask import Flask, render_template_string, request, jsonify

# 路径设置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(BASE_DIR)  # laicai-biz/
DB = os.path.join(BASE_DIR, "db", "laicai.db")
sys.path.insert(0, APP_DIR)  # 让 system.tools.query 能正确导入

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# ====== HTML模板 ======
HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>来财AI客服</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Microsoft YaHei", sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }
  
  /* 顶部标题 */
  .header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; }
  .header h1 { font-size: 18px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
  .header .subtitle { font-size: 12px; opacity: 0.7; }
  .status-dot { width: 8px; height: 8px; background: #4ade80; border-radius: 50%; display: inline-block; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
  
  /* 聊天区域 */
  .chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
  .message { max-width: 75%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
  .message.user { align-self: flex-end; background: #1890ff; color: white; border-bottom-right-radius: 4px; }
  .message.bot { align-self: flex-start; background: white; color: #333; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .message.system { align-self: center; background: #fffbe6; color: #ad6800; font-size: 12px; text-align: center; max-width: 90%; }
  .timestamp { font-size: 11px; color: #999; margin-top: 4px; text-align: right; }
  
  /* 欢迎页 */
  .welcome { text-align: center; padding: 40px 20px; color: #666; }
  .welcome h2 { color: #1a1a2e; margin-bottom: 16px; font-size: 20px; }
  .welcome p { margin: 8px 0; font-size: 14px; }
  .quick-reply { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 20px; }
  .quick-btn { background: white; border: 1px solid #ddd; padding: 8px 16px; border-radius: 20px; font-size: 13px; cursor: pointer; transition: all 0.2s; }
  .quick-btn:hover { background: #1890ff; color: white; border-color: #1890ff; }
  
  /* 底部输入区 */
  .input-area { background: white; padding: 12px 16px; border-top: 1px solid #eee; display: flex; gap: 10px; align-items: flex-end; }
  .input-area textarea { flex: 1; border: 1px solid #d9d9d9; border-radius: 8px; padding: 10px 12px; font-size: 14px; resize: none; outline: none; min-height: 44px; max-height: 120px; font-family: inherit; }
  .input-area textarea:focus { border-color: #1890ff; box-shadow: 0 0 0 2px rgba(24,144,255,0.2); }
  .send-btn { background: #1890ff; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; transition: background 0.2s; }
  .send-btn:hover { background: #1677ff; }
  .send-btn:disabled { background: #d9d9d9; cursor: not-allowed; }
  
  /* 加载动画 */
  .loading { display: flex; gap: 4px; align-items: center; padding: 10px 14px; }
  .loading span { width: 6px; height: 6px; background: #999; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
  .loading span:nth-child(1) { animation-delay: -0.32s; }
  .loading span:nth-child(2) { animation-delay: -0.16s; }
  @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>🧵 来财AI客服</h1>
    <div class="subtitle">叠石桥面料行业智能助手</div>
  </div>
  <div><span class="status-dot"></span> 在线</div>
</div>

<div class="chat-container" id="chatContainer">
  <div class="welcome">
    <h2>👋 欢迎使用来财AI客服</h2>
    <p>我可以帮您：查产品、查库存、下订单、查进度...</p>
    <div class="quick-reply">
      <button class="quick-btn" onclick="send('60s天丝多少钱')">查价格</button>
      <button class="quick-btn" onclick="send('FC-001有货吗')">查库存</button>
      <button class="quick-btn" onclick="send('今日经营情况')">经营日报</button>
      <button class="quick-btn" onclick="send('怎么用')">使用帮助</button>
    </div>
  </div>
</div>

<div class="input-area">
  <textarea id="msgInput" placeholder="输入消息，按 Enter 发送..." rows="1" onkeydown="handleKey(event)"></textarea>
  <button class="send-btn" id="sendBtn" onclick="sendMsg()">发送</button>
</div>

<script>
let loadingDiv = null;

function scrollBottom() {
  const c = document.getElementById('chatContainer');
  c.scrollTop = c.scrollHeight;
}

function addMsg(text, type) {
  const container = document.getElementById('chatContainer');
  const div = document.createElement('div');
  div.className = 'message ' + type;
  div.innerHTML = text.replace(/\n/g, '<br>');
  container.appendChild(div);
  scrollBottom();
}

function addLoading() {
  const container = document.getElementById('chatContainer');
  loadingDiv = document.createElement('div');
  loadingDiv.className = 'message bot loading';
  loadingDiv.innerHTML = '<span></span><span></span><span></span>';
  container.appendChild(loadingDiv);
  scrollBottom();
}

function removeLoading() {
  if (loadingDiv) { loadingDiv.remove(); loadingDiv = null; }
}

async function send(text) {
  const input = document.getElementById('msgInput');
  const btn = document.getElementById('sendBtn');
  if (!text) { text = input.value.trim(); if (!text) return; }
  addMsg(text, 'user');
  input.value = '';
  btn.disabled = true;
  addLoading();
  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text})
    });
    const data = await resp.json();
    removeLoading();
    addMsg(data.reply, 'bot');
  } catch(e) {
    removeLoading();
    addMsg('⚠️ 网络错误，请检查服务器是否运行中', 'bot');
  }
  btn.disabled = false;
  input.focus();
}

function sendMsg() { send(''); }

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
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
    return render_template_string(HTML)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    msg = data.get('message', '').strip()
    if not msg:
        return jsonify({'reply': '请输入内容'})
    
    try:
        # 调用AI客服核心
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
    print("=" * 40)
    print("  🧵 来财AI客服 - 网页版")
    print("=" * 40)
    print(f"  启动中... http://localhost:{PORT}")
    print("  按 Ctrl+C 停止服务器")
    print("=" * 40)
    threading.Thread(target=open_browser, daemon=True).start()
    server = make_server('127.0.0.1', PORT, app)
    server.serve_forever()
