import ffmpeg
import tempfile
import os
import time
import asyncio
from telethon import TelegramClient
from telethon.tl.types import PeerChannel, DocumentAttributeVideo
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import FloodWaitError

# ✅ API credentials
api_id = '5763819'  # Ganti dengan API ID Anda
api_hash = '5b391bbd20571c5c8306d40489d6c59d'  # Ganti dengan API Hash Anda
session_name = 'session_name'

# ✅ Source dan target channel
source_channel_id = 2398751095
target_channel_link = "https://t.me/+3G87SSWq-w0zYWQ8"
start_message = 6126
end_message = 9155

# ✅ Ukuran maksimal video (600MB)
MAX_FILE_SIZE_MB = 600
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # Konversi ke byte

async def get_video_metadata(video_path):
    """Mendapatkan metadata video dan membuat thumbnail."""
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
        
        if video_stream:
            duration = int(float(video_stream["duration"]))  # Durasi video dalam detik
            width = int(video_stream["width"])  # Lebar video
            height = int(video_stream["height"])  # Tinggi video

            # ✅ Buat file thumbnail sementara
            thumb_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
            (
                ffmpeg.input(video_path, ss=1)  # Ambil frame pertama
                .output(thumb_path, vframes=1, format="image2", vcodec="mjpeg")
                .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
            )
            return duration, width, height, thumb_path
    except Exception as e:
        print(f"⚠️ Gagal mendapatkan metadata video: {e}")
    return 0, 1280, 720, None

async def download_and_send_video(message, target, client):
    """Download video dari source channel dan kirim ke target channel dengan metadata + thumbnail."""
    try:
        if message.file.size > MAX_FILE_SIZE_BYTES:
            print(f"⏭️ Video {message.id} dilewati (ukuran terlalu besar).")
            return

        start_time = time.time()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            file_path = temp_file.name
            await message.download_media(file=file_path)

        download_time = time.time() - start_time
        
        duration, width, height, thumb_path = await get_video_metadata(file_path)

        start_upload = time.time()
        await client.send_file(
            target,
            file_path,
            caption=message.text or "Video no caption",
            attributes=[DocumentAttributeVideo(
                duration=duration,
                w=width,
                h=height,
                supports_streaming=True
            )],
            thumb=thumb_path if thumb_path else None
        )
        upload_time = time.time() - start_upload

        os.remove(file_path)
        if thumb_path:
            os.remove(thumb_path)

        print(f"✅ Video {message.id} selesai ({download_time:.2f}s download, {upload_time:.2f}s upload)")
    except Exception as e:
        print(f"❌ Error mengirim video {message.id}: {e}")

async def main():
    async with TelegramClient(session_name, api_id, api_hash) as client:
        try:
            source_channel = await client.get_entity(PeerChannel(source_channel_id))
            print(f"📌 Terhubung ke source channel: {source_channel.title}")
            await client(JoinChannelRequest(target_channel_link))
            target_channel = await client.get_entity(target_channel_link)
            print(f"📌 Terhubung ke target channel: {target_channel.title}")

            tasks = []
            async for message in client.iter_messages(
                source_channel,
                reverse=True,
                offset_id=start_message - 1,
                limit=end_message - start_message + 1
            ):
                if message.video:
                    print(f"🎥 Memproses video {message.id}...")
                    tasks.append(download_and_send_video(message, target_channel, client))
                    
                    if len(tasks) >= 50:
                        await asyncio.gather(*tasks)
                        tasks = []
            
            if tasks:
                await asyncio.gather(*tasks)
        except FloodWaitError as e:
            print(f"⚠️ Rate limit! Menunggu {e.seconds} detik...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
