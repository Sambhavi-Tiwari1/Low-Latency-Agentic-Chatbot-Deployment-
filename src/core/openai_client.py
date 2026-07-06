"""
OpenAI API Client with optimized performance
"""
import openai
import asyncio
import logging
from typing import Dict, List, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class OpenAIClient:
    """
    OpenAI API client with performance optimizations [citation:3]
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = openai.AsyncOpenAI()
        self.default_model = config.get('openai', {}).get('model', 'gpt-4o-mini')
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def chat_completion(self, messages: List[Dict[str, str]], 
                             model: Optional[str] = None,
                             temperature: Optional[float] = None,
                             max_tokens: Optional[int] = None,
                             prediction: Optional[str] = None,
                             stream: bool = False,
                             **kwargs) -> Any:
        """
        Chat completion with performance optimizations
        
        Args:
            messages: List of messages
            model: Model name
            temperature: Temperature setting
            max_tokens: Maximum tokens
            prediction: Predicted output for faster generation [citation:6]
            stream: Whether to stream responses
            
        Returns:
            Chat completion response
        """
        model = model or self.default_model
        temperature = temperature or self.config.get('openai', {}).get('temperature', 0.7)
        max_tokens = max_tokens or self.config.get('openai', {}).get('max_tokens', 1000)
        
        # Build request parameters
        params = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            **kwargs
        }
        
        # Add prediction if provided [citation:6]
        if prediction and self.config['optimization']['predicted_outputs']:
            params['prediction'] = {
                'type': 'content',
                'content': prediction
            }
        
        try:
            if stream:
                return await self.client.chat.completions.create(**params, stream=True)
            else:
                return await self.client.chat.completions.create(**params)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def classify_intent(self, user_input: str,
                            reasoning_effort: str = "minimal") -> Dict:
        """
        Fast intent classification with minimal reasoning [citation:9]
        """
        messages = [
            {
                "role": "system",
                "content": """Classify the user's intent into one of:
                - greeting: Casual hello/goodbye
                - simple_question: Direct factual question
                - technical_assistance: Code, debugging, technical help
                - customer_support: Product/service issues
                - task_execution: Action/command requests
                - general: Other conversations
                
                Return JSON: {"intent": "intent_type", "confidence": 0.0-1.0}"""
            },
            {"role": "user", "content": user_input}
        ]
        
        # Use minimal reasoning for speed [citation:9]
        response = await self.chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=50,
            reasoning_effort=reasoning_effort
        )
        
        try:
            import json
            return json.loads(response.choices[0].message.content)
        except:
            return {"intent": "general", "confidence": 0.7}
    
    async def stream_with_prediction(self, messages: List[Dict],
                                   prediction: str,
                                   **kwargs) -> Any:
        """
        Stream response with predicted output for lower latency [citation:6]
        """
        return await self.chat_completion(
            messages=messages,
            prediction=prediction,
            stream=True,
            **kwargs
        )
