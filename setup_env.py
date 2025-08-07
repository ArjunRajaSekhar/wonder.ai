#!/usr/bin/env python3
"""
Setup script for Wonder.ai environment configuration
"""
import os
import sys

def check_environment():
    """Check if required environment variables are set"""
    hf_token = os.environ.get("HF_TOKEN")
    huggingface_api_key = os.environ.get("HUGGINGFACE_API_KEY")
    
    print("🔍 Checking environment variables...")
    
    if hf_token:
        print("✅ HF_TOKEN is set")
        return True
    elif huggingface_api_key:
        print("✅ HUGGINGFACE_API_KEY is set")
        return True
    else:
        print("❌ No API key found")
        print("\nTo fix this, you need to:")
        print("1. Get a Hugging Face API token from https://huggingface.co/settings/tokens")
        print("2. Set one of these environment variables:")
        print("   - HF_TOKEN")
        print("   - HUGGINGFACE_API_KEY")
        print("\nYou can set it temporarily with:")
        print("export HF_TOKEN='your_token_here'")
        print("export HUGGINGFACE_API_KEY='your_token_here'")
        print("\nOr add it to your shell profile (.bashrc, .zshrc, etc.)")
        return False

def test_glm_client():
    """Test the GLM client connection"""
    try:
        from utils.glm_client import GLMClient
        print("\n🧪 Testing GLM client...")
        
        client = GLMClient()
        print("✅ GLM client initialized successfully")
        
        # Test with a simple prompt
        test_messages = [
            {"role": "user", "content": "Hello, can you respond with 'Test successful'?"}
        ]
        
        response = client.chat_completion(test_messages, temperature=0.1, max_tokens=50)
        print(f"✅ Test response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ GLM client test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Wonder.ai Environment Setup")
    print("=" * 40)
    
    if check_environment():
        if test_glm_client():
            print("\n🎉 Setup complete! Your environment is ready.")
            print("You can now run your Wonder.ai application.")
        else:
            print("\n❌ Setup failed. Please check your API token and try again.")
            sys.exit(1)
    else:
        print("\n❌ Setup incomplete. Please set the required environment variables.")
        sys.exit(1) 