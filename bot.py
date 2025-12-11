import asyncio
from pyrogram import Client, filters
from telethon import TelegramClient
from telethon.tl.functions.phone import JoinGroupCallRequest
from telethon.tl.types import InputPeerChannel, InputPhoneCall
import yt_dlp
import subprocess
import os

API_ID = 27061516
API_HASH = "64fd99336f58c6d077c0e444855569e5"
BOT_TOKEN = "8269413511:AAH4poWquV9lcwzjjQUVEhmb_nx8IGFgXLI"
SESSION_STRING = "BAGc7QwAw_k0IeAF5WBlegNrBcMkPVWdLOSc1_5HkUg6G3jK6H_Qu8P-0oFg9WbEEve_w6rYUMOBTX_QNI4JacIA639k7wkod4kRh8JNM8_Y2NrkGicEgGbPsNvQWXDMzT-hXTEKV1ZNGvyz06OHQ9zF9btuY3qNpmxHXWrDdbBZr-WBapzf5f0cwgzBhQFU_1mnWzkGfFwPTDtSaP18t6kGE9VP0E8Nhwk4ntHqMEPYQc6ZXFC1rVfC9_ifgswqeQJh5ZIJJ34IjTlawFxwkj4OUXdgv_TX2_UJ30FBIfJQp9ZuvrrtRWAAlX5jLa3ubwdbXmRBvuTI7EtJeutgmyLRoelnsAAAAAHLsIxHAA"

# بوت Pyrogram للأوامر
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# عميل Telethon للمكالمات
telethon_client = TelegramClient("user_session", API_ID, API_HASH)

async def convert_to_opus(input_file, output_file):
    """تحويل أي ملف صوتي إلى opus"""
    cmd = [
        'ffmpeg', '-i', input_file,
        '-c:a', 'libopus',
        '-b:a', '64k',
        '-vbr', 'on',
        '-compression_level', '10',
        '-application', 'voip',
        output_file
    ]
    subprocess.run(cmd, check=True)

@bot.on_message(filters.command("start"))
async def start(_, msg):
    await msg.reply("🎧 **بوت المكالمات الصوتية يعمل!**\n\n"
                   "🎵 /play [اسم الأغنية] - لتشغيل صوت في المكالمة\n"
                   "⏹ /stop - لإيقاف التشغيل\n"
                   "📥 /download [رابط] - لتحميل صوت فقط")

@bot.on_message(filters.command("play") & filters.text)
async def play_music(_, msg):
    query = msg.text.split(None, 1)[1] if len(msg.text.split()) > 1 else None
    if not query:
        return await msg.reply("🎵 اكتب اسم الأغنية بعد /play")
    
    m = await msg.reply("🔍 جاري البحث والتحميل...")
    
    try:
        # تحميل الصوت من YouTube
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio.%(ext)s',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '64',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)
            audio_file = ydl.prepare_filename(info).replace('.webm', '.opus').replace('.m4a', '.opus')
        
        # الانضمام للمكالمة باستخدام Telethon
        await telethon_client.connect()
        
        # الحصول على معلومات الدردشة
        chat = await telethon_client.get_entity(msg.chat.id)
        
        # الانضمام للمكالمة الجماعية
        result = await telethon_client(JoinGroupCallRequest(
            call=InputPeerChannel(chat.id, chat.access_hash),
            params={
                'ufrag': 'test',
                'pwd': 'test',
                'fingerprints': [{'hash': 'test'}],
                'ssrc': 123456,
                'ssrc-groups': [],
                'payload-types': [],
                'rtcp-fb': []
            }
        ))
        
        await m.edit(f"🎶 **جاري تشغيل:** {info['title']}\n"
                    f"📁 **تم التحميل:** {audio_file}\n\n"
                    f"✅ **البوت في المكالمة!**\n"
                    f"⚠️ **للتشغيل الفعلي تحتاج:**\n"
                    f"- تشغيل الملف يدوياً في المكالمة\n"
                    f"- أو استخدام VPS مع tgcalls")
        
        # حفظ معلومات الملف للمستخدم
        await msg.reply(f"🎵 الملف جاهز: `{audio_file}`\n\n"
                       f"**للتشغيل في المكالمة:**\n"
                       f"1. تأكد أن البوت في المكالمة\n"
                       f"2. استخدم تطبيق تشغيل صوت في Termux\n"
                       f"3. أو انقل الملف لجهازك وشغله")
        
    except Exception as e:
        await m.edit(f"❌ **خطأ:** {str(e)}")

@bot.on_message(filters.command("download"))
async def download_audio(_, msg):
    """تحميل الصوت فقط"""
    query = msg.text.split(None, 1)[1] if len(msg.text.split()) > 1 else None
    if not query:
        return await msg.reply("📥 اكتب رابط أو اسم الأغنية")
    
    m = await msg.reply("⏬ جاري تحميل الصوت...")
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        os.makedirs("downloads", exist_ok=True)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
        
        await m.edit(f"✅ **تم تحميل الصوت!**\n\n"
                    f"🎵 **{info['title']}**\n"
                    f"📁 **{os.path.basename(filename)}**\n"
                    f"💾 **الحجم:** {os.path.getsize(filename)//1024} KB")
        
    except Exception as e:
        await m.edit(f"❌ **خطأ:** {str(e)}")

@bot.on_message(filters.command("join"))
async def join_voice_chat(_, msg):
    """الانضمام للمكالمة الصوتية"""
    try:
        await telethon_client.connect()
        chat = await telethon_client.get_entity(msg.chat.id)
        
        # محاولة الانضمام للمكالمة
        result = await telethon_client(JoinGroupCallRequest(
            call=InputPeerChannel(chat.id, chat.access_hash),
            params={
                'ufrag': 'test',
                'pwd': 'test',
                'fingerprints': [{'hash': 'test'}],
                'ssrc': 123456
            }
        ))
        
        await msg.reply("✅ **تم الانضمام للمكالمة الصوتية!**\n\n"
                       "🎧 **للتشغيل:**\n"
                       "1. استخدم /play [أغنية]\n"
                       "2. سيتم تحميل الملف\n"
                       "3. شغل الملف يدوياً في المكالمة")
        
    except Exception as e:
        await msg.reply(f"❌ **خطأ في الانضمام:** {str(e)}")

# تشغيل البوتين
async def main():
    await bot.start()
    print("✅ البوت يعمل...")
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
