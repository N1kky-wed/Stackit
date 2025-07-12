import os
import json
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


api_key = os.environ.get("GEMINI_API_KEY")


if not api_key:
    logging.error("GEMINI_API_KEY not found in environment variables. Please create a .env file and add it.")


client = genai.Client(api_key=api_key)

def generate_ai_answer(question_title, question_description):
    """
    Generate an AI answer for a question using Gemini 2.5 Flash
    """
    try:
        prompt = f"""You are Stellar, an AI assistant helping users on a Q&A forum called StackIt.
Please provide a helpful, accurate, and detailed answer to the following question.

Question Title: {question_title}
Question Description: {question_description}

Please provide a comprehensive answer that:
1. Directly addresses the question
2. Provides clear explanations
3. Includes practical examples when appropriate
4. Uses proper formatting with markdown
5. Is professional and helpful in tone

Keep your response focused and relevant to the question asked."""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text or "I apologize, but I'm unable to generate a response at the moment."
    
    except Exception as e:
        logging.error(f"Error generating AI answer: {e}")
        return """I apologize, but I'm currently unable to generate a response due to a technical issue. 
Please try mentioning me again later, or feel free to ask the community for help!

Error: AI service temporarily unavailable."""

def check_stellar_mention(text):
    """
    Check if @Stellar is mentioned in the text
    """
    import re
    # Strip HTML tags for checking mentions
    clean_text = re.sub(r'<[^>]+>', '', text)
    return "@Stellar" in clean_text or "@stellar" in clean_text.lower()
