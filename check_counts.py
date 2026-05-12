import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

for col in ["irs_rag_v1", "schema"]:
    try:
        count = client.get_collection(col).points_count
        print(f"Collection '{col}': {count} points")
    except Exception as e:
        print(f"Error checking '{col}': {e}")
