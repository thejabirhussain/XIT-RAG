#!/bin/bash

# IRS RAG Ingestion Scripts
# Usage: Run each command individually or execute the entire script
# Make sure your API server is running on http://localhost:8000 (or update the URL)

API_URL="http://localhost:8000/ingest"

# PDF Forms (First Batch)
echo "Starting PDF Forms (First Batch) ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"

# PDF Forms (Second Batch – Extended List)
echo "Starting PDF Forms (Second Batch – Extended List) ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"

# Help / ITA / FAQs (HTML)
echo "Starting Help / ITA / FAQs (HTML) ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"

# Tax Topics (HTML)
echo "Starting Tax Topics (HTML) ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"

# Publications (HTML)
echo "Starting Publications (HTML) ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"

# Forms & Instructions (HTML Hub)
echo "Starting Forms & Instructions (HTML Hub) ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"

# IRB (HTML)
echo "Starting IRB (HTML) ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"

# Credits & Deductions (HTML)
echo "Starting Credits & Deductions (HTML) ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"

# Core Hubs - Individuals
echo "Starting Core Hubs - Individuals ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"

# Core Hubs - Businesses
echo "Starting Core Hubs - Businesses ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"

# Newsroom (Broad)
echo "Starting Newsroom (Broad) ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"

# Publications / Forms PDFs (Deep Sweep)
echo "Starting Publications / Forms PDFs (Deep Sweep) ingestion..."
curl -X POST "$API_URL" \
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

echo -e "\n\n"
echo "All ingestion scripts completed!"

