from google import genai
from parser_pptx_json import getJSON

client = genai.Client(api_key="AIzaSyB4Ie0Q-MM3PTtc4WhI1yVEsfIsyeOAbGY")
json = getJSON()

def promptGemini(client, json):
    json = getJSON()
    response = client.models.generate_content(model="gemini-2.0-flash", contents="Give me a Summary of the meaningful text in this JSON file:" + json)

    return response

