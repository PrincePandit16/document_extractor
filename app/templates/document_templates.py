from dataclasses import dataclass, field
from typing import List, Dict, Any
from app.core.enums import DocumentType


@dataclass
class FieldConfig:
    """Configuration for a single extractable field."""
    name: str
    description: str
    required: bool = True
    field_type: str = "string"  # string, date, number
    aliases: List[str] = field(default_factory=list)


@dataclass
class DocumentTemplate:
    """Template defining what to extract from a document type."""
    doc_type: DocumentType
    display_name: str
    description: str
    fields: List[FieldConfig]
    keywords: List[str]  # Keywords to detect this doc type
    llm_hints: str = ""  # Extra hints for LLM

    def get_field_names(self) -> List[str]:
        return [f.name for f in self.fields]

    def to_extraction_prompt(self) -> str:
        field_list = "\n".join(
            f"- {f.name} ({f.field_type}): {f.description}"
            + (" [REQUIRED]" if f.required else " [OPTIONAL]")
            for f in self.fields
        )
        return f"""Extract the following fields from this {self.display_name}:
{field_list}

{self.llm_hints}

Return ONLY a valid JSON object with these exact field names as keys. 
Use null for missing/unclear fields. No explanations, just JSON."""


# ── Template Definitions ──────────────────────────────────────────────────────

AADHAAR_TEMPLATE = DocumentTemplate(
    doc_type=DocumentType.AADHAAR,
    display_name="Aadhaar Card",
    description="Indian government-issued identity document",
    keywords=["aadhaar", "uid", "unique identification", "uidai", "government of india", "आधार"],
    fields=[
        FieldConfig("name", "Full name of the card holder", required=True),
        FieldConfig("aadhaar_number", "12-digit Aadhaar number (format: XXXX XXXX XXXX)", required=True),
        FieldConfig("dob", "Date of birth (DD/MM/YYYY)", required=True, field_type="date"),
        FieldConfig("gender", "Gender (Male/Female/Other)", required=True),
        FieldConfig("address", "Full residential address", required=False),
        FieldConfig("pincode", "6-digit PIN code", required=False),
        FieldConfig("mobile_last4", "Last 4 digits of registered mobile", required=False),
        FieldConfig("vid", "Virtual ID (16 digits) if present", required=False),
    ],
    llm_hints="Aadhaar numbers are 12 digits often shown as XXXX XXXX XXXX. The DOB may be shown as 'Year of Birth' only (YYYY). Address includes state and PIN code.",
)

DRIVING_LICENCE_TEMPLATE = DocumentTemplate(
    doc_type=DocumentType.DRIVING_LICENCE,
    display_name="Driving Licence",
    description="Indian driving licence issued by RTO",
    keywords=["driving licence", "dl no", "driving license", "motor vehicles", "rto", "transport"],
    fields=[
        FieldConfig("licence_number", "Driving licence number (e.g., MH01 20230012345)", required=True),
        FieldConfig("name", "Full name of the licence holder", required=True),
        FieldConfig("dob", "Date of birth (DD/MM/YYYY)", required=True, field_type="date"),
        FieldConfig("issue_date", "Date of issue (DD/MM/YYYY)", required=True, field_type="date"),
        FieldConfig("expiry_date", "Date of expiry (DD/MM/YYYY)", required=True, field_type="date"),
        FieldConfig("address", "Residential address", required=False),
        FieldConfig("vehicle_classes", "Authorised vehicle classes (e.g., LMV, MCWG)", required=False),
        FieldConfig("issuing_rto", "Issuing RTO authority", required=False),
        FieldConfig("father_husband_name", "Father's or husband's name", required=False),
        FieldConfig("blood_group", "Blood group", required=False),
    ],
    llm_hints="Licence numbers in India follow state code + RTO code + year + serial format. Vehicle classes like LMV (Light Motor Vehicle), MCWG (Motorcycle With Gear).",
)

PASSPORT_TEMPLATE = DocumentTemplate(
    doc_type=DocumentType.PASSPORT,
    display_name="Passport",
    description="Indian passport issued by Ministry of External Affairs",
    keywords=["passport", "republic of india", "ministry of external affairs", "passport no", "nationality"],
    fields=[
        FieldConfig("passport_number", "Passport number (e.g., A1234567)", required=True),
        FieldConfig("surname", "Surname/Last name", required=True),
        FieldConfig("given_names", "Given names / First and middle name", required=True),
        FieldConfig("nationality", "Nationality", required=True),
        FieldConfig("dob", "Date of birth (DD/MM/YYYY)", required=True, field_type="date"),
        FieldConfig("gender", "Gender (M/F)", required=True),
        FieldConfig("place_of_birth", "Place of birth", required=False),
        FieldConfig("issue_date", "Date of issue (DD/MM/YYYY)", required=True, field_type="date"),
        FieldConfig("expiry_date", "Date of expiry (DD/MM/YYYY)", required=True, field_type="date"),
        FieldConfig("issuing_authority", "Issuing authority / place", required=False),
        FieldConfig("mrz_line1", "First line of Machine Readable Zone", required=False),
        FieldConfig("mrz_line2", "Second line of Machine Readable Zone", required=False),
        FieldConfig("file_number", "File number", required=False),
    ],
    llm_hints="Indian passports have a dark blue cover. Passport numbers start with a letter followed by 7 digits. MRZ lines are at the bottom of the photo page.",
)

INVOICE_TEMPLATE = DocumentTemplate(
    doc_type=DocumentType.INVOICE,
    display_name="Invoice",
    description="Business invoice / tax invoice",
    keywords=["invoice", "bill", "tax invoice", "gst", "gstin", "total amount", "payment due"],
    fields=[
        FieldConfig("invoice_number", "Invoice/Bill number", required=True),
        FieldConfig("invoice_date", "Invoice date (DD/MM/YYYY)", required=True, field_type="date"),
        FieldConfig("seller_name", "Seller / vendor company name", required=True),
        FieldConfig("seller_gstin", "Seller GSTIN (15-character GST number)", required=False),
        FieldConfig("buyer_name", "Buyer / customer name or company", required=True),
        FieldConfig("buyer_gstin", "Buyer GSTIN if present", required=False),
        FieldConfig("subtotal", "Subtotal before taxes", required=False, field_type="number"),
        FieldConfig("cgst_amount", "CGST amount", required=False, field_type="number"),
        FieldConfig("sgst_amount", "SGST amount", required=False, field_type="number"),
        FieldConfig("igst_amount", "IGST amount", required=False, field_type="number"),
        FieldConfig("total_amount", "Total payable amount including taxes", required=True, field_type="number"),
        FieldConfig("currency", "Currency (default INR)", required=False),
        FieldConfig("due_date", "Payment due date if mentioned", required=False, field_type="date"),
        FieldConfig("line_items", "List of items/services billed (brief)", required=False),
    ],
    llm_hints="Indian invoices include GSTIN. Amounts may use Indian number formatting (lakhs, crores). Extract numeric values without currency symbols.",
)

# Registry of all templates
TEMPLATE_REGISTRY: Dict[str, DocumentTemplate] = {
    DocumentType.AADHAAR: AADHAAR_TEMPLATE,
    DocumentType.DRIVING_LICENCE: DRIVING_LICENCE_TEMPLATE,
    DocumentType.PASSPORT: PASSPORT_TEMPLATE,
    DocumentType.INVOICE: INVOICE_TEMPLATE,
}


def get_template(doc_type: DocumentType) -> DocumentTemplate:
    """Retrieve template by document type."""
    template = TEMPLATE_REGISTRY.get(doc_type)
    if not template:
        from app.utils.exceptions import TemplateNotFoundException
        raise TemplateNotFoundException(doc_type)
    return template


def detect_document_type(text: str) -> DocumentType:
    """Detect document type from OCR text using keyword matching."""
    text_lower = text.lower()
    scores: Dict[DocumentType, int] = {}

    for doc_type, template in TEMPLATE_REGISTRY.items():
        score = sum(1 for kw in template.keywords if kw.lower() in text_lower)
        if score > 0:
            scores[doc_type] = score

    if not scores:
        return DocumentType.UNKNOWN

    return max(scores, key=scores.get)
