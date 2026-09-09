import os
import discord
from discord.ext import tasks
import feedparser
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import re

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Daftar sumber RSS tepercaya
RSS_FEEDS = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
    "The Verge AI": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "MIT Technology Review AI": "https://www.technologyreview.com/feed/",
    "AI Trends": "https://www.aitrends.com/feed/"
}

sent_links = set()

def ambil_berita():
    hasil = []
    batas_waktu = datetime.now(timezone.utc) - timedelta(hours=24)

    for sumber, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            link = entry.link
            if link in sent_links:
                continue

            if hasattr(entry, "published_parsed"):
                waktu_terbit = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if waktu_terbit < batas_waktu:
                    continue

            # Ambil deskripsi singkat
            deskripsi = ""
            if hasattr(entry, "summary"):
                import re
                deskripsi = re.sub("<[^<]+?>", "", entry.summary)  # buang tag HTML
                deskripsi = deskripsi[:200] + "..." if len(deskripsi) > 200 else deskripsi

            # Ambil gambar thumbnail kalau ada
            gambar = None
            if hasattr(entry, "media_content") and entry.media_content:
                gambar = entry.media_content[0].get("url")
            elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                gambar = entry.media_thumbnail[0].get("url")

            hasil.append({
                "judul": entry.title,
                "link": link,
                "sumber": sumber,
                "deskripsi": deskripsi,
                "gambar": gambar
            })
            sent_links.add(link)

    return hasil

@client.event
async def on_ready():
    print(f"Bot berhasil login sebagai {client.user}")
    kirim_berita_harian.start()

@tasks.loop(hours=24)
async def kirim_berita_harian():
    try:
        channel = await client.fetch_channel(channel_id)
    except discord.NotFound:
        print(f"Error: Channel {channel_id} tidak ditemukan.")
        return
    except discord.Forbidden:
        print("Error: Bot tidak punya izin akses channel ini.")
        return

    berita_list = ambil_berita()

    if not berita_list:
        await channel.send("Tidak ada berita AI baru hari ini.")
        return

    # Kirim judul pembuka sekali
    await channel.send("## 🤖 Breaking News AI Hari Ini")

    # Kirim tiap berita sebagai embed terpisah
    for berita in berita_list[:10]:
        embed = discord.Embed(
            title=berita["judul"],
            url=berita["link"],
            description=berita["deskripsi"],
            color=discord.Color.blue()
        )
        embed.set_author(name=berita["sumber"])
        if berita["gambar"]:
            embed.set_image(url=berita["gambar"])
        embed.set_footer(text="Baca selengkapnya di link judul")

        await channel.send(embed=embed)
        
client.run(token)