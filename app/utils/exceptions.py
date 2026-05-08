class DocExtractorException(Exception):
    """Base exception for DocExtractor."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class DocumentNotFoundException(DocExtractorException):
    def __init__(self, doc_id: int):
        super().__init__(f"Document with ID {doc_id} not found", "DOC_NOT_FOUND")


class UnsupportedDocumentTypeException(DocExtractorException):
    def __init__(self, doc_type: str):
        super().__init__(f"Unsupported document type: {doc_type}", "UNSUPPORTED_TYPE")


class OCRExtractionException(DocExtractorException):
    def __init__(self, detail: str):
        super().__init__(f"OCR extraction failed: {detail}", "OCR_FAILED")


class LLMExtractionException(DocExtractorException):
    def __init__(self, detail: str):
        super().__init__(f"LLM extraction failed: {detail}", "LLM_FAILED")


class FileValidationException(DocExtractorException):
    def __init__(self, detail: str):
        super().__init__(f"File validation failed: {detail}", "FILE_INVALID")


class DatabaseException(DocExtractorException):
    def __init__(self, detail: str):
        super().__init__(f"Database operation failed: {detail}", "DB_ERROR")


class TemplateNotFoundException(DocExtractorException):
    def __init__(self, template_name: str):
        super().__init__(f"Template not found: {template_name}", "TEMPLATE_NOT_FOUND")
