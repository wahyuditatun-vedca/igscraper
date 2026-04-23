# 🔬 MBG Research Scraper — Streamlit App

Tools berbasis Streamlit untuk pengumpulan data Instagram dalam rangka penelitian tesis S2 Ilmu Komputer dengan topik **"Analisis Wacana Rasional Program Makan Bergizi Gratis (MBG) di Instagram"** menggunakan kerangka teori Habermas (Public Sphere & Communicative Rationality).

**Peneliti:** Tatun — S2 Ilmu Komputer
**Pembimbing:** Dr. Arie Qur'ania, M.Kom

---

## 📦 Instalasi

### 1. Persyaratan
- Python 3.9+
- Akun Instagram (disarankan akun terpisah untuk penelitian)
- Koneksi internet stabil

### 2. Setup Environment

```bash
# Buat virtual environment (recommended)
python -m venv venv

# Aktivasi (Linux/Mac)
source venv/bin/activate

# Aktivasi (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi

```bash
streamlit run app.py
```

Aplikasi akan terbuka otomatis di browser pada `http://localhost:8501`

---

## 🧭 Alur Penggunaan

### Tahap 1: Persiapan Etis (WAJIB sebelum scraping)
- ✅ Konsultasi dengan Dr. Arie Qur'ania, M.Kom
- ✅ Ethical review dari komite etika universitas
- ✅ Dokumentasi approval dalam proposal tesis

### Tahap 2: Setup Akun
1. Buat akun Instagram terpisah untuk penelitian (menghindari risiko pada akun utama)
2. Login ke Instagram via browser terlebih dahulu untuk verifikasi device
3. Jika aktif 2FA, siapkan akses ke email/SMS untuk kode verifikasi

### Tahap 3: Scraping Posts
1. Buka halaman **Login** → input kredensial
2. Buka halaman **Scrape Posts** → konfigurasi hashtag dan parameter
3. Jalankan scraping (delay antar hashtag 15 detik direkomendasikan)
4. Target: 200-500 posts per hashtag, total 500-2000 posts

### Tahap 4: Scraping Comments
1. Buka halaman **Scrape Comments**
2. Filter posts dengan minimum comment count (misal ≥5) untuk fokus pada diskusi aktif
3. Target: 50-100 comments per post, total 5000-10000 comments

### Tahap 5: Manual Coding (Framework Habermas)
Klasifikasi setiap komentar ke dalam 5 kategori:

| Kode | Kategori | Validity Claim | Indikator |
|------|----------|----------------|-----------|
| **FAC** | Factual Argument | Truthfulness | Data, statistik, sumber referensi |
| **NOR** | Normative Argument | Rightness | Nilai, norma, kebijakan |
| **EMP** | Emotional/Personal | Sincerity | Cerita pribadi, pengalaman |
| **DIA** | Dialogical Response | Deliberation | Respon kritis terhadap argumen lain |
| **NON** | Non-Communicative | Absent | Spam, ad hominem, trolling |

**Tips:**
- Lakukan inter-rater coding dengan rekan untuk reliability (Cohen's Kappa)
- Coding 200-300 sampel untuk validitas statistik
- Anda juga bisa melakukan coding di NVivo/ATLAS.ti lalu import CSV

### Tahap 6: Export & Analisis
- Export CSV → import ke NVivo/ATLAS.ti/SPSS
- Export Metadata JSON → dokumentasi penelitian
- DRS (Deliberative Rationality Score) sebagai indikator quick analysis

---

## 📊 Struktur Output

### `mbg_posts.csv`
```
post_id, source_hashtag, caption, likes_count, comments_count,
posted_date, posted_timestamp, hashtags, media_type,
engagement_rate, post_url
```

### `mbg_comments.csv`
```
post_id, post_caption_preview, source_hashtag, comment_id,
comment_text, comment_likes, user_id_anonymized, timestamp,
habermas_code (setelah coding)
```

### `mbg_metadata.json`
Dokumentasi penelitian untuk appendix tesis: timestamp, statistik koleksi, catatan etis, distribusi coding.

---

## 🔐 Catatan Keamanan & Etika

### Anonymization
Semua username di-hash dengan MD5 menjadi format `USER_XXXXXXXX`. Hash ini reproducible (username sama → hash sama) tapi tidak reversible.

### Data Yang DIKUMPULKAN
- ✅ Caption publik
- ✅ Komentar publik
- ✅ Metrik engagement (likes, comments count)
- ✅ Hashtag
- ✅ Timestamp

### Data Yang TIDAK DIKUMPULKAN
- ❌ Private messages
- ❌ Username asli (otomatis di-hash)
- ❌ Email, nomor telepon
- ❌ Foto profil
- ❌ Data akun private

### Best Practices untuk Publikasi
1. Tidak pernah publish username asli
2. Sample quotes yang dipublish harus di-paraphrase atau diberi izin
3. Dataset final hanya di-share dengan approval komite etika
4. Sertakan ethical approval letter di appendix tesis

---

## ⚠️ Troubleshooting

### `401 Unauthorized` saat Login
- Cek username/password
- Instagram mungkin minta verifikasi — coba login via browser dulu
- Jika aktif 2FA, masukkan kode di opsi 2FA

### `429 Too Many Requests`
- Rate-limit Instagram aktif
- Tunggu 24-48 jam
- Increase delay antar hashtag/post
- Gunakan akun lain

### `Challenge Required`
- Instagram mendeteksi aktivitas tidak biasa
- Login via browser → verifikasi identitas
- Kurangi volume scraping

### Aplikasi Lambat
- Kurangi `Posts per Hashtag`
- Tambah delay antar request
- Jalankan di jaringan yang stabil (bukan WiFi publik)

---

## 📁 Struktur Proyek

```
mbg_scraper/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
├── README.md              # Dokumentasi ini
├── scraper_log.txt        # Log aktivitas (auto-generated)
└── .env                   # (opsional) Credentials storage
```

---

## 🎓 Referensi Teoritis

- Habermas, J. (1984). *The Theory of Communicative Action, Vol. 1*.
- Habermas, J. (1989). *The Structural Transformation of the Public Sphere*.
- Dahlberg, L. (2001). *The Internet and Democratic Discourse*.
- Fairclough, N. (2003). *Analysing Discourse*.

---

## 📞 Kontak

Untuk pertanyaan teknis atau akademik terkait tools ini:
- Pembimbing: Dr. Arie Qur'ania, M.Kom
- Komite Etika Riset Universitas

---

*Tools ini dibuat khusus untuk keperluan akademik. Pastikan selalu mematuhi etika penelitian, ToS Instagram, dan regulasi privasi data yang berlaku.*
