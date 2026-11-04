import os
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.document import Document, ProcessingStatus
from app.models.user import User
from app.api.auth import get_current_user
from app.services.ingestion.pipeline import ingestion_pipeline
from app.services.retrieval.vector_store import vector_store
from app.services.retrieval.bm25_store import bm25_store
from app.schemas.document import DocumentResponse, DocumentUploadResponse

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Uploads document, detects duplicates via SHA-256, and dispatches async indexing job."""
    file_bytes = await file.read()
    
    try:
        doc, is_duplicate = await ingestion_pipeline.ingest_upload(
            filename=file.filename,
            file_bytes=file_bytes,
            uploader_id=current_user.id if current_user else None,
            db=db
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    if is_duplicate:
        return DocumentUploadResponse(
            id=doc.id,
            filename=doc.filename,
            status=doc.status,
            message="Document content identical to existing upload. Deduplication applied; skipping re-indexing.",
            is_duplicate=True
        )

    # Dispatch background indexing task
    background_tasks.add_task(ingestion_pipeline.process_document_async, doc.id)

    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.filename,
        status=ProcessingStatus.PENDING,
        message="File accepted for asynchronous processing.",
        is_duplicate=False
    )

@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all uploaded documents with status and chunk stats."""
    stmt = select(Document).order_by(Document.created_at.desc())
    res = await db.execute(stmt)
    docs = res.scalars().all()
    return [DocumentResponse.model_validate(d) for d in docs]

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves document processing status and details."""
    stmt = select(Document).where(Document.id == document_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes document record, file on disk, vector embeddings, and BM25 index."""
    stmt = select(Document).where(Document.id == document_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Remove from vector & BM25 stores
    vector_store.delete_document_chunks(document_id)
    bm25_store.delete_document_chunks(document_id)

    # 2. Remove physical file
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # 3. Delete DB record
    await db.delete(doc)
    await db.commit()

    return {"message": f"Document '{doc.filename}' deleted successfully."}
