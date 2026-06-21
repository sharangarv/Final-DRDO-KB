drdo_kb/
├── drdo_kb/                    # Django project config
│   ├── settings.py             # All settings (DB, crawler config, paths)
│   └── urls.py
│
├── knowledge_base/             # Main app — models, views, admin
│   ├── models.py               # ★ All Django models (see below)
│   ├── views.py                # Dashboard, article list/detail, labs
│   ├── admin.py                # Full admin UI
│   └── migrations/
│
├── crawler/                    # Crawler + cleaner app
│   ├── drdo_crawler.py         # ★ BFS web crawler → raw JSON + RawPage DB
│   ├── cleaner.py              # ★ Cleans raw JSON → Article DB records
│   ├── seed_labs.py            # Seeds 39 DRDO labs into the database
│   └── management/commands/
│       ├── crawl_drdo.py       # python manage.py crawl_drdo
│       ├── clean_pages.py      # python manage.py clean_pages
│       ├── crawl_and_clean.py  # python manage.py crawl_and_clean  ← use this
│       └── seed_labs.py        # python manage.py seed_labs
│
├── templates/knowledge_base/   # HTML templates for the web UI
├── crawler_output/
│   ├── raw/                    # ★ Raw JSON files (one per crawled page)
│   └── clean/                  # ★ Cleaned JSON files
├── drdo_knowledge_base.db      # SQLite database
└── crawler.log                 # Crawl + clean log file
```

---

## Django Models

| Model | Purpose |
|---|---|
| `Laboratory` | 39 DRDO labs with acronym, city, cluster |
| `Tag` | Keyword tags (many-to-many with Article) |
| `CrawlSession` | Audit trail for each crawl run |
| `RawPage` | Raw crawled page (text, HTML pointer, JSON path) |
| `Article` | ★ Clean structured knowledge unit (title, full_text, headings, tables, links …) |
| `Technology` | Extended info for technology/product pages |
| `Publication` | Journal papers and DRDO reports |

1. Install dependencies
```bash
pip install django requests beautifulsoup4 lxml
```

### 2. Set up the database
```bash
python manage.py migrate
python manage.py seed_labs        # populate 39 DRDO labs
python manage.py createsuperuser
```

### 3. Run the full pipeline
```bash
# Crawl 100 pages, then clean & store everything
python manage.py crawl_and_clean --max-pages 100

# Or run steps separately:
python manage.py crawl_drdo   --max-pages 200 --delay 2
python manage.py clean_pages  --limit 200
```

### 4. Start the web server
```bash
python manage.py runserver
```
Then open http://127.0.0.1:8000/

---

## Pipeline Flow

```
drdo.gov.in
    │
    ▼  (Step 1: DRDOCrawler — drdo_crawler.py)
RawPage (DB)  +  crawler_output/raw/<hash>.json
    │
    ▼  (Step 2: PageCleaner — cleaner.py)
Article (DB)  +  crawler_output/clean/<hash>_clean.json
    │
    ▼  (Step 3: Optional enrichment)
Technology / Publication (DB)
```

### Raw JSON format (crawler_output/raw/)
```json
{
  "url": "https://www.drdo.gov.in/...",
  "http_status": 200,
  "crawled_at": "2024-01-15T10:30:00Z",
  "page_title": "...",
  "meta_description": "...",
  "meta_keywords": "...",
  "headings": [{"level": 1, "text": "..."}],
  "full_text": "... (raw, with boilerplate) ...",
  "paragraphs": ["...", "..."],
  "links": [{"url": "...", "text": "..."}],
  "images": [{"src": "...", "alt": "..."}],
  "tables": [[["col1", "col2"], ["val1", "val2"]]]
}
```

### Clean JSON format (crawler_output/clean/)
```json
{
  "source_url": "...",
  "title": "...",
  "content_type": "news|publication|technology|lab_profile|...",
  "summary": "First 3 sentences ...",
  "full_text": "... (boilerplate removed, deduped) ...",
  "word_count": 847,
  "headings": [...],
  "tables": [...],
  "links": [...],
  "images": [...],
  "meta_description": "...",
  "meta_keywords": "...",
  "published_date": "2024-01-10",
  "tags": ["missile", "radar", "sensor"],
  "language": "en",
  "cleaned_at": "2024-01-15T10:35:00Z"
}
```

---

## Crawler Settings (settings.py)

| Setting | Default | Description |
|---|---|---|
| `DRDO_BASE_URL` | `https://www.drdo.gov.in` | Crawl seed URL |
| `CRAWLER_DELAY` | `1.5` | Seconds between requests (be polite!) |
| `CRAWLER_MAX_PAGES` | `500` | Max pages per session |
| `CRAWLER_TIMEOUT` | `30` | Request timeout (seconds) |
| `RAW_JSON_DIR` | `crawler_output/raw/` | Raw JSON output folder |
| `CLEAN_JSON_DIR` | `crawler_output/clean/` | Cleaned JSON output folder |

---

## Admin Panel
URL: http://127.0.0.1:8000/admin/
Login: admin / admin123

All models are registered with search, filters, and inline editing.
