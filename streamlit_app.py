import streamlit as st
import requests
import json
import os
from pathlib import Path

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(
    page_title="DocExtractor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E40AF;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748B;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-completed { background:#D1FAE5; color:#065F46; }
    .status-failed    { background:#FEE2E2; color:#991B1B; }
    .status-pending   { background:#FEF3C7; color:#92400E; }
    .status-processing{ background:#DBEAFE; color:#1E40AF; }
    .field-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
    }
    .confidence-bar {
        height: 6px;
        border-radius: 3px;
        background: #E2E8F0;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)


def api_get(endpoint: str):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=30)
        return r.json() if r.ok else None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def api_post_file(endpoint: str, file_bytes: bytes, filename: str, params: dict = None):
    try:
        r = requests.post(
            f"{API_BASE}{endpoint}",
            files={"file": (filename, file_bytes, "application/octet-stream")},
            params=params or {},
            timeout=120,
        )
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500


def api_delete(endpoint: str):
    try:
        r = requests.delete(f"{API_BASE}{endpoint}", timeout=10)
        return r.ok
    except:
        return False


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📄 DocExtractor")
    st.markdown("*Intelligent Document Extraction*")
    st.divider()

    page = st.radio(
        "Navigation",
        ["🚀 Upload & Extract", "📋 Document History", "🔍 Document Details", "❤️ Health Check"],
        label_visibility="collapsed",
    )

    st.divider()

    # Health status
    health = api_get("/health")
    if health:
        ocr_ok = health.get("ocr_available", False)
        llm_ok = health.get("llm_available", False)
        st.markdown(f"**OCR:** {'✅' if ocr_ok else '⚠️'} {'Ready' if ocr_ok else 'Not found'}")
        st.markdown(f"**LLM (Groq):** {'✅' if llm_ok else '❌'} {'Connected' if llm_ok else 'No API key'}")
        st.markdown(f"**Model:** `{health.get('groq_model', 'N/A')}`")
    else:
        st.warning("⚠️ API not reachable")

    st.divider()
    st.caption("Supported: Aadhaar • DL • Passport • Invoice")


# ── Page: Upload & Extract ─────────────────────────────────────────────────────
if "🚀 Upload & Extract" in page:
    st.markdown('<div class="main-header">📄 Upload Document</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload any Indian ID or invoice for automatic extraction</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=["jpg", "jpeg", "png", "pdf"],
            help="Supported: Aadhaar Card, Driving Licence, Passport, Invoice",
        )

    with col2:
        doc_type = st.selectbox(
            "Document Type",
            options=["auto", "aadhaar", "driving_licence", "passport", "invoice"],
            format_func=lambda x: {
                "auto": "🤖 Auto Detect",
                "aadhaar": "🪪 Aadhaar Card",
                "driving_licence": "🚗 Driving Licence",
                "passport": "📘 Passport",
                "invoice": "🧾 Invoice",
            }.get(x, x),
        )

    if uploaded_file:
        if uploaded_file.type.startswith("image"):
            st.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)
        else:
            st.info(f"📄 PDF: {uploaded_file.name}")

        if st.button("🔍 Extract Information", type="primary", use_container_width=True):
            with st.spinner("Processing document... (OCR + LLM extraction)"):
                file_bytes = uploaded_file.read()
                result, status_code = api_post_file(
                    "/documents/upload",
                    file_bytes,
                    uploaded_file.name,
                    {"doc_type": doc_type},
                )

            if status_code in (200, 201) and "id" in result:
                st.success(f"✅ Extraction complete! Document ID: **{result['id']}**")

                # Show results
                st.markdown("### 📊 Extracted Information")

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Document Type", result.get("doc_type", "N/A").replace("_", " ").title())
                col_b.metric("Status", result.get("status", "N/A").title())
                conf = result.get("confidence_score")
                col_c.metric("OCR Confidence", f"{conf*100:.1f}%" if conf else "N/A")

                if result.get("extracted_data"):
                    st.markdown("#### Extracted Fields")
                    data = result["extracted_data"]
                    cols = st.columns(2)
                    for i, (k, v) in enumerate(data.items()):
                        if not k.startswith("extra_"):
                            with cols[i % 2]:
                                st.markdown(f"""
                                <div class="field-card">
                                    <strong>{k.replace('_', ' ').title()}</strong><br>
                                    <span style="color:#1E40AF">{v or '—'}</span>
                                </div>""", unsafe_allow_html=True)

                if result.get("raw_ocr_text"):
                    with st.expander("📝 Raw OCR Text"):
                        st.text(result["raw_ocr_text"][:2000])

                st.session_state["last_doc_id"] = result["id"]

            else:
                # Detailed error handling
                if isinstance(result.get("detail"), dict):
                    err = result["detail"].get("error", str(result["detail"]))
                else:
                    err = result.get("detail", result.get("error", "Unknown error"))
                
                st.error(f"❌ Extraction failed: {err}")
                
                # Show debugging info
                with st.expander("🔍 Debug Information"):
                    st.json({"status_code": status_code, "response": result})


# ── Page: Document History ─────────────────────────────────────────────────────
elif "📋 Document History" in page:
    st.markdown('<div class="main-header">📋 Document History</div>', unsafe_allow_html=True)

    docs_resp = api_get("/documents?limit=50")

    if docs_resp and docs_resp.get("documents"):
        docs = docs_resp["documents"]
        st.info(f"Total documents: **{docs_resp['total']}**")

        for doc in docs:
            status = doc.get("status", "unknown")
            status_class = f"status-{status}"
            doc_type = doc.get("doc_type", "unknown").replace("_", " ").title()

            with st.expander(f"📄 [{doc['id']}] {doc['original_filename']} — {doc_type}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"**ID:** {doc['id']}")
                c2.markdown(f"**Type:** {doc_type}")
                c3.markdown(f"**Status:** `{status}`")
                c4.markdown(f"**Created:** {doc['created_at'][:10]}")

                if doc.get("extracted_data"):
                    st.json(doc["extracted_data"])

                col_view, col_del = st.columns([3, 1])
                if col_del.button("🗑️ Delete", key=f"del_{doc['id']}"):
                    if api_delete(f"/documents/{doc['id']}"):
                        st.success("Deleted!")
                        st.rerun()
    else:
        st.info("No documents yet. Upload one to get started!")


# ── Page: Document Details ─────────────────────────────────────────────────────
elif "🔍 Document Details" in page:
    st.markdown('<div class="main-header">🔍 Document Details</div>', unsafe_allow_html=True)

    default_id = st.session_state.get("last_doc_id", 1)
    doc_id = st.number_input("Enter Document ID", min_value=1, value=default_id, step=1)

    if st.button("🔎 Fetch Details", type="primary"):
        doc = api_get(f"/documents/{doc_id}")
        if doc:
            st.markdown(f"### Document #{doc_id}: {doc['original_filename']}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Type", doc.get("doc_type", "N/A").replace("_", " ").title())
            c2.metric("Status", doc.get("status", "N/A"))
            conf = doc.get("confidence_score")
            c3.metric("Confidence", f"{conf*100:.1f}%" if conf else "N/A")

            tab1, tab2, tab3 = st.tabs(["📊 Extracted Fields", "📝 OCR Text", "📜 Logs"])

            with tab1:
                if doc.get("extracted_data"):
                    for k, v in doc["extracted_data"].items():
                        st.markdown(f"""<div class="field-card">
                            <strong>{k.replace('_', ' ').title()}</strong>: {v or '—'}
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info("No extracted data available")

            with tab2:
                st.text_area("Raw OCR Text", doc.get("raw_ocr_text", ""), height=300)

            with tab3:
                logs = api_get(f"/documents/{doc_id}/logs")
                if logs:
                    for log in logs:
                        icon = {"info": "ℹ️", "error": "❌", "warning": "⚠️"}.get(log["level"], "•")
                        st.markdown(f"`{log['created_at'][11:19]}` {icon} **[{log['stage']}]** {log['message']}")
                else:
                    st.info("No logs available")
        else:
            st.error(f"Document {doc_id} not found")


# ── Page: Health Check ─────────────────────────────────────────────────────────
elif "❤️ Health Check" in page:
    st.markdown('<div class="main-header">❤️ System Health</div>', unsafe_allow_html=True)

    health = api_get("/health")
    if health:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("API Status", "✅ Online")
            st.metric("App Version", health.get("version", "N/A"))
            st.metric("OCR Engine", "✅ Ready" if health.get("ocr_available") else "❌ Not available")
        with col2:
            st.metric("LLM Service", "✅ Connected" if health.get("llm_available") else "❌ No API key")
            st.metric("Model", health.get("groq_model", "N/A"))
            st.metric("App Name", health.get("app_name", "N/A"))

        st.markdown("### API Configuration")
        st.code(f"API Base URL: {API_BASE}", language="text")
        st.markdown("### Supported Document Types")
        st.markdown("""
        | Type | Description | Key Fields |
        |------|-------------|------------|
        | **Aadhaar** | Indian UID card | Name, UID Number, DOB, Gender, Address |
        | **Driving Licence** | RTO issued DL | Licence No, Name, DOB, Expiry, Vehicle Classes |
        | **Passport** | Indian passport | Passport No, Name, DOB, Expiry, MRZ |
        | **Invoice** | GST/Tax Invoice | Invoice No, Seller, Buyer, GSTIN, Total Amount |
        """)
    else:
        st.error("❌ Cannot reach API. Make sure the FastAPI server is running.")
        st.code(f"Run: uvicorn main:app --reload --port 8000", language="bash")
