import os
from pathlib import Path
from typing import Tuple
from PIL import Image
import pytesseract
from loguru import logger
from config.settings import settings
from app.utils.exceptions import OCRExtractionException
from app.utils.logging import log_execution


class OCRService:
    """OCR service using Tesseract for text extraction from images."""

    def __init__(self):
        if settings.TESSERACT_CMD and os.path.exists(settings.TESSERACT_CMD):
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        logger.info(f"OCR Service initialized with engine: {settings.OCR_ENGINE}")

    @log_execution
    def extract_text(self, file_path: str) -> Tuple[str, float]:
        """
        Extract text from image file.
        Returns (text, confidence_score).
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise OCRExtractionException(f"File not found: {file_path}")

            ext = path.suffix.lower()
            if ext == ".pdf":
                text, confidence = self._extract_from_pdf(file_path)
            else:
                text, confidence = self._extract_from_image(file_path)

            logger.info(f"OCR extracted {len(text)} chars from {path.name}, confidence={confidence:.2f}")
            return text, confidence

        except OCRExtractionException:
            raise
        except Exception as e:
            raise OCRExtractionException(str(e))

    def _extract_from_image(self, file_path: str) -> Tuple[str, float]:
        """Extract text from image file."""
        img = Image.open(file_path)
        img = self._preprocess_image(img)

        # Get text with confidence data
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT,
                                          lang="eng+hin", config="--psm 3")
        
        # Calculate average confidence (filter out -1 values)
        confidences = [int(c) for c in data["conf"] if int(c) > 0]
        avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.0

        text = pytesseract.image_to_string(img, lang="eng+hin", config="--psm 3")
        return text.strip(), avg_confidence

    def _extract_from_pdf(self, file_path: str) -> Tuple[str, float]:
        """Extract text from PDF by converting pages to images."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            all_text = []
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img_path = f"/tmp/_page_{page.number}.png"
                pix.save(img_path)
                text, _ = self._extract_from_image(img_path)
                all_text.append(text)
                os.remove(img_path)
            return "\n\n".join(all_text), 0.75
        except ImportError:
            # Fallback: try direct text extraction
            logger.warning("PyMuPDF not available, falling back to direct PDF text")
            return self._pdf_direct_text(file_path)

    def _pdf_direct_text(self, file_path: str) -> Tuple[str, float]:
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            return text.strip(), 0.85
        except Exception as e:
            raise OCRExtractionException(f"PDF text extraction failed: {e}")

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """Basic image preprocessing to improve OCR accuracy."""
        # Convert to RGB if needed
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        
        # Upscale small images
        w, h = img.size
        if w < 800:
            scale = 800 / w
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        return img

    def is_available(self) -> bool:
        """Check if Tesseract is properly installed."""
        try:
            version = pytesseract.get_tesseract_version()
            logger.debug(f"Tesseract version: {version}")
            return True
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
            return False
