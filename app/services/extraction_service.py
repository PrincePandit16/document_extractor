from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.db.repository import DocumentRepository
from app.db.models import Document
from app.services.ocr_service import OCRService
from app.services.llm_service import LLMService
from app.services.file_service import FileService
from app.templates.document_templates import get_template, detect_document_type
from app.core.enums import DocumentType, ExtractionStatus
from app.utils.exceptions import (
    DocExtractorException,
    UnsupportedDocumentTypeException,
    OCRExtractionException,
    LLMExtractionException,
)
from app.utils.logging import log_execution


class ExtractionService:
    """
    Orchestrates the full document extraction pipeline:
    1. Save uploaded file
    2. OCR → raw text
    3. Detect document type
    4. LLM → structured fields
    5. Persist results
    """

    def __init__(self, db: Session):
        self.repo = DocumentRepository(db)
        self.ocr = OCRService()
        self.llm = LLMService()
        self.file_svc = FileService()

    @log_execution
    def upload_and_extract(
        self,
        file_content: bytes,
        original_filename: str,
        doc_type_hint: Optional[str] = None,
    ) -> Document:
        """Full pipeline: upload → OCR → extract → store."""

        # 1. Save file
        saved_name, file_path, mime_type, file_size = self.file_svc.save_upload(
            file_content, original_filename
        )

        # 2. Create DB record
        doc = self.repo.create(
            filename=saved_name,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
        )

        try:
            # 3. Update status to processing
            self.repo.update_status(doc.id, ExtractionStatus.PROCESSING)
            self.repo.add_log(doc.id, "pipeline", "Extraction pipeline started")

            # 4. OCR
            logger.info(f"[Doc {doc.id}] Starting OCR on {original_filename}")
            raw_text, confidence = self.ocr.extract_text(file_path)
            self.repo.add_log(doc.id, "ocr", f"OCR completed, {len(raw_text)} chars, confidence={confidence:.2f}")

            # 5. Detect document type
            if doc_type_hint and doc_type_hint != "auto":
                doc_type = DocumentType(doc_type_hint)
            else:
                doc_type = detect_document_type(raw_text)
                if doc_type == DocumentType.UNKNOWN:
                    # Fallback to LLM classification
                    llm_type_str = self.llm.detect_document_type_with_llm(raw_text)
                    try:
                        doc_type = DocumentType(llm_type_str)
                    except ValueError:
                        doc_type = DocumentType.UNKNOWN

            self.repo.add_log(doc.id, "detection", f"Document type detected: {doc_type}")
            logger.info(f"[Doc {doc.id}] Detected type: {doc_type}")

            if doc_type == DocumentType.UNKNOWN:
                raise UnsupportedDocumentTypeException("Could not determine document type")

            # 6. Get template and extract fields via LLM
            template = get_template(doc_type)
            extracted_data = self.llm.extract_fields(raw_text, template)
            self.repo.add_log(doc.id, "llm", f"LLM extracted {len(extracted_data)} fields")

            # 7. Store results
            doc = self.repo.update_extraction(
                doc_id=doc.id,
                doc_type=doc_type,
                raw_ocr_text=raw_text,
                extracted_data=extracted_data,
                confidence_score=confidence,
            )
            self.repo.add_log(doc.id, "pipeline", "Extraction completed successfully")
            logger.info(f"[Doc {doc.id}] Extraction completed successfully")
            return doc

        except DocExtractorException as e:
            logger.error(f"[Doc {doc.id}] Extraction failed: {e.message}")
            self.repo.add_log(doc.id, "error", e.message, level="error")
            self.repo.update_status(doc.id, ExtractionStatus.FAILED, e.message)
            raise
        except Exception as e:
            logger.error(f"[Doc {doc.id}] Unexpected error: {e}")
            self.repo.add_log(doc.id, "error", str(e), level="error")
            self.repo.update_status(doc.id, ExtractionStatus.FAILED, str(e))
            raise

    @log_execution
    def get_document(self, doc_id: int) -> Document:
        return self.repo.get_by_id(doc_id)

    @log_execution
    def list_documents(self, skip: int = 0, limit: int = 50):
        return self.repo.list_all(skip=skip, limit=limit)

    @log_execution
    def delete_document(self, doc_id: int) -> bool:
        doc = self.repo.get_by_id(doc_id)
        self.file_svc.delete_file(doc.file_path)
        return self.repo.delete(doc_id)

    def get_extraction_logs(self, doc_id: int):
        return self.repo.get_logs(doc_id)

    def get_system_health(self) -> Dict[str, Any]:
        return {
            "ocr_available": self.ocr.is_available(),
            "llm_available": self.llm.is_available(),
            "groq_model": self.llm.model,
        }
