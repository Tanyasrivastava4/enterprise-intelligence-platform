import os
import re
import pickle
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from app.core.config import settings

class BM25Store:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BM25Store, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.persist_path = os.path.join(settings.CHROMA_PERSIST_DIR, "bm25_index.pkl")
        self.chunks_data: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None
        self._load()

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, alphanumeric tokenization
        return re.findall(r"\w+", text.lower())

    def _load(self):
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, "rb") as f:
                    data = pickle.load(f)
                    self.chunks_data = data.get("chunks_data", [])
                    self.tokenized_corpus = [self._tokenize(c["text"]) for c in self.chunks_data]
                    if self.tokenized_corpus:
                        self.bm25 = BM25Okapi(self.tokenized_corpus)
            except Exception as e:
                print(f"Error loading BM25 index: {e}")
                self.chunks_data = []
                self.tokenized_corpus = []
                self.bm25 = None

    def _save(self):
        try:
            with open(self.persist_path, "wb") as f:
                pickle.dump({"chunks_data": self.chunks_data}, f)
        except Exception as e:
            print(f"Error saving BM25 index: {e}")

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Adds new chunks to the BM25 index."""
        if not chunks:
            return

        # Filter out existing chunk_ids to avoid duplicates
        existing_ids = {c["chunk_id"] for c in self.chunks_data}
        new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]

        if not new_chunks:
            return

        self.chunks_data.extend(new_chunks)
        self.tokenized_corpus = [self._tokenize(c["text"]) for c in self.chunks_data]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        self._save()

    def delete_document_chunks(self, document_id: str):
        """Removes all chunks belonging to a document from BM25 index."""
        self.chunks_data = [c for c in self.chunks_data if c["document_id"] != document_id]
        if self.chunks_data:
            self.tokenized_corpus = [self._tokenize(c["text"]) for c in self.chunks_data]
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.tokenized_corpus = []
            self.bm25 = None
        self._save()

    def query(
        self,
        query_text: str,
        n_results: int = 10,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Queries the BM25 index and returns ranked chunks."""
        if not self.bm25 or not self.chunks_data:
            return []

        tokens = self._tokenize(query_text)
        if not tokens:
            return []

        doc_scores = self.bm25.get_scores(tokens)
        scored_pairs = list(enumerate(doc_scores))
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_pairs:
            if score <= 0:
                continue

            chunk = self.chunks_data[idx]
            if document_ids and chunk["document_id"] not in document_ids:
                continue

            results.append({
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "document_name": chunk["document_name"],
                "page_or_row": chunk.get("page_or_row", 1),
                "chunk_index": chunk.get("chunk_index", 0),
                "text": chunk["text"],
                "score": float(score),
                "retrieval_source": "bm25_sparse"
            })

            if len(results) >= n_results:
                break

        return results

bm25_store = BM25Store()
