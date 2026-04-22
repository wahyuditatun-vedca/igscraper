#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER INSTAGRAM UNTUK PENELITIAN DELIBERATIVE RATIONALITY
Diskusi Makan Bergizi Gratis (MBG) dengan Framework Habermas

Author: Tatun (Graduate Student, S2 Ilmu Komputer)
Date: 2026
Purpose: Data collection for thesis on communicative rationality
Ethical Review: Requires IRB approval before deployment

CATATAN PENTING:
- Anonymisasi semua user data sebelum analisis
- Hanya ambil data publik (captions, comments publik, metrics)
- Jangan ambil user ID atau private information
- Log semua aktivitas scraping
"""

from instagrapi import Client
import csv
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import time
import hashlib

# ============================================================================
# SETUP LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# KONFIGURASI
# ============================================================================

class Config:
    """Konfigurasi penelitian"""
    
    # Instagram credentials (ganti dengan akun Anda)
    INSTAGRAM_USERNAME = 'your_username'
    INSTAGRAM_PASSWORD = 'your_password'
    
    # Target hashtags untuk penelitian MBG
    HASHTAGS = [
        'makanbergizigratisdki',
        'makanbergizigratismedan',
        'makanbergizigratisjakarta',
        'makan bergizi gratis',
        'MBG Indonesia',
        'program makan bergizi',
        'makan gratis sekolah'
    ]
    
    # Parameters scraping
    POSTS_PER_HASHTAG = 500  # Bisa disesuaikan
    COMMENTS_PER_POST = 100
    TIMEFRAME_DAYS = 180  # 6 bulan terakhir
    
    # Output files
    OUTPUT_DIR = './'
    POSTS_CSV = 'mbg_posts_data.csv'
    COMMENTS_CSV = 'mbg_comments_data.csv'
    METADATA_JSON = 'scraping_metadata.json'
    
    # Rate limiting (hindari ban)
    DELAY_BETWEEN_REQUESTS = 2  # detik
    DELAY_BETWEEN_HASHTAGS = 10  # detik


# ============================================================================
# ANONYMIZATION & DATA CLEANING
# ============================================================================

def anonymize_username(username: str) -> str:
    """
    Anonimasi username menggunakan hash untuk maintain integrity
    tapi tetap reproducible untuk analysis
    """
    return 'USER_' + hashlib.md5(username.encode()).hexdigest()[:8].upper()


def clean_text(text: str) -> str:
    """Bersihkan teks dari karakter aneh"""
    if not text:
        return ""
    return text.replace('\n', ' ').replace('\r', ' ').strip()


# ============================================================================
# INSTAGRAM SCRAPER CLASS
# ============================================================================

class MBGResearchScraper:
    """
    Scraper Instagram untuk penelitian deliberative rationality
    Fokus pada diskusi Makan Bergizi Gratis (MBG)
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.client = Client()
        self.session_started = datetime.now()
        self.posts_collected = 0
        self.comments_collected = 0
        self.errors = []
        
        logger.info("=" * 70)
        logger.info("INISIALISASI SCRAPER INSTAGRAM PENELITIAN MBG")
        logger.info("=" * 70)
        logger.info(f"Target hashtags: {', '.join(config.HASHTAGS)}")
        logger.info(f"Posts per hashtag: {config.POSTS_PER_HASHTAG}")
        logger.info(f"Timeframe: {config.TIMEFRAME_DAYS} hari terakhir")
    
    def login(self) -> bool:
        """Login ke Instagram"""
        try:
            logger.info("Attempting login...")
            self.client.login(
                self.config.INSTAGRAM_USERNAME,
                self.config.INSTAGRAM_PASSWORD
            )
            logger.info("✓ Login berhasil")
            return True
        except Exception as e:
            logger.error(f"✗ Login gagal: {str(e)}")
            self.errors.append(f"Login error: {str(e)}")
            return False
    
    def scrape_hashtag_posts(self) -> List[Dict]:
        """
        Scrape posts dari hashtag yang relevan
        
        Returns:
            List of dictionaries containing post data
        """
        all_posts = []
        
        for hashtag in self.config.HASHTAGS:
            logger.info(f"\nScraping hashtag: #{hashtag}")
            
            try:
                # Ambil posts dari hashtag
                medias = self.client.hashtag_medias_recent(
                    hashtag,
                    amount=self.config.POSTS_PER_HASHTAG
                )
                
                for media in medias:
                    # Filter berdasarkan timeframe
                    if (datetime.now() - media.taken_at).days > self.config.TIMEFRAME_DAYS:
                        continue
                    
                    post_data = {
                        'post_id': str(media.id),
                        'caption': clean_text(media.caption) if media.caption else '',
                        'likes_count': media.like_count or 0,
                        'comments_count': media.comment_count or 0,
                        'posted_date': media.taken_at.isoformat(),
                        'posted_timestamp': int(media.taken_at.timestamp()),
                        'hashtags': ','.join(media.caption_hashtags) if media.caption_hashtags else '',
                        'media_type': media.media_type,
                        'engagement_rate': self._calculate_engagement(media)
                    }
                    
                    all_posts.append(post_data)
                    self.posts_collected += 1
                
                logger.info(f"✓ Collected {len(medias)} posts dari #{hashtag}")
                time.sleep(self.config.DELAY_BETWEEN_HASHTAGS)
                
            except Exception as e:
                logger.error(f"✗ Error scraping #{hashtag}: {str(e)}")
                self.errors.append(f"Hashtag {hashtag} error: {str(e)}")
                continue
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Total posts collected: {self.posts_collected}")
        logger.info(f"{'='*70}")
        
        return all_posts
    
    def scrape_comments(self, posts: List[Dict]) -> List[Dict]:
        """
        Scrape comments dari posts
        
        PENELITIAN: Ini penting untuk analisis communicative rationality
        Comments menunjukkan discourse dan deliberation
        
        Args:
            posts: List of post dictionaries dengan post_id
        
        Returns:
            List of dictionaries containing comment data
        """
        all_comments = []
        
        logger.info(f"\nMemulai scraping comments dari {len(posts)} posts...")
        
        for idx, post in enumerate(posts, 1):
            post_id = post['post_id']
            post_caption_preview = post['caption'][:50] + "..." if len(post['caption']) > 50 else post['caption']
            
            try:
                logger.info(f"[{idx}/{len(posts)}] Post ID: {post_id}")
                
                # Ambil comments
                comments = self.client.media_comments(
                    media_id=post_id,
                    amount=self.config.COMMENTS_PER_POST
                )
                
                for comment in comments:
                    comment_data = {
                        'post_id': post_id,
                        'post_caption_preview': clean_text(post_caption_preview),
                        'comment_id': str(comment.pk),
                        'comment_text': clean_text(comment.text),
                        'comment_likes': comment.like_count or 0,
                        'user_id_anonymized': anonymize_username(comment.user.username),
                        'timestamp': comment.created_at.isoformat() if comment.created_at else '',
                        'reply_count': len(comment.replies) if hasattr(comment, 'replies') else 0,
                    }
                    all_comments.append(comment_data)
                    self.comments_collected += 1
                
                logger.info(f"  → Collected {len(comments)} comments")
                time.sleep(self.config.DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                logger.error(f"  ✗ Error on post {post_id}: {str(e)}")
                self.errors.append(f"Post {post_id} comments error: {str(e)}")
                continue
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Total comments collected: {self.comments_collected}")
        logger.info(f"{'='*70}")
        
        return all_comments
    
    @staticmethod
    def _calculate_engagement(media) -> float:
        """Hitung engagement rate"""
        total_engagement = (media.like_count or 0) + (media.comment_count or 0)
        # Note: Instagram followers tidak selalu tersedia, gunakan aproksimasi
        estimated_reach = (media.like_count or 0) * 10  # Rough estimate
        if estimated_reach == 0:
            return 0
        return (total_engagement / estimated_reach) * 100
    
    def save_posts(self, posts: List[Dict]) -> bool:
        """Simpan posts ke CSV"""
        try:
            filepath = self.config.OUTPUT_DIR + self.config.POSTS_CSV
            
            if not posts:
                logger.warning("No posts to save")
                return False
            
            fieldnames = posts[0].keys()
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(posts)
            
            logger.info(f"✓ Posts saved: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error saving posts: {str(e)}")
            self.errors.append(f"Save posts error: {str(e)}")
            return False
    
    def save_comments(self, comments: List[Dict]) -> bool:
        """Simpan comments ke CSV"""
        try:
            filepath = self.config.OUTPUT_DIR + self.config.COMMENTS_CSV
            
            if not comments:
                logger.warning("No comments to save")
                return False
            
            fieldnames = comments[0].keys()
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(comments)
            
            logger.info(f"✓ Comments saved: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error saving comments: {str(e)}")
            self.errors.append(f"Save comments error: {str(e)}")
            return False
    
    def save_metadata(self) -> bool:
        """Simpan metadata scraping untuk dokumentasi penelitian"""
        try:
            metadata = {
                'session_info': {
                    'started': self.session_started.isoformat(),
                    'completed': datetime.now().isoformat(),
                    'total_duration_minutes': (datetime.now() - self.session_started).total_seconds() / 60
                },
                'collection_stats': {
                    'posts_collected': self.posts_collected,
                    'comments_collected': self.comments_collected,
                    'hashtags_targeted': self.config.HASHTAGS,
                    'timeframe_days': self.config.TIMEFRAME_DAYS
                },
                'research_info': {
                    'project': 'Deliberative Rationality in MBG Discussion on Instagram',
                    'framework': 'Habermas Public Sphere & Communicative Rationality',
                    'ethical_note': 'All data anonymized. User IDs hashed. Comments only from public posts.'
                },
                'errors': self.errors if self.errors else 'None'
            }
            
            filepath = self.config.OUTPUT_DIR + self.config.METADATA_JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Metadata saved: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error saving metadata: {str(e)}")
            return False
    
    def run(self) -> bool:
        """
        Jalankan full scraping pipeline
        """
        logger.info("Starting scraping pipeline...")
        
        # Step 1: Login
        if not self.login():
            return False
        
        # Step 2: Scrape posts
        posts = self.scrape_hashtag_posts()
        if not posts:
            logger.error("No posts collected. Exiting.")
            return False
        
        # Step 3: Scrape comments
        comments = self.scrape_comments(posts)
        
        # Step 4: Save data
        self.save_posts(posts)
        self.save_comments(comments)
        self.save_metadata()
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("SCRAPING COMPLETE - SUMMARY")
        logger.info("="*70)
        logger.info(f"Posts collected: {self.posts_collected}")
        logger.info(f"Comments collected: {self.comments_collected}")
        logger.info(f"Errors: {len(self.errors)}")
        logger.info(f"Files saved in: {self.config.OUTPUT_DIR}")
        logger.info("="*70 + "\n")
        
        return True


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    
    # Initialize configuration
    config = Config()
    
    # Initialize scraper
    scraper = MBGResearchScraper(config)
    
    # Run scraping
    success = scraper.run()
    
    # Exit status
    exit(0 if success else 1)
