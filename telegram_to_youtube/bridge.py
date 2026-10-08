import os
import json
import asyncio
import subprocess
import glob
from telethon import TelegramClient

def get_firefox_profile():
    """البحث التلقائي عن بروفايل فايرفوكس الخاص بالمستخدم لسرقة الجلسة وتخطي حماية جوجل"""
    appdata = os.getenv('APPDATA')
    if not appdata: return None
    profiles_path = os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles')
    if not os.path.exists(profiles_path): return None
    
    # البحث عن البروفايل الأساسي
    profiles = glob.glob(os.path.join(profiles_path, '*default-release*'))
    if profiles: return profiles[0]
    
    profiles = glob.glob(os.path.join(profiles_path, '*default*'))
    if profiles: return profiles[0]
    return None

API_ID = '37147534'
API_HASH = '1b22a18d3c5f04409b1f11952b165197'
CHANNEL_ID = -1004247712091

print("\n==================================================")
limit_input = input("كم عدد الفيديوهات التي تريد جلبها ورفعها للتجربة؟ (اكتب رقماً، أو 0 لجلب القناة بالكامل): ")
try:
    max_videos = int(limit_input)
except ValueError:
    max_videos = 1
print("==================================================\n")

client = TelegramClient('bridge_session', API_ID, API_HASH)

async def main():
    print("🚀 بدء أداة سحب الفيديوهات والرفع على يوتيوب...")
    output_dir = "Telegram_Downloads"
    os.makedirs(output_dir, exist_ok=True)
    
    # الحصول على مسار البروفايل لتخطي تسجيل الدخول
    profile_path = get_firefox_profile()
    if profile_path:
        print(f"🦊 تم العثور على بروفايل فايرفوكس الخاص بك بنجاح!")
    else:
        print("⚠️ لم يتم العثور على بروفايل فايرفوكس، سيتم فتح متصفح جديد فارغ.")
        
    processed_count = 0

    async for message in client.iter_messages(CHANNEL_ID, reverse=True):
        if message.video:
            print(f"\n🎥 تم العثور على فيديو: {message.id}")
            
            video_path = os.path.abspath(os.path.join(output_dir, f"video_{message.id}.mp4"))
            meta_path = os.path.abspath(os.path.join(output_dir, f"meta_{message.id}.json"))
            
            print(f"⬇️ جاري تنزيل الفيديو...")
            await message.download_media(file=video_path)
            
            text = message.text or ""
            lines = text.strip().split('\n')
            
            if lines and lines[0].strip():
                title = lines[0].strip()[:100]
                description = '\n'.join(lines[1:]).strip()
            else:
                title = f"فيديو من تيليجرام {message.id}"
                description = ""
                
            tags = [word[1:] for word in text.split() if word.startswith('#')]
            meta = {"title": title, "description": description, "tags": tags}
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=4)
            
            print("🔄 تمرير الفيديو والبيانات لمتصفح الرفع...")
            
            # بناء أمر التشغيل بناءً على توفر البروفايل
            if profile_path:
                cmd = f'cd youtube_uploader_selenium && python upload.py --video "{video_path}" --meta "{meta_path}" --profile "{profile_path}"'
            else:
                cmd = f'cd youtube_uploader_selenium && python upload.py --video "{video_path}" --meta "{meta_path}"'
            
            try:
                subprocess.run(cmd, shell=True, check=True)
                print("✅ اكتمل الرفع ليوتيوب بنجاح!")
                
                print("🧹 تنظيف الملفات المؤقتة لتوفير المساحة...")
                if os.path.exists(video_path): os.remove(video_path)
                if os.path.exists(meta_path): os.remove(meta_path)
                
            except subprocess.CalledProcessError:
                print("❌ حدث خطأ في أداة الرفع الخاصة بيوتيوب.")
                print("⚠️ تم إيقاف الحذف التلقائي لتتمكن من فحص الملفات.")
                break 
            
            processed_count += 1
            if max_videos > 0 and processed_count >= max_videos:
                print(f"\n🎯 تم الانتهاء من تجربة جلب ورفع {max_videos} فيديوهات بنجاح!")
                break
            
            print("⏳ انتظار 3 ثوانٍ فقط قبل الفيديو التالي...")
            await asyncio.sleep(3)

with client:
    client.loop.run_until_complete(main())
