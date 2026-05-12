import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

try:
    collections = client.get_collections()
    print("Available collections:")
    for c in collections.collections:
        print(f" - {c.name}")
except Exception as e:
    print(f"Error: {e}")
