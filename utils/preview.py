import base64
import streamlit.components.v1 as components
import tempfile
import os

def create_preview(html_code, css_code, js_code):
    """
    Create a preview of the website
    """
    # Create a complete HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Website Preview</title>
        <style>
            {css_code}
        </style>
    </head>
    <body>
        {html_code}
        <script>
            {js_code}
        </script>
    </body>
    </html>
    """
    
    # Create a temporary file
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "preview.html")
    
    with open(file_path, "w") as f:
        f.write(full_html)
    
    return file_path
