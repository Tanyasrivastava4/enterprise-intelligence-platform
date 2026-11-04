import os
import hashlib
import aiofiles
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document, ProcessingStatus
from app.services.ingestion.parsers import DocumentParser
from app.services.ingestion.chunker import RecursiveChunker
from app.services.retrieval.vector_store import vector_store
from app.services.retrieval.bm25_store import bm25_store
from app.core.config import settings
from app.core.database import AsyncSessionLocal

class IngestionPipeline:

    @staticmethod
    def calculate_sha256(file_bytes: bytes) -> str:
        """Computes SHA-256 hash of file content for deduplication."""
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        return hasher.hexdigest()

    @staticmethod
    def validate_file(filename: str, file_size: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validates extension and file size."""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            return False, f"Unsupported file extension '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}", None

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            return False, f"File exceeds maximum size limit of {settings.MAX_UPLOAD_SIZE_MB}MB", None

        return True, None, ext

    async def ingest_upload(
        self,
        filename: str,
        file_bytes: bytes,
        uploader_id: Optional[str],
        db: AsyncSession
    ) -> Tuple[Document, bool]:
        """Validates, checks for duplicates, saves file and creates document record.

        Returns (document, is_duplicate).
        """
        is_valid, err, ext = self.validate_file(filename, len(file_bytes))
        if not is_valid:
            raise ValueError(err)

        content_hash = self.calculate_sha256(file_bytes)

        # Check for existing duplicate document by content_hash
        stmt = select(Document).where(Document.content_hash == content_hash)
        result = await db.execute(stmt)
        existing_doc = result.scalar_one_or_none()

        if existing_doc:
            # Duplicate detected - return existing record without re-indexing
            return existing_doc, True

        # Save to disk
        safe_filename = f"{content_hash[:12]}_{filename.replace(' ', '_')}"
        save_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

        with open(save_path, "wb") as f:
            f.write(file_bytes)

        # Create Document record in PENDING status
        doc = Document(
            filename=filename,
            file_path=save_path,
            file_type=ext.replace(".", ""),
            file_size_bytes=len(file_bytes),
            content_hash=content_hash,
            status=ProcessingStatus.PENDING,
            uploader_id=uploader_id
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        return doc, False

    @staticmethod
    async def process_document_async(document_id: str):
        """Asynchronous background worker that parses, chunks, and indexes a document."""
        async with AsyncSessionLocal() as session:
            stmt = select(Document).where(Document.id == document_id)
            res = await session.execute(stmt)
            doc = res.scalar_one_or_none()

            if not doc:
                return

            try:
                # 1. Update status to PROCESSING
                doc.status = ProcessingStatus.PROCESSING
                await session.commit()

                # 2. Parse document sections
                sections = DocumentParser.parse(doc.file_path, doc.file_type)

                # 3. Chunk sections
                chunker = RecursiveChunker()
                chunks = chunker.chunk_document_sections(sections, doc.id, doc.filename)

                if not chunks:
                    doc.status = ProcessingStatus.FAILED
                    doc.error_message = "No extractable text or content found in document"
                    await session.commit()
                    return

                # 4. Embed and Index in Dense Vector Store & Sparse BM25
                vector_store.add_chunks(chunks)
                bm25_store.add_chunks(chunks)

                # 5. Update status to INDEXED
                total_chars = sum(c["char_count"] for c in chunks)
                doc.chunk_count = len(chunks)
                doc.character_count = total_chars
                doc.status = ProcessingStatus.INDEXED
                doc.error_message = None
                await session.commit()

            except Exception as e:
                doc.status = ProcessingStatus.FAILED
                doc.error_message = f"Processing error: {str(e)}"
                await session.commit()

ingestion_pipeline = IngestionPipeline()
