"""
Context Management with reasoning item caching [citation:11]
"""
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Manage conversation context with reasoning item persistence [citation:11]
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.max_history = config.get('context', {}).get('max_history', 50)
        self.include_reasoning = config.get('context', {}).get('include_reasoning', True)
        self.sessions = {}  # In-memory storage
        self.cache = {}     # Reasoning cache
    
    def get_context(self, user_id: str, 
                   conversation_history: List[Dict] = None) -> Dict:
        """
        Get context for a user session
        """
        # Get or create session
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                'history': [],
                'reasoning_items': [],
                'created_at': datetime.now().isoformat()
            }
        
        session = self.sessions[user_id]
        
        # Update with provided history
        if conversation_history:
            session['history'] = conversation_history[-self.max_history:]
        
        # Include reasoning items if enabled [citation:11]
        context = {
            'history': session['history'],
            'reasoning_items': session.get('reasoning_items', []) if self.include_reasoning else [],
            'session_created': session['created_at']
        }
        
        return context
    
    def update_context(self, user_id: str, user_input: str, assistant_response: str,
                      reasoning_items: List = None) -> None:
        """
        Update context with new interaction
        """
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                'history': [],
                'reasoning_items': [],
                'created_at': datetime.now().isoformat()
            }
        
        session = self.sessions[user_id]
        
        # Add user message
        session['history'].append({
            'role': 'user',
            'content': user_input
        })
        
        # Add assistant response
        session['history'].append({
            'role': 'assistant',
            'content': assistant_response
        })
        
        # Add reasoning items [citation:11]
        if reasoning_items and self.include_reasoning:
            # Cache reasoning items for future use
            session['reasoning_items'].extend(reasoning_items)
        
        # Trim history
        if len(session['history']) > self.max_history:
            session['history'] = session['history'][-self.max_history:]
        
        # Cache reasoning items for performance [citation:11]
        if reasoning_items:
            cache_key = f"{user_id}_{hashlib.md5(str(reasoning_items).encode()).hexdigest()}"
            self.cache[cache_key] = {
                'items': reasoning_items,
                'timestamp': datetime.now()
            }
    
    def get_reasoning_items(self, user_id: str) -> List:
        """
        Get cached reasoning items [citation:11]
        """
        session = self.sessions.get(user_id, {})
        return session.get('reasoning_items', []) if self.include_reasoning else []
    
    def clear_context(self, user_id: str) -> None:
        """
        Clear user context
        """
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"Cleared context for user: {user_id}")
    
    def get_context_for_api(self, user_id: str, 
                           include_reasoning: bool = True) -> List[Dict]:
        """
        Prepare context for API call [citation:11]
        """
        session = self.sessions.get(user_id, {})
        history = session.get('history', [])
        
        # For API, include reasoning items in the input
        if include_reasoning and self.include_reasoning:
            reasoning_items = session.get('reasoning_items', [])
            if reasoning_items:
                # Add reasoning items as special messages
                for item in reasoning_items:
                    if isinstance(item, dict):
                        history.insert(-1, item)  # Insert before last message
        
        return history[-self.max_history:]
