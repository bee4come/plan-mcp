"""Gemini API client for interacting with Google's Generative AI."""

import json
from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..config import get_config
from ..utils.logger import logger

T = TypeVar('T', bound=BaseModel)


class GeminiClient:
    """Client for interacting with the Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini client."""
        config = get_config()
        config.validate_config()
        
        genai.configure(api_key=config.gemini_api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            config.gemini_model,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        logger.info(f"Gemini client initialized with model: {config.gemini_model}")
    
    async def generate_content(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate content using Gemini.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt to prepend
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text content
        """
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            logger.debug(f"Generating content with prompt length: {len(full_prompt)}")
            
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )
            
            result = response.text
            logger.debug(f"Generated response length: {len(result)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            raise RuntimeError(f"Gemini API error: {str(e)}") from e
    
    async def generate_json(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> T:
        """Generate JSON content that conforms to a Pydantic model.
        
        Args:
            prompt: The user prompt
            response_model: Pydantic model class for response validation
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_retries: Number of retries for JSON parsing
            
        Returns:
            Instance of response_model with generated content
        """
        # Add JSON instruction to system prompt
        json_instruction = f"""
You must respond with valid JSON that conforms to this schema:
{response_model.model_json_schema()}

Important: Return ONLY the JSON object, no markdown formatting, no explanations.
"""
        
        full_system_prompt = f"{system_prompt or ''}\n\n{json_instruction}".strip()
        
        for attempt in range(max_retries):
            try:
                response = await self.generate_content(
                    prompt=prompt,
                    system_prompt=full_system_prompt,
                    temperature=temperature,
                )
                
                # Clean the response
                cleaned = response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
                
                # Parse JSON
                data = json.loads(cleaned)
                
                # Validate with Pydantic
                return response_model.model_validate(data)
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"JSON parsing attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to parse JSON after {max_retries} attempts")
                    logger.error(f"Raw response: {response if 'response' in locals() else 'No response'}")
                    raise RuntimeError(f"Failed to generate valid JSON: {str(e)}") from e
                continue