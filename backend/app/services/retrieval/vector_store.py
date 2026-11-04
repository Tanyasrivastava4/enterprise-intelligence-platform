import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from app.core.config import settings

class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = "enterprise_knowledge_base"
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self._embedding_model = None

    @property
    def embedding_model(self):
        """Lazy loads embedding model on first retrieval/indexing to guarantee instantaneous Uvicorn startup."""
        if self._embedding_model is None:
            print(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}...")
            self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            print("Embedding model loaded successfully.")
        return self._embedding_model

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Generates embeddings and indexes chunks with metadata in ChromaDB."""
        if not chunks:
            return

        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [
            {
                "document_id": c["document_id"],
                "document_name": c["document_name"],
                "page_or_row": c["page_or_row"],
                "chunk_index": c["chunk_index"],
                "char_count": c["char_count"]
            }
            for c in chunks
        ]

        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True).tolist()
        
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    def delete_document_chunks(self, document_id: str):
        """Deletes all chunks associated with a specific document ID."""
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception as e:
            print(f"Error deleting chunks for doc {document_id}: {e}")

    def query(
        self,
        query_text: str,
        n_results: int = 10,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Queries the vector store and returns chunks with cosine similarity scores."""
        query_embedding = self.embedding_model.encode([query_text], convert_to_numpy=True).tolist()[0]
        
        where_filter = None
        if document_ids and len(document_ids) == 1:
            where_filter = {"document_id": document_ids[0]}
        elif document_ids and len(document_ids) > 1:
            where_filter = {"document_id": {"$in": document_ids}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        candidates = []
        if results and results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for chunk_id, text, meta, dist in zip(ids, docs, metas, distances):
                # Chroma returns cosine distance (0 to 2), where 0 is identical.
                # Cosine similarity = 1 - distance
                similarity = max(0.0, 1.0 - dist)
                candidates.append({
                    "chunk_id": chunk_id,
                    "document_id": meta.get("document_id"),
                    "document_name": meta.get("document_name"),
                    "page_or_row": meta.get("page_or_row", 1),
                    "chunk_index": meta.get("chunk_index", 0),
                    "text": text,
                    "score": similarity,
                    "retrieval_source": "dense_vector"
                })

        return candidates

vector_store = VectorStore()
