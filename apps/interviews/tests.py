"""
Quick test script to verify AI connectors are working.
Run this from Django shell or as a standalone script.
"""
import os
import sys
from pathlib import Path

# Add Django project to path if running standalone
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiresight.settings')
import django
django.setup()

from django.conf import settings
import json

print("=" * 80)
print("TESTING AI CONNECTORS")
print("=" * 80)

# Test 1: Check Gemini configuration
print("\n1. CHECKING GEMINI CONFIGURATION")
print("-" * 40)
try:
    from google import genai
    print("✓ google.genai import successful")
    
    if hasattr(settings, 'GEMINI_KEYS') and settings.GEMINI_KEYS:
        print(f"✓ Found {len(settings.GEMINI_KEYS)} Gemini API key(s)")
        
        # Test connection
        client = genai.Client(api_key=settings.GEMINI_KEYS[0])
        print("✓ Gemini client initialized successfully")
        
        # Try a simple generation
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents='Say "Hello, I am working!" in JSON format: {"message": "your message here"}',
            config={'response_mime_type': 'application/json'}
        )
        print(f"✓ Gemini test response: {response.text[:100]}...")
        
    else:
        print("✗ No GEMINI_KEYS found in settings")
        
except ImportError as e:
    print(f"✗ Could not import google.genai: {e}")
    print("  Install with: pip install google-genai")
except Exception as e:
    print(f"✗ Gemini test failed: {e}")

# Test 2: Check Mistral configuration
print("\n2. CHECKING MISTRAL CONFIGURATION")
print("-" * 40)
try:
    import requests
    
    mistral_key = getattr(settings, 'MISTRAL_AI_API_KEY', '')
    if mistral_key:
        print("✓ Mistral API key found")
        
        # Test connection with correct endpoint
        url = "https://api.mistral.ai/v1/chat/completions"
        payload = {
            'model': 'mistral-small-latest',
            'messages': [
                {'role': 'user', 'content': 'Say "Hello!" in JSON: {"message": "your message"}'}
            ],
            'max_tokens': 100
        }
        headers = {
            'Authorization': f'Bearer {mistral_key}',
            'Content-Type': 'application/json'
        }
        
        print(f"  Testing endpoint: {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']['content']
            print(f"✓ Mistral test response: {message[:100]}...")
        else:
            print(f"✗ Mistral returned status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
    else:
        print("✗ No MISTRAL_AI_API_KEY found in settings")
        
except Exception as e:
    print(f"✗ Mistral test failed: {e}")

# Test 3: Test AIConnector class
print("\n3. TESTING AICONNECTOR CLASS")
print("-" * 40)
try:
    from apps.interviews.ai_connector import AIConnector, PromptBuilder
    
    connector = AIConnector()
    print("✓ AIConnector initialized")
    
    # Create a mock session object
    class MockSession:
        id = 999
        interview_type = 'PHONE'
        difficulty = 'Medium'
        focus_area = 'Technical'
        application = None
        
        def __init__(self):
            self.settings = {
                'number_of_questions': 3,
                'focus_areas': ['Python', 'Django']
            }
        
        @property
        def number_of_questions(self):
            return 3
    
    mock_session = MockSession()
    print("✓ Mock session created")
    
    # Test prompt building
    prompt = connector._build_context_prompt(mock_session)
    print(f"✓ Generated prompt ({len(prompt)} chars)")
    print(f"  Preview: {prompt[:150]}...")
    
    print("\n✓ ALL BASIC TESTS PASSED")
    print("\nYou can now test actual question generation in Django shell:")
    print("  from apps.interviews.models import InterviewPracticeSession")
    print("  from apps.interviews.ai_connector import AIConnector")
    print("  session = InterviewPracticeSession.objects.first()")
    print("  connector = AIConnector()")
    print("  questions, raw, model = connector.generate_questions(session)")
    
except Exception as e:
    print(f"✗ AIConnector test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)