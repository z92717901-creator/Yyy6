import asyncio
import json
import os
import threading
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================== 📋 الإعدادات (من متغيرات البيئة) ==================
API_ID = int(os.environ.get("API_ID", "3993099"))
API_HASH = os.environ.get("API_HASH", "7375b6b2163edc378d949480d066093e")
SOURCE_BOT_ID = os.environ.get("SOURCE_BOT_ID", "@Gg5677bot")
SESSION_STRING = os.environ.get("SESSION_STRING", "1ApWapzMBu7unu6O4wHY30mW1plFpKZOSTWLTCsgJyFyjYa1UwxSTAODTNmqQNxQfaNW71TLIxHySeorVvEPr31JbtdXyTp6i4ZDcvi0hBAa5a3lQYunvw9O5mPalQieos18iCZAKL44u5pWR7v6sMOqsYiBx-C9mC9x7tRClkEQXAFHRqpc_IsaE_5bCCx5NmVNZLMJtibeIUyrzFNDiBXFO67wUTTwmomaAJ2gx8rGxIcf4SJQhzq_dfSDDFIcttffXSr5bs1g2RKBRk3AqdTp6HHXPsEp5UuVihlbryYo9tKMp9x0n3Fl4Qai1K7CWXvgKP80WpS-h5OXWLTh3qP3twyei1sU=")

DATA_FILE = "messages.json"
MAX_MESSAGES = 500

app = Flask(__name__)
lock = threading.Lock()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH, loop=loop)

# ================== 📦 تحميل وحفظ الرسائل ==================
def load_messages():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطأ تحميل: {e}")
            return []
    return []

def save_messages(msgs):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)

messages = load_messages()
print(f"✅ تم تحميل {len(messages)} رسالة محفوظة")

# ================== 🌐 واجهة الموقع (نفس كودك مع تحسينات) ==================
HTML_CODE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>💧 محطة نبع الصويرة</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Segoe UI',Tahoma,Arial,sans-serif;background:#f0f9ff;color:#334155;}
header{background:linear-gradient(135deg,#0ea5e9,#0284c7);color:#fff;text-align:center;padding:18px;position:sticky;top:0;z-index:100;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
header h1{font-size:20px;}
.status-bar{text-align:center;padding:6px;font-size:12px;color:#64748b;background:#f8fafc;border-bottom:1px solid #e2e8f0;}
#messages{max-width:700px;margin:15px auto;padding:0 12px;padding-bottom:90px;display:flex;flex-direction:column;gap:12px;min-height:350px;}
.msg{background:#fff;padding:12px 15px;border-radius:18px 18px 18px 4px;max-width:85%;align-self:flex-start;box-shadow:0 1px 3px rgba(0,0,0,0.06);line-height:1.5;}
.msg.me{background:#0ea5e9;color:#fff;border-radius:18px 18px 4px 18px;align-self:flex-end;}
.msg-meta{font-size:11px;margin-bottom:4px;opacity:0.7;}
.msg.me .msg-meta{color:#e0f2fe;}
.msg-text{white-space:pre-wrap;word-break:break-word;}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}
.bot-btn{background:#f0f9ff;color:#0284c7;border:1px solid #bae6fd;padding:8px 14px;border-radius:20px;cursor:pointer;font-size:14px;transition:0.2s;}
.bot-btn:hover{background:#0ea5e9;color:#fff;}
#input-area{position:fixed;bottom:0;left:0;right:0;background:#fff;padding:12px;box-shadow:0 -2px 10px rgba(0,0,0,0.05);}
.input-row{max-width:700px;margin:0 auto;display:flex;gap:8px;}
#msg-input{flex:1;padding:12px 15px;border:1px solid #cbd5e1;border-radius:25px;font-size:15px;outline:none;}
#msg-input:focus{border-color:#0ea5e9;}
#send-btn{background:#0ea5e9;color:#fff;border:none;padding:12px 20px;border-radius:25px;cursor:pointer;font-weight:bold;}
#send-btn:disabled{background:#94a3b8;cursor:not-allowed;}
.welcome{text-align:center;padding:40px 20px;color:#64748b;}
</style>
</head>
<body>
<header><h1>💧 محطة نبع الصويرة</h1></header>
<div class="status-bar" id="status">جاري التحميل...</div>
<div id="messages"><div class="welcome">👋 أهلاً بك! جميع رسائلك محفوظة دائماً ✅</div></div>
<div id="input-area">
  <div class="input-row">
    <input type="text" id="msg-input" placeholder="اكتب رسالتك هنا...">
    <button id="send-btn" onclick="sendMessage()">إرسال</button>
  </div>
</div>

<script>
let lastCount = -1;
let sending = false;

async function loadMessages(){
  try{
    const res = await fetch('/api/messages');
    const msgs = await res.json();
    document.getElementById('status').innerText = `✅ محفوظ — ${msgs.length} رسالة`;
    
    if(msgs.length === lastCount) return;
    lastCount = msgs.length;
    
    const container = document.getElementById('messages');
    container.innerHTML = '';
    
    if(msgs.length === 0){
      container.innerHTML = '<div class="welcome">👋 لا توجد رسائل حتى الآن. اكتب رسالة لتبدأ ✅</div>';
    } else {
      msgs.forEach(m=>{
        const d = document.createElement('div');
        d.className = 'msg' + (m.is_me ? ' me' : '');
        let html = '<div class="msg-meta">' + (m.is_me ? '👤 أنت' : '💧 البوت') + ' • ' + (m.time||'') + '</div>';
        if(m.text) html += '<div class="msg-text">' + escapeHtml(m.text) + '</div>';
        if(m.buttons && m.buttons.length>0){
          html += '<div class="btns">';
          m.buttons.forEach(btn=>{
            html += '<button class="bot-btn" onclick="sendByButton(\\''+btn.replace(/'/g,"\\\\'")+'\\')">'+escapeHtml(btn)+'</button>';
          });
          html += '</div>';
        }
        d.innerHTML = html;
        container.appendChild(d);
      });
    }
    window.scrollTo(0, document.body.scrollHeight);
  }catch(e){
    document.getElementById('status').innerHTML = '<span style="color:red">❌ خطأ في الاتصال</span>';
  }
}

async function sendByButton(text){
  document.getElementById('msg-input').value = text;
  await sendMessage();
}

async function sendMessage(){
  if(sending) return;
  const input = document.getElementById('msg-input');
  const btn = document.getElementById('send-btn');
  const text = input.value.trim();
  if(!text) return;
  
  sending = true;
  btn.disabled = true;
  input.value = '';
  
  try{
    const res = await fetch('/api/send',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text:text})
    });
    const data = await res.json();
    if(!data.ok) alert('❌ فشل الإرسال');
  }catch(e){
    alert('❌ فشل الاتصال');
  } finally {
    sending = false;
    btn.disabled = false;
  }
  setTimeout(loadMessages, 800);
}

function escapeHtml(t){
  const div = document.createElement('div');
  div.textContent = t;
  return div.innerHTML;
}

document.getElementById('msg-input').addEventListener('keydown',e=>{
  if(e.key==='Enter') sendMessage();
});

setInterval(loadMessages, 1500);
loadMessages();
</script>
</body>
</html>
"""

# ================== 🔌 واجهات API ==================
@app.route('/')
def index():
    return render_template_string(HTML_CODE)

@app.route('/health')
def health():
    return jsonify({"ok": True, "count": len(messages)})

@app.route('/api/messages')
def get_msgs():
    with lock:
        return jsonify(messages[-MAX_MESSAGES:])

@app.route('/api/send', methods=['POST'])
def send_msg():
    global messages
    data = request.get_json(silent=True) or {}
    text = (data.get('text','')).strip()
    if not text:
        return jsonify({"ok":False, "error":"نص فارغ"}), 400
    if len(text) > 4000:
        return jsonify({"ok":False, "error":"النص طويل جداً"}), 400
    
    new_msg = {
        "text": text,
        "is_me": True,
        "buttons": [],
        "time": datetime.now().strftime("%H:%M:%S")
    }
    
    with lock:
        messages.append(new_msg)
        if len(messages) > MAX_MESSAGES:
            messages = messages[-MAX_MESSAGES:]
        save_messages(messages)
    
    async def _send():
        try:
            await asyncio.wait_for(client.send_message(SOURCE_BOT_ID, text), timeout=15)
        except Exception as e:
            print(f"❌ خطأ الإرسال: {e}")
            raise
    
    try:
        future = asyncio.run_coroutine_threadsafe(_send(), loop)
        future.result(timeout=20)
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({"ok":False, "error":str(e)}), 500

# ================== 📥 استقبال رسائل البوت ==================
@client.on(events.NewMessage(from_users=SOURCE_BOT_ID))
async def on_msg(event):
    global messages
    text = event.raw_text or ""
    buttons = []
    if event.message.buttons:
        try:
            buttons = [btn.text for row in event.message.buttons for btn in row if btn.text]
        except:
            pass
    
    new_msg = {
        "text": text,
        "is_me": False,
        "buttons": buttons,
        "time": datetime.now().strftime("%H:%M:%S")
    }
    
    with lock:
        messages.append(new_msg)
        if len(messages) > MAX_MESSAGES:
            messages = messages[-MAX_MESSAGES:]
        save_messages(messages)
    
    print(f"📥 حفظ: {text[:40]}")

# ================== 🚀 التشغيل ==================
def start_tg():
    async def run():
        try:
            await client.start()
            print("✅ البوت شغال — الحفظ في JSON مستمر ✅")
            await client.run_until_disconnected()
        except Exception as e:
            print(f"❌ خطأ Telegram: {e}")
    
    loop.run_until_complete(run())

if __name__ == '__main__':
    threading.Thread(target=start_tg, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)