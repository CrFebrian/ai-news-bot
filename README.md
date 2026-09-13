# 🤖 AI News Bot

Bot Discord otomatis yang mengirimkan breaking news seputar dunia Artificial Intelligence (AI) setiap hari. Bot ini mengambil berita terbaru dari sumber-sumber tepercaya, lalu mengirimkannya ke channel Discord dalam format yang rapi dan mudah dibaca tanpa perlu command manual dari user.

## ✨ Fitur

- Mengambil berita AI otomatis dari beberapa RSS feed tepercaya
- Filter berita hanya yang terbit dalam 24 jam terakhir
- Deduplikasi — berita yang sudah pernah dikirim tidak akan dikirim ulang
- Tampilan embed rapi per berita (judul, sumber, deskripsi singkat, link)
- Berjalan otomatis setiap 24 jam sekali tanpa campur tangan manual
  
## 🛠️ Tech Stack

| Tools | Kegunaan |
|---|---|
| Python | Bahasa pemrograman utama |
| discord.py | Library untuk membangun bot Discord |
| feedparser | Membaca dan parsing RSS feed |
| python-dotenv | Mengelola environment variable secara aman |

## 📰 Sumber Berita

Bot ini menarik data dari RSS feed berikut:

- **TechCrunch AI** — `techcrunch.com/category/artificial-intelligence`
- **VentureBeat AI** — `venturebeat.com/category/ai`
- **The Verge AI** — `theverge.com/ai-artificial-intelligence`

## ⚙️ Cara Kerja

Alur kerja bot ini, dari bot menyala sampai berita terkirim:

1. **Bot online** — saat dijalankan, bot login ke Discord menggunakan token dari `.env`, lalu memulai jadwal otomatis (`tasks.loop`) yang berjalan setiap 24 jam.

2. **Ambil berita** — fungsi `ambil_berita()` membaca setiap RSS feed yang terdaftar di `RSS_FEEDS`, mengambil 5 artikel teratas per sumber.

3. **Filter berita**:
   - Berita yang terbit **lebih dari 24 jam lalu** dilewati (tidak basi/lama)
   - Berita yang **linknya sudah pernah dikirim** dilewati (disimpan di `sent_links`, mencegah duplikat)

4. **Bersihkan deskripsi** — ringkasan artikel dari RSS dibersihkan dari tag HTML dan dipotong maksimal 200 karakter agar rapi ditampilkan.

5. **Kirim ke Discord** — bot mengambil channel tujuan lewat `CHANNEL_ID`, mengirim 1 pesan judul pembuka, lalu setiap berita dikirim sebagai **embed terpisah** (judul jadi link, nama sumber, deskripsi singkat).

6. **Ulangi otomatis** — proses di atas berulang setiap 24 jam selama bot tetap online di Railway.

## 📋 Contoh Hasil di Discord

```
🤖 Breaking News AI Hari Ini

┌─────────────────────────────────
│ TechCrunch AI
│ Hackers are stealing Claude tokens from subscribers
│ Last month, a Claude user noticed his account was 
│ consuming tokens even though he wasn't working...
│ Baca selengkapnya di link judul
└─────────────────────────────────

┌─────────────────────────────────
│ VentureBeat AI
│ [judul berita lain]
│ [deskripsi singkat]
└─────────────────────────────────

... (hingga 10 berita per hari)
```

## 📁 Struktur Project

```
ai-news-bot/
├── .env              # token & channel ID (rahasia, tidak di-upload)
├── .gitignore         # daftar file yang diabaikan Git
├── bot.py             # kode utama bot
├── requirements.txt   # daftar library yang dibutuhkan
└── Procfile           # instruksi menjalankan bot untuk Railway
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
   ```
4. Jalankan bot:
   ```bash
   python bot.py
   ```

## ☁️ Deployment

Bot di-deploy menggunakan **Railway**, terhubung langsung ke repo GitHub ini. Setiap kali ada `git push` ke branch `main`, Railway otomatis build ulang dan restart bot dengan versi terbaru.

Environment variable (`DISCORD_TOKEN`, `CHANNEL_ID`) diatur langsung di dashboard Railway pada tab **Variables**, bukan lewat file `.env` (karena file tersebut tidak ikut ter-upload demi keamanan).

## 🔮 Rencana Pengembangan

- [ ] Menambahkan gambar/thumbnail per berita (menunggu integrasi AI API)
- [ ] Rangkuman berita otomatis menggunakan AI
- [ ] Jadwal pengiriman pada jam tetap (misal selalu jam 08:00)
- [ ] Command manual untuk trigger pengiriman berita kapan saja

## ⚠️ Catatan Keamanan

File `.env` **tidak boleh** di-commit ke GitHub karena berisi token rahasia. File ini sudah otomatis diabaikan lewat `.gitignore`. Jangan pernah menuliskan token secara langsung (hardcode) di dalam `bot.py`.
