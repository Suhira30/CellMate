"""
Copy pre-embedded chunks from evaluation collections (vectorstore/eval)
into the production vector store (vectorstore/nie_biology_unit02).
This allows zero-cost instant population of the production database!
"""
import chromadb
from chromadb.config import Settings
from src.config import VECTORSTORE_DIR

def copy_eval_to_production(source_collection_name: str = "eval_hybrid_structure_recursive"):
    eval_db_path = VECTORSTORE_DIR / "eval"

    print(f"📦 Connecting to eval database at {eval_db_path}...")
    eval_client = chromadb.PersistentClient(
        path=str(eval_db_path),
        settings=Settings(anonymized_telemetry=False)
    )

    try:
        eval_coll = eval_client.get_collection(source_collection_name)
    except Exception as e:
        print(f"❌ Source collection '{source_collection_name}' not found: {e}")
        return False

    count = eval_coll.count()
    if count == 0:
        print(f"⚠️ Source collection '{source_collection_name}' is empty (0 chunks).")
        return False

    print(f"🔍 Found {count} chunks in '{source_collection_name}'. Extracting...")

    all_data = eval_coll.get(include=["documents", "metadatas", "embeddings"])

    ids = all_data["ids"]
    documents = all_data["documents"]
    metadatas = all_data["metadatas"]
    embeddings = all_data["embeddings"]

    print(f"📥 Connecting to production database at {VECTORSTORE_DIR}...")
    prod_client = chromadb.PersistentClient(
        path=str(VECTORSTORE_DIR),
        settings=Settings(anonymized_telemetry=False)
    )

    prod_coll = prod_client.get_or_create_collection(
        name="nie_biology_unit02",
        metadata={"hnsw:space": "cosine"}
    )

    print(f"📥 Copying {len(ids)} chunks to production collection 'nie_biology_unit02'...")
    prod_coll.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )

    print(f"✅ Production collection 'nie_biology_unit02' successfully populated! Total chunks: {prod_coll.count()}")
    return True

if __name__ == "__main__":
    copy_eval_to_production()
