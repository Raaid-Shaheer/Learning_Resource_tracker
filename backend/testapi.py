import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load your .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print(f"API Key found: {'Yes' if api_key else 'No'}")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'System Online' if you can hear me.")
        print(f"Response from AI: {response.text}")
    except Exception as e:
        print(f"Error: {e}")