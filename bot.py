import os
import re
import requests
import discord
from discord.ext import tasks
import feedparser
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

# ================== SETUP ==================
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
channel_id = int(os.getenv("CHANNEL_ID"))
groq_api_key = os.getenv("GROQ_API_KEY")
print(f"API Key terbaca: {groq_api_key[:10]}..." if groq_api_key else "API Key KOSONG/tidak terbaca!")

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

# Warna embed per kategori, biar gampang dibedain sekilas
KATEGORI_WARNA = {
    "Research": discord.Color.purple(),
    "Produk": discord.Color.green(),
    "Bisnis": discord.Color.gold(),
    "Security": discord.Color.red(),
    "Government": discord.Color.dark_grey(),
    "Lainnya": discord.Color.blue(),
}

sent_links = set()

# Jadwal kirim: setiap hari jam 09:00 WIB (UTC+7)
WIB = timezone(timedelta(hours=7))
JAM_KIRIM = datetime.strptime("09:00", "%H:%M").replace(tzinfo=WIB).time()


# ================== AMBIL GAMBAR ARTIKEL ==================
def ambil_gambar_artikel(url):
    """Scraping meta tag og:image dari halaman artikel asli."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=6)
        soup = BeautifulSoup(response.content, "html.parser")
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image.get("content")
    except Exception as e:
        print(f"[Gambar] Gagal ambil dari {url}: {e}")
    return None


# ================== RANGKUM + KATEGORI PAKAI GROQ ==================
def rangkum_dan_kategori(judul, deskripsi_mentah):
    """
    Panggil Groq API untuk:
    1. Merangkum berita jadi 2-3 kalimat singkat & akurat
    2. Menentukan kategori: Research, Produk, Bisnis, Security, Government
    Kalau API gagal/limit, fallback ke deskripsi asli + kategori 'Lainnya'.
    """
    if not groq_api_key:
        return deskripsi_mentah[:200], "Lainnya"

    prompt = f"""Kamu adalah asisten yang merangkum berita AI secara akurat dan netral.

Judul: {judul}
Isi mentah: {deskripsi_mentah}

Tugas:
1. Buat rangkuman 2-3 kalimat dalam Bahasa Indonesia, jelas dan faktual, jangan tambahkan opini atau informasi yang tidak ada di teks asli.
2. Tentukan SATU kategori paling sesuai dari daftar ini saja: Research, Produk, Bisnis, Security, Government.

Jawab HANYA dalam format persis seperti ini, tanpa tambahan apapun:
RINGKASAN: <isi ringkasan>
KATEGORI: <salah satu kategori>"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 300,
            },
            timeout=15,
        )
        response.raise_for_status()
        hasil = response.json()["choices"][0]["message"]["content"]

        ringkasan_match = re.search(r"RINGKASAN:\s*(.+)", hasil)
        kategori_match = re.search(r"KATEGORI:\s*(\w+)", hasil)

        ringkasan = ringkasan_match.group(1).strip() if ringkasan_match else deskripsi_mentah[:200]
        kategori = kategori_match.group(1).strip() if kategori_match else "Lainnya"

        if kategori not in KATEGORI_WARNA:
            kategori = "Lainnya"

        return ringkasan, kategori

    except Exception as e:
        print(f"[Groq] Gagal proses AI: {e}")
        return deskripsi_mentah[:200], "Lainnya"


# ================== AMBIL BERITA DARI RSS ==================
def ambil_berita():
    hasil = []
    batas_waktu = datetime.now(timezone.utc) - timedelta(hours=24)

    for sumber, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        print(f"[DEBUG] {sumber}: total entry ditemukan = {len(feed.entries)}")
        for entry in feed.entries[:5]:
            link = entry.link
            if link in sent_links:
                print(f"[DEBUG] Skip (sudah pernah dikirim): {entry.title}")
                continue

            if hasattr(entry, "published_parsed"):
                waktu_terbit = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if waktu_terbit < batas_waktu:
                    print(f"[DEBUG] Skip (lebih dari 24 jam): {entry.title}")
                    continue

            deskripsi_mentah = ""
            if hasattr(entry, "summary"):
                deskripsi_mentah = re.sub("<[^<]+?>", "", entry.summary)

            hasil.append({
                "judul": entry.title,
                "link": link,
                "sumber": sumber,
                "deskripsi_mentah": deskripsi_mentah,
            })
            sent_links.add(link)

    print(f"[DEBUG] Total berita lolos filter: {len(hasil)}")
    return hasil


# ================== DISCORD EVENTS ==================
@client.event
async def on_ready():
    print(f"Bot berhasil login sebagai {client.user}")
    print(f"Jadwal kirim otomatis diatur jam {JAM_KIRIM} WIB setiap hari")
    kirim_berita_harian.start()

@tasks.loop(time=JAM_KIRIM)
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

    await channel.send("## 🤖 Breaking News AI Hari Ini")

    for berita in berita_list[:10]:
        # Proses AI: rangkum + kategori
        ringkasan, kategori = rangkum_dan_kategori(berita["judul"], berita["deskripsi_mentah"])

        # Ambil gambar dari halaman artikel asli
        gambar = ambil_gambar_artikel(berita["link"])

        embed = discord.Embed(
            title=berita["judul"],
            url=berita["link"],
            description=ringkasan,
            color=KATEGORI_WARNA.get(kategori, discord.Color.blue()),
        )
        embed.set_author(name=berita["sumber"])
        embed.add_field(name="Kategori", value=kategori, inline=True)
        if gambar:
            embed.set_image(url=gambar)
        embed.set_footer(text="Baca selengkapnya di link judul")

        await channel.send(embed=embed)


client.run(token)