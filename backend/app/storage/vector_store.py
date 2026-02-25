"""ChromaDB vector store for RAG retrieval."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Optional
from app.config import settings
import logging
import os

logger = logging.getLogger(__name__)

os.makedirs(settings.chroma_path, exist_ok=True)


class VectorStore:
    def __init__(self):
        self._client = None

    def _get_client(self) -> chromadb.Client:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=settings.chroma_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        client = self._get_client()
        return client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[dict],
        ids: List[str],
    ) -> None:
        """Upsert text documents with metadata."""
        if not documents:
            return
        collection = self.get_or_create_collection(collection_name)
        try:
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
        except Exception as e:
            logger.error(f"Error upserting to {collection_name}: {e}")

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 10,
        where: Optional[dict] = None,
    ) -> List[dict]:
        """Query collection and return results with metadata."""
        try:
            collection = self.get_or_create_collection(collection_name)
            count = collection.count()
            if count == 0:
                return []
            n = min(n_results, count)
            kwargs = {"query_texts": [query_text], "n_results": n}
            if where:
                kwargs["where"] = where

            results = collection.query(**kwargs)
            output = []
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            ids = results.get("ids", [[]])[0]

            for doc, meta, dist, rid in zip(documents, metadatas, distances, ids):
                output.append({
                    "id": rid,
                    "text": doc,
                    "metadata": meta,
                    "distance": dist,
                })
            return output
        except Exception as e:
            logger.error(f"Error querying {collection_name}: {e}")
            return []

    def delete_collection(self, name: str) -> None:
        try:
            client = self._get_client()
            client.delete_collection(name)
        except Exception as e:
            logger.error(f"Error deleting collection {name}: {e}")


vector_store = VectorStore()
