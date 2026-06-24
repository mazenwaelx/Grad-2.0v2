"""
LLM initialization and management
"""
import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI


def init_llm(model_name: str):
    """Initialize the LLM with specified model and optimized settings"""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    # Try different model name formats (using available models)
    model_variants = [
        model_name,
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash-001",
        "models/gemini-flash-latest",
    ]
    
    for i, model_variant in enumerate(model_variants):
        try:
            print(f"[DEBUG] Trying model: {model_variant}")
            llm = ChatGoogleGenerativeAI(
                model=model_variant,
                google_api_key=api_key,
                temperature=0.1,
                max_tokens=4096,  # Reduced from 8192 to prevent repetition loops
                top_p=0.95,
                top_k=40,
                convert_system_message_to_human=True,
                max_retries=5,  # Increased from 3 to 5 - LangChain will handle retries with exponential backoff
            )
            
            # Test the model with a simple query
            test_response = llm.invoke("Test")
            print(f"[SUCCESS] Model {model_variant} works!")
            return llm
            
        except Exception as e:
            error_str = str(e)
            print(f"[ERROR] Model {model_variant} failed: {error_str[:100]}...")
            
            # If rate limited, wait before trying next model
            if "429" in error_str or "quota" in error_str.lower() or "resource" in error_str.lower():
                if i < len(model_variants) - 1:
                    print(f"[INFO] Rate limited, waiting 2 seconds before trying next model...")
                    time.sleep(2)  # Reduced from 5 to 2 seconds
            continue
    
    raise ValueError(f"All model variants failed. Please check your API key and model availability.")
