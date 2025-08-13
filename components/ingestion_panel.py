# components/ingestion_panel.py
import os, json, io, base64
import streamlit as st

from data.projects import get_project, update_project
from data.documents import upsert_document, list_documents
from utils.ingestion import extract_text_from_pdf, extract_text_from_image, sniff_filetype
from utils.vector_store import ProjectVectorStore
from utils.glm_client import GLMClient

def render_ingestion_panel(user_email: str, project_id: str):
    st.subheader("📎 Documents & Knowledge Base")

    # Load current prompt from project
    proj = get_project(user_email, project_id)
    init_prompt = proj.get("prompt", "") if proj else ""

    with st.expander("Initial thinking prompt (used when parsing docs)", expanded=True):
        new_prompt = st.text_area("Prompt", value=init_prompt, height=140, placeholder="e.g., You're a web app architect... Focus on extracting requirements, entities, and UI hints.")
        if st.button("Save Prompt", key="save_proj_prompt"):
            update_project(user_email, project_id, {"prompt": new_prompt})
            st.success("Saved project prompt.")

    st.markdown("---")
    st.write("Upload PDFs or images. We'll parse them and add to your project's FAISS vector DB.")
    files = st.file_uploader("Upload files", type=["pdf", "png", "jpg", "jpeg", "webp"], accept_multiple_files=True)

    if st.button("Process & Index", type="primary") and files:
        glm = GLMClient()
        store = ProjectVectorStore.for_project(project_id)
        processed = 0

        for f in files:
            fbytes = f.read()
            ftype = sniff_filetype(f.name)
            text = ""
            if ftype == "pdf":
                text = extract_text_from_pdf(fbytes)
            elif ftype == "image":
                text = extract_text_from_image(fbytes)
                if not text:
                    # As a fallback, pass a note; user can re-run with OCR installed
                    text = "[Image uploaded; install easyocr to OCR locally, or enable multimodal LLM to interpret directly.]"

            # Always add raw text to vector store (chunked lightly)
            chunks = _chunk_text(text, 1000, 200) if text else ["(no text extracted)"]
            metas = [{"type": "doc", "file": f.name, "pos": i} for i, _ in enumerate(chunks)]
            store.add_texts(chunks, metas)

            # Ask LLM for a compact analysis using the project's initial prompt
            analysis = glm.analyze_text(new_prompt or init_prompt, text[:6000] if text else f"(Image file: {f.name})")
            upsert_document(user_email, project_id, doc_id=f.name, meta={
                "file": f.name,
                "analysis": analysis,
                "size": len(fbytes),
                "kind": ftype,
            })
            processed += 1

        st.success(f"Processed and indexed {processed} file(s).")

    # Show existing docs
    docs = list_documents(user_email, project_id)
    if docs:
        st.markdown("**Indexed documents:**")
        for d in docs:
            st.markdown("---")
            st.write(f"**{d.get('file','(unknown)')}** — {d.get('kind','')} • {d.get('size',0)} bytes")
            st.code(d.get("analysis", ""), language="json")


def _chunk_text(text: str, size: int, overlap: int):
    text = text or ""
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0:
            start = 0
        if start >= len(text):
            break
    return chunks
