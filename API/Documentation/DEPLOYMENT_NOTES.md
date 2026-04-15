# Deployment Notes - Async Ingestion Fix

## Important: Deploy Code Changes First

The timeout fix requires deploying the updated code to Azure. The current code on Azure is still using the synchronous (blocking) version.

## What Changed

The `/ingest` endpoint now:
1. Runs ingestion in a background thread pool
2. Returns immediately (no waiting)
3. Processes ingestion asynchronously

## Files Modified

- `controllers/rag_controller.py` - Updated to use async thread pool execution

## Deployment Steps

1. **Commit the changes:**
   ```bash
   git add controllers/rag_controller.py
   git commit -m "Fix: Make ingestion endpoint async to prevent timeout"
   git push
   ```

2. **Deploy to Azure:**
   - If using Azure App Service with Git deployment, push will auto-deploy
   - If using manual deployment, upload the updated files
   - Restart the Azure App Service if needed

3. **Verify deployment:**
   ```bash
   curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
     -H "Content-Type: application/json" \
     -d '{
       "seed_url": "https://www.irs.gov",
       "max_pages": 10,
       "concurrency": 1
     }'
   ```
   
   You should get an immediate response (not a timeout):
   ```json
   {
     "status": "accepted",
     "message": "Ingestion started in background",
     ...
   }
   ```

## Testing After Deployment

After deploying, test with a small batch first:

```bash
curl -X POST https://complyia-ai-api.azurewebsites.net/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov",
    "max_pages": 10,
    "concurrency": 2
  }'
```

Expected: Immediate response with `"status": "accepted"`

Then check stats to verify ingestion is running:
```bash
curl -X GET https://complyia-ai-api.azurewebsites.net/api/stats
```

## If Still Getting Timeouts

If you still get 504 errors after deployment:

1. **Check Azure App Service logs** - Verify the new code is running
2. **Check Azure timeout settings** - Some Azure configurations have additional timeouts
3. **Verify the endpoint** - Make sure you're hitting the correct URL
4. **Check application startup** - Ensure the app restarted with new code

## Alternative: Azure Function or Queue

For production at scale, consider:
- Azure Functions for ingestion (better for long-running tasks)
- Azure Queue Storage + Worker process
- Azure Container Instances for batch processing

The current solution works for most cases but may need adjustment for very large batches.

