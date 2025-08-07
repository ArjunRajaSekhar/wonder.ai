# Wonder.ai Setup Guide

## Prerequisites

1. Python 3.8 or higher
2. A Hugging Face account with API access

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Environment Configuration

### Step 1: Get Your Hugging Face API Token

1. Go to [Hugging Face Settings](https://huggingface.co/settings/tokens)
2. Create a new token with appropriate permissions
3. Copy the token (you'll need it for the next step)

### Step 2: Set Environment Variables

You have several options to set the environment variable:

#### Option A: Temporary (for current session only)
```bash
export HF_TOKEN='your_huggingface_token_here'
```

#### Option B: Permanent (add to shell profile)
Add this line to your `~/.bashrc`, `~/.zshrc`, or equivalent:
```bash
export HF_TOKEN='your_huggingface_token_here'
```

Then reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

#### Option C: Using a .env file (recommended for development)
Create a `.env` file in the project root:
```bash
echo "HF_TOKEN=your_huggingface_token_here" > .env
```

### Step 3: Verify Setup

Run the setup verification script:
```bash
python setup_env.py
```

This will check if your environment is properly configured and test the GLM client connection.

## Running the Application

Once your environment is set up, you can run the application:

```bash
python app.py
```

## Troubleshooting

### Error: "API key not found"
- Make sure you've set the `HF_TOKEN` environment variable
- Verify the token is valid and has the correct permissions
- Try running `python setup_env.py` to test the configuration

### Error: "The api_key client option must be set"
- This error occurs when the OpenAI client can't find the API key
- Ensure you're using `HF_TOKEN` or `HUGGINGFACE_API_KEY` (not `OPENAI_API_KEY`)
- Check that the environment variable is properly set with `echo $HF_TOKEN`

### Error: "Error generating chat completion"
- Check your internet connection
- Verify your Hugging Face token has access to the GLM-4.5 model
- Ensure you have sufficient API credits/quota

## Alternative Environment Variables

The application supports these environment variable names:
- `HF_TOKEN` (preferred)
- `HUGGINGFACE_API_KEY` (alternative)

## Security Notes

- Never commit your API token to version control
- Use environment variables instead of hardcoding tokens
- Consider using a `.env` file for local development (add it to `.gitignore`) 