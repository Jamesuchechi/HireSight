from google import genai
from dotenv import load_dotenv
import os

load_dotenv()  

# Fetch them individually
primary = os.getenv("GEMINI_API_KEY_PRIMARY")
secondary = os.getenv("GEMINI_API_KEY_SECONDARY")

# Use primary if it exists, otherwise use secondary
api_key = primary or secondary

if not api_key:
    raise ValueError("No Gemini API keys found in .env file.")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Tell me what you think will happen between chelsea and Napoli today."
)

print(response.text)
