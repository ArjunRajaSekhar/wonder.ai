import streamlit as st
from streamlit_extras.switch_page_button import switch_page

def render_sidebar():
    """
    Render the sidebar with navigation and information
    """
    # Hide default navigation
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            .nav-button {
                width: 100%;
                margin-bottom: 5px;
            }
            .nav-button.active {
                background-color: #ff4b4b;
                color: white;
            }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if "page" not in st.session_state:
            st.session_state.page = "gallery"
        st.title("AI Website Builder")
        st.markdown("---")
        
        # Navigation
        st.subheader("Navigation")
        
        # Navigation selectbox
        nav_option = st.selectbox(
            "Choose a page:",
            ["🏠 Home", "🖼️ Gallery", "ℹ️ About"],
            key="nav_select"
        )
        
        # Handle navigation based on selection
        if nav_option == "🖼️ Gallery":
            st.session_state.page = "pages/gallery"
        elif nav_option == "ℹ️ About":
            st.session_state.page = "pages/about"
        # Home is the default page, so no need to switch

        st.markdown("---")
        
        # Information
        st.subheader("How it works")
        st.markdown("""
        1. Describe your website
        2. Click "Generate Website"
        3. Customize as needed
        4. Export your website
        """)
        
        st.markdown("---")
        
        # Tips
        st.subheader("Tips for better results")
        st.markdown("""
        - Be specific about your needs
        - Mention color preferences
        - Describe the layout you want
        - Include any specific features
        """)