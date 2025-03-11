import os
import json
import time
import logging
import httpx
from typing import Dict, Any, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Load configuration from environment variables
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
HTTPS_PROXY = os.getenv('HTTPS_PROXY')

def create_openai_client():
    """
    Create and configure an Azure OpenAI client.
    
    Returns:
        AzureOpenAI: Configured client or None if configuration is invalid
    """
    # Check for Azure OpenAI credentials
    if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME]):
        logger.error("Missing Azure OpenAI credentials - check environment variables")
        return None
    
    # Create HTTP client with proxy if configured
    http_client = None
    if HTTPS_PROXY:
        logger.info(f"Using proxy: {HTTPS_PROXY}")
        http_client = httpx.Client(
            transport=httpx.HTTPTransport(
                proxy=httpx.Proxy(url=HTTPS_PROXY)
            ),
            verify=False
        )
    
    # Initialize OpenAI client
    try:
        logger.info(f"Initializing Azure OpenAI client with endpoint: {AZURE_OPENAI_ENDPOINT}")
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            http_client=http_client
        )
        return client
    except Exception as e:
        logger.error(f"Error initializing Azure OpenAI client: {str(e)}")
        return None

def get_completion_with_retries(
    text: str, 
    system_prompt: str, 
    max_retries: int = 3, 
    retry_delay: int = 60,
    temperature: float = 0,
    response_format: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Call Azure OpenAI with retry logic.
    
    Args:
        text: The text to send to the model
        system_prompt: Instructions for the model
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds
        temperature: Model temperature setting
        response_format: Optional format for the response
        
    Returns:
        Dict containing the response or error information
    """
    client = create_openai_client()
    if not client:
        return {"error": "Azure OpenAI credentials not configured"}
    
    # Using exponential backoff for retries
    for attempt in range(max_retries):
        try:
            logger.info(f"API call attempt {attempt+1}/{max_retries}")
            
            request_params = {
                "model": AZURE_OPENAI_DEPLOYMENT_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": temperature
            }
            
            if response_format:
                request_params["response_format"] = response_format
            
            start_time = time.time()
            response = client.chat.completions.create(**request_params)
            end_time = time.time()
            
            # Parse the response
            response_text = response.choices[0].message.content
            
            try:
                # If response is JSON, parse it
                if response_format and response_format.get("type") == "json_object":
                    result = json.loads(response_text)
                else:
                    result = {"content": response_text}
                
                # Add processing time metadata
                result["processing_time"] = f"{end_time - start_time:.2f} seconds"
                
                logger.info("API call completed successfully")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {e}")
                return {
                    "error": "Failed to parse JSON response",
                    "raw_content": response_text
                }
                
        except Exception as api_error:
            logger.error(f"Error in API call (attempt {attempt+1}): {str(api_error)}")
            if attempt < max_retries - 1:
                backoff_time = retry_delay * (2 ** attempt)
                logger.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)  # Exponential backoff
    
    logger.error(f"All {max_retries} API call attempts failed")
    return {"error": "Failed after multiple attempts"}