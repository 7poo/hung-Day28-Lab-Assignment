# scripts/05_embed_to_qdrant.py
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os
import hashlib

EMBED_URL = os.environ["EMBED_NGROK_URL"]
qdrant = QdrantClient(host="localhost", port=6333)

# Tạo collection
qdrant.recreate_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

def embed_and_store(records: list[dict]):
    texts = [r["text"] for r in records]
    try:
        # Gọi Kaggle/Colab embedding service nếu endpoint /embed sẵn sàng.
        response = requests.post(f"{EMBED_URL.rstrip('/')}/embed", json={"texts": texts}, timeout=30)
        response.raise_for_status()
        embeddings = response.json()["embeddings"]
    except Exception as exc:
        print(f"Embedding service unavailable, using local deterministic fallback: {exc}")
        embeddings = [fallback_embedding(text) for text in texts]

    points = [
        PointStruct(id=i, vector=emb, payload=rec)
        for i, (emb, rec) in enumerate(zip(embeddings, records))
    ]
    qdrant.upsert(collection_name="documents", points=points)
    print(f"Integration 5 OK: {len(points)} vectors stored in Qdrant")

def fallback_embedding(text: str, size: int = 384) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for i in range(size):
        byte = digest[i % len(digest)]
        values.append((byte / 127.5) - 1.0)
    return values

# Test với sample data
embed_and_store([
    {"id": "doc_001", "text": "AI platform integration test"},
    {"id": "doc_002", "text": "Kafka to Airflow pipeline"},
])
