# 🚀 QUICK START: MBG Research Tool Simplified

**Versi ini TIDAK perlu login Instagram — input data manual.**

---

## 📦 Setup (2 Menit)

```bash
# 1. Masuk folder
cd mbg_scraper_simplified

# 2. Install dependencies
pip install -r requirements_simplified.txt

# 3. Jalankan app
streamlit run app_simplified.py
```

Browser akan otomatis buka: `http://localhost:8501`

---

## 🎯 Cara Pakai

### 1️⃣ Input Data (📝 Input Data)
```
Opsi A: Paste captions dari Instagram
├─ Buka Instagram post/hashtag di browser
├─ Copy caption text
├─ Paste ke form di app
└─ Klik "Add Captions"

Opsi B: Upload CSV
├─ Format: post_id, caption, likes_count, dll
└─ Klik upload → CSV akan ter-import

Opsi C: Paste comments
├─ Format: username: comment text
├─ Pisahkan dengan ---
└─ Klik "Add Comments"
```

### 2️⃣ Coding Framework (🏷️ Coding)
```
1. Pilih status filter (belum dikode / semua / sudah dikode)
2. Lihat comment satu per satu
3. Pilih kategori Habermas:
   - FAC = Factual (data, statistik)
   - NOR = Normative (nilai, kebijakan)
   - EMP = Emotional (cerita pribadi)
   - DIA = Dialogical (respon argumen)
   - NON = Non-Communicative (spam, ad hominem)
4. Klik tombol save
5. Lanjut ke comment berikutnya
```

### 3️⃣ Analisis (📈 Analisis)
```
Lihat:
- Distribusi kategori (berapa FAC, NOR, dll)
- Bar chart kategorisasi
- DRS Score (Deliberative Rationality Score)
- Interpretasi hasil
```

### 4️⃣ Export (📤 Export)
```
Download:
- Posts CSV (untuk analisis lanjutan)
- Comments CSV (dengan habermas_code)
- Metadata JSON (dokumentasi research)
```

---

## 💡 Contoh Workflow

**Hari 1:**
```
1. Buka Instagram explore/hashtag
2. Copy 10-20 captions interesting
3. Paste di "Input Data → Paste Captions"
4. Lihat preview di "Preview"
5. Export CSV
```

**Hari 2-3:**
```
1. Dari setiap post yang ada, copy comments
2. Paste di "Input Data → Paste Comments"
3. Auto-organize, username di-anonimasi
```

**Hari 4-7:**
```
1. Ke "Coding Framework"
2. Coding satu-per-satu
3. Tracking progress
```

**Hari 8:**
```
1. Lihat analisis di "Analisis"
2. Cek DRS Score
3. Export semua data
```

---

## ✨ Fitur

✅ **Tanpa login Instagram** — Aman, no API issues
✅ **Input manual** — Fleksibel, bisa dari mana saja
✅ **Auto-anonymisasi** — Username di-hash MD5
✅ **Habermas coding** — 5 kategori argumentasi
✅ **DRS Score** — Deliberative Rationality Score
✅ **Progress tracking** — Lihat berapa yang sudah dikode
✅ **Export CSV & JSON** — Siap untuk analisis lanjutan

---

## 📋 Data Format

### Untuk Paste Captions:
```
Caption 1 text here...
---
Caption 2 text here...
---
Caption 3 text here...
```

### Untuk CSV Upload:
```
post_id,caption,likes_count,comments_count,posted_date
POST_0001,"Anak bisa fokus belajar...",100,25,2024-01-15
POST_0002,"Program MBG sangat membantu...",200,50,2024-01-20
```

### Untuk Paste Comments:
```
username1: Bagus sekali programnya!
---
username2: Setuju, sangat membantu anak saya
---
user_abc: Kapan dimulainya?
```

---

## 🎓 Framework Habermas

**5 Kategori Argumentasi:**

| Kode | Nama | Validity Claim | Indikator |
|------|------|----------------|-----------|
| FAC | Factual | Truthfulness | Data, statistik, sumber |
| NOR | Normative | Rightness | Nilai, norma, kebijakan |
| EMP | Emotional | Sincerity | Cerita pribadi, pengalaman |
| DIA | Dialogical | Deliberation | Respon kritis argumen lain |
| NON | Non-Communicative | Absent | Spam, ad hominem, trolling |

---

## ⏱️ Waktu

- **Setup:** 2 menit
- **Input 100 captions:** 10-15 menit
- **Input 100 comments:** 10-15 menit
- **Coding 300 comments:** 4-6 jam
- **Analisis & export:** 10 menit

---

## ✅ Keuntungan dibanding versi original

✅ **Tidak perlu login Instagram** — Menghindari security issues
✅ **Simpel** — Fokus pada data organization & coding
✅ **Fleksibel** — Input data dari berbagai sumber
✅ **Reliable** — Tidak ada API rate-limit
✅ **Tetap proper** — Framework Habermas tetap intact
✅ **Cepat mulai** — Bisa langsung pakai hari ini

---

## 🚀 Mulai sekarang!

```bash
cd mbg_scraper_simplified
pip install -r requirements_simplified.txt
streamlit run app_simplified.py
```

Good luck! 🎓
