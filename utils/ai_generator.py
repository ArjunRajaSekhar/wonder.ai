from utils.glm_client import GLMClient
from templates.base_templates import get_base_template

def generate_website(prompt, options):
    """
    Generate website code using GLM-4.5 based on user prompt and customization options
    """
    # Initialize GLM client
    glm_client = GLMClient()
    
    # Generate website code
    html_code, css_code, js_code = glm_client.generate_website_code(prompt, options)
    
    # Apply base template if needed
    html_code = get_base_template(html_code, css_code, js_code)
    
    return html_code, css_code, js_code