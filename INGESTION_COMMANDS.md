# IRS RAG Ingestion Commands

This document contains all the ingestion commands for the IRS RAG application. 

**Important Notes:**
1. **Remove any comments from JSON** - JSON does not support comments
2. **Don't use placeholder values** - Never use `"string"` as a value. Use `null` or omit optional fields
3. **Base URL:** Update `http://localhost:8000` to your actual API URL (e.g., `https://complyia-ai-api.azurewebsites.net/api`)

**Common Error:** If you see `[Errno 2] No such file or directory: 'string'`, you're using placeholder values. See `INGESTION_EXAMPLES.md` for correct usage.

---

## PDF Forms (First Batch)

```bash
curl -X POST http://localhost:8000/ingest \
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

## PDF Forms (Second Batch – Extended List)

```bash
curl -X POST http://localhost:8000/ingest \
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

## Help / ITA / FAQs (HTML)

```bash
curl -X POST http://localhost:8000/ingest \
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

## Tax Topics (HTML)

```bash
curl -X POST http://localhost:8000/ingest \
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

## Publications (HTML)

```bash
curl -X POST http://localhost:8000/ingest \
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

## Forms & Instructions (HTML Hub)

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/forms-instructions",
    "allow_prefix": ["/forms-instructions"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 1200,
    "concurrency": 6
  }'
```

## IRB (HTML)

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/irb",
    "allow_prefix": ["/irb"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 2000,
    "concurrency": 6
  }'
```

## Credits & Deductions (HTML)

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov/credits-deductions",
    "allow_prefix": ["/credits-deductions"],
    "only_html": true,
    "include_seed": true,
    "follow_links": true,
    "max_pages": 2000,
    "concurrency": 6
  }'
```

## Core Hubs - Individuals

```bash
curl -X POST http://localhost:8000/ingest \
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

## Core Hubs - Businesses

```bash
curl -X POST http://localhost:8000/ingest \
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

## Newsroom (Broad)

```bash
curl -X POST http://localhost:8000/ingest \
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

## Publications / Forms PDFs (Deep Sweep)

```bash
curl -X POST http://localhost:8000/ingest \
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

## Usage Notes

1. **Update the API URL:** Replace `http://localhost:8000` with your actual API endpoint (e.g., `https://complyia-ai-api.azurewebsites.net/api`)

2. **Run scripts individually:** Each command can be run independently. Wait for one to complete before starting the next.

3. **Monitor progress:** Check the response JSON for ingestion statistics including:
   - `pages_processed`: Number of pages successfully processed
   - `total_chunks`: Total chunks created and stored
   - `target_urls_found`: Number of URLs discovered

4. **Using the shell script:** You can also run all commands at once using:
   ```bash
   chmod +x ingestion_scripts.sh
   ./ingestion_scripts.sh
   ```

