import os
from openai import OpenAI

class GLMClient:
    """
    Client for interacting with GLM-4.5 model via Hugging Face
    """
    def __init__(self):
        # Get API key from environment variables
        api_key = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
        
        if not api_key:
            raise ValueError(
                "API key not found. Please set either HF_TOKEN or HUGGINGFACE_API_KEY "
                "environment variable with your Hugging Face API token."
            )
        
        # Initialize OpenAI client with Hugging Face router
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=api_key,
        )
        self.model = "zai-org/GLM-4.5:novita"
    
    def chat_completion(self, messages, temperature=1, max_tokens=20000):
        """
        Generate a chat completion using GLM-4.5
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error generating chat completion: {str(e)}")
    
    def generate_website_code(self, prompt, options):
        """
        Generate website code using GLM-4.5
        """
        system_prompt = """
        You are an expert web developer specializing in creating modern, responsive websites.
        Generate a complete website based on the user's description.
        
        Your response should include:
        1. Complete HTML code with semantic structure
        2. CSS code for styling (modern, responsive design)
        3. JavaScript code for interactivity (if needed)
        
        Format your response as:
        ```html
        [HTML code here]
        ```
        ```css
        [CSS code here]
        ```
        ```javascript
        [JavaScript code here]
        ```
        """
        
        # Add customization options to the prompt
        customization_text = f"""
        Customization requirements:
        - Color scheme: {options['color_scheme']}
        - Font family: {options['font_family']}
        - Layout style: {options['layout']}
        """
        
        # Combine user prompt with customization
        full_prompt = f"{prompt}\n\n{customization_text}"
        
        # Make API call
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
        
        response_text = self.chat_completion(messages)
        
        # Parse the response to extract HTML, CSS, and JavaScript
        html_code = ""
        css_code = ""
        js_code = ""
        
        # Split by code blocks
        parts = response_text.split("```")
        if len(parts) >= 6:
            html_code = parts[1].replace("html\n", "", 1)
            css_code = parts[3].replace("css\n", "", 1)
            js_code = parts[5].replace("javascript\n", "", 1)
        
        return html_code, css_code, js_code