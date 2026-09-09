import os
import discord
from discord.ext import tasks
import feedparser
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

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
        # ambil 5 teratas per sumber
        for entry in feed.entries[:5]:  
            link = entry.link
            if link in sent_links:
                continue

            # cek tanggal biar cuma ambil berita 24 jam terakhir
            if hasattr(entry, "published_parsed"):
                waktu_terbit = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if waktu_terbit < batas_waktu:
                    continue

            hasil.append({
                "judul": entry.title,
                "link": link,
                "sumber": sumber
            })
            sent_links.add(link)

    return hasil

@client.event
async def on_ready():
    print(f"Bot berhasil login sebagai {client.user}")
    kirim_berita_harian.start()

@tasks.loop(hours=24)
async def kirim_berita_harian():
    channel = client.get_channel(channel_id)
    berita_list = ambil_berita()

    if not berita_list:
        await channel.send("Tidak ada berita AI baru hari ini.")
        return

    embed = discord.Embed(
        title="🤖 Breaking News AI Hari Ini",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )

    for berita in berita_list[:10]:
        embed.add_field(
            name=f"[{berita['sumber']}] {berita['judul']}",
            value=f"[Baca selengkapnya]({berita['link']})",
            inline=False
        )

    await channel.send(embed=embed)
client.run(token)