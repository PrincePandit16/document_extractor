from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.enums import DocumentType, ExtractionStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_filename: str
    file_size: Optional[int]
    mime_type: Optional[str]
    doc_type: DocumentType
    status: ExtractionStatus
    raw_ocr_text: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]


class ExtractionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    stage: Optional[str]
    message: Optional[str]
    level: str
    created_at: datetime

class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    ocr_available: bool
    llm_available: bool
    groq_model: str


class ErrorResponse(BaseModel):
    error: str
    code: str
    detail: Optional[str] = None


class ExtractionPreviewResponse(BaseModel):
    doc_id: int
    doc_type: str
    extracted_fields: Dict[str, Any]
    confidence_score: Optional[float]
    ocr_preview: str  # First 500 chars of OCR text
