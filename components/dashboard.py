# components/dashboard.py
import uuid
import streamlit as st
from data.projects import list_projects, create_project, get_project

def render_dashboard(user_email: str):
    st.header("Your Projects")

    # One-time creation guards
    st.session_state.setdefault("_create_nonce", None)
    st.session_state.setdefault("_create_pid", None)

    with st.expander(
        "Create new project",
        expanded=True if not st.session_state.get("current_project_id") else False
    ):
        with st.form("new_project_form", clear_on_submit=True):
            name = st.text_input("Project name", placeholder="e.g., My Photography Portfolio")
            prompt = st.text_area(
                "Initial prompt (optional)",
                height=100,
                placeholder="Describe what you want to build…"
            )
            submitted = st.form_submit_button("Create project")

        if submitted:
            if not name.strip():
                st.error("Please enter a project name.")
            else:
                # Create a stable nonce and project_id for this submit only
                if not st.session_state._create_nonce:
                    st.session_state._create_nonce = uuid.uuid4().hex
                if not st.session_state._create_pid:
                    st.session_state._create_pid = f"prj_{st.session_state._create_nonce[:10]}"

                idem = st.session_state._create_nonce
                pid = st.session_state._create_pid

                doc = create_project(
                    user_email,
                    name=name.strip(),
                    prompt=prompt,
                    options=st.session_state.get("customization_options", {}),
                    project_id=pid,
                    idempotency_key=idem,   # <-- backend enforces single row for this
                )

                st.session_state.current_project_id = doc["project_id"]
                st.success("Project created.")

                # Clear nonce so a future create is a new op
                st.session_state._create_nonce = None
                st.session_state._create_pid = None

                # No explicit st.rerun() needed; form submit already triggers a rerun.

    projs = list_projects(user_email)
    if not projs:
        st.info("No projects yet. Create one above.")
        return

    # Simple list with open buttons
    for p in projs:
        cols = st.columns([4, 2, 2, 2])
        cols[0].markdown(f"**{p['name']}**  \n`{p['project_id']}`")
        cols[1].write(p.get("status", "new"))
        ts = p.get("updated_at")
        cols[2].write(ts.strftime("%Y-%m-%d %H:%M") if ts else "")
        if cols[3].button("Open", key=f"open_{p['project_id']}"):
            st.session_state.current_project_id = p["project_id"]
            st.success(f"Opened {p['name']}")
            # No hard rerun here either; button click already reruns the app.

def load_project_into_state(user_email: str, project_id: str):
    from data.projects import get_project
    doc = get_project(user_email, project_id)
    if not doc:
        st.error("Project not found or you don't have access.")
        return None
    # Load into session
    st.session_state.generated_code = doc.get("code")
    st.session_state.preview_url = doc.get("preview_url")
    # Keep the latest prompt/options visible in the builder UI
    st.session_state.builder_prompt = doc.get("prompt", "")
    if doc.get("options"):
        st.session_state.customization_options = doc["options"]
    return doc
