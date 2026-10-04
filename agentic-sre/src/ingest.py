import os
import glob
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "sre_runbooks")

def init_qdrant_collection(client: QdrantClient):
    """Creates the collection in Qdrant with hybrid search settings."""
    collections = [c.name for c in client.get_collections().collections]
    
    if COLLECTION_NAME in collections:
        print(f"Collection '{COLLECTION_NAME}' already exists. Recreating...")
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=1536,  # text-embedding-3-small dimensionality
            distance=models.Distance.COSINE
        )
    )
    
    # Payload index for full-text / keyword filtering
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="page_content",
        field_schema=models.TextIndexParams(
            type="text",
            tokenizer=models.TokenizerType.WORD,
            min_token_len=2,
            max_token_len=15,
            lowercase=True
        )
    )
    print(f"Created collection '{COLLECTION_NAME}' successfully.")

def run_ingestion():
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    init_qdrant_collection(client)

    runbook_files = glob.glob("data/runbooks/*.md")
    if not runbook_files:
        raise FileNotFoundError("No runbooks found in data/runbooks/")

    documents = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n", " "]
    )

    for filepath in runbook_files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        filename = os.path.basename(filepath)
        chunks = text_splitter.split_text(content)
        
        for idx, chunk in enumerate(chunks):
            documents.append({
                "content": chunk,
                "metadata": {"source": filename, "chunk_id": idx}
            })

    print(f"Extracted {len(documents)} chunks from {len(runbook_files)} runbooks.")

    points = []
    for idx, doc in enumerate(documents):
        vector = embeddings.embed_query(doc["content"])
        points.append(
            models.PointStruct(
                id=idx,
                vector=vector,
                payload={
                    "page_content": doc["content"],
                    "metadata": doc["metadata"]
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    print(f"Successfully indexed {len(points)} points into Qdrant.")

if __name__ == "__main__":
    run_ingestion()