from google import genai
from dotenv import load_dotenv
import os

load_dotenv()  

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Give me a brief overview of a project I can build in 3 days."
)

print(response.text)
