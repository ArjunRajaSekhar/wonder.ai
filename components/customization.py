import streamlit as st

def render_customization():
    """
    Render customization options for the generated website
    """
    st.subheader("Customize Website")
    
    # Color scheme
    color_scheme = st.selectbox(
        "Color Scheme",
        ["default", "dark", "light", "colorful", "minimal"],
        index=["default", "dark", "light", "colorful", "minimal"].index(
            st.session_state.customization_options['color_scheme']
        )
    )
    st.session_state.customization_options['color_scheme'] = color_scheme
    
    # Font family
    font_family = st.selectbox(
        "Font Family",
        ["Arial", "Times New Roman", "Courier New", "Georgia", "Verdana"],
        index=["Arial", "Times New Roman", "Courier New", "Georgia", "Verdana"].index(
            st.session_state.customization_options['font_family']
        )
    )
    st.session_state.customization_options['font_family'] = font_family
    
    # Layout style
    layout = st.selectbox(
        "Layout Style",
        ["modern", "classic", "minimal", "grid", "sidebar"],
        index=["modern", "classic", "minimal", "grid", "sidebar"].index(
            st.session_state.customization_options['layout']
        )
    )
    st.session_state.customization_options['layout'] = layout
    
    # Apply customization button
    if st.button("Apply Customization", type="secondary"):
        if st.session_state.generated_code:
            # Regenerate with new options
            from utils.ai_generator import generate_website
            from utils.preview import create_preview
            
            with st.spinner("Applying customization..."):
                # Extract the original prompt from the generated code
                # In a real implementation, we would store the original prompt
                original_prompt = "A website with updated customization"
                
                # Regenerate
                html_code, css_code, js_code = generate_website(
                    prompt=original_prompt,
                    options=st.session_state.customization_options
                )
                
                # Update session state
                st.session_state.generated_code = {
                    'html': html_code,
                    'css': css_code,
                    'js': js_code
                }
                
                # Update preview
                st.session_state.preview_url = create_preview(html_code, css_code, js_code)
                st.success("Customization applied!")
                # st.experimental_rerun()