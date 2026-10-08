import os
import json
import asyncio
import subprocess
import glob
import threading
from datetime import datetime, timedelta
from flask import Flask, request, render_template_string, jsonify
from telethon import TelegramClient

app = Flask(__name__)

status_logs = []
is_running = False

def log(msg):
    print(msg)
    status_logs.append(msg)

def get_firefox_profile():
    appdata = os.getenv('APPDATA')
    if not appdata: return None
    profiles_path = os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles')
    if not os.path.exists(profiles_path): return None
    profiles = glob.glob(os.path.join(profiles_path, '*default-release*'))
    if profiles: return profiles[0]
    profiles = glob.glob(os.path.join(profiles_path, '*default*'))
    if profiles: return profiles[0]
    return None

API_ID = '37147534'
API_HASH = '1b22a18d3c5f04409b1f11952b165197'

def run_automation_sync(channel_id, max_videos):
    global is_running
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_automation(channel_id, max_videos))
    except Exception as e:
        log(f"❌ حدث خطأ غير متوقع: {str(e)}")
    finally:
        is_running = False
        log("\n✅ [النظام]: البوت متوقف الآن وبانتظار أمر جديد.")

async def run_automation(channel_id, max_videos):
    log("🚀 بدء أداة سحب الفيديوهات والرفع المجدول على يوتيوب...")
    output_dir = "Telegram_Downloads"
    os.makedirs(output_dir, exist_ok=True)
    
    # إعدادات الجدولة

    profile_path = get_firefox_profile()
    if profile_path:
        log("🦊 تم العثور على بروفايل فايرفوكس لتخطي التسجيل.")
    else:
        log("⚠️ لم يتم العثور على بروفايل فايرفوكس.")

    client = TelegramClient('bridge_session', API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        log("❌ خطأ: الحساب غير مسجل الدخول.")
        return

    processed_count = 0
    try:
        if isinstance(channel_id, str) and channel_id.lstrip('-').isdigit():
            channel_id = int(channel_id)

        async for message in client.iter_messages(channel_id, reverse=True):
            if message.video:
                log(f"\n🎥 تم العثور على فيديو: {message.id}")
                
                video_path = os.path.abspath(os.path.join(output_dir, f"video_{message.id}.mp4"))
                meta_path = os.path.abspath(os.path.join(output_dir, f"meta_{message.id}.json"))
                
                log("⬇️ جاري تنزيل الفيديو...")
                await message.download_media(file=video_path)
                
                text = message.text or ""
                lines = text.strip().split('\n')
                
                if lines and lines[0].strip():
                    title = lines[0].strip()[:100]
                    description = '\n'.join(lines[1:]).strip()
                else:
                    title = f"فيديو من تيليجرام {message.id}"
                    description = ""
                    
                tags = [word[1:] for word in text.split() if word.startswith("#")]
                meta = { "title": title, "description": description, "tags": tags }
                import json
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=4)
                log("?? ??????? ????? ???????")
                if profile_path:
                    cmd = f'cd youtube_uploader_selenium && python upload.py --video "{video_path}" --meta "{meta_path}" --profile "{profile_path}"'
                else:
                    cmd = f'cd youtube_uploader_selenium && python upload.py --video "{video_path}" --meta "{meta_path}"'
                
                try:
                    subprocess.run(cmd, shell=True, check=True)
                    log("✅ اكتمل الرفع (وتمت جدولته) ليوتيوب بنجاح!")
                    log("🧹 تنظيف الملفات المؤقتة لتوفير المساحة...")
                    if os.path.exists(video_path): os.remove(video_path)
                    if os.path.exists(meta_path): os.remove(meta_path)
                except subprocess.CalledProcessError:
                    log("❌ حدث خطأ في أداة الرفع الخاصة بيوتيوب.")
                    break 
                
                processed_count += 1
                if max_videos > 0 and processed_count >= max_videos:
                    log(f"\n🎯 تم الانتهاء من جلب ورفع {max_videos} فيديوهات بنجاح!")
                    break
                
                log("⏳ انتظار 3 ثوانٍ فقط قبل الفيديو التالي...")
                await asyncio.sleep(3)
    except Exception as e:
        log(f"❌ خطأ أثناء العملية: {str(e)}")
    finally:
        await client.disconnect()

HTML_PAGE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>لوحة الأتمتة: تيليجرام ➡️ يوتيوب</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #1f2937; }
        ::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 4px; }
    </style>
</head>
<body class="bg-gray-100 p-4 md:p-10 font-sans">
    <div class="max-w-4xl mx-auto bg-white p-6 md:p-8 rounded-xl shadow-2xl">
        <h1 class="text-3xl font-extrabold text-center text-blue-600 mb-8">🚀 أداة النقل التلقائي المجدول</h1>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
                <label class="block text-gray-700 font-bold mb-2">معرف القناة</label>
                <input type="text" id="channel" value="-1004247712091" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-left font-mono" dir="ltr">
            </div>
            <div>
                <label class="block text-gray-700 font-bold mb-2">عدد الفيديوهات (0 = الكل)</label>
                <input type="number" id="limit" value="1" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-left font-mono" dir="ltr">
            </div>
        </div>
        
        <button onclick="startBot()" id="startBtn" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-lg text-lg transition duration-200 shadow-md">▶️ ابدأ العملية الآن</button>
        
        <div class="mt-8">
            <h2 class="text-xl font-bold text-gray-800 mb-3 flex items-center">
                <span class="mr-2">🖥️</span> شاشة المراقبة المباشرة
            </h2>
            <div id="logs" class="bg-gray-900 text-green-400 p-5 rounded-lg h-80 overflow-y-auto font-mono text-sm leading-relaxed whitespace-pre-wrap shadow-inner" dir="ltr">يتم الآن تهيئة النظام...</div>
        </div>
    </div>

    <script>
        // تعيين تاريخ اليوم كقيمة افتراضية
        
        
        function startBot() {
            const channel = document.getElementById('channel').value;
            const limit = document.getElementById('limit').value;
            
            const btn = document.getElementById('startBtn');
            btn.disabled = true;
            btn.innerHTML = '? ???? ??? ?????...';
            btn.classList.replace('bg-blue-600', 'bg-gray-500');
            
            fetch('/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    channel_id: channel, 
                    limit: parseInt(limit)
                })
            }).then(res => {
                setTimeout(() => {
                    btn.disabled = false;
                    btn.innerHTML = '▶️ ابدأ العملية الآن';
                    btn.classList.replace('bg-gray-500', 'bg-blue-600');
                }, 3000);
            });
        }

        setInterval(() => {
            fetch('/logs').then(res => res.json()).then(data => {
                const logsDiv = document.getElementById('logs');
                if(data.logs.length > 0) {
                    const newText = data.logs.join('\\n');
                    if (logsDiv.innerHTML !== newText) {
                        logsDiv.innerHTML = newText;
                        logsDiv.scrollTop = logsDiv.scrollHeight;
                    }
                }
            });
        }, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/start', methods=['POST'])
def start():
    global is_running, status_logs
    if is_running:
        return jsonify({"status": "already_running"}), 400
    
    data = request.json
    channel_id = data.get('channel_id', '-1004247712091')
    limit = data.get('limit', 1)
    
    status_logs = ["[??????]: ???? ?????? ????? ???? ????? ???????..."]
    is_running = True
    
    thread = threading.Thread(target=run_automation_sync, args=(channel_id, limit))
    thread.start()
    
    return jsonify({"status": "started"})

@app.route('/logs')
def get_logs():
    return jsonify({"logs": status_logs})

if __name__ == '__main__':
    log("🌍 السيرفر المحلي يعمل. يمكنك التحكم بالبوت من خلال المتصفح.")
    app.run(port=5000)
