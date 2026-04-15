# Ingestion API - Correct Usage Examples

## Common Error: Using Placeholder Values

**❌ WRONG** - Don't use placeholder strings like `"string"`:
```json
{
  "allow_prefix": ["string"],
  "forms": ["string"],
  "url_file": "string"
}
```

**✅ CORRECT** - Use `null` or omit optional fields:
```json
{
  "allow_prefix": null,
  "forms": null,
  "url_file": null
}
```

Or simply omit them:
```json
{
  "seed_url": "https://www.irs.gov",
  "max_pages": 100,
  "concurrency": 2
}
```

---

## Basic Examples

### Example 1: Simple HTML Ingestion
```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov",
    "max_pages": 100,
    "concurrency": 2,
    "only_html": true
  }'
```

### Example 2: PDF Only with Form Filter
```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov",
    "max_pages": 500,
    "concurrency": 4,
    "forms": ["1120", "1040", "1065"],
    "allow_prefix": ["/pub/irs-pdf"],
    "only_pdf": true
  }'
```

### Example 3: HTML with Prefix Filter
```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/help",
    "max_pages": 3000,
    "concurrency": 6,
    "allow_prefix": ["/help", "/help/ita", "/help/faq"],
    "only_html": true
  }'
```

### Example 4: Using URL File (if you have a file with URLs)
```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov",
    "max_pages": 100,
    "concurrency": 2,
    "url_file": "/path/to/your/urls.txt"
  }'
```

**Note:** The `url_file` must be a valid file path on the server where the API is running. If you don't have a file, set it to `null` or omit it.

---

## Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `seed_url` | string | Yes | `"https://www.irs.gov"` | Starting URL for crawling |
| `max_pages` | integer | No | `100` | Maximum pages to crawl (1-10000) |
| `concurrency` | integer | No | `2` | Parallel workers (1-10) |
| `allow_prefix` | array[string] | No | `null` | Only crawl URLs with these prefixes |
| `only_html` | boolean | No | `false` | Only crawl HTML pages |
| `only_pdf` | boolean | No | `false` | Only crawl PDF files |
| `forms` | array[string] | No | `null` | Only crawl URLs containing these form names |
| `include_seed` | boolean | No | `true` | Include seed_url in crawl |
| `follow_links` | boolean | No | `true` | Follow links from pages |
| `url_file` | string | No | `null` | Path to file with URLs (one per line) |

---

## Quick Test Command

Minimal working example:
```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov",
    "max_pages": 10,
    "concurrency": 1
  }'
```

