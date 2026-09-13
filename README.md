# 🤖 AI News Bot

Bot Discord otomatis yang mengirimkan breaking news seputar dunia Artificial Intelligence (AI) setiap hari. Bot ini mengambil berita terbaru dari sumber-sumber tepercaya, merangkumnya dengan AI, mengelompokkannya per kategori, lalu mengirimkannya ke channel Discord dalam format embed yang rapi lengkap dengan gambar otomatis tanpa command manual.

## ✨ Fitur

- Mengambil berita AI otomatis dari beberapa RSS feed tepercaya
- Filter berita hanya yang terbit dalam 24 jam terakhir
- **Kategorisasi otomatis** per berita (Research, Produk, Bisnis, Security, Government) dengan warna embed berbeda per kategori
- **Gambar thumbnail otomatis** — diambil langsung dari halaman artikel asli (meta tag `og:image`)

## 🛠️ Tech Stack

| Tools | Kegunaan |
|---|---|
| Python | Bahasa pemrograman utama |
| discord.py | Library untuk membangun bot Discord |
| feedparser | Membaca dan parsing RSS feed |
| python-dotenv | Mengelola environment variable secara aman |
| requests | Memanggil Groq API & scraping halaman artikel |
| BeautifulSoup4 | Ambil gambar (`og:image`) dari halaman artikel |
| Groq API | Rangkum berita & tentukan kategori otomatis (gratis) |

## 📰 Sumber Berita

Bot ini menarik data dari RSS feed berikut:

- **TechCrunch AI** — `techcrunch.com/category/artificial-intelligence`
- **VentureBeat AI** — `venturebeat.com/category/ai`
- **The Verge AI** — `theverge.com/ai-artificial-intelligence`

> Sumber bisa ditambah/dikurangi dengan mengedit dictionary `RSS_FEEDS` di `bot.py`.

## ⚙️ Cara Kerja

Alur kerja bot ini, dari bot menyala sampai berita terkirim:

1. **Bot online** — bot login ke Discord menggunakan token dari environment variable, lalu jadwal otomatis diatur untuk selalu jalan jam **09:00 WIB** setiap hari (`tasks.loop(time=...)` dengan timezone UTC+7).

2. **Ambil berita** — fungsi `ambil_berita()` membaca setiap RSS feed di `RSS_FEEDS` dengan header `User-Agent` (supaya tidak diblokir situs), mengambil 5 artikel teratas per sumber.

3. **Filter berita**:
   - Berita yang terbit **lebih dari 48 jam lalu** dilewati
   - Berita yang **linknya sudah pernah dikirim** dilewati (disimpan di `sent_links`, mencegah duplikat)

4. **Proses AI (`rangkum_dan_kategori()`)** — judul dan deskripsi mentah tiap berita dikirim ke Groq API dengan instruksi tegas untuk **tidak menambah opini/informasi di luar teks asli**, menghasilkan:
   - Ringkasan 2-3 kalimat berbahasa Indonesia
   - Satu kategori: `Research`, `Produk`, `Bisnis`, `Security`, atau `Government`

5. **Ambil gambar (`ambil_gambar_artikel()`)** — bot membuka halaman artikel asli dan mengambil meta tag `og:image`, yaitu gambar preview yang sama seperti yang muncul saat link di-share di media sosial.

6. **Kirim ke Discord** — tiap berita dikirim sebagai **embed terpisah**: judul (jadi link), nama sumber, kategori, ringkasan AI, gambar, dan warna embed yang berbeda sesuai kategori.

7. **Ulangi otomatis** — proses di atas berulang setiap hari jam 09:00 WIB selama bot tetap online.

## 📋 Contoh Hasil di Discord

```
🤖 Breaking News AI Hari Ini

┌─────────────────────────────────
│ TechCrunch AI
│ OpenAI's Sam Altman says it would be 'ill-advised' 
│ to go public in 2026
│
│ Ringkasan: OpenAI telah mengajukan IPO secara 
│ konfidensial, namun CEO Sam Altman menegaskan 
│ perusahaan tidak akan go public tahun ini.
│
│ Kategori: Bisnis
│ [gambar thumbnail artikel]
│ Baca selengkapnya di link judul
└─────────────────────────────────

... (hingga 10 berita per hari, warna embed beda per kategori)
```

## 📁 Struktur Project

```
ai-news-bot/
├── .env              # token
├── .gitignore        # daftar file yang diabaikan Git
├── bot.py            # kode utama bot
├── requirements.txt  # daftar library yang dibutuhkan
└── Procfile          # instruksi menjalankan bot untuk Railway
```

## 🚀 Setup & Instalasi

1. Clone repo ini, lalu masuk ke foldernya
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Buat file `.env` berisi:
   ```
   DISCORD_TOKEN=token_bot_kamu
   CHANNEL_ID=id_channel_tujuan
   GROQ_API_KEY=api_key_groq_kamu
   ```
4. Jalankan bot:
   ```bash
   python bot.py
   ```
   
## 🐛 Troubleshooting & Lessons Learned

Beberapa kendala yang pernah ditemui selama development, dicatat sebagai referensi:

- **`AttributeError: 'NoneType' object has no attribute 'send'`** — terjadi kalau `client.get_channel()` gagal menemukan channel (biasanya karena cache belum ke-load). Solusi: pakai `await client.fetch_channel()` yang request langsung ke Discord API.
- **`404 model_not_found` dari Groq** — nama model yang di-hardcode sudah tidak aktif lagi. Selalu cek model aktif di Playground Groq sebelum submit ke production.
- **RSS feed mengembalikan 0 entry** — beberapa situs memblokir request tanpa `User-Agent` header. Solusi: tambahkan `request_headers={"User-Agent": "Mozilla/5.0"}` di `feedparser.parse()`. Gunakan `feed.bozo` dan `feed.bozo_exception` untuk debug kalau feed gagal di-parse.
- **Berita yang lolos filter terlalu sedikit** — filter 24 jam kadang terlalu ketat untuk sumber yang jarang update. Diperlonggar jadi 48 jam.
- **RSS feed sering tidak menyertakan data gambar** — solusinya scraping meta tag `og:image` langsung dari halaman artikel, bukan mengandalkan data dari RSS.

## 🔮 Rencana Pengembangan Selanjutnya

- [ ] Slash command manual untuk trigger pengiriman berita kapan saja (`/news`)
- [ ] Filter berita by kategori atau sumber lewat command
- [ ] Multi-channel — kirim ke channel berbeda sesuai kategori berita

## ⚠️ Catatan Keamanan

File `.env` **tidak boleh** di-commit ke GitHub karena berisi token dan API key rahasia. File ini sudah otomatis diabaikan lewat `.gitignore`. Jangan pernah menuliskan token/API key secara langsung (hardcode) di dalam `bot.py`.
