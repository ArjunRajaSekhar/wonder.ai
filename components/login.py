# components/login.py
import streamlit as st
from auth.db import authenticate, create_user, get_user_by_email

def render_auth():
    st.markdown("### Sign in to continue")

    tabs = st.tabs(["Sign In", "Create Account"])

    with tabs[0]:
        with st.form("signin_form", clear_on_submit=False):
            email = st.text_input("Email", key="signin_email")
            password = st.text_input("Password", type="password", key="signin_password")
            submitted = st.form_submit_button("Sign In")
            if submitted:
                if not email or not password:
                    st.error("Please enter your email and password.")
                else:
                    user = authenticate(email, password)
                    if user:
                        st.session_state.user = {
                            "id": str(user["_id"]),
                            "email": user["email"],
                            "name": user.get("full_name") or user["email"].split("@")[0],
                            "role": user.get("role", "user"),
                        }
                        st.success(f"Welcome back, {st.session_state.user['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")

    with tabs[1]:
        with st.form("signup_form", clear_on_submit=True):
            full_name = st.text_input("Full name (optional)", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
            submitted = st.form_submit_button("Create Account")
            if submitted:
                if not email or not password:
                    st.error("Email and password are required.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                elif get_user_by_email(email):
                    st.error("An account with that email already exists.")
                else:
                    user = create_user(email, password, full_name)
                    st.session_state.user = {
                        "id": str(user["_id"]),
                        "email": user["email"],
                        "name": user.get("full_name") or user["email"].split("@")[0],
                        "role": user.get("role", "user"),
                    }
                    st.success("Account created. You’re signed in!")
                    st.rerun()

def render_user_menu():
    user = st.session_state.get("user")
    if not user:
        return
    with st.sidebar.expander("Account", expanded=True):
        st.write(f"**Signed in as:** {user['name']} ({user['email']})")
        if st.button("Sign out"):
            for k in ["user", "generated_code", "preview_url"]:
                st.session_state.pop(k, None)
            st.success("Signed out.")
            st.rerun()
