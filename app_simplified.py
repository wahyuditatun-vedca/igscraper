#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STREAMLIT APP — MBG RESEARCH (SIMPLIFIED VERSION)
Tanpa Login Instagram — Input Manual dari User

Fokus pada:
1. Data organization (copy-paste dari Instagram)
2. Habermas coding framework
3. Analysis & export

Author: Claude AI
For: Tatun (S2 Ilmu Komputer)
Supervisor: Dr. Arie Qur'ania, M.Kom
"""

import streamlit as st
import pandas as pd
import json
import hashlib
from datetime import datetime
from pathlib import Path
import io

# ============================================================================
# SETUP
# ============================================================================

st.set_page_config(
    page_title="MBG Research - Data Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .info-box {
        background-color: #ebf8ff;
        border-left: 4px solid #3182ce;
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
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================

if 'posts_data' not in st.session_state:
    st.session_state.posts_data = []
if 'comments_data' not in st.session_state:
    st.session_state.comments_data = []

def anonymize_username(username: str) -> str:
    """Hash username untuk anonymisasi"""
    if not username or username.strip() == '':
        return "USER_ANONYMOUS"
    return 'USER_' + hashlib.md5(username.encode()).hexdigest()[:8].upper()

# ============================================================================
# HALAMAN: BERANDA
# ============================================================================

def page_beranda():
    st.markdown('<p class="main-header">🔬 MBG Research — Data Analysis Tool</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <b>Tools untuk Penelitian Deliberative Rationality</b><br>
    Versi Simplified: Input data manual, fokus pada coding & analysis.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Posts", len(st.session_state.posts_data))
    with col2:
        st.metric("Comments", len(st.session_state.comments_data))
    with col3:
        if st.session_state.comments_data:
            coded = len([c for c in st.session_state.comments_data if c.get('habermas_code', 'UNCODED') != 'UNCODED'])
            st.metric("Coded", f"{coded}/{len(st.session_state.comments_data)}")
        else:
            st.metric("Coded", "0/0")

    st.markdown("---")
    st.markdown("**📋 Alur Kerja**")
    st.write("""
    1. **📝 Input Data** — Paste captions & comments dari Instagram
    2. **🏷️ Coding Framework** — Klasifikasi dengan 5 kategori Habermas
    3. **📊 Analisis** — Lihat distribusi & DRS Score
    4. **📤 Export** — Download CSV & metadata
    """)

    st.markdown("---")
    st.markdown("**🎓 Framework Habermas (5 Kategori)**")
    framework_df = pd.DataFrame({
        'Kategori': ['Factual Argument', 'Normative Argument', 'Emotional/Personal', 'Dialogical Response', 'Non-Communicative'],
        'Kode': ['FAC', 'NOR', 'EMP', 'DIA', 'NON'],
        'Indikator': [
            'Data, statistik, sumber',
            'Nilai, norma, kebijakan',
            'Cerita pribadi, pengalaman',
            'Respon argumen lain',
            'Ad hominem, spam, trolling'
        ]
    })
    st.dataframe(framework_df, use_container_width=True, hide_index=True)

# ============================================================================
# HALAMAN: INPUT DATA
# ============================================================================

def page_input_data():
    st.markdown('<p class="main-header">📝 Input Data</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <b>3 Cara Input Data:</b><br>
    1. Paste captions dari Instagram (manual)<br>
    2. Upload CSV dari tool lain<br>
    3. Paste comments satu-satu
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Paste Captions", "Upload CSV", "Paste Comments"])

    # TAB 1: Paste Captions
    with tab1:
        st.markdown("**Cara:**")
        st.write("""
        1. Buka Instagram post atau hashtag di browser
        2. Copy caption text
        3. Paste di bawah
        """)

        caption_input = st.text_area(
            "Paste caption Instagram (satu per baris, pisahkan dengan --- )",
            height=200,
            placeholder="Caption 1\n---\nCaption 2\n---\nCaption 3"
        )

        if st.button("➕ Add Captions", type="primary"):
            if caption_input.strip():
                captions = caption_input.split('---')
                for idx, caption in enumerate(captions, 1):
                    caption_clean = caption.strip()
                    if caption_clean:
                        post_data = {
                            'post_id': f"POST_{len(st.session_state.posts_data) + idx:04d}",
                            'caption': caption_clean,
                            'likes_count': 0,
                            'comments_count': 0,
                            'posted_date': datetime.now().isoformat(),
                        }
                        st.session_state.posts_data.append(post_data)
                st.success(f"✓ Ditambahkan {len([c for c in captions if c.strip()])} captions")
                st.rerun()

    # TAB 2: Upload CSV
    with tab2:
        st.markdown("**Upload CSV dengan kolom:**")
        st.code("""
        post_id, caption, likes_count, comments_count, posted_date
        POST_0001, "Anak bisa fokus belajar...", 100, 25, 2024-01-15
        POST_0002, "Program MBG sangat membantu...", 200, 50, 2024-01-20
        """)

        uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.posts_data.extend(df.to_dict('records'))
                st.success(f"✓ {len(df)} posts dari CSV ditambahkan")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # TAB 3: Paste Comments
    with tab3:
        st.markdown("**Cara:**")
        st.write("""
        1. Pilih POST yang akan ditambahkan comments
        2. Copy comment text dari Instagram
        3. Paste di bawah
        """)

        if st.session_state.posts_data:
            post_options = {p['post_id']: p['caption'][:50] + "..." for p in st.session_state.posts_data}
            selected_post = st.selectbox("Pilih post:", list(post_options.keys()), format_func=lambda x: post_options[x])

            comments_input = st.text_area(
                "Paste comments (format: username: comment text) — pisahkan dengan ---",
                height=200,
                placeholder="user123: Bagus sekali programnya!\n---\nuser456: Setuju, sangat membantu anak saya"
            )

            if st.button("➕ Add Comments", type="primary"):
                if comments_input.strip():
                    comments = comments_input.split('---')
                    added = 0
                    for comment in comments:
                        comment_clean = comment.strip()
                        if comment_clean and ':' in comment_clean:
                            username, text = comment_clean.split(':', 1)
                            comment_data = {
                                'post_id': selected_post,
                                'comment_id': f"COMMENT_{len(st.session_state.comments_data) + added:05d}",
                                'comment_text': text.strip(),
                                'user_id_anonymized': anonymize_username(username.strip()),
                                'timestamp': datetime.now().isoformat(),
                                'habermas_code': 'UNCODED'
                            }
                            st.session_state.comments_data.append(comment_data)
                            added += 1
                    st.success(f"✓ Ditambahkan {added} comments")
                    st.rerun()
        else:
            st.warning("Belum ada posts. Tambahkan posts terlebih dahulu di tab pertama.")

# ============================================================================
# HALAMAN: DATA PREVIEW
# ============================================================================

def page_data_preview():
    st.markdown('<p class="main-header">📊 Data Preview</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Posts", "Comments"])

    with tab1:
        if st.session_state.posts_data:
            df = pd.DataFrame(st.session_state.posts_data)
            st.write(f"**Total: {len(df)} posts**")
            display_cols = ['post_id', 'caption', 'likes_count', 'comments_count']
            display_df = df[display_cols].copy()
            display_df['caption'] = display_df['caption'].str[:100] + '...'
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada posts. Input data di halaman 'Input Data'.")

    with tab2:
        if st.session_state.comments_data:
            df = pd.DataFrame(st.session_state.comments_data)
            st.write(f"**Total: {len(df)} comments**")
            display_cols = ['post_id', 'comment_id', 'user_id_anonymized', 'comment_text', 'habermas_code']
            display_df = df[display_cols].copy()
            display_df['comment_text'] = display_df['comment_text'].str[:80] + '...'
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada comments.")

# ============================================================================
# HALAMAN: CODING FRAMEWORK
# ============================================================================

def page_coding():
    st.markdown('<p class="main-header">🏷️ Coding Framework Habermas</p>', unsafe_allow_html=True)

    if not st.session_state.comments_data:
        st.warning("Belum ada data comments. Input data terlebih dahulu.")
        return

    df = pd.DataFrame(st.session_state.comments_data)
    coded = len(df[df['habermas_code'] != 'UNCODED'])
    total = len(df)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Comments", total)
    with col2:
        st.metric("Sudah Dikode", coded)
    with col3:
        st.metric("Progress", f"{coded/total*100:.0f}%" if total > 0 else "0%")

    st.markdown("---")

    filter_status = st.selectbox(
        "Filter:",
        ["Belum dikode", "Semua", "Sudah dikode"]
    )

    if filter_status == "Belum dikode":
        working_df = df[df['habermas_code'] == 'UNCODED'].copy()
    elif filter_status == "Sudah dikode":
        working_df = df[df['habermas_code'] != 'UNCODED'].copy()
    else:
        working_df = df.copy()

    if len(working_df) == 0:
        st.info("Tidak ada comments sesuai filter.")
        return

    samples_per_page = st.number_input("Comments per halaman", min_value=1, max_value=20, value=5)
    total_pages = max(1, (len(working_df) - 1) // samples_per_page + 1)
    page = st.number_input(f"Halaman (1-{total_pages})", min_value=1, max_value=total_pages, value=1)

    start_idx = (page - 1) * samples_per_page
    end_idx = min(start_idx + samples_per_page, len(working_df))
    page_df = working_df.iloc[start_idx:end_idx]

    code_options = {
        'UNCODED': 'Belum dikode',
        'FAC': 'FAC - Factual (data, statistik)',
        'NOR': 'NOR - Normative (nilai, kebijakan)',
        'EMP': 'EMP - Emotional (cerita pribadi)',
        'DIA': 'DIA - Dialogical (respon argumen)',
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
                    "Kategori",
                    options=options_list,
                    format_func=lambda x: code_options[x],
                    index=current_idx,
                    key=f"code_{row['comment_id']}"
                )
            with col2:
                st.write("")
                st.write("")
                if st.button("💾", key=f"save_{row['comment_id']}"):
                    for item in st.session_state.comments_data:
                        if item['comment_id'] == row['comment_id']:
                            item['habermas_code'] = new_code
                            break
                    st.success("✓")
                    st.rerun()

            st.markdown("---")

# ============================================================================
# HALAMAN: ANALISIS
# ============================================================================

def page_analisis():
    st.markdown('<p class="main-header">📈 Analisis</p>', unsafe_allow_html=True)

    if not st.session_state.comments_data:
        st.warning("Belum ada data.")
        return

    df = pd.DataFrame(st.session_state.comments_data)

    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Comments", len(df))
    with col2:
        st.metric("Unique Users", df['user_id_anonymized'].nunique())
    with col3:
        st.metric("Avg Comment Length", f"{df['comment_text'].str.len().mean():.0f} char")

    st.markdown("---")

    # Distribusi coding
    coded = df[df['habermas_code'] != 'UNCODED']
    if len(coded) > 0:
        st.markdown("**Distribusi Kategori Habermas**")

        dist = coded['habermas_code'].value_counts().reset_index()
        dist.columns = ['Kode', 'Jumlah']
        dist['Persentase'] = (dist['Jumlah'] / dist['Jumlah'].sum() * 100).round(2)

        col1, col2 = st.columns([1, 1])
        with col1:
            st.dataframe(dist, hide_index=True, use_container_width=True)
        with col2:
            st.bar_chart(dist.set_index('Kode')['Jumlah'])

        # DRS Score
        st.markdown("---")
        st.markdown("**Deliberative Rationality Score (DRS)**")

        total_coded = len(coded)
        fac = (coded['habermas_code'] == 'FAC').sum() / total_coded * 100
        dia = (coded['habermas_code'] == 'DIA').sum() / total_coded * 100
        nor = (coded['habermas_code'] == 'NOR').sum() / total_coded * 100
        emp = (coded['habermas_code'] == 'EMP').sum() / total_coded * 100
        non = (coded['habermas_code'] == 'NON').sum() / total_coded * 100

        drs = (fac * 0.3 + dia * 0.3 + nor * 0.2 + emp * 0.1 - non * 0.3)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("DRS Score", f"{drs:.1f}")
        with col2:
            st.metric("FAC + DIA", f"{fac + dia:.1f}%")
        with col3:
            st.metric("NON-Comm", f"{non:.1f}%")

        if drs >= 60:
            st.success("🟢 **Tinggi** — Diskusi mencerminkan deliberatif rationality yang kuat")
        elif drs >= 30:
            st.info("🟡 **Sedang** — Ada elemen deliberatif, campuran")
        else:
            st.warning("🔴 **Rendah** — Didominasi komunikasi non-deliberatif")
    else:
        st.info("Coding belum ada. Mulai coding di halaman 'Coding Framework'.")

# ============================================================================
# HALAMAN: EXPORT
# ============================================================================

def page_export():
    st.markdown('<p class="main-header">📤 Export Data</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Posts CSV**")
        if st.session_state.posts_data:
            df = pd.DataFrame(st.session_state.posts_data)
            csv = df.to_csv(index=False, encoding='utf-8').encode('utf-8')
            st.download_button(
                "⬇️ Download Posts CSV",
                data=csv,
                file_name=f"mbg_posts_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Belum ada data posts")

    with col2:
        st.markdown("**Comments CSV**")
        if st.session_state.comments_data:
            df = pd.DataFrame(st.session_state.comments_data)
            csv = df.to_csv(index=False, encoding='utf-8').encode('utf-8')
            st.download_button(
                "⬇️ Download Comments CSV",
                data=csv,
                file_name=f"mbg_comments_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Belum ada data comments")

    st.markdown("---")

    st.markdown("**Metadata JSON**")
    metadata = {
        "research": {
            "title": "Analisis Wacana Rasional Program Makan Bergizi Gratis (MBG) di Instagram",
            "framework": "Habermas Public Sphere & Communicative Rationality",
            "researcher": "Tatun (S2 Ilmu Komputer)",
            "supervisor": "Dr. Arie Qur'ania, M.Kom"
        },
        "collection": {
            "total_posts": len(st.session_state.posts_data),
            "total_comments": len(st.session_state.comments_data),
            "export_date": datetime.now().isoformat()
        },
        "ethical_note": "Data dikumpulkan untuk research akademik. Username di-anonimasi dengan MD5 hash."
    }

    if st.session_state.comments_data:
        df = pd.DataFrame(st.session_state.comments_data)
        coded = df[df['habermas_code'] != 'UNCODED']
        if len(coded) > 0:
            metadata['coding'] = coded['habermas_code'].value_counts().to_dict()

    json_str = json.dumps(metadata, indent=2, ensure_ascii=False).encode('utf-8')
    st.download_button(
        "⬇️ Download Metadata JSON",
        data=json_str,
        file_name=f"mbg_metadata_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json",
        use_container_width=True
    )

    st.json(metadata)

# ============================================================================
# MAIN
# ============================================================================

def main():
    with st.sidebar:
        st.markdown("### 🔬 MBG Research Tool")
        st.caption("Simplified Version (No Instagram Login)")

        page = st.radio(
            "Menu",
            ["🏠 Beranda", "📝 Input Data", "📊 Preview", "🏷️ Coding", "📈 Analisis", "📤 Export"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.caption(f"**Posts:** {len(st.session_state.posts_data)}")
        st.caption(f"**Comments:** {len(st.session_state.comments_data)}")

    if "Beranda" in page:
        page_beranda()
    elif "Input Data" in page:
        page_input_data()
    elif "Preview" in page:
        page_data_preview()
    elif "Coding" in page:
        page_coding()
    elif "Analisis" in page:
        page_analisis()
    elif "Export" in page:
        page_export()

if __name__ == "__main__":
    main()
