# Handling Gateway Timeout Issues

## Problem

When ingesting large numbers of pages (e.g., 500+ pages), you may encounter **504 Gateway Timeout** errors. This happens because:

1. Azure App Service has a ~230 second (4 minutes) timeout for HTTP requests
2. Processing 500 PDF pages with 4 concurrent workers can take 10-30+ minutes
3. The synchronous endpoint waits for completion before responding

## Solution Implemented

The `/ingest` endpoint now uses **FastAPI BackgroundTasks** to process ingestion asynchronously:

- ✅ Returns immediately with acceptance message
- ✅ Ingestion continues in background
- ✅ No timeout errors
- ✅ Check `/stats` endpoint to monitor progress

## Usage

The endpoint now returns immediately:

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov",
    "forms": ["1120-M3","1120-D","4797"],
    "allow_prefix": ["/pub/irs-pdf"],
    "only_pdf": true,
    "max_pages": 500,
    "concurrency": 4
  }'
```

**Response:**
```json
{
  "status": "accepted",
  "message": "Ingestion started in background",
  "seed_url": "https://www.irs.gov",
  "max_pages": 500,
  "concurrency": 4,
  "note": "Ingestion is processing. Check /stats endpoint for progress."
}
```

## Monitoring Progress

Check the `/stats` endpoint to see ingestion progress:

```bash
curl -X GET https://complyia-ai-api.azurewebsites.net/api/stats
```

## Alternative: Reduce Pages for Testing

If you want to test with synchronous processing (wait for completion), reduce `max_pages`:

```bash
# Test with smaller batch
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov",
    "forms": ["1120"],
    "allow_prefix": ["/pub/irs-pdf"],
    "only_pdf": true,
    "max_pages": 10,
    "concurrency": 2
  }'
```

## Best Practices

1. **For Production:** Use the async endpoint (current implementation) - it handles any number of pages
2. **For Testing:** Start with `max_pages: 10-50` to verify the pipeline works
3. **Monitor:** Use `/stats` endpoint to track ingestion progress
4. **Batch Processing:** Run multiple smaller batches if you need to track individual completion

## Expected Processing Times

Approximate times per page (varies by content size):
- **HTML pages:** 2-5 seconds per page
- **PDF files:** 5-15 seconds per page (depends on PDF size)

With `concurrency: 4`:
- 100 pages: ~5-10 minutes
- 500 pages: ~25-50 minutes
- 1000 pages: ~50-100 minutes

The async implementation allows all of these to run without timeout issues.

