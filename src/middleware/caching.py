"""
Response caching middleware for low-latency responses
"""
import logging
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger(__name__)

class ResponseCache:
    """
    Multi-level response cache (in-memory + optional Redis)
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.max_size = 1000
        self.cache = OrderedDict()
        self.ttl = config.get('cache_ttl', 3600)  # 1 hour default
        self.enabled = config.get('response_caching', True)
        self.logger = logging.getLogger(__name__)
    
    def _generate_key(self, user_input: str, context: Dict) -> str:
        """Generate cache key from input and context"""
        key_data = {
            'input': user_input,
            'context': context.get('history', [])[-5:]  # Last 5 messages
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, user_input: str, context: Dict) -> Optional[str]:
        """
        Get cached response
        """
        if not self.enabled:
            return None
        
        key = self._generate_key(user_input, context)
        
        if key in self.cache:
            entry = self.cache[key]
            # Check TTL
            if datetime.now() - entry['timestamp'] < timedelta(seconds=self.ttl):
                # Move to end (LRU)
                self.cache.move_to_end(key)
                self.logger.debug(f"Cache hit for: {user_input[:30]}...")
                return entry['response']
            else:
                del self.cache[key]
                self.logger.debug("Cache entry expired")
        
        return None
    
    def set(self, user_input: str, context: Dict, response: str) -> None:
        """
        Cache a response
        """
        if not self.enabled:
            return
        
        key = self._generate_key(user_input, context)
        
        self.cache[key] = {
            'response': response,
            'timestamp': datetime.now()
        }
        
        # LRU eviction
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
        
        self.logger.debug(f"Cached response for: {user_input[:30]}...")
    
    def clear(self) -> None:
        """Clear cache"""
        self.cache.clear()
        self.logger.info("Cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'enabled': self.enabled
        }
