"""
Data Cleaner
============
Reads raw JSON files produced by DRDOCrawler, applies cleaning rules,
and produces clean JSON + Article DB records.

Usage:
    python manage.py clean_pages          # clean all uncleaned RawPages
    python manage.py clean_pages --limit 50
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime, date

from django.conf import settings

logger = logging.getLogger('crawler')


# ── Text Cleaning Utilities ─────────────────────────────────────────────────

# Patterns that indicate boilerplate / nav text
BOILERPLATE_PATTERNS = [
    r'skip to (?:main )?content',
    r'home\s*[>›»|]\s*',
    r'copyright\s*©?\s*\d{4}',
    r'all rights reserved',
    r'website\s+(?:designed|developed|maintained)\s+by',
    r'last\s+updated?\s*[:–]?\s*\d',
    r'screen\s+reader\s+access',
    r'sitemap',
    r'facebook|twitter|youtube|linkedin|instagram',
    r'^\s*[\|\-–—•·]\s*$',                  # lone separators
]
_BP_RE = [re.compile(p, re.I) for p in BOILERPLATE_PATTERNS]


def is_boilerplate(line: str) -> bool:
    return any(p.search(line) for p in _BP_RE)


def clean_text(raw: str) -> str:
    """Remove boilerplate, collapse whitespace, deduplicate lines."""
    lines = raw.splitlines()
    seen  = set()
    clean = []
    for line in lines:
        line = line.strip()
        if not line or is_boilerplate(line):
            continue
        if line in seen:
            continue
        seen.add(line)
        clean.append(line)
    return '\n'.join(clean)


def extract_summary(text: str, max_sentences: int = 3) -> str:
    """Return first *max_sentences* sentences of cleaned text."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return ' '.join(sentences[:max_sentences])


def extract_date(text: str, title: str = '') -> date | None:
    """Try to extract a publication date from text or title."""
    DATE_PATTERNS = [
        r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})',           # DD/MM/YYYY
        r'(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})',             # YYYY-MM-DD
        r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]+(\d{4})',
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})',
    ]
    MONTHS = dict(jan=1, feb=2, mar=3, apr=4, may=5, jun=6,
                  jul=7, aug=8, sep=9, oct=10, nov=11, dec=12)

    source = f"{title} {text[:2000]}"
    for pat in DATE_PATTERNS:
        m = re.search(pat, source, re.I)
        if m:
            try:
                g = m.groups()
                # YYYY-MM-DD
                if len(g[0]) == 4 and g[0].isdigit():
                    return date(int(g[0]), int(g[1]), int(g[2]))
                # DD Mon YYYY
                if g[1].lower() in MONTHS:
                    return date(int(g[2]), MONTHS[g[1].lower()], int(g[0]))
                # Mon DD YYYY
                if g[0].lower() in MONTHS:
                    return date(int(g[2]), MONTHS[g[0].lower()], int(g[1]))
                # DD/MM/YYYY
                day, month, year = int(g[0]), int(g[1]), int(g[2])
                if year < 100:
                    year += 2000
                return date(year, month, day)
            except (ValueError, TypeError):
                pass
    return None


def detect_content_type(url: str, title: str, text: str) -> str:
    """Heuristic content-type classification."""
    u = url.lower()
    t = (title + ' ' + text[:500]).lower()

    if any(k in u for k in ['/news', '/press', '/media']):      return 'news'
    if any(k in u for k in ['/publication', '/paper', '/journal']): return 'publication'
    if any(k in u for k in ['/technology', '/product', '/tech']): return 'technology'
    if any(k in u for k in ['/lab', '/laboratory']):            return 'lab_profile'
    if any(k in u for k in ['/tender', '/procurement']):        return 'tender'
    if any(k in u for k in ['/award', '/achiev']):              return 'achievement'
    if any(k in u for k in ['/contact', '/director', '/staff']): return 'contact'
    if any(k in u for k in ['/event', '/seminar', '/conf']):    return 'event'
    if 'news' in t or 'press release' in t:                     return 'news'
    if 'technology' in t or 'patent' in t:                      return 'technology'
    if 'publication' in t or 'journal' in t or 'doi' in t:      return 'publication'
    return 'other'


def extract_tags(title: str, text: str) -> list[str]:
    """Extract keyword tags from content."""
    TECH_KEYWORDS = [
        'missile', 'radar', 'sonar', 'electronic', 'laser', 'sensor',
        'armour', 'armor', 'drone', 'uav', 'satellite', 'propulsion',
        'explosive', 'combat', 'submarine', 'warhead', 'navigation',
        'cybersecurity', 'cryptography', 'material', 'composite',
        'biomedical', 'pharmaceutical', 'defence', 'defense',
        'nuclear', 'chemical', 'biological', 'aeronautics', 'avionics',
        'communication', 'network', 'ai', 'machine learning',
    ]
    combined = (title + ' ' + text[:3000]).lower()
    return [kw for kw in TECH_KEYWORDS if kw in combined]


def clean_links(links: list, base_url: str) -> list:
    """Filter to internal / meaningful links only."""
    seen = set()
    out  = []
    for lnk in links:
        url  = lnk.get('url', '').strip()
        text = lnk.get('text', '').strip()
        if not url or url in seen:
            continue
        if not text or len(text) < 3:
            continue
        seen.add(url)
        out.append({'url': url, 'text': text})
    return out[:100]   # cap at 100 links


# ── Clean Dict Builder ──────────────────────────────────────────────────────

def build_clean_record(raw: dict) -> dict:
    """
    Transform a raw-page dict into a clean, structured record.
    Returns a dict ready for JSON serialisation and DB insertion.
    """
    url        = raw.get('url', '')
    raw_title  = raw.get('page_title', '').strip()
    raw_text   = raw.get('full_text', '')

    # Clean text
    cleaned_text = clean_text(raw_text)

    # Title fallback
    title = raw_title or (
        next((h['text'] for h in raw.get('headings', []) if h['level'] == 1), '')
        or url
    )

    summary      = extract_summary(cleaned_text)
    pub_date     = extract_date(cleaned_text, title)
    content_type = detect_content_type(url, title, cleaned_text)
    tags         = extract_tags(title, cleaned_text)

    return {
        # Provenance
        'source_url':        url,
        'http_status':       raw.get('http_status', 200),
        'crawled_at':        raw.get('crawled_at', ''),
        'cleaned_at':        datetime.utcnow().isoformat() + 'Z',

        # Core
        'title':             title,
        'content_type':      content_type,
        'summary':           summary,
        'full_text':         cleaned_text,
        'word_count':        len(cleaned_text.split()),

        # Structured elements
        'headings':          raw.get('headings', []),
        'tables':            raw.get('tables', []),
        'links':             clean_links(raw.get('links', []), url),
        'images':            raw.get('images', [])[:50],

        # Meta
        'meta_description':  raw.get('meta_description', '').strip(),
        'meta_keywords':     raw.get('meta_keywords', '').strip(),

        # Extracted
        'published_date':    pub_date.isoformat() if pub_date else None,
        'tags':              tags,
        'language':          'en',
    }


# ── File-level Cleaning ─────────────────────────────────────────────────────

def clean_raw_file(raw_path: str) -> dict | None:
    """Load a raw JSON file, clean it, save clean JSON, return clean dict."""
    try:
        with open(raw_path, encoding='utf-8') as f:
            raw = json.load(f)
    except Exception as exc:
        logger.error(f"Cannot read {raw_path}: {exc}")
        return None

    # Skip very short pages (likely nav/error pages)
    if len(raw.get('full_text', '')) < 200:
        logger.info(f"  SKIP (too short): {raw.get('url')}")
        return None

    clean = build_clean_record(raw)

    # Save clean JSON
    Path(settings.CLEAN_JSON_DIR).mkdir(parents=True, exist_ok=True)
    fname      = Path(raw_path).stem + '_clean.json'
    clean_path = Path(settings.CLEAN_JSON_DIR) / fname
    with open(clean_path, 'w', encoding='utf-8') as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)

    clean['_clean_json_path'] = str(clean_path)
    return clean


# ── DB Insertion ────────────────────────────────────────────────────────────

def insert_article(clean: dict, raw_page=None):
    """Create or update an Article (and related models) from a clean dict."""
    from knowledge_base.models import Article, Tag

    tags_data = clean.pop('tags', [])
    _ = clean.pop('_clean_json_path', '')

    pub_date = None
    if clean.get('published_date'):
        try:
            pub_date = date.fromisoformat(clean['published_date'])
        except ValueError:
            pass

    article, created = Article.objects.update_or_create(
        source_url=clean['source_url'],
        defaults={
            'raw_page':          raw_page,
            'title':             clean['title'][:500],
            'content_type':      clean['content_type'],
            'summary':           clean.get('summary', ''),
            'full_text':         clean.get('full_text', ''),
            'headings':          clean.get('headings', []),
            'tables':            clean.get('tables', []),
            'links':             clean.get('links', []),
            'images':            clean.get('images', []),
            'meta_keywords':     clean.get('meta_keywords', ''),
            'meta_description':  clean.get('meta_description', ''),
            'language':          clean.get('language', 'en'),
            'published_date':    pub_date,
            'clean_json_path':   clean.get('_clean_json_path', '')[:500],
        }
    )

    # Tags
    for tag_name in tags_data:
        tag, _ = Tag.objects.get_or_create(name=tag_name)
        article.tags.add(tag)

    action = 'Created' if created else 'Updated'
    logger.info(f"  {action} Article → {article.title[:70]}")
    return article


# ── Batch Cleaner ───────────────────────────────────────────────────────────

class PageCleaner:
    """Clean all unprocessed RawPage records."""

    def run(self, limit: int = None):
        from knowledge_base.models import RawPage

        qs = RawPage.objects.filter(is_cleaned=False, json_file_path__gt='')
        if limit:
            qs = qs[:limit]

        total = qs.count()
        logger.info(f"Cleaning {total} raw pages…")

        cleaned = failed = skipped = 0
        for raw_page in qs:
            if not os.path.exists(raw_page.json_file_path):
                logger.warning(f"  Missing file: {raw_page.json_file_path}")
                failed += 1
                continue

            clean = clean_raw_file(raw_page.json_file_path)
            if not clean:
                skipped += 1
                raw_page.is_cleaned = True
                raw_page.save(update_fields=['is_cleaned'])
                continue

            try:
                insert_article(clean, raw_page=raw_page)
                raw_page.is_cleaned = True
                raw_page.save(update_fields=['is_cleaned'])
                cleaned += 1
            except Exception as exc:
                logger.error(f"  DB error for {raw_page.url}: {exc}")
                failed += 1

        print(f"\n✅ Cleaning done!  Cleaned: {cleaned} | Skipped: {skipped} | Failed: {failed}")
        return cleaned, skipped, failed
