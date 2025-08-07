import streamlit as st
import streamlit.components.v1 as components
import os

def render_preview(preview_url):
    """
    Render the website preview in Streamlit
    """
    if preview_url:
        with open(preview_url, 'r') as f:
            html_content = f.read()
        
        # Use components.html to render the preview
        components.html(html_content, height=600,width=800, scrolling=True)
    else:
        st.info("Generate a website to see the preview here")