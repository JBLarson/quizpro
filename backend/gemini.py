# backend/gemini.py
# Wrapper module for Google Gemini Generative AI SDK to support quiz generation in QuizPro.

import google.generativeai as genai
import os

# ------------------------------------------------------------------------------
# Configure the Google Gemini SDK:
# - Reads the GEMINI_API_KEY environment variable (set via .env)
# - Allows subsequent API calls to use this key for authentication.
# ------------------------------------------------------------------------------
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Expose the configured genai client as `client` for legacy imports and direct use.
client = genai

# ------------------------------------------------------------------------------
# Function: promptGemini
# Purpose: Send a text prompt to the Google Gemini model and return the generated text.
# Inputs:
#   - client_arg: (ignored) legacy parameter retained for compatibility
#   - prompt_text: the prompt string to send to the model
# Process:
#   - Instantiate a new GenerativeModel using the 'gemini-2.0-flash' endpoint
#   - Call generate_content() with the prompt_text
#   - Extract and return the 'text' attribute of the response
# Outputs:
#   - Generated text response from the Gemini model
# ------------------------------------------------------------------------------
def promptGemini(client_arg, prompt_text):
    # Create a Gemini model instance (flash version for low-latency responses)
    model = genai.GenerativeModel("gemini-2.0-flash")
    # Request content generation based on the prompt
    response = model.generate_content(prompt_text)
    # Return the text content, or fallback to raw response if missing
    return getattr(response, "text", response)

# ------------------------------------------------------------------------------
# Function: requestMC
# Purpose: Build a standard multiple-choice question prompt template for Gemini.
# Inputs:
#   - contentInput: raw content (e.g., slide text) to base MCQs on
# Outputs:
#   - A formatted prompt string that instructs Gemini to generate 30 MCQs
# ------------------------------------------------------------------------------
def requestMC(contentInput):
    # Define a consistent MCQ template to ensure uniform output format.
    standardPrompt = f"""I need you to act as if you are a professional tutor. """
    # The template instructs the model to generate multiple-choice questions only
    standardPrompt += f"Analyze the following input content:\n{contentInput}\n"  
    standardPrompt += (
        "You're going to provide me with 30 multiple choice questions, BASED SOLELY "
        "on the provided input content. The format of each question should look "
        "like this:\n1. Which factor does NOT influence human perception? (A) X (B) Y (C) Z (D) W**"
    )
    return standardPrompt
