import re
from typing import List, Dict, Any, Tuple

class PromptInjectionShield:
    """Treats retrieved document chunks as untrusted input and prevents

    prompt injection attacks embedded inside document text.
    """

    SUSPICIOUS_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(all\s+)?(system|safety)\s+prompts",
        r"you\s+are\s+now\s+(an?\s+)?(unrestricted|jailbroken|dan|developer\s+mode)",
        r"system\s*:\s*override",
        r"reveal\s+(your\s+)?(system\s+prompt|secret\s+key|api\s+key)",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"\[INST\]",
        r"\[/INST\]",
    ]

    @classmethod
    def sanitize_chunk_text(cls, text: str) -> Tuple[str, bool]:
        """Detects and defangs suspicious prompt injection strings in text."""
        sanitized = text
        threat_detected = False

        for pattern in cls.SUSPICIOUS_PATTERNS:
            matches = list(re.finditer(pattern, sanitized, re.IGNORECASE))
            if matches:
                threat_detected = True
                sanitized = re.sub(
                    pattern,
                    r"[DEFANGED_INJECTION_ATTEMPT]",
                    sanitized,
                    flags=re.IGNORECASE
                )

        return sanitized, threat_detected

    @classmethod
    def build_enveloped_context(cls, chunks: List[Dict[str, Any]]) -> Tuple[str, int]:
        """Encloses untrusted document chunks inside strict XML boundary tags."""
        context_blocks = []
        threats_count = 0

        for idx, chunk in enumerate(chunks):
            raw_text = chunk.get("text", "")
            sanitized_text, threat = cls.sanitize_chunk_text(raw_text)
            if threat:
                threats_count += 1

            cid = chunk.get("chunk_id", f"c_{idx}")
            doc_name = chunk.get("document_name", "Unknown")
            page_or_row = chunk.get("page_or_row", 1)

            block = (
                f'<untrusted_document_context chunk_id="{cid}" document="{doc_name}" page_or_row="{page_or_row}">\n'
                f'{sanitized_text}\n'
                f'</untrusted_document_context>'
            )
            context_blocks.append(block)

        enveloped_context = "\n\n".join(context_blocks)
        return enveloped_context, threats_count

prompt_injection_shield = PromptInjectionShield()
