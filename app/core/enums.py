from enum import Enum


class DocumentType(str, Enum):
    AADHAAR = "aadhaar"
    DRIVING_LICENCE = "driving_licence"
    PASSPORT = "passport"
    INVOICE = "invoice"
    UNKNOWN = "unknown"


class ExtractionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OCREngine(str, Enum):
    TESSERACT = "tesseract"
    PADDLEOCR = "paddleocr"


DOCUMENT_TYPE_LABELS = {
    DocumentType.AADHAAR: "Aadhaar Card",
    DocumentType.DRIVING_LICENCE: "Driving Licence",
    DocumentType.PASSPORT: "Passport",
    DocumentType.INVOICE: "Invoice",
    DocumentType.UNKNOWN: "Unknown",
}
