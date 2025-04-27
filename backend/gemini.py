import genai
"""Module to send prompts to Gemini LLM; no import-time execution or JSON parsing here."""

client = genai.Client(api_key="AIzaSyB4Ie0Q-MM3PTtc4WhI1yVEsfIsyeOAbGY")

def promptGemini(client, prompt_text):
    """Send the prompt_text to Gemini and return its response content."""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt_text
    )
    return getattr(response, 'text', response)

