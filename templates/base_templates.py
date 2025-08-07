def get_base_template(html_content, css_content, js_content):
    """
    Apply a base template to the generated HTML content
    """
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generated Website</title>
        <style>
            {css_content}
        </style>
    </head>
    <body>
        {html_content}
        <script>
            {js_content}
        </script>
    </body>
    </html>
    """