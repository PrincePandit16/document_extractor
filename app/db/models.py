from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SAEnum, Float
from sqlalchemy.orm import declarative_base
from app.core.enums import DocumentType, ExtractionStatus

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))

    doc_type = Column(SAEnum(DocumentType), nullable=False, default=DocumentType.UNKNOWN)
    status = Column(SAEnum(ExtractionStatus), nullable=False, default=ExtractionStatus.PENDING)

    raw_ocr_text = Column(Text)
    extracted_data = Column(JSON)
    confidence_score = Column(Float)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Document id={self.id} type={self.doc_type} status={self.status}>"


class ExtractionLog(Base):
    __tablename__ = "extraction_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False)
    stage = Column(String(50))  # ocr, llm, validation
    message = Column(Text)
    level = Column(String(20), default="info")
    metadata_ = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
