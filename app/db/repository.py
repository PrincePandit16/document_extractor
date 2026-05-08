from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import Document, ExtractionLog
from app.core.enums import DocumentType, ExtractionStatus
from app.utils.exceptions import DocumentNotFoundException, DatabaseException
from app.utils.logging import log_execution
from loguru import logger


class DocumentRepository:
    """Repository pattern for Document CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    @log_execution
    def create(self, filename: str, original_filename: str, file_path: str,
               file_size: int, mime_type: str) -> Document:
        try:
            doc = Document(
                filename=filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                status=ExtractionStatus.PENDING,
            )
            self.db.add(doc)
            self.db.commit()
            self.db.refresh(doc)
            logger.info(f"Created document record id={doc.id}")
            return doc
        except Exception as e:
            self.db.rollback()
            raise DatabaseException(str(e))

    @log_execution
    def get_by_id(self, doc_id: int) -> Document:
        doc = self.db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise DocumentNotFoundException(doc_id)
        return doc

    @log_execution
    def list_all(self, skip: int = 0, limit: int = 50) -> List[Document]:
        return self.db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    @log_execution
    def update_status(self, doc_id: int, status: ExtractionStatus,
                      error_message: str = None) -> Document:
        doc = self.get_by_id(doc_id)
        doc.status = status
        if error_message:
            doc.error_message = error_message
        self.db.commit()
        self.db.refresh(doc)
        return doc

    @log_execution
    def update_extraction(self, doc_id: int, doc_type: DocumentType,
                          raw_ocr_text: str, extracted_data: Dict[str, Any],
                          confidence_score: float = None) -> Document:
        doc = self.get_by_id(doc_id)
        doc.doc_type = doc_type
        doc.raw_ocr_text = raw_ocr_text
        doc.extracted_data = extracted_data
        doc.confidence_score = confidence_score
        doc.status = ExtractionStatus.COMPLETED
        self.db.commit()
        self.db.refresh(doc)
        return doc

    @log_execution
    def delete(self, doc_id: int) -> bool:
        doc = self.get_by_id(doc_id)
        self.db.delete(doc)
        self.db.commit()
        logger.info(f"Deleted document id={doc_id}")
        return True

    def add_log(self, document_id: int, stage: str, message: str,
                level: str = "info", metadata: Dict = None):
        log_entry = ExtractionLog(
            document_id=document_id,
            stage=stage,
            message=message,
            level=level,
            metadata_=metadata or {},
        )
        self.db.add(log_entry)
        self.db.commit()

    def get_logs(self, document_id: int) -> List[ExtractionLog]:
        return self.db.query(ExtractionLog)\
            .filter(ExtractionLog.document_id == document_id)\
            .order_by(ExtractionLog.created_at)\
            .all()
