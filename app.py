from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()  

# Fetch Groq API key
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("No Groq API key found in .env file.")

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": "Tell me what you think will happen between chelsea and Napoli today."}
    ],
    temperature=0.7
)

print(response.choices[0].message.content)
