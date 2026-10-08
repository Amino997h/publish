import asyncio
import os
import json
from telethon import TelegramClient
from youtube_uploader_selenium import YouTubeUploader

# ================= الإعدادات =================
# احصل على هذه البيانات من https://my.telegram.org
API_ID = 'ضع_رقم_الـ_API_هنا'
API_HASH = 'ضع_الـ_HASH_هنا'
CHANNEL_ID = -1000000000000 # ضع معرف القناة هنا، تأكد أنه رقم يبدأ بـ -100

# مسار بروفايل فايرفوكس لتخطي تسجيل الدخول في يوتيوب
# ابحث عن about:profiles في متصفح فايرفوكس وانسخ مسار المجلد Root Directory
FIREFOX_PROFILE_PATH = r'C:\Users\User\AppData\Roaming\Mozilla\Firefox\Profiles\your_profile.default'

client = TelegramClient('bot_session', API_ID, API_HASH)

async def main():
    print("🚀 بدء تشغيل بوت النقل التلقائي من تيليجرام إلى يوتيوب...")
    
    # المرور على الرسائل من الأقدم للأحدث لنقل المحتوى القديم والجديد
    async for message in client.iter_messages(CHANNEL_ID, reverse=True):
        if message.video:
            print(f"\n🎥 تم العثور على فيديو! رقم الرسالة: {message.id}")
            
            # 1. تنزيل الفيديو
            video_path = f"video_{message.id}.mp4"
            print(f"⬇️ جاري تحميل الفيديو: {video_path}...")
            await message.download_media(file=video_path)
            
            # 2. استخراج البيانات (العنوان، الوصف، الهاشتاغات)
            text = message.text or ""
            lines = text.split('\n')
            
            # نأخذ أول سطر كعنوان (بحد أقصى 100 حرف ليناسب يوتيوب)
            title = lines[0][:100] if lines else f"فيديو من تيليجرام {message.id}"
            description = text
            # استخراج الهاشتاغات فقط (بدون علامة #)
            tags = [word[1:] for word in text.split() if word.startswith('#')]
            
            metadata = {
                "title": title,
                "description": description,
                "tags": tags
            }
            
            meta_path = f"meta_{message.id}.json"
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
            print("📝 تم إنشاء ملف بيانات الفيديو (metadata).")
            
            # 3. الرفع إلى يوتيوب
            print(f"⬆️ جاري الرفع إلى يوتيوب...")
            try:
                uploader = YouTubeUploader(video_path, meta_path, FIREFOX_PROFILE_PATH)
                was_video_uploaded, video_id = uploader.upload()
                
                if was_video_uploaded:
                    print(f"✅ تم رفع الفيديو بنجاح! الرابط: https://youtu.be/{video_id}")
                else:
                    print("❌ حدث خطأ أثناء الرفع لم يتم استرجاع الرابط.")
            except Exception as e:
                print(f"❌ فشل الرفع: {e}")
                
            # 4. تنظيف الملفات المؤقتة لتوفير المساحة
            print("🧹 جاري تنظيف الملفات المؤقتة...")
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(meta_path):
                os.remove(meta_path)
                
            print("⏳ تم التنظيف، ننتظر قليلاً قبل الفيديو التالي لتجنب الحظر...")
            # توقف مؤقت بسيط لتجنب قيود تيليجرام ويوتيوب
            await asyncio.sleep(15) 

with client:
    client.loop.run_until_complete(main())
