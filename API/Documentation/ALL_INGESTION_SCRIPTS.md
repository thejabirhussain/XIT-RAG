# All Ingestion Scripts - Complete Reference

**API Endpoint:** `https://complyia-ai-api.azurewebsites.net/api/ingest`

**Note:** For local testing, replace the URL with `http://localhost:8000/ingest`

---

## PDF Forms

### PDF Forms (First Batch)

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov",
    "forms": ["1120","4562","4626","8858","5471","1065","8865","1118"],
    "allow_prefix": ["/pub/irs-pdf"],
    "only_pdf": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 500,
    "concurrency": 4
  }'
```

### PDF Forms (Second Batch – Extended List)

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov",
    "forms": ["1120-M3","1120-D","4797","4562","8949","5471","8858","8865","8865-K1","8865-K2","8865-K3","8990","8992","1065","1065-M3","1065-K1","1065-K2","1065-K3","3800","1118","7004"],
    "allow_prefix": ["/pub/irs-pdf"],
    "only_pdf": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 500,
    "concurrency": 4
  }'
```

---

## Help / ITA / FAQs

### Help / ITA / FAQs (HTML)

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/help",
    "allow_prefix": ["/help", "/help/ita", "/help/faq", "/help/keywords"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 3000,
    "concurrency": 6
  }'
```

---

## Tax Topics

### Tax Topics (HTML)

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/taxtopics",
    "allow_prefix": ["/taxtopics"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 2000,
    "concurrency": 6
  }'
```

---

## Publications

### Publications (HTML)

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/publications",
    "allow_prefix": ["/publications"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 3000,
    "concurrency": 6
  }'
```

---

## Forms & Instructions

### Forms & Instructions (HTML Hub)

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/forms-instructions",
    "allow_prefix": ["/forms-instructions"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 2000,
    "concurrency": 6
  }'
```

### Publications/Forms PDFs (Deep Sweep)

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/forms-instructions",
    "allow_prefix": ["/pub/irs-pdf"],
    "only_pdf": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 10000,
    "concurrency": 4
  }'
```

---

## IRB (Internal Revenue Bulletin)

### IRB (HTML Issues)

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/irb",
    "allow_prefix": ["/irb"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 3000,
    "concurrency": 6
  }'
```

---

## IRS-Drop

### IRS-Drop (Notices, Announcements)

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/pub/irs-drop",
    "allow_prefix": ["/pub/irs-drop"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 3000,
    "concurrency": 6
  }'
```

---

## Credits & Deductions

### Credits & Deductions (HTML)

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/credits-deductions",
    "allow_prefix": ["/credits-deductions"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 3000,
    "concurrency": 6
  }'
```

---

## Core Hubs

### Individuals

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/individuals",
    "allow_prefix": ["/individuals"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 4000,
    "concurrency": 6
  }'
```

### Businesses

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/businesses",
    "allow_prefix": ["/businesses"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 4000,
    "concurrency": 6
  }'
```

### Small Businesses/Self-Employed

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/businesses/small-businesses-self-employed",
    "allow_prefix": ["/businesses/small-businesses-self-employed"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 3000,
    "concurrency": 6
  }'
```

### Charities & Nonprofits

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/charities-non-profits",
    "allow_prefix": ["/charities-non-profits"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 2500,
    "concurrency": 6
  }'
```

### Retirement Plans

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/retirement-plans",
    "allow_prefix": ["/retirement-plans"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 2500,
    "concurrency": 6
  }'
```

### Government Entities

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/government-entities",
    "allow_prefix": ["/government-entities"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 2000,
    "concurrency": 6
  }'
```

---

## Newsroom

### Newsroom (Broad)

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/newsroom",
    "allow_prefix": ["/newsroom"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 4000,
    "concurrency": 6
  }'
```

### Newsroom - IRS Tax Tips

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/newsroom/irs-tax-tips",
    "allow_prefix": ["/newsroom/irs-tax-tips"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 3000,
    "concurrency": 6
  }'
```

### Newsroom - IRS Newswire

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/newsroom/irs-newswire",
    "allow_prefix": ["/newsroom/irs-newswire"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 3000,
    "concurrency": 6
  }'
```

---

## Broad Sweep (Optional)

### Combined Multiple Hubs

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov",
    "allow_prefix": ["/help", "/taxtopics", "/publications", "/forms-instructions", "/irb", "/credits-deductions", "/individuals", "/businesses", "/newsroom"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 8000,
    "concurrency": 6
  }'
```

**Note:** If this yields 0 targets due to sitemap filtering, run hub-specific commands above instead.

---

## Notes

### Best Practices

1. **Always use `include_seed: true` and `follow_links: true`** - These are set by default in the API
2. **Monitor progress** - Check the `/stats` endpoint to see ingestion progress:
   ```bash
   curl -X GET https://complyia-ai-api.azurewebsites.net/api/stats
   ```
3. **Run sequentially** - Wait for one ingestion to complete before starting the next
4. **Start small** - Test with smaller `max_pages` first to verify the pipeline works

### URL File Method (Advanced)

The `url_file` parameter requires a file path on the server. If you need to use this method:

1. Generate a file of URLs from the IRS sitemap:
   ```bash
   curl -s https://www.irs.gov/sitemap.xml \
     | grep -o 'https://www.irs.gov[^<]*' \
     | grep '/compliance' \
     > compliance_urls.txt
   ```

2. Upload the file to your server and reference it:
   ```bash
   curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
     -H "Content-Type: application/json" \
     -d '{
       "url_file": "/path/to/compliance_urls.txt",
       "only_html": true,
       "max_pages": 5000,
       "concurrency": 6
     }'
   ```

### Environment Variables

If you encounter embedding errors, these environment variables can help (set on the server):

- **OpenAI embeddings:**
  ```
  EMBEDDINGS_PROVIDER=OPENAI
  OPENAI_API_KEY=your_key_here
  ```

- **Local CPU fallback:**
  ```
  PYTORCH_ENABLE_MPS_FALLBACK=1
  SENTENCE_TRANSFORMERS_DEVICE=cpu
  ```

---

## Quick Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `seed_url` | string | `"https://www.irs.gov"` | Starting URL for crawling |
| `max_pages` | integer | `100` | Maximum pages to crawl (1-10000) |
| `concurrency` | integer | `2` | Parallel workers (1-10) |
| `allow_prefix` | array[string] | `null` | Only crawl URLs with these prefixes |
| `only_html` | boolean | `false` | Only crawl HTML pages |
| `only_pdf` | boolean | `false` | Only crawl PDF files |
| `forms` | array[string] | `null` | Only crawl URLs containing these form names |
| `include_seed` | boolean | `true` | Include seed_url in crawl |
| `follow_links` | boolean | `true` | Follow links from pages |
| `url_file` | string | `null` | Path to file with URLs (server-side) |

