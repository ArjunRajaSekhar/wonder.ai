import streamlit as st
import os
import uuid
from dotenv import load_dotenv

from utils.ai_generator import generate_website
from utils.preview import create_preview
from utils.export import export_website
from components.sidebar import render_sidebar
from components.preview_panel import render_preview
from components.customization import render_customization

# Auth UI
from components.login import render_auth, render_user_menu

# NEW: dashboard + persistence
from components.dashboard import render_dashboard, load_project_into_state
from data.projects import save_generation, get_project, update_project

load_dotenv(dotenv_path=".env.example")

# Page configuration
st.set_page_config(
    page_title="AI Website Builder",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session defaults
st.session_state.setdefault("generated_code", None)
st.session_state.setdefault("preview_url", None)
st.session_state.setdefault("customization_options", {
    "color_scheme": "default",
    "font_family": "Arial",
    "layout": "modern"
})
st.session_state.setdefault("user", None)
st.session_state.setdefault("thread_id", f"thread-{uuid.uuid4().hex[:8]}")
st.session_state.setdefault("current_project_id", None)
st.session_state.setdefault("builder_prompt", "")

def main():
    # Sidebar (account + your existing sidebar)
    render_user_menu()   # shows signed-in user + Sign out button (no-op if not signed in)
    render_sidebar()

    # Require login
    if not st.session_state.user:
        st.title("AI Website Builder")
        st.info("Please sign in to access your dashboard and projects.")
        render_auth()    # renders Sign In / Create Account tabs (Mongo)
        return

    # Top-level navigation
    tabs = st.tabs(["🏠 Dashboard", "🛠️ Builder"])
    user_email = st.session_state.user["email"]

    # DASHBOARD
    with tabs[0]:
        render_dashboard(user_email)
        # Quick open-in-builder if a project is already selected
        if st.session_state.get("current_project_id"):
            proj = get_project(user_email, st.session_state.current_project_id)
            if proj:
                st.success(f"Current project: {proj['name']} ({proj['project_id']})")
                if st.button("Open in Builder"):
                    st.session_state.current_project_id = proj["project_id"]
                    st.session_state.nav_choice = "Builder"
                    try:
                        st.rerun()
                    except AttributeError:
                        st.experimental_rerun()
                    return

    # BUILDER
    with tabs[1]:
        # Must have a selected project
        if not st.session_state.get("current_project_id"):
            st.warning("No project selected. Go to the Dashboard to create or open a project.")
            return

        # Load the selected project's latest state into the UI/session
        doc = load_project_into_state(user_email, st.session_state.current_project_id)
        if not doc:
            return

        st.title(f"Builder — {doc['name']}")
        st.caption(f"Project ID: `{doc['project_id']}`")

        # Prompt (persisted with project)
        user_prompt = st.text_area(
            "Describe your website:",
            height=150,
            value=st.session_state.get("builder_prompt", doc.get("prompt", "")),
            placeholder="E.g., A portfolio website for a photographer with a dark theme and gallery...",
            help="Describe the website you want to create in detail",
            key="builder_prompt_area"
        )

        c1, c2 = st.columns([1, 1])
        generate_button = c1.button("Generate Website", type="primary", use_container_width=True)
        back_to_dash = c2.button("Back to Dashboard", use_container_width=True)

        if back_to_dash:
            # Switch tab by clearing selection; dashboard will show list
            st.session_state.current_project_id = st.session_state.current_project_id
            st.experimental_rerun()

        # Handle generation
        if generate_button and user_prompt:
            with st.spinner("Generating your website..."):
                try:
                    html_code, css_code, js_code = generate_website(
                        prompt=user_prompt,
                        options=st.session_state.customization_options
                    )

                    code = {"html": html_code, "css": css_code, "js": js_code}
                    preview_url = create_preview(html_code, css_code, js_code)

                    # Put in session
                    st.session_state.generated_code = code
                    st.session_state.preview_url = preview_url
                    st.session_state.builder_prompt = user_prompt

                    # Persist to DB
                    save_generation(
                        user_email=user_email,
                        project_id=st.session_state.current_project_id,
                        prompt=user_prompt,
                        options=st.session_state.customization_options,
                        code=code,
                        preview_url=preview_url
                    )
                    st.success("Website generated and saved to your project!")
                except Exception as e:
                    st.error(f"Error generating website: {str(e)}")
                    st.info("Please try again with a different description or check your API key.")

        # Preview & customization
        if st.session_state.generated_code:
            preview_col, custom_col = st.columns([3, 1])
            with preview_col:
                render_preview(st.session_state.preview_url)
            with custom_col:
                render_customization()

            st.subheader("Export Your Website")
            export_format = st.selectbox("Export format", ["HTML Files", "React Project", "Vue Project"])
            if st.button("Export Website", type="secondary"):
                with st.spinner("Preparing export..."):
                    export_data = export_website(st.session_state.generated_code, format=export_format)
                    st.download_button(
                        label="Download Website",
                        data=export_data,
                        file_name=f"website_{uuid.uuid4().hex[:8]}.zip",
                        mime="application/zip"
                    )
                    update_project(user_email, st.session_state.current_project_id, {"status": "exported"})

if __name__ == "__main__":
    main()
