from typing import List, Dict, Any, Optional
from app.services.retrieval.vector_store import vector_store
from app.services.retrieval.bm25_store import bm25_store
from app.core.config import settings

class HybridRetriever:
    """Combines Dense Vector Semantic Search and Sparse BM25 Keyword Search

    using Reciprocal Rank Fusion (RRF) and Score Thresholding.
    """

    def __init__(self, k_constant: int = 60, similarity_threshold: float = settings.SIMILARITY_THRESHOLD):
        self.k_constant = k_constant
        self.similarity_threshold = similarity_threshold

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """Performs hybrid retrieval combining dense and sparse rankings."""
        # 1. Fetch dense vector results
        dense_results = vector_store.query(
            query_text=query,
            n_results=top_k * 2,
            document_ids=document_ids
        )

        if not use_hybrid:
            # Dense only fallback
            filtered = [r for r in dense_results if r["score"] >= self.similarity_threshold]
            return filtered[:top_k]

        # 2. Fetch sparse BM25 results
        sparse_results = bm25_store.query(
            query_text=query,
            n_results=top_k * 2,
            document_ids=document_ids
        )

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        chunk_lookup: Dict[str, Dict[str, Any]] = {}

        # Process dense ranks
        for rank, item in enumerate(dense_results):
            cid = item["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.k_constant + rank + 1))
            chunk_lookup[cid] = item

        # Process sparse ranks
        for rank, item in enumerate(sparse_results):
            cid = item["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.k_constant + rank + 1))
            if cid not in chunk_lookup:
                chunk_lookup[cid] = item

        # 4. Sort by merged RRF score
        sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        final_chunks = []
        for cid in sorted_cids:
            chunk = chunk_lookup[cid]
            # Copy chunk and attach combined RRF score
            merged_chunk = dict(chunk)
            merged_chunk["rrf_score"] = round(rrf_scores[cid], 5)
            # Retain original cosine similarity score if available
            orig_score = chunk.get("score", 0.0)
            merged_chunk["similarity_score"] = orig_score

            # Grounding check: Ensure at least one search method saw sufficient signal
            if chunk.get("retrieval_source") == "dense_vector" and orig_score < self.similarity_threshold:
                # If dense similarity is weak and not found in BM25, skip
                if cid not in [s["chunk_id"] for s in sparse_results]:
                    continue

            final_chunks.append(merged_chunk)
            if len(final_chunks) >= top_k:
                break

        return final_chunks

hybrid_retriever = HybridRetriever()
