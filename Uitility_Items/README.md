# IRS RAG Application

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Data Ingestion

To ingest data into the RAG system, use the `/ingest` endpoint. See `INGESTION_COMMANDS.md` for all available ingestion scripts.

**Quick Example:**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_url": "https://www.irs.gov",
    "max_pages": 100,
    "concurrency": 2,
    "only_html": true
  }'
```

**Important:** JSON does not support comments. Remove any comments from JSON payloads before sending requests.

For complete ingestion scripts, see:
- `INGESTION_COMMANDS.md` - Individual commands for copy-paste
- `ingestion_scripts.sh` - Executable shell script with all commands

## API Endpoints

- `POST /ingest` - Ingest data from URLs
- `POST /query` - Query the RAG system
- `GET /stats` - Get ingestion statistics

## Project Structure

- **Controllers** - Handling HTTP Requests
- **Services** - Core functions of the business logic 
- **Handlers** - Orchestrating those functions to perform the API call
- **Models** - Request, response and other schemas
- **Helpers** - Helper functions for the Services folder (domain specific delegated logic)
- **Utils** - Cross Cutting simple functions used across different domains

All constants in respective files on the top of the code.

`.env` file only has private/secret variables like qdrant url and API key (Ollama url of VM must also be added).

## Git Commands

```bash
git status
git add .
git commit -m "quick commit"
git push
```


## UI setup

```bash
npm install
npm run dev
```
