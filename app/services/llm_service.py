import json
import re
from typing import Dict, Any, Optional
from groq import Groq
from loguru import logger
from config.settings import settings
from app.utils.exceptions import LLMExtractionException
from app.utils.logging import log_execution
from app.templates.document_templates import DocumentTemplate


class LLMService:
    """LLM service using Groq for intelligent field extraction."""

    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not set — LLM extraction will fail")
            self.client = None
        else:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        logger.info(f"LLM Service initialized with model: {self.model}")

    @log_execution
    def extract_fields(self, ocr_text: str, template: DocumentTemplate) -> Dict[str, Any]:
        """
        Use Groq LLM to extract structured fields from OCR text using template.
        """
        if not self.client:
            raise LLMExtractionException("Groq API key not configured")

        if not ocr_text or len(ocr_text.strip()) < 10:
            raise LLMExtractionException("OCR text is too short for extraction")

        prompt = self._build_prompt(ocr_text, template)

        try:
            logger.debug(f"Sending extraction request to Groq for {template.doc_type}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert document data extraction AI. "
                            "Extract structured information from OCR text accurately. "
                            "Always respond with valid JSON only — no markdown, no explanation."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1500,
                temperature=0.1,
            )

            raw_response = response.choices[0].message.content.strip()
            logger.debug(f"LLM raw response: {raw_response[:300]}")

            extracted = self._parse_json_response(raw_response)
            validated = self._validate_and_clean(extracted, template)

            logger.info(f"LLM extracted {len(validated)} fields for {template.doc_type}")
            return validated

        except LLMExtractionException:
            raise
        except Exception as e:
            raise LLMExtractionException(str(e))

    def _build_prompt(self, ocr_text: str, template: DocumentTemplate) -> str:
        extraction_prompt = template.to_extraction_prompt()
        return f"""{extraction_prompt}

--- OCR TEXT START ---
{ocr_text[:4000]}
--- OCR TEXT END ---

JSON output:"""

    def _parse_json_response(self, raw: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling common formatting issues."""
        # Strip markdown code blocks
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        raw = raw.strip("`").strip()

        # Find JSON object
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            raw = match.group(0)

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}\nRaw: {raw[:500]}")
            raise LLMExtractionException(f"Invalid JSON from LLM: {e}")

    def _validate_and_clean(self, data: Dict[str, Any],
                             template: DocumentTemplate) -> Dict[str, Any]:
        """Validate extracted data against template fields."""
        result = {}
        expected_fields = {f.name for f in template.fields}

        for field in template.fields:
            value = data.get(field.name)
            if value in (None, "", "null", "N/A", "n/a", "NA"):
                result[field.name] = None
            else:
                result[field.name] = str(value).strip() if value else None

        # Include any extra fields LLM returned
        for k, v in data.items():
            if k not in expected_fields:
                result[f"extra_{k}"] = v

        return result

    @log_execution
    def detect_document_type_with_llm(self, ocr_text: str) -> str:
        """Use LLM to classify document type when keyword matching fails."""
        if not self.client:
            return "unknown"

        prompt = f"""Classify this document into one of these types:
- aadhaar (Indian Aadhaar Card)
- driving_licence (Indian Driving Licence)
- passport (Indian Passport)
- invoice (Business Invoice)
- unknown

OCR Text (first 500 chars):
{ocr_text[:500]}

Reply with ONLY the document type (one word, lowercase, use underscore)."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0.0,
            )
            doc_type = response.choices[0].message.content.strip().lower()
            valid = {"aadhaar", "driving_licence", "passport", "invoice", "unknown"}
            return doc_type if doc_type in valid else "unknown"
        except Exception as e:
            logger.warning(f"LLM doc type detection failed: {e}")
            return "unknown"

    def is_available(self) -> bool:
        return self.client is not None
