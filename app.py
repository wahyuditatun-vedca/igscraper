#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STREAMLIT APP - INSTAGRAM SCRAPER UNTUK PENELITIAN DELIBERATIVE RATIONALITY
Penelitian: Analisis Wacana Rasional Program Makan Bergizi Gratis (MBG) di Instagram
Framework: Habermas Public Sphere & Communicative Rationality

Author   : Tatun (Mahasiswa S2 Ilmu Komputer)
Pembimbing: Dr. Arie Qur'ania, M.Kom
Purpose  : Tools scraping untuk pengumpulan data thesis

CATATAN PENTING:
- Tools ini hanya untuk keperluan akademik
- Wajib mendapat approval komite etika sebelum digunakan
- Data user di-anonimasi otomatis menggunakan hash
- Hanya mengumpulkan data publik (caption & komentar publik)
"""

import streamlit as st
import pandas as pd
import json
import hashlib
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging
import io

# ============================================================================
# SETUP LOGGING
# ============================================================================

LOG_FILE = "scraper_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# KONFIGURASI HALAMAN
# ============================================================================

st.set_page_config(
    page_title="MBG Research Scraper",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan akademik
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1f3a5f;
        border-bottom: 3px solid #1f3a5f;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #2c5282;
        font-weight: 600;
        margin-top: 1rem;
    }
    .info-box {
        background-color: #ebf8ff;
        border-left: 4px solid #3182ce;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fffaf0;
        border-left: 4px solid #dd6b20;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #f0fff4;
        border-left: 4px solid #38a169;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f7fafc;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def anonymize_username(username: str) -> str:
    """Anonimasi username menggunakan MD5 hash (reproducible tapi tidak reversible)."""
    if not username:
        return "USER_ANONYMOUS"
    return 'USER_' + hashlib.md5(username.encode()).hexdigest()[:8].upper()


def clean_text(text: str) -> str:
    """Bersihkan teks dari karakter yang mengganggu CSV."""
    if not text:
        return ""
    return text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()


def init_session_state():
    """Inisialisasi session state untuk menyimpan data antar halaman."""
    defaults = {
        'logged_in': False,
        'client': None,
        'posts_data': [],
        'comments_data': [],
        'scraping_errors': [],
        'session_started': None,
        'last_scrape_time': None,
        'login_username': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================================
# INSTAGRAPI HANDLER (dengan graceful import)
# ============================================================================

def try_import_instagrapi():
    """Coba import instagrapi, return None jika belum terinstall."""
    try:
        from instagrapi import Client
        return Client
    except ImportError:
        return None


def perform_login(username: str, password: str, verification_code: str = ""):
    """Login ke Instagram dengan handling 2FA/challenge."""
    Client = try_import_instagrapi()
    if Client is None:
        return False, "Library 'instagrapi' belum terinstall. Jalankan: pip install instagrapi"

    try:
        client = Client()
        client.delay_range = [1, 3]  # Natural delay

        if verification_code:
            client.login(username, password, verification_code=verification_code)
        else:
            client.login(username, password)

        st.session_state.client = client
        st.session_state.logged_in = True
        st.session_state.login_username = username
        st.session_state.session_started = datetime.now()
        logger.info(f"Login berhasil untuk user: {username}")
        return True, "Login berhasil!"
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Login gagal: {error_msg}")
        return False, f"Login gagal: {error_msg}"


def scrape_hashtag_posts(hashtag: str, amount: int, timeframe_days: int, progress_callback=None):
    """Scrape posts dari sebuah hashtag dengan progress tracking."""
    client = st.session_state.client
    if client is None:
        return [], ["Belum login"]

    posts = []
    errors = []
    cutoff_date = datetime.now() - timedelta(days=timeframe_days)

    try:
        # Bersihkan hashtag dari # dan spasi
        clean_hashtag = hashtag.replace('#', '').replace(' ', '').strip().lower()
        logger.info(f"Scraping hashtag: #{clean_hashtag} (target: {amount} posts)")

        medias = client.hashtag_medias_recent(clean_hashtag, amount=amount)
        total = len(medias)

        for idx, media in enumerate(medias, 1):
            try:
                # Filter timeframe
                taken_at = media.taken_at.replace(tzinfo=None) if media.taken_at.tzinfo else media.taken_at
                if taken_at < cutoff_date:
                    continue

                caption = media.caption_text if hasattr(media, 'caption_text') else (media.caption or '')
                hashtags_list = []
                if hasattr(media, 'caption_hashtags') and media.caption_hashtags:
                    hashtags_list = media.caption_hashtags

                engagement = calculate_engagement(media)

                post_data = {
                    'post_id': str(media.id),
                    'source_hashtag': clean_hashtag,
                    'caption': clean_text(caption),
                    'likes_count': media.like_count or 0,
                    'comments_count': media.comment_count or 0,
                    'posted_date': taken_at.isoformat(),
                    'posted_timestamp': int(taken_at.timestamp()),
                    'hashtags': ','.join(hashtags_list),
                    'media_type': str(media.media_type),
                    'engagement_rate': engagement,
                    'post_url': f"https://instagram.com/p/{media.code}/" if hasattr(media, 'code') else '',
                }
                posts.append(post_data)

                if progress_callback:
                    progress_callback(idx / total, f"Post {idx}/{total} dari #{clean_hashtag}")

                time.sleep(1)  # Small delay per post iteration

            except Exception as e:
                errors.append(f"Post error: {str(e)}")
                continue

    except Exception as e:
        err = f"Gagal scrape #{hashtag}: {str(e)}"
        logger.error(err)
        errors.append(err)

    return posts, errors


def scrape_post_comments(post_id: str, amount: int):
    """Scrape comments dari sebuah post."""
    client = st.session_state.client
    if client is None:
        return [], ["Belum login"]

    comments = []
    errors = []

    try:
        comment_list = client.media_comments(media_id=post_id, amount=amount)
        for comment in comment_list:
            try:
                username = comment.user.username if hasattr(comment, 'user') and comment.user else 'unknown'
                created = comment.created_at_utc if hasattr(comment, 'created_at_utc') else comment.created_at

                comment_data = {
                    'post_id': post_id,
                    'comment_id': str(comment.pk),
                    'comment_text': clean_text(comment.text),
                    'comment_likes': getattr(comment, 'like_count', 0) or 0,
                    'user_id_anonymized': anonymize_username(username),
                    'timestamp': created.isoformat() if created else '',
                }
                comments.append(comment_data)
            except Exception as e:
                errors.append(f"Comment parse error: {str(e)}")
                continue

    except Exception as e:
        errors.append(f"Gagal scrape comments post {post_id}: {str(e)}")

    return comments, errors


def calculate_engagement(media) -> float:
    """Hitung estimasi engagement rate."""
    likes = media.like_count or 0
    comments = media.comment_count or 0
    total = likes + comments
    est_reach = likes * 10 if likes > 0 else 1
    return round((total / est_reach) * 100, 2) if est_reach > 0 else 0.0


# ============================================================================
# HALAMAN: BERANDA
# ============================================================================

def page_beranda():
    st.markdown('<p class="main-header">🔬 MBG Research Scraper</p>', unsafe_allow_html=True)
    st.markdown("**Tools Pengumpulan Data Instagram untuk Penelitian Deliberative Rationality**")

    st.markdown("""
    <div class="info-box">
    <b>Tentang Tools Ini</b><br>
    Aplikasi ini dirancang khusus untuk penelitian thesis S2 Ilmu Komputer dengan topik
    <i>"Analisis Wacana Rasional Program Makan Bergizi Gratis (MBG) di Instagram"</i>
    menggunakan kerangka teori Habermas tentang Public Sphere dan Communicative Rationality.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status Login", "✓ Aktif" if st.session_state.logged_in else "✗ Belum Login")
    with col2:
        st.metric("Posts Terkumpul", len(st.session_state.posts_data))
    with col3:
        st.metric("Comments Terkumpul", len(st.session_state.comments_data))

    st.markdown('<p class="sub-header">📋 Alur Kerja Penelitian</p>', unsafe_allow_html=True)

    workflow = [
        ("1️⃣", "Login Instagram", "Autentikasi akun Instagram untuk akses API"),
        ("2️⃣", "Konfigurasi Hashtag", "Tentukan hashtag target (#makanbergizigratis, dll)"),
        ("3️⃣", "Scrape Posts", "Kumpulkan posts berdasarkan hashtag dan timeframe"),
        ("4️⃣", "Scrape Comments", "Kumpulkan komentar untuk analisis deliberatif"),
        ("5️⃣", "Coding Framework", "Klasifikasi komentar berdasarkan tipe argumentasi Habermas"),
        ("6️⃣", "Export Data", "Unduh dataset dalam format CSV & JSON metadata"),
    ]

    for emoji, title, desc in workflow:
        st.markdown(f"**{emoji} {title}** — {desc}")

    st.markdown('<p class="sub-header">⚠️ Checklist Etika Penelitian</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="warning-box">
    <b>Sebelum menjalankan scraping, pastikan:</b>
    <ul>
        <li>✓ Sudah konsultasi dengan Dr. Arie Qur'ania, M.Kom</li>
        <li>✓ Mendapat approval dari komite etika riset universitas</li>
        <li>✓ Hanya mengumpulkan data publik</li>
        <li>✓ Username user akan di-anonimasi otomatis (hash MD5)</li>
        <li>✓ Data tidak akan dipublikasikan tanpa izin eksplisit</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="sub-header">🎯 Framework Teoritis</p>', unsafe_allow_html=True)

    framework_df = pd.DataFrame({
        'Kategori Argumentasi': ['Factual Argument', 'Normative Argument', 'Emotional/Personal',
                                 'Dialogical Response', 'Non-Communicative'],
        'Kode': ['FAC', 'NOR', 'EMP', 'DIA', 'NON'],
        'Validity Claim (Habermas)': ['Truthfulness', 'Rightness', 'Sincerity', 'Deliberation', 'Absent'],
        'Indikator': [
            'Data, statistik, sumber referensi',
            'Nilai, norma, kebijakan',
            'Pengalaman pribadi, cerita',
            'Merespon argumen lain secara kritis',
            'Ad hominem, spam, trolling'
        ]
    })
    st.dataframe(framework_df, use_container_width=True, hide_index=True)


# ============================================================================
# HALAMAN: LOGIN
# ============================================================================

def page_login():
    st.markdown('<p class="main-header">🔐 Login Instagram</p>', unsafe_allow_html=True)

    if try_import_instagrapi() is None:
        st.error("Library `instagrapi` belum terinstall!")
        st.code("pip install instagrapi", language="bash")
        st.info("Setelah install, restart aplikasi Streamlit.")
        return

    if st.session_state.logged_in:
        st.markdown(f"""
        <div class="success-box">
        ✓ <b>Sudah login</b> sebagai: <code>{st.session_state.login_username}</code><br>
        Session dimulai: {st.session_state.session_started.strftime('%d %B %Y, %H:%M:%S')}
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Logout", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.client = None
            st.session_state.login_username = None
            st.rerun()
        return

    st.markdown("""
    <div class="warning-box">
    <b>Rekomendasi:</b> Gunakan akun Instagram terpisah khusus untuk penelitian
    (bukan akun utama) untuk menghindari risiko rate-limit atau suspend.
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username Instagram", placeholder="contoh: tatun_research")
        password = st.text_input("Password", type="password")

        with st.expander("🔒 Opsi 2FA (Two-Factor Authentication)"):
            verification_code = st.text_input(
                "Kode Verifikasi (isi hanya jika akun Anda aktif 2FA)",
                placeholder="6 digit kode"
            )

        submitted = st.form_submit_button("🔓 Login", type="primary")

        if submitted:
            if not username or not password:
                st.error("Username dan password harus diisi")
            else:
                with st.spinner("Melakukan autentikasi..."):
                    success, message = perform_login(username, password, verification_code)
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
                        if "challenge" in message.lower() or "2fa" in message.lower():
                            st.info("Instagram meminta verifikasi. Cek email/SMS, masukkan kode di bagian 2FA.")

    st.markdown("---")
    st.markdown("**Catatan Keamanan:**")
    st.caption("""
    • Kredensial hanya disimpan di session memory, tidak di disk  
    • Gunakan `.env` file jika deploy aplikasi ini ke server  
    • JANGAN commit kredensial ke repository Git
    """)


# ============================================================================
# HALAMAN: SCRAPE POSTS
# ============================================================================

def page_scrape_posts():
    st.markdown('<p class="main-header">📥 Scrape Posts dari Hashtag</p>', unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("⚠️ Silakan login terlebih dahulu di halaman Login.")
        return

    st.markdown("**Konfigurasi Scraping**")

    # Default hashtags untuk MBG
    default_hashtags = [
        "makanbergizigratis",
        "makanbergizigratisdki",
        "mbgindonesia",
        "programmbg",
        "makangizigratissekolah"
    ]

    col1, col2 = st.columns([2, 1])
    with col1:
        hashtag_input = st.text_area(
            "Daftar Hashtag (satu per baris, tanpa #)",
            value="\n".join(default_hashtags),
            height=150,
            help="Masukkan hashtag target untuk penelitian MBG"
        )

    with col2:
        posts_per_hashtag = st.number_input(
            "Posts per Hashtag",
            min_value=10, max_value=2000, value=200, step=50,
            help="Rekomendasi: 200-500 per hashtag"
        )
        timeframe_days = st.number_input(
            "Timeframe (hari)",
            min_value=7, max_value=365, value=180, step=30,
            help="Posts dari berapa hari terakhir"
        )
        delay_between = st.number_input(
            "Delay antar Hashtag (detik)",
            min_value=5, max_value=60, value=15, step=5,
            help="Hindari rate limit Instagram"
        )

    hashtags = [h.strip().replace('#', '') for h in hashtag_input.split('\n') if h.strip()]

    st.markdown(f"**Ringkasan:** {len(hashtags)} hashtag × {posts_per_hashtag} posts = maksimal **{len(hashtags) * posts_per_hashtag} posts**")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        start_button = st.button("🚀 Mulai Scraping Posts", type="primary", use_container_width=True)
    with col2:
        if st.session_state.posts_data:
            if st.button("🗑️ Hapus Data Posts Lama", use_container_width=True):
                st.session_state.posts_data = []
                st.rerun()

    if start_button:
        if not hashtags:
            st.error("Masukkan minimal satu hashtag")
            return

        progress_bar = st.progress(0.0)
        status_text = st.empty()
        error_placeholder = st.empty()

        all_posts = []
        all_errors = []

        for i, hashtag in enumerate(hashtags):
            status_text.info(f"🔍 Scraping #{hashtag} ({i+1}/{len(hashtags)})")

            def update_progress(pct, msg):
                overall = (i + pct) / len(hashtags)
                progress_bar.progress(min(overall, 1.0))
                status_text.info(f"[{i+1}/{len(hashtags)}] {msg}")

            posts, errors = scrape_hashtag_posts(
                hashtag, posts_per_hashtag, timeframe_days, update_progress
            )
            all_posts.extend(posts)
            all_errors.extend(errors)

            status_text.success(f"✓ #{hashtag}: {len(posts)} posts terkumpul")

            if i < len(hashtags) - 1:
                status_text.info(f"⏱️ Menunggu {delay_between} detik sebelum hashtag berikutnya...")
                time.sleep(delay_between)

        # Deduplikasi berdasarkan post_id
        seen = set()
        unique_posts = []
        for p in all_posts:
            if p['post_id'] not in seen:
                seen.add(p['post_id'])
                unique_posts.append(p)

        st.session_state.posts_data.extend(unique_posts)
        st.session_state.scraping_errors.extend(all_errors)
        st.session_state.last_scrape_time = datetime.now()

        progress_bar.progress(1.0)
        status_text.empty()

        st.success(f"✅ Selesai! Total **{len(unique_posts)} unique posts** terkumpul (dari {len(all_posts)} total)")
        if all_errors:
            with st.expander(f"⚠️ Errors ({len(all_errors)})"):
                for err in all_errors[:20]:
                    st.code(err)

    # Preview data
    if st.session_state.posts_data:
        st.markdown("---")
        st.markdown('<p class="sub-header">📊 Preview Data Posts</p>', unsafe_allow_html=True)

        df = pd.DataFrame(st.session_state.posts_data)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Posts", len(df))
        with col2:
            st.metric("Total Likes", f"{df['likes_count'].sum():,}")
        with col3:
            st.metric("Total Comments", f"{df['comments_count'].sum():,}")
        with col4:
            st.metric("Avg Engagement", f"{df['engagement_rate'].mean():.2f}%")

        preview_cols = ['post_id', 'source_hashtag', 'caption', 'likes_count', 'comments_count', 'posted_date']
        display_df = df[preview_cols].copy()
        display_df['caption'] = display_df['caption'].str[:100] + '...'
        st.dataframe(display_df, use_container_width=True, hide_index=True)


# ============================================================================
# HALAMAN: SCRAPE COMMENTS
# ============================================================================

def page_scrape_comments():
    st.markdown('<p class="main-header">💬 Scrape Comments</p>', unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("⚠️ Silakan login terlebih dahulu.")
        return

    if not st.session_state.posts_data:
        st.warning("⚠️ Belum ada data posts. Silakan scrape posts terlebih dahulu di halaman 'Scrape Posts'.")
        return

    st.markdown(f"**Posts tersedia:** {len(st.session_state.posts_data)} posts siap di-scrape comments-nya")

    col1, col2 = st.columns(2)
    with col1:
        comments_per_post = st.number_input(
            "Comments per Post",
            min_value=10, max_value=500, value=50, step=10,
            help="Rekomendasi: 50-100 untuk analisis deliberatif"
        )
    with col2:
        delay_between_posts = st.number_input(
            "Delay antar Post (detik)",
            min_value=1, max_value=30, value=3, step=1
        )

    # Filter posts
    st.markdown("**Filter Posts (opsional)**")
    col1, col2 = st.columns(2)
    with col1:
        min_comments = st.number_input(
            "Minimum Comments Count",
            min_value=0, max_value=10000, value=5, step=5,
            help="Hanya scrape post yang punya minimal N comments"
        )
    with col2:
        max_posts_to_process = st.number_input(
            "Maksimum Posts Diproses",
            min_value=1, max_value=len(st.session_state.posts_data),
            value=min(100, len(st.session_state.posts_data)), step=10
        )

    # Hitung estimasi
    df_posts = pd.DataFrame(st.session_state.posts_data)
    filtered = df_posts[df_posts['comments_count'] >= min_comments].head(max_posts_to_process)
    st.info(f"📊 **{len(filtered)} posts** akan diproses, estimasi **~{len(filtered) * comments_per_post} comments** (maksimal)")

    col1, col2 = st.columns(2)
    with col1:
        start_button = st.button("💬 Mulai Scrape Comments", type="primary", use_container_width=True)
    with col2:
        if st.session_state.comments_data:
            if st.button("🗑️ Hapus Comments Lama", use_container_width=True):
                st.session_state.comments_data = []
                st.rerun()

    if start_button:
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        all_comments = []
        all_errors = []
        total = len(filtered)

        for idx, (_, post) in enumerate(filtered.iterrows(), 1):
            post_id = post['post_id']
            status_text.info(f"💬 [{idx}/{total}] Scrape comments dari post {post_id}")

            comments, errors = scrape_post_comments(post_id, comments_per_post)

            # Tambahkan preview caption ke setiap comment untuk kontek
            caption_preview = post['caption'][:60] + '...' if len(post['caption']) > 60 else post['caption']
            for c in comments:
                c['post_caption_preview'] = caption_preview
                c['source_hashtag'] = post.get('source_hashtag', '')

            all_comments.extend(comments)
            all_errors.extend(errors)

            progress_bar.progress(idx / total)
            time.sleep(delay_between_posts)

        st.session_state.comments_data.extend(all_comments)
        st.session_state.scraping_errors.extend(all_errors)

        progress_bar.progress(1.0)
        status_text.empty()

        st.success(f"✅ Selesai! **{len(all_comments)} comments** terkumpul dari {total} posts")
        if all_errors:
            with st.expander(f"⚠️ Errors ({len(all_errors)})"):
                for err in all_errors[:20]:
                    st.code(err)

    # Preview
    if st.session_state.comments_data:
        st.markdown("---")
        st.markdown('<p class="sub-header">📊 Preview Comments</p>', unsafe_allow_html=True)

        df = pd.DataFrame(st.session_state.comments_data)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Comments", len(df))
        with col2:
            st.metric("Unique Users (hashed)", df['user_id_anonymized'].nunique())
        with col3:
            st.metric("Avg Comment Length",
                      f"{df['comment_text'].str.len().mean():.0f} karakter")

        display_cols = ['post_id', 'user_id_anonymized', 'comment_text', 'comment_likes', 'timestamp']
        display_df = df[display_cols].copy()
        display_df['comment_text'] = display_df['comment_text'].str[:150] + '...'
        st.dataframe(display_df, use_container_width=True, hide_index=True)


# ============================================================================
# HALAMAN: CODING FRAMEWORK
# ============================================================================

def page_coding():
    st.markdown('<p class="main-header">🏷️ Coding Framework Habermas</p>', unsafe_allow_html=True)

    if not st.session_state.comments_data:
        st.warning("⚠️ Belum ada data comments. Silakan scrape comments terlebih dahulu.")
        return

    st.markdown("""
    <div class="info-box">
    <b>Manual Coding untuk Analisis Deliberative Rationality</b><br>
    Klasifikasi setiap komentar berdasarkan 5 kategori argumentasi Habermas.
    Coding manual diperlukan untuk reliabilitas penelitian (Cohen's Kappa).
    </div>
    """, unsafe_allow_html=True)

    df = pd.DataFrame(st.session_state.comments_data)

    # Initialize coding column jika belum ada
    if 'habermas_code' not in df.columns:
        df['habermas_code'] = 'UNCODED'
    else:
        df['habermas_code'] = df['habermas_code'].fillna('UNCODED')

    # Statistik coding
    st.markdown('<p class="sub-header">📊 Progress Coding</p>', unsafe_allow_html=True)

    code_counts = df['habermas_code'].value_counts()
    coded_count = len(df[df['habermas_code'] != 'UNCODED'])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Comments", len(df))
    with col2:
        st.metric("Sudah Di-coding", coded_count)
    with col3:
        progress_pct = (coded_count / len(df) * 100) if len(df) > 0 else 0
        st.metric("Progress", f"{progress_pct:.1f}%")

    # Distribusi coding
    if coded_count > 0:
        coded_df = df[df['habermas_code'] != 'UNCODED']
        dist = coded_df['habermas_code'].value_counts().reset_index()
        dist.columns = ['Kode', 'Jumlah']
        dist['Persentase'] = (dist['Jumlah'] / dist['Jumlah'].sum() * 100).round(2)

        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("**Distribusi Kategori**")
            st.dataframe(dist, hide_index=True, use_container_width=True)
        with col2:
            st.bar_chart(dist.set_index('Kode')['Jumlah'])

    st.markdown("---")
    st.markdown('<p class="sub-header">✏️ Coding Interface</p>', unsafe_allow_html=True)

    # Filter untuk coding
    col1, col2 = st.columns(2)
    with col1:
        filter_status = st.selectbox(
            "Filter Status",
            ["Hanya yang belum di-coding", "Semua comments", "Hanya yang sudah di-coding"]
        )
    with col2:
        samples_per_page = st.number_input("Comments per halaman", min_value=1, max_value=20, value=5)

    if filter_status == "Hanya yang belum di-coding":
        working_df = df[df['habermas_code'] == 'UNCODED'].copy()
    elif filter_status == "Hanya yang sudah di-coding":
        working_df = df[df['habermas_code'] != 'UNCODED'].copy()
    else:
        working_df = df.copy()

    if len(working_df) == 0:
        st.info("Tidak ada comment sesuai filter.")
        return

    # Pagination
    total_pages = max(1, (len(working_df) - 1) // samples_per_page + 1)
    page = st.number_input(f"Halaman (1-{total_pages})", min_value=1, max_value=total_pages, value=1)

    start_idx = (page - 1) * samples_per_page
    end_idx = min(start_idx + samples_per_page, len(working_df))
    page_df = working_df.iloc[start_idx:end_idx]

    st.markdown(f"**Menampilkan comment {start_idx+1}-{end_idx} dari {len(working_df)}**")

    # Interface coding per comment
    code_options = {
        'UNCODED': 'Belum di-coding',
        'FAC': 'FAC - Factual Argument (data, statistik)',
        'NOR': 'NOR - Normative Argument (nilai, kebijakan)',
        'EMP': 'EMP - Emotional/Personal (cerita pribadi)',
        'DIA': 'DIA - Dialogical Response (respon argumen lain)',
        'NON': 'NON - Non-Communicative (spam, ad hominem)',
    }

    for idx, row in page_df.iterrows():
        with st.container():
            st.markdown(f"**Comment ID:** `{row['comment_id']}` | **User:** `{row['user_id_anonymized']}`")
            st.markdown(f"> {row['comment_text']}")

            col1, col2 = st.columns([3, 1])
            with col1:
                current_code = row['habermas_code']
                options_list = list(code_options.keys())
                current_idx = options_list.index(current_code) if current_code in options_list else 0

                new_code = st.selectbox(
                    "Kategori Habermas",
                    options=options_list,
                    format_func=lambda x: code_options[x],
                    index=current_idx,
                    key=f"code_{row['comment_id']}"
                )
            with col2:
                st.write("")
                st.write("")
                if st.button("💾 Save", key=f"save_{row['comment_id']}"):
                    # Update dalam session state
                    for item in st.session_state.comments_data:
                        if item['comment_id'] == row['comment_id']:
                            item['habermas_code'] = new_code
                            break
                    st.success("Tersimpan!")
                    time.sleep(0.3)
                    st.rerun()

            st.markdown("---")

    # Bulk action
    st.markdown('<p class="sub-header">⚡ Bulk Actions</p>', unsafe_allow_html=True)
    with st.expander("Import coding dari CSV eksternal"):
        st.caption("Jika Anda menggunakan NVivo/ATLAS.ti atau coding manual di Excel, upload CSV dengan kolom `comment_id` dan `habermas_code`.")
        uploaded_coding = st.file_uploader("Upload CSV coding", type=['csv'], key="coding_upload")
        if uploaded_coding is not None:
            try:
                coding_df = pd.read_csv(uploaded_coding)
                if 'comment_id' in coding_df.columns and 'habermas_code' in coding_df.columns:
                    updated = 0
                    code_map = dict(zip(coding_df['comment_id'].astype(str), coding_df['habermas_code']))
                    for item in st.session_state.comments_data:
                        if item['comment_id'] in code_map:
                            item['habermas_code'] = code_map[item['comment_id']]
                            updated += 1
                    st.success(f"✓ {updated} codes berhasil di-import")
                else:
                    st.error("CSV harus punya kolom `comment_id` dan `habermas_code`")
            except Exception as e:
                st.error(f"Error: {e}")


# ============================================================================
# HALAMAN: EXPORT DATA
# ============================================================================

def page_export():
    st.markdown('<p class="main-header">📤 Export Data Penelitian</p>', unsafe_allow_html=True)

    if not st.session_state.posts_data and not st.session_state.comments_data:
        st.warning("⚠️ Belum ada data untuk di-export. Silakan scrape data terlebih dahulu.")
        return

    st.markdown("""
    <div class="info-box">
    <b>Export data untuk analisis lanjutan</b><br>
    Data dapat di-export ke format CSV (untuk NVivo, ATLAS.ti, atau Excel) atau JSON (untuk dokumentasi).
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Export Posts
    with col1:
        st.markdown('<p class="sub-header">📝 Posts Data</p>', unsafe_allow_html=True)
        if st.session_state.posts_data:
            df_posts = pd.DataFrame(st.session_state.posts_data)
            st.write(f"**{len(df_posts)} posts** siap di-export")

            csv_posts = df_posts.to_csv(index=False, encoding='utf-8').encode('utf-8')
            st.download_button(
                "⬇️ Download Posts (CSV)",
                data=csv_posts,
                file_name=f"mbg_posts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

            json_posts = df_posts.to_json(orient='records', indent=2, force_ascii=False).encode('utf-8')
            st.download_button(
                "⬇️ Download Posts (JSON)",
                data=json_posts,
                file_name=f"mbg_posts_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.info("Belum ada data posts")

    # Export Comments
    with col2:
        st.markdown('<p class="sub-header">💬 Comments Data</p>', unsafe_allow_html=True)
        if st.session_state.comments_data:
            df_comments = pd.DataFrame(st.session_state.comments_data)
            st.write(f"**{len(df_comments)} comments** siap di-export")

            csv_comments = df_comments.to_csv(index=False, encoding='utf-8').encode('utf-8')
            st.download_button(
                "⬇️ Download Comments (CSV)",
                data=csv_comments,
                file_name=f"mbg_comments_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

            json_comments = df_comments.to_json(orient='records', indent=2, force_ascii=False).encode('utf-8')
            st.download_button(
                "⬇️ Download Comments (JSON)",
                data=json_comments,
                file_name=f"mbg_comments_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.info("Belum ada data comments")

    st.markdown("---")

    # Metadata untuk transparansi penelitian
    st.markdown('<p class="sub-header">📋 Research Metadata</p>', unsafe_allow_html=True)

    metadata = {
        "research_info": {
            "title": "Analisis Wacana Rasional Program Makan Bergizi Gratis (MBG) di Instagram",
            "framework": "Habermas Public Sphere & Communicative Rationality",
            "researcher": "Tatun (S2 Ilmu Komputer)",
            "supervisor": "Dr. Arie Qur'ania, M.Kom",
            "paradigm": "Interpretivist"
        },
        "session_info": {
            "session_started": st.session_state.session_started.isoformat() if st.session_state.session_started else None,
            "export_timestamp": datetime.now().isoformat(),
            "login_account_anonymized": anonymize_username(st.session_state.login_username or "")
        },
        "collection_stats": {
            "total_posts": len(st.session_state.posts_data),
            "total_comments": len(st.session_state.comments_data),
            "total_errors": len(st.session_state.scraping_errors)
        },
        "ethical_note": (
            "Data dikumpulkan untuk keperluan akademik. "
            "Semua username di-anonimasi menggunakan MD5 hash. "
            "Hanya data publik yang dikumpulkan (captions dan komentar publik). "
            "Penelitian telah/akan mendapat approval dari komite etika universitas."
        )
    }

    # Tambahkan distribusi coding jika ada
    if st.session_state.comments_data:
        df_comm = pd.DataFrame(st.session_state.comments_data)
        if 'habermas_code' in df_comm.columns:
            coded = df_comm[df_comm['habermas_code'] != 'UNCODED']
            if len(coded) > 0:
                metadata["coding_distribution"] = coded['habermas_code'].value_counts().to_dict()
                metadata["coding_progress"] = f"{len(coded)}/{len(df_comm)} ({len(coded)/len(df_comm)*100:.1f}%)"

    st.json(metadata)

    metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False).encode('utf-8')
    st.download_button(
        "⬇️ Download Metadata (JSON)",
        data=metadata_json,
        file_name=f"mbg_metadata_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json"
    )

    # Analisis quick stats
    if st.session_state.comments_data:
        df_comm = pd.DataFrame(st.session_state.comments_data)
        if 'habermas_code' in df_comm.columns:
            coded = df_comm[df_comm['habermas_code'] != 'UNCODED']
            if len(coded) > 0:
                st.markdown("---")
                st.markdown('<p class="sub-header">📈 Quick Analysis — Deliberative Rationality Score</p>',
                            unsafe_allow_html=True)

                code_counts = coded['habermas_code'].value_counts()
                total_coded = len(coded)

                fac_pct = (code_counts.get('FAC', 0) / total_coded) * 100
                dia_pct = (code_counts.get('DIA', 0) / total_coded) * 100
                nor_pct = (code_counts.get('NOR', 0) / total_coded) * 100
                emp_pct = (code_counts.get('EMP', 0) / total_coded) * 100
                non_pct = (code_counts.get('NON', 0) / total_coded) * 100

                # Deliberative Rationality Score (DRS) — weighted composite
                drs = (fac_pct * 0.3 + dia_pct * 0.3 + nor_pct * 0.2 + emp_pct * 0.1 - non_pct * 0.3)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("DRS Score", f"{drs:.1f}",
                              help="Deliberative Rationality Score: komposit weighted dari kategori argumentasi")
                with col2:
                    st.metric("Factual+Dialogical", f"{fac_pct + dia_pct:.1f}%",
                              help="Indikator utama deliberasi rasional")
                with col3:
                    st.metric("Non-Communicative", f"{non_pct:.1f}%",
                              help="Indikator distorsi komunikasi")

                interpretation = ""
                if drs >= 60:
                    interpretation = "🟢 **Tinggi** — Diskusi mencerminkan deliberative rationality yang kuat"
                elif drs >= 30:
                    interpretation = "🟡 **Sedang** — Ada elemen deliberatif, tapi masih campuran"
                else:
                    interpretation = "🔴 **Rendah** — Diskusi didominasi komunikasi non-deliberatif"

                st.markdown(f"**Interpretasi:** {interpretation}")
                st.caption("Catatan: DRS adalah indikator kuantitatif bantu. Analisis kualitatif mendalam tetap diperlukan untuk thesis.")


# ============================================================================
# HALAMAN: LOG & DIAGNOSTIK
# ============================================================================

def page_logs():
    st.markdown('<p class="main-header">📋 Log & Diagnostik</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📄 Log File", "⚠️ Errors", "🔧 Session State"])

    with tab1:
        st.markdown("**Log aktivitas scraping**")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log_content = f.read()
            st.text_area("Isi log", log_content, height=400)

            with open(LOG_FILE, 'rb') as f:
                st.download_button(
                    "⬇️ Download Log",
                    data=f.read(),
                    file_name=f"scraper_log_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )
        else:
            st.info("Belum ada log file")

    with tab2:
        if st.session_state.scraping_errors:
            st.markdown(f"**{len(st.session_state.scraping_errors)} errors tercatat**")
            for i, err in enumerate(st.session_state.scraping_errors, 1):
                st.code(f"[{i}] {err}")

            if st.button("🗑️ Clear Errors"):
                st.session_state.scraping_errors = []
                st.rerun()
        else:
            st.success("✓ Tidak ada error tercatat")

    with tab3:
        st.markdown("**Current Session State**")
        state_summary = {
            "logged_in": st.session_state.logged_in,
            "username": st.session_state.login_username,
            "session_started": str(st.session_state.session_started) if st.session_state.session_started else None,
            "posts_in_memory": len(st.session_state.posts_data),
            "comments_in_memory": len(st.session_state.comments_data),
            "errors_count": len(st.session_state.scraping_errors),
        }
        st.json(state_summary)

        st.markdown("---")
        st.warning("⚠️ Reset akan menghapus semua data di memory!")
        if st.button("🔄 Reset Semua Data", type="secondary"):
            for key in ['posts_data', 'comments_data', 'scraping_errors']:
                st.session_state[key] = []
            st.success("Data di-reset")
            time.sleep(1)
            st.rerun()


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    init_session_state()

    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🔬 MBG Research Scraper")
        st.caption("S2 Ilmu Komputer — Thesis Tools")
        st.markdown("---")

        page = st.radio(
            "Navigasi",
            [
                "🏠 Beranda",
                "🔐 Login",
                "📥 Scrape Posts",
                "💬 Scrape Comments",
                "🏷️ Coding Framework",
                "📤 Export Data",
                "📋 Log & Diagnostik",
            ],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.caption("**Status:**")
        if st.session_state.logged_in:
            st.success(f"✓ {st.session_state.login_username}")
        else:
            st.error("✗ Belum login")

        st.caption(f"📝 Posts: {len(st.session_state.posts_data)}")
        st.caption(f"💬 Comments: {len(st.session_state.comments_data)}")

        st.markdown("---")
        st.caption("""
        **Framework:**  
        Habermas Public Sphere  
        Communicative Rationality
        """)

    # Route ke halaman yang sesuai
    if "Beranda" in page:
        page_beranda()
    elif "Login" in page:
        page_login()
    elif "Scrape Posts" in page:
        page_scrape_posts()
    elif "Scrape Comments" in page:
        page_scrape_comments()
    elif "Coding" in page:
        page_coding()
    elif "Export" in page:
        page_export()
    elif "Log" in page:
        page_logs()


if __name__ == "__main__":
    main()
