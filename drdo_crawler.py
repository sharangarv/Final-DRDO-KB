"""
DRDO Website Crawler
====================
Crawls https://www.drdo.gov.in recursively, saves each page as a
raw JSON file, and records a RawPage entry in the database.

Usage (from project root):
    python manage.py shell -c "from crawler.drdo_crawler import DRDOCrawler; DRDOCrawler().run()"
  or via management command:
    python manage.py crawl_drdo --max-pages 100
"""

import os
import re
import json
import time
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque

import requests
from bs4 import BeautifulSoup

import django
from django.conf import settings

logger = logging.getLogger('crawler')


# ── Helpers ────────────────────────────────────────────────────────────────

def ensure_dirs():
    """Create output directories if missing."""
    for d in [settings.RAW_JSON_DIR, settings.CLEAN_JSON_DIR]:
        Path(d).mkdir(parents=True, exist_ok=True)


def url_fingerprint(url: str) -> str:
    """MD5 fingerprint of a normalised URL (used as filename)."""
    clean = urldefrag(url)[0].rstrip('/')
    return hashlib.md5(clean.encode()).hexdigest()


def is_internal(url: str, base: str) -> bool:
    """Return True if *url* belongs to the same domain as *base*."""
    return urlparse(url).netloc == urlparse(base).netloc


def should_skip(url: str) -> bool:
    """Skip binary / irrelevant file types."""
    SKIP_EXTS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
                 '.pptx', '.zip', '.rar', '.mp4', '.mp3', '.jpg',
                 '.jpeg', '.png', '.gif', '.svg', '.ico', '.css', '.js'}
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in SKIP_EXTS)


# ── Extractor ──────────────────────────────────────────────────────────────

def extract_page_data(url: str, html: str, http_status: int) -> dict:
    """
    Parse raw HTML and return a structured dict.
    This is saved as the RAW JSON (no cleaning applied yet).
    """
    soup = BeautifulSoup(html, 'lxml')

    # Remove noise tags
    for tag in soup(['script', 'style', 'noscript', 'iframe',
                     'header', 'footer', 'nav']):
        tag.decompose()

    # Title
    title = ''
    if soup.title:
        title = soup.title.get_text(strip=True)
    if not title:
        h1 = soup.find('h1')
        title = h1.get_text(strip=True) if h1 else url

    # Meta
    meta_desc = ''
    meta_kw   = ''
    for m in soup.find_all('meta'):
        name = (m.get('name') or m.get('property') or '').lower()
        if name == 'description':
            meta_desc = m.get('content', '')
        elif name == 'keywords':
            meta_kw = m.get('content', '')

    # Headings
    headings = []
    for level in range(1, 7):
        for h in soup.find_all(f'h{level}'):
            text = h.get_text(strip=True)
            if text:
                headings.append({'level': level, 'text': text})

    # Full visible text
    full_text = soup.get_text(separator='\n', strip=True)

    # Paragraphs
    paragraphs = [p.get_text(strip=True)
                  for p in soup.find_all('p')
                  if len(p.get_text(strip=True)) > 30]

    # Links
    links = []
    for a in soup.find_all('a', href=True):
        href = urljoin(url, a['href'])
        text = a.get_text(strip=True)
        if href.startswith('http'):
            links.append({'url': href, 'text': text})

    # Images
    images = []
    for img in soup.find_all('img'):
        images.append({
            'src': urljoin(url, img.get('src', '')),
            'alt': img.get('alt', ''),
        })

    # Tables
    tables = []
    for tbl in soup.find_all('table'):
        rows = []
        for tr in tbl.find_all('tr'):
            cells = [td.get_text(strip=True)
                     for td in tr.find_all(['td', 'th'])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)

    return {
        'url':              url,
        'http_status':      http_status,
        'crawled_at':       datetime.utcnow().isoformat() + 'Z',
        'page_title':       title,
        'meta_description': meta_desc,
        'meta_keywords':    meta_kw,
        'headings':         headings,
        'full_text':        full_text,
        'paragraphs':       paragraphs,
        'links':            links,
        'images':           images,
        'tables':           tables,
    }


# ── Main Crawler Class ─────────────────────────────────────────────────────

class DRDOCrawler:
    """
    BFS web crawler for drdo.gov.in.

    Steps
    -----
    1.  Fetch page HTML
    2.  Extract structured data → raw dict
    3.  Save raw dict to  RAW_JSON_DIR/<fingerprint>.json
    4.  Create  RawPage  DB record
    5.  Enqueue new internal links
    """

    def __init__(self, seed_url: str = None, max_pages: int = None,
                 delay: float = None):
        self.seed_url  = seed_url  or settings.DRDO_BASE_URL
        self.max_pages = max_pages or settings.CRAWLER_MAX_PAGES
        self.delay     = delay     or settings.CRAWLER_DELAY
        self.session_obj = None   # Django CrawlSession instance
        self._http     = self._build_session()

    # ── HTTP Session ──────────────────────────────────────────────────────

    def _build_session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update({
            'User-Agent': settings.CRAWLER_USER_AGENT,
            'Accept':     'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        return s

    # ── Django session record ─────────────────────────────────────────────

    def _start_session(self):
        from knowledge_base.models import CrawlSession
        self.session_obj = CrawlSession.objects.create(
            seed_url=self.seed_url,
            status='running',
        )
        logger.info(f"[Session {self.session_obj.pk}] Crawl started → {self.seed_url}")
        return self.session_obj

    def _finish_session(self, status='completed'):
        from django.utils import timezone
        if self.session_obj:
            self.session_obj.status     = status
            self.session_obj.finished_at = timezone.now()
            self.session_obj.save()
            logger.info(
                f"[Session {self.session_obj.pk}] Crawl {status} | "
                f"pages_crawled={self.session_obj.pages_crawled} "
                f"pages_failed={self.session_obj.pages_failed}"
            )

    # ── Crawl single page ─────────────────────────────────────────────────

    def fetch(self, url: str) -> tuple[str | None, int]:
        """Return (html, status_code) or (None, status_code) on error."""
        try:
            resp = self._http.get(url, timeout=settings.CRAWLER_TIMEOUT,
                                  allow_redirects=True)
            ct = resp.headers.get('Content-Type', '')
            if 'html' not in ct:
                return None, resp.status_code
            resp.encoding = resp.apparent_encoding
            return resp.text, resp.status_code
        except Exception as exc:
            logger.warning(f"FETCH ERROR {url}: {exc}")
            return None, 0

    def save_raw_json(self, data: dict, fingerprint: str) -> str:
        """Write raw JSON to disk, return file path."""
        ensure_dirs()
        path = Path(settings.RAW_JSON_DIR) / f"{fingerprint}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(path)

    def record_raw_page(self, data: dict, json_path: str, session):
        """Create RawPage DB record."""
        from knowledge_base.models import RawPage
        RawPage.objects.update_or_create(
            url=data['url'],
            defaults={
                'session':        session,
                'page_title':     data.get('page_title', ''),
                'raw_text':       data.get('full_text', '')[:50000],
                'http_status':    data.get('http_status', 200),
                'json_file_path': json_path,
                'is_cleaned':     False,
            }
        )

    # ── BFS Loop ──────────────────────────────────────────────────────────

    def run(self):
        ensure_dirs()
        session = self._start_session()

        visited = set()
        queue   = deque([self.seed_url])
        failed  = 0

        try:
            while queue and len(visited) < self.max_pages:
                url = queue.popleft()
                url = urldefrag(url)[0].rstrip('/')

                if url in visited or should_skip(url):
                    continue
                visited.add(url)

                logger.info(f"[{len(visited)}/{self.max_pages}] Crawling → {url}")
                html, status = self.fetch(url)

                if not html:
                    failed += 1
                    session.pages_failed = failed
                    session.save(update_fields=['pages_failed'])
                    time.sleep(self.delay)
                    continue

                # Extract structured data
                data = extract_page_data(url, html, status)
                fp   = url_fingerprint(url)

                # Save raw JSON to disk
                json_path = self.save_raw_json(data, fp)

                # Persist RawPage record
                self.record_raw_page(data, json_path, session)

                # Update session counter
                session.pages_crawled = len(visited)
                session.save(update_fields=['pages_crawled'])

                # Enqueue new internal links
                for link in data.get('links', []):
                    href = link['url']
                    if (is_internal(href, self.seed_url)
                            and href not in visited
                            and not should_skip(href)):
                        queue.append(href)

                logger.info(f"  ✓ Saved → {json_path}")
                time.sleep(self.delay)

        except KeyboardInterrupt:
            logger.warning("Crawl interrupted by user.")
            self._finish_session('partial')
            return

        except Exception as exc:
            logger.error(f"Crawl crashed: {exc}", exc_info=True)
            self._finish_session('failed')
            raise

        self._finish_session('completed')
        print(f"\n✅ Crawl done! Pages saved: {len(visited)} | Failed: {failed}")
        print(f"   Raw JSON → {settings.RAW_JSON_DIR}")
