from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from loguru import logger

from app.db.database import get_db
from app.services.extraction_service import ExtractionService
from app.schemas.schemas import (
    DocumentResponse,
    DocumentListResponse,
    ExtractionLogResponse,
    HealthResponse,
    ErrorResponse,
    ExtractionPreviewResponse,
)
from app.utils.exceptions import (
    DocExtractorException,
    DocumentNotFoundException,
    FileValidationException,
)
from config.settings import settings

router = APIRouter()


def get_extraction_service(db: Session = Depends(get_db)) -> ExtractionService:
    return ExtractionService(db)


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(svc: ExtractionService = Depends(get_extraction_service)):
    health = svc.get_system_health()
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        **health,
    )


# ── Documents ────────────────────────────────────────────────────────────────

@router.post("/documents/upload", response_model=DocumentResponse, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    doc_type: Optional[str] = Query(default="auto", description="Document type hint or 'auto'"),
    svc: ExtractionService = Depends(get_extraction_service),
):
    """Upload a document and extract information from it."""
    try:
        content = await file.read()
        doc = svc.upload_and_extract(
            file_content=content,
            original_filename=file.filename,
            doc_type_hint=doc_type,
        )
        return DocumentResponse.model_validate(doc)
    except FileValidationException as e:
        raise HTTPException(status_code=400, detail={"error": e.message, "code": e.code})
    except DocExtractorException as e:
        raise HTTPException(status_code=422, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.error(f"Unexpected error in upload: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL_ERROR"})


@router.get("/documents", response_model=DocumentListResponse, tags=["Documents"])
def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    svc: ExtractionService = Depends(get_extraction_service),
):
    """List all processed documents."""
    docs = svc.list_documents(skip=skip, limit=limit)
    return DocumentListResponse(
        total=len(docs),
        documents=[DocumentResponse.model_validate(d) for d in docs],
    )


@router.get("/documents/{doc_id}", response_model=DocumentResponse, tags=["Documents"])
def get_document(
    doc_id: int,
    svc: ExtractionService = Depends(get_extraction_service),
):
    """Get a specific document by ID."""
    try:
        doc = svc.get_document(doc_id)
        return DocumentResponse.model_validate(doc)
    except DocumentNotFoundException as e:
        raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})


@router.get("/documents/{doc_id}/preview", response_model=ExtractionPreviewResponse, tags=["Documents"])
def get_extraction_preview(
    doc_id: int,
    svc: ExtractionService = Depends(get_extraction_service),
):
    """Get extraction preview for a document."""
    try:
        doc = svc.get_document(doc_id)
        return ExtractionPreviewResponse(
            doc_id=doc.id,
            doc_type=doc.doc_type.value,
            extracted_fields=doc.extracted_data or {},
            confidence_score=doc.confidence_score,
            ocr_preview=(doc.raw_ocr_text or "")[:500],
        )
    except DocumentNotFoundException as e:
        raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})


@router.get("/documents/{doc_id}/logs", response_model=List[ExtractionLogResponse], tags=["Documents"])
def get_document_logs(
    doc_id: int,
    svc: ExtractionService = Depends(get_extraction_service),
):
    """Get processing logs for a document."""
    try:
        logs = svc.get_extraction_logs(doc_id)
        return [ExtractionLogResponse.model_validate(l) for l in logs]
    except DocumentNotFoundException as e:
        raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})


@router.delete("/documents/{doc_id}", tags=["Documents"])
def delete_document(
    doc_id: int,
    svc: ExtractionService = Depends(get_extraction_service),
):
    """Delete a document and its extracted data."""
    try:
        svc.delete_document(doc_id)
        return {"message": f"Document {doc_id} deleted successfully"}
    except DocumentNotFoundException as e:
        raise HTTPException(status_code=404, detail={"error": e.message, "code": e.code})
