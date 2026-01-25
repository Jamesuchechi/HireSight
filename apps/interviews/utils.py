import google.generativeai as genai
from django.conf import settings
from google.api_core import exceptions
import logging

logger = logging.getLogger(__name__)

def generate_with_full_fallback(prompt):
    """
    Iterates through all API keys, and for each key, tries all models
    until a successful response is received.
    
    Returns:
        str: The generated response text, or error message if all keys fail
    """
    if not settings.GEMINI_KEYS:
        error_msg = "Error: No Gemini API keys configured in settings"
        logger.error(error_msg)
        return error_msg
    
    errors = []
    
    for api_key in settings.GEMINI_KEYS:
        if not api_key:
            continue
            
        # Configure the SDK with the current key in the loop
        genai.configure(api_key=api_key)
        key_identifier = api_key[:8] + "..." if len(api_key) > 8 else api_key
        
        for model_name in settings.GEMINI_MODELS:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                
                # Success! Return the text immediately
                logger.info(f"Successfully generated content using {model_name} with key {key_identifier}")
                return response.text
                
            except exceptions.ResourceExhausted as e:
                # Quota hit for this specific Key + Model combo
                error_msg = f"Quota exhausted for {model_name} on key {key_identifier}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue 
                
            except exceptions.InvalidArgument as e:
                # Useful if you have a typo in your model name
                error_msg = f"Model {model_name} not found or invalid argument"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
                
            except Exception as e:
                # Catch-all for network issues or other API errors
                error_msg = f"Error with {model_name} on key {key_identifier}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                break  # Move to the next API key
    
    # All keys and models have failed
    detailed_error = "Error: All Gemini API keys and models exhausted their quota or failed.\n" + "\n".join(errors)
    logger.error(detailed_error)
    return detailed_error