"""
Utility functions for AI integration with Mistral and Groq fallback.
Mistral is the primary AI provider, with Groq as the fallback.
"""
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Import Mistral SDK (primary)
try:
    from mistralai import Mistral
except ImportError:
    Mistral = None
    logger.warning("mistralai package not installed. Run: pip install mistralai")

# Import Groq SDK (fallback)
try:
    from groq import Groq
except ImportError:
    Groq = None
    logger.warning("groq package not installed. Run: pip install groq")


def generate_text_with_fallback(prompt, json_mode=False):
    """
    Attempts to generate text using the primary AI (Mistral), and falls back
    to the secondary AI (Groq) on failure. This is the recommended function
    for simple text generation.

    Args:
        prompt (str): The prompt to send to the AI.
        json_mode (bool): Whether to request a JSON response format.

    Returns:
        str: The generated response text, or an error message if all fallbacks fail.
    """
    # 1. Attempt Primary AI: Mistral
    mistral_key = getattr(settings, 'MISTRAL_AI_API_KEY', '')
    mistral_model = getattr(settings, 'MISTRAL_AI_MODEL', 'mistral-small-latest')

    if Mistral and mistral_key:
        logger.info("Attempting text generation with primary AI (Mistral)...")
        try:
            client = Mistral(api_key=mistral_key)
            messages = [{"role": "user", "content": prompt}]

            response = client.chat.complete(
                model=mistral_model,
                messages=messages,
                temperature=0.7,
            )

            content = response.choices[0].message.content
            if content:
                logger.info("Successfully generated text with Mistral.")
                return content.strip()
        except Exception as e:
            logger.warning(f"Mistral generation failed. Falling back to Groq. Error: {e}")

    # 2. Fallback to Secondary AI: Groq
    logger.warning("Falling back to secondary AI (Groq)...")
    groq_key = getattr(settings, 'GROQ_API_KEY', '')
    groq_model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
    
    if not Groq or not groq_key:
        error_msg = "Error: Both Mistral and Groq AI are unavailable. No API keys configured."
        logger.error(error_msg)
        return error_msg
    
    try:
        client = Groq(api_key=groq_key)
        
        response_format = {"type": "json_object"} if json_mode else None
        
        response = client.chat.completions.create(
            model=groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format=response_format
        )
        
        content = response.choices[0].message.content
        if content:
            logger.info("Successfully generated text with Groq.")
            return content.strip()
    except Exception as e:
        error_msg = f"Error: Both Mistral and Groq generation failed. Groq error: {e}"
        logger.error(error_msg)
        return error_msg


# Backward compatibility aliases (in case other code imports these)
def generate_content(prompt):
    """Backward compatibility wrapper."""
    return generate_text_with_fallback(prompt)


def generate_json(prompt):
    """Generate JSON response with AI (Mistral/Groq fallback)."""
    return generate_text_with_fallback(prompt, json_mode=True)