import streamlit as st
import os
import uuid
from utils.ai_generator import generate_website
from utils.preview import create_preview
from utils.export import export_website
from components.sidebar import render_sidebar
from components.preview_panel import render_preview
from components.customization import render_customization
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.example")
# print(os.getenv("HF_TOKEN"))

# Page configuration
st.set_page_config(
    page_title="AI Website Builder",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'generated_code' not in st.session_state:
    st.session_state.generated_code = None
if 'preview_url' not in st.session_state:
    st.session_state.preview_url = None
if 'customization_options' not in st.session_state:
    st.session_state.customization_options = {
        'color_scheme': 'default',
        'font_family': 'Arial',
        'layout': 'modern'
    }

def main():
    # Render sidebar
    render_sidebar()
    
    # Main content area
    st.title("AI Website Builder")
    st.markdown("Create stunning websites with AI assistance")
    
    # Prompt input
    user_prompt = st.text_area(
        "Describe your website:",
        height=150,
        placeholder="E.g., A portfolio website for a photographer with a dark theme and gallery...",
        help="Describe the website you want to create in detail"
    )
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("Generate Website", type="primary", use_container_width=True)
    
    # Handle generation
    if generate_button and user_prompt:
        with st.spinner("Generating your website..."):
            try:
                # Generate website code
                html_code, css_code, js_code = generate_website(
                    prompt=user_prompt,
                    options=st.session_state.customization_options
                )
                
                # Store generated code
                st.session_state.generated_code = {
                    'html': html_code,
                    'css': css_code,
                    'js': js_code
                }
                
                # Create preview
                st.session_state.preview_url = create_preview(html_code, css_code, js_code)
                st.success("Website generated successfully!")
            except Exception as e:
                st.error(f"Error generating website: {str(e)}")
                st.info("Please try again with a different description or check your API key.")
    
    # Display preview and customization if code is generated
    if st.session_state.generated_code:
        # Create two columns for preview and customization
        preview_col, custom_col = st.columns([3, 1])
        
        with preview_col:
            render_preview(st.session_state.preview_url)
        
        with custom_col:
            render_customization()
    
    # Export section
    if st.session_state.generated_code:
        st.subheader("Export Your Website")
        export_format = st.selectbox("Export format", ["HTML Files", "React Project", "Vue Project"])
        
        if st.button("Export Website", type="secondary"):
            with st.spinner("Preparing export..."):
                export_data = export_website(
                    st.session_state.generated_code,
                    format=export_format
                )
                st.download_button(
                    label="Download Website",
                    data=export_data,
                    file_name=f"website_{uuid.uuid4().hex[:8]}.zip",
                    mime="application/zip"
                )

if __name__ == "__main__":
    main()