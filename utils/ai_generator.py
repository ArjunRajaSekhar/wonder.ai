import streamlit as st
from utils.glm_client import GLMClient
from templates.base_templates import get_base_template

log = st.container()
out = st.container()

MAX_TEXT = 4000  # keep logs small

def _truncate_text(s: str, n: int = MAX_TEXT) -> str:
    if not isinstance(s, str):
        try:
            s = json.dumps(s, ensure_ascii=False)
        except Exception:
            s = str(s)
    return (s[:n] + " …[truncated]") if len(s) > n else s

def ui_hook(event: dict):
    try:
        stage = event.get("stage", "stage").upper()
        summary = event.get("summary", {})
        images = event.get("images", [])

        with st.expander(f"🔹 {stage}", expanded=True):
            # Render a compact summary only
            if summary:
                # stringify + truncate to avoid crashing st.json
                st.text(_truncate_text(summary, 2000))
            # Render at most 2 images (thumbnails)
            for img in (images or [])[:2]:
                url = img.get("url")
                if url:
                    st.image(url, caption=img.get("alt", ""), use_column_width=True)
    except Exception as e:
        # Never let the log view crash the app
        st.caption(f"(log render error hidden: {e})")

def generate_website(prompt, options):
    """
    Generate website code using GLM-4.5 (agentic).
    """
    glm_client = GLMClient()

    # merge UI options with thread_id for LangGraph checkpointer continuity
    merged_options = {
        **(options or {}),
        "thread_id": st.session_state.thread_id,
    }

    result = glm_client.generate_website_code_agentic(
        prompt=prompt,
        options=merged_options,
        generate_images=True,
        ui_hook=ui_hook,
    )

    code = result.get("modified_code") or result.get("code") or {"html": "", "css": "", "js": ""}
    html_code, css_code, js_code = code["html"], code["css"], code["js"]

    # Apply base template wrapper
    html_code = get_base_template(html_code, css_code, js_code)

    return html_code, css_code, js_code
