import os
import sys
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, OptimizersConfigDiff, HnswConfigDiff
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer

# We use the same configuration as `irs_rag_v1`
COLLECTION_NAME = "schema"
VECTOR_SIZE = 384
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
QDRANT_URL = "http://localhost:6333"

import re

def extract_chunks_from_pdf(pdf_path):
    print(f"Reading PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    chunks = []
    
    current_table = None
    current_section = None
    current_text = []

    table_pattern = re.compile(r"\[TABLE:\s*(.*?)\]")
    section_pattern = re.compile(r"\[SECTION:\s*(.*?)\]")
    
    def finalize_chunk():
        if current_text and current_table and current_section:
            chunks.append({
                "table": current_table,
                "section": current_section,
                "text": "\n".join(current_text).strip()
            })
        current_text.clear()

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            has_table = table_pattern.search(line)
            has_section = section_pattern.search(line)
            
            if has_table or has_section:
                finalize_chunk()
                if has_table:
                    current_table = has_table.group(1).strip()
                if has_section:
                    current_section = has_section.group(1).strip()
                current_text.append(line)
            else:
                current_text.append(line)
                
    finalize_chunk()
    return chunks

def setup_collection(client):
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        print(f"Creating collection {COLLECTION_NAME}...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
            optimizers_config=OptimizersConfigDiff(memmap_threshold=20000),
        )
        try:
            client.update_collection(
                collection_name=COLLECTION_NAME,
                hnsw_config=HnswConfigDiff(
                    m=64,
                    ef_construct=128,
                    full_scan_threshold=10000,
                ),
                optimizers_config=OptimizersConfigDiff(
                    default_segment_number=2,
                ),
            )
        except Exception as e:
            print(f"Note: HNSW update skipped ({e})")

def main():
    pdf_path = "/Users/shaikmohammedjabirhussain/Downloads/schema_for_vectordb.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        sys.exit(1)
        
    chunks = extract_chunks_from_pdf(pdf_path)
    print(f"Extracted {len(chunks)} chunks.")
    
    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    
    print("Connecting to Qdrant...")
    client = QdrantClient(url=QDRANT_URL)
    setup_collection(client)
    
    points = []
    for i, chunk in enumerate(chunks):
        embedding = model.encode(chunk["text"], show_progress_bar=False, convert_to_numpy=True)
        embedding = embedding.astype(np.float32).tolist()
        
        payload = {
            "table": chunk["table"],
            "section": chunk["section"],
            "text": chunk["text"],
            "source": "schema_for_vectordb.pdf",
            "content_type": "schema",
        }
        
        # We need a unique ID, generating deterministically or sequentially
        # For simplicity, sequential with a prefix or just an integer
        point_id = i + 1
        
        points.append(PointStruct(id=point_id, vector=embedding, payload=payload))
        
    if points:
        print(f"Upserting {len(points)} points into '{COLLECTION_NAME}' collection...")
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print("Done!")
    else:
        print("No points to upsert.")

if __name__ == "__main__":
    main()
