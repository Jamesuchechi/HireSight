"""
Utility functions for Gemini API with full fallback support.
Updated to use new google.genai SDK (not deprecated google.generativeai).
Now includes Mistral as a primary option with Gemini as a fallback.
"""
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Use NEW SDK (not deprecated google.generativeai)
try:
    from google import genai
    from google.genai import types
except ImportError as e:
    genai = None
    types = None
    logger.warning(f"Could not import google.genai: {e}. Install with: pip install google-genai")

# Import Mistral SDK
try:
    from mistralai import Mistral
except ImportError:
    Mistral = None
    logger.warning("mistralai package not installed. Run: pip install mistralai")


def generate_with_full_fallback(prompt, json_mode=True):
    """
    Iterates through all API keys, and for each key, tries all models
    until a successful response is received.
    
    Updated to use new google.genai SDK instead of deprecated google.generativeai.
    
    Args:
        prompt (str): The prompt to send to Gemini
        json_mode (bool): Whether to request a JSON response format from Gemini.
        
    Returns:
        str: The generated response text, or error message if all keys fail
    """
    if genai is None:
        error_msg = "Error: google.genai SDK not installed. Run: pip install google-genai"
        logger.error(error_msg)
        return error_msg
    
    if not hasattr(settings, 'GEMINI_KEYS') or not settings.GEMINI_KEYS:
        error_msg = "Error: No Gemini API keys configured in settings"
        logger.error(error_msg)
        return error_msg
    
    errors = []
    
    for api_key in settings.GEMINI_KEYS:
        if not api_key:
            continue
        
        key_identifier = api_key[:8] + "..." if len(api_key) > 8 else api_key
        
        try:
            # NEW SDK: Create client with API key
            client = genai.Client(api_key=api_key)
        except Exception as client_err:
            error_msg = f"Failed to create client with key {key_identifier}: {client_err}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue
        
        # Try each model with this key
        models = getattr(settings, 'GEMINI_MODELS', ['gemini-2.0-flash-exp'])
        for model_name in models:
            try:
                config = {'temperature': 0.7}
                if json_mode:
                    config['response_mime_type'] = 'application/json'

                # NEW SDK: Use client.models.generate_content
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                
                # Success! Return the text immediately
                logger.info(f"Successfully generated content using {model_name} with key {key_identifier}")
                return response.text
                
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Check for specific error types
                if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg or 'quota' in error_msg.lower():
                    # Quota hit for this specific Key + Model combo
                    log_msg = f"Quota exhausted for {model_name} on key {key_identifier}"
                    logger.warning(log_msg)
                    errors.append(log_msg)
                    continue
                
                elif '400' in error_msg or 'INVALID_ARGUMENT' in error_msg or 'not found' in error_msg.lower():
                    # Model not found or invalid argument
                    log_msg = f"Model {model_name} not found or invalid argument (key {key_identifier})"
                    logger.warning(log_msg)
                    errors.append(log_msg)
                    continue
                
                else:
                    # Catch-all for network issues or other API errors
                    log_msg = f"Error with {model_name} on key {key_identifier}: {error_type}: {error_msg}"
                    logger.error(log_msg)
                    errors.append(log_msg)
                    break  # Move to the next API key
    
    # All keys and models have failed
    detailed_error = "Error: All Gemini API keys and models exhausted their quota or failed.\n" + "\n".join(errors)
    logger.error(detailed_error)
    return detailed_error


def generate_text_with_fallback(prompt, json_mode=False):
    """
    Attempts to generate text using the primary AI (Mistral), and falls back
    to the secondary AI (Gemini) on failure. This is the recommended function
    for simple text generation.

    Args:
        prompt (str): The prompt to send to the AI.
        json_mode (bool): Whether to request a JSON response format (primarily for Gemini).

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
            logger.warning(f"Mistral generation failed. Falling back to Gemini. Error: {e}")

    # 2. Fallback to Secondary AI: Gemini
    logger.warning("Falling back to secondary AI (Gemini)...")
    return generate_with_full_fallback(prompt, json_mode=json_mode)


def generate_with_gemini(prompt, temperature=0.7, max_tokens=None, json_mode=True):
    """
    Simplified Gemini generation using first available key.
    
    Args:
        prompt (str): The prompt to send
        temperature (float): Temperature for generation (0.0-1.0)
        max_tokens (int, optional): Max tokens to generate
        json_mode (bool): Whether to request JSON response format
        
    Returns:
        str: Generated text or error message
    """
    if genai is None:
        return "Error: google.genai SDK not installed"
    
    if not hasattr(settings, 'GEMINI_KEYS') or not settings.GEMINI_KEYS:
        return "Error: No Gemini API keys configured"
    
    try:
        client = genai.Client(api_key=settings.GEMINI_KEYS[0])
        
        config = {
            'temperature': temperature,
        }
        
        if json_mode:
            config['response_mime_type'] = 'application/json'
        
        if max_tokens:
            config['max_output_tokens'] = max_tokens
        
        # Use first available model
        model_name = getattr(settings, 'GEMINI_MODELS', ['gemini-2.0-flash-exp'])[0]
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        
        return response.text
        
    except Exception as e:
        error_msg = f"Error generating with Gemini: {e}"
        logger.error(error_msg)
        return f"Error: {str(e)}"


# Backward compatibility aliases (in case other code imports these)
def generate_content(prompt):
    """Backward compatibility wrapper."""
    return generate_text_with_fallback(prompt)


def generate_json(prompt):
    """Generate JSON response with Gemini."""
    return generate_text_with_fallback(prompt, json_mode=True)