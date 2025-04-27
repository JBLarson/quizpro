# backend/gemini.py

import google.generativeai as genai
import os

# Configure the SDK with a default key from the environment (for legacy endpoints)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Expose the module itself as `client` so `from .gemini import client` continues to work
client = genai

def promptGemini(client_arg, prompt_text):
    """Send the prompt_text to Gemini and return its response content."""
    # Ignore client_arg (legacy); use the globally-configured genai
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt_text)
    return getattr(response, "text", response)

def requestMC(contentInput):
    """Builds a standard multiple-choice prompt based on input content."""
    standardPrompt = f"""I need you to act as if you are a professional tutor. Analyze the following input content.
    You're going to provide me with 30 multiple choice questions, BASED SOLELY on the provided input content.
    The format of each question should look like this
    1.  Which of the following factors does NOT heavily influence human perception, according to the presentation?
        *   (A) Past experience
        *   (B) Current context
        *   (C) Future goals
        *   (D) Innate preferences
        *   **(D)**
    The **()** denotes the correct answer. Questions MUST follow this template.
    """
    return standardPrompt
