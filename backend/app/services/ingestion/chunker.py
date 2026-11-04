import uuid
from typing import List, Dict, Any
from app.core.config import settings

class RecursiveChunker:
    """Splits structured text into semantic chunks with overlapping boundaries and metadata."""

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]
        return self._recursive_split(text, separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        final_chunks = []
        separator = separators[-1]
        new_separators = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator else list(text)
        current_chunk = []
        current_length = 0

        for piece in splits:
            piece_len = len(piece) + (len(separator) if current_chunk else 0)
            if current_length + piece_len > self.chunk_size:
                if current_chunk:
                    joined = separator.join(current_chunk).strip()
                    if len(joined) > self.chunk_size and new_separators:
                        final_chunks.extend(self._recursive_split(joined, new_separators))
                    elif joined:
                        final_chunks.append(joined)
                    
                    # Calculate overlap
                    overlap_acc = []
                    overlap_len = 0
                    for prev_piece in reversed(current_chunk):
                        if overlap_len + len(prev_piece) <= self.chunk_overlap:
                            overlap_acc.insert(0, prev_piece)
                            overlap_len += len(prev_piece)
                        else:
                            break
                    current_chunk = overlap_acc
                    current_length = overlap_len
                else:
                    if new_separators:
                        final_chunks.extend(self._recursive_split(piece, new_separators))
                    elif piece.strip():
                        final_chunks.append(piece.strip())
                    continue

            current_chunk.append(piece)
            current_length += piece_len

        if current_chunk:
            joined = separator.join(current_chunk).strip()
            if joined:
                final_chunks.append(joined)

        return final_chunks

    def chunk_document_sections(
        self,
        sections: List[Dict[str, Any]],
        document_id: str,
        document_name: str
    ) -> List[Dict[str, Any]]:
        """Takes parsed sections (with page/row metadata) and produces final chunk records."""
        chunks = []
        global_chunk_idx = 0

        for section in sections:
            raw_text = section.get("text", "")
            page_or_row = section.get("page_or_row", 1)
            source_type = section.get("source_type", "section")

            sub_chunks = self.split_text(raw_text)
            for sub_text in sub_chunks:
                clean_text = sub_text.strip()
                if not clean_text or len(clean_text) < 15: # Ignore trivial whitespace or tiny fragments
                    continue

                chunk_id = f"{document_id}_c{global_chunk_idx}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "document_name": document_name,
                    "page_or_row": page_or_row,
                    "chunk_index": global_chunk_idx,
                    "text": clean_text,
                    "source_type": source_type,
                    "char_count": len(clean_text)
                })
                global_chunk_idx += 1

        return chunks
