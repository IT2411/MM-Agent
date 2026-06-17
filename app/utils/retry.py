import asyncio
import logging

logger = logging.getLogger("agent.robustness")

async def execute_with_retry(func, *args, **kwargs):
    """
    Executes an async Gemini API call with exponential backoff retries 
    if a 429 Rate Limit/Resource Exhausted exception occurs.
    """
    max_retries = 3
    delay = 3.0  # Initial wait delay in seconds
    
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_message = str(e)
            
            # Identify if the exception is due to a rate limit (429 / RESOURCE_EXHAUSTED)
            if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Rate limit encountered. Retrying in {delay}s "
                        f"(Attempt {attempt + 1}/{max_retries})..."
                    )
                    await asyncio.sleep(delay)
                    delay *= 2.0  # Double the wait time (exponential backoff)
                    continue
            
            # Re-raise the exception if retries are exhausted or it is a different error
            raise e