import asyncio
import json
import os
import threading
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================== الإعدادات ==================
API_ID = int(os.environ.get("API_ID", "3993099"))
API_HASH = os.environ.get("API_HASH", "7375b6b2163edc378d949480d066093e")
SOURCE_BOT_ID = os.environ.get("SOURCE_BOT_ID", "@Gg5677bot")
SESSION_STRING = os.environ.get("SESSION_STRING", "...")

DATA_FILE = "messages.json"
MAX_MESSAGES = 500

app = Flask(__name__)
lock = threading.Lock()

# ✅ إنشاء عميل Telethon في الخيط الرئيسي فقط
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ================== تحميل وحفظ ==================
def load_messages():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_messages(msgs):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)

messages = load_messages()
print(f"✅ تم تحميل {len(messages)} رسالة محفوظة")

# ================== واجهة HTML (نفس الكود السابق) ==================
# ... (اترك HTML_CODE كما هو) ...

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

# ✅ إرسال الرسالة - يعمل في الخيط الرئيسي (نفس خيط Telethon)
@app.route('/api/send', methods=['POST'])
def send_msg():
    global messages
    data = request.get_json(silent=True) or {}
    text = (data.get('text', '')).strip()
    if not text:
        return jsonify({"ok": False, "error": "نص فارغ"}), 400
    if len(text) > 4000:
        return jsonify({"ok": False, "error": "النص طويل جداً"}), 400

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

    # ✅ استدعاء متزامن (sync) من الخيط الرئيسي
    try:
        # يمكن استخدام client.send_message مباشرة في وضع sync
        client.send_message(SOURCE_BOT_ID, text)
        return jsonify({"ok": True})
    except Exception as e:
        print(f"❌ خطأ الإرسال: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# ================== استقبال رسائل البوت ==================
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

# ================== تشغيل Flask في خيط منفصل ==================
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

# ================== التشغيل الرئيسي ==================
if __name__ == '__main__':
    # ✅ تشغيل Flask في خيط daemon
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask بدأ على المنفذ:", os.environ.get("PORT", 10000))

    # ✅ Telethon يعمل في الخيط الرئيسي
    try:
        client.start()
        print("✅ البوت شغال — الحفظ في JSON مستمر")
        client.run_until_disconnected()
    except Exception as e:
        print(f"❌ خطأ Telegram: {e}")