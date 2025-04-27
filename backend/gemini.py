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

# prompt for requesting multiple choice questions
def requestMC(contentInput):
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