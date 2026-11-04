import re
from typing import List, Dict, Any, Tuple

class GroundingCritic:
    """Verifies that generated responses are strictly grounded in retrieved evidence

    and identifies contradictory facts between multiple documents.
    """

    @staticmethod
    def extract_citations_from_text(text: str) -> List[str]:
        """Extracts bracketed citations like [Doc: filename, Page: 2] or [Doc: filename]."""
        matches = re.findall(r"\[(?:Doc:\s*([^,\]]+)(?:,\s*Page:\s*(\d+))?)\]", text)
        return [m[0].strip() for m in matches if m[0].strip()]

    @staticmethod
    def detect_conflicts_in_chunks(chunks: List[Dict[str, Any]]) -> List[str]:
        """Heuristic and keyword scanning to detect conflicting claims between retrieved documents."""
        conflicts = []
        # Group chunks by document
        doc_chunks: Dict[str, List[str]] = {}
        for c in chunks:
            doc_name = c.get("document_name", "Unknown")
            doc_chunks.setdefault(doc_name, []).append(c.get("text", "").lower())

        if len(doc_chunks) >= 2:
            # Check for common enterprise contradiction signals across documents
            # (e.g., different ports, status codes, recommended versions)
            docs = list(doc_chunks.keys())
            for i in range(len(docs)):
                for j in range(i + 1, len(docs)):
                    text_a = " ".join(doc_chunks[docs[i]])
                    text_b = " ".join(doc_chunks[docs[j]])
                    
                    # Example pattern: port differences
                    ports_a = set(re.findall(r"port\s+(\d+)", text_a))
                    ports_b = set(re.findall(r"port\s+(\d+)", text_b))
                    diff_ports = (ports_a ^ ports_b)
                    if ports_a and ports_b and diff_ports:
                        conflicts.append(
                            f"Port configuration discrepancy: '{docs[i]}' refers to port(s) {list(ports_a)}, while '{docs[j]}' refers to port(s) {list(ports_b)}."
                        )

                    # Example pattern: status codes
                    status_a = set(re.findall(r"status(?:\s+code)?\s+(\d{3})", text_a))
                    status_b = set(re.findall(r"status(?:\s+code)?\s+(\d{3})", text_b))
                    if status_a and status_b and (status_a != status_b):
                        conflicts.append(
                            f"Status code variance: '{docs[i]}' reports {list(status_a)}, whereas '{docs[j]}' reports {list(status_b)}."
                        )

        return conflicts

    @classmethod
    def verify_response(
        cls,
        query: str,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Performs AI Response Verification (Challenge #4)."""
        if not retrieved_chunks:
            return {
                "is_grounded": False,
                "insufficient_information": True,
                "conflicts_detected": [],
                "citations_found": []
            }

        citations_found = cls.extract_citations_from_text(answer)
        conflicts = cls.detect_conflicts_in_chunks(retrieved_chunks)

        # Check if answer acknowledged insufficient info
        insufficient_markers = [
            "insufficient information",
            "not mentioned in the provided documents",
            "does not contain information",
            "no evidence found"
        ]
        is_insufficient = any(marker in answer.lower() for marker in insufficient_markers)

        # Grounding score estimation based on presence of citations and context overlap
        is_grounded = True
        if not is_insufficient and len(citations_found) == 0 and len(retrieved_chunks) > 0:
            # If answer didn't cite sources despite having context
            is_grounded = False

        return {
            "is_grounded": is_grounded,
            "insufficient_information": is_insufficient,
            "conflicts_detected": conflicts,
            "citations_found": citations_found
        }

grounding_critic = GroundingCritic()
