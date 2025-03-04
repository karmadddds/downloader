import asyncio
import time
import os
from telethon import TelegramClient
from telethon.errors import FloodWaitError

# ✅ API credentials
api_id = 5763819  # Ganti dengan API ID Anda
api_hash = '5b391bbd20571c5c8306d40489d6c59d'  # Ganti dengan API Hash Anda

# ✅ Source dan target channel
source_channel_link = "https://t.me/+w63KcyBe9LxjYzM1"  # Ganti dengan link channel sumber
target_channel_link = "https://t.me/+TOePF2vz7kM1M2E5"  # Ganti dengan link channel tujuan

# ✅ Rentang pesan yang akan diteruskan
start_message_id = 58657
end_message_id = 58850

async def forward_media(client, source, target):
    tasks = []
    album = []
    total_media = 0
    start_time = time.time()
    last_grouped_id = None
    
    async for message in client.iter_messages(source, min_id=start_message_id - 1, max_id=end_message_id + 1, reverse=True):
        if message.photo or message.video:  # Hanya foto dan video
            if message.grouped_id:
                if last_grouped_id is None or message.grouped_id == last_grouped_id:
                    album.append(message)
                else:
                    # Kirim album sebelumnya sebelum memulai album baru
                    if album:
                        tasks.append(client.send_file(target, [m.media for m in album], caption=album[0].text or ""))
                        total_media += len(album)
                    album = [message]
                last_grouped_id = message.grouped_id
            else:
                # Kirim album jika ada sebelum mengirim media tunggal
                if album:
                    tasks.append(client.send_file(target, [m.media for m in album], caption=album[0].text or ""))
                    total_media += len(album)
                    album = []
                tasks.append(client.send_file(target, message.media, caption=message.text or ""))
                total_media += 1
            
            # Kirim batch hanya jika album sudah lengkap
            if last_grouped_id is None and len(tasks) >= 50:
                await asyncio.gather(*tasks)
                tasks = []
    
    # Kirim sisa album terakhir jika ada
    if album:
        tasks.append(client.send_file(target, [m.media for m in album], caption=album[0].text or ""))
        total_media += len(album)
    
    if tasks:
        await asyncio.gather(*tasks)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    speed = total_media / elapsed_time if elapsed_time > 0 else 0
    print(f"✅ {total_media} media berhasil dikirim dalam {elapsed_time:.2f} detik ({speed:.2f} media/detik)")

async def main():
    async with TelegramClient("session", api_id, api_hash) as client:
        try:
            print("🔄 Menghubungkan ke Telegram...")
            source_channel = await client.get_entity(source_channel_link)
            target_channel = await client.get_entity(target_channel_link)
            print(f"📌 Terhubung ke source: {source_channel.title}, target: {target_channel.title}")
            
            await forward_media(client, source_channel, target_channel)
        except FloodWaitError as e:
            print(f"⚠️ Rate limit! Menunggu {e.seconds} detik...")
            await asyncio.sleep(e.seconds)
            await main()  # Coba lagi setelah delay
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
