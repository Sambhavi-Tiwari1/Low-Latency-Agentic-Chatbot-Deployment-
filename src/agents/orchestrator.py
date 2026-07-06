"""
Orchestrator Agent - Routes tasks and manages multi-agent workflow
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core.openai_client import OpenAIClient
from ..core.context_manager import ContextManager
from .research import ResearchAgent
from .analysis import AnalysisAgent
from .generation import GenerationAgent
from .execution import ExecutionAgent

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Orchestrator Agent: Routes tasks to appropriate agents with parallel execution
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.openai_client = OpenAIClient(config)
        self.context_manager = ContextManager(config)
        
        # Initialize specialized agents
        self.research_agent = ResearchAgent(config)
        self.analysis_agent = AnalysisAgent(config)
        self.generation_agent = GenerationAgent(config)
        self.execution_agent = ExecutionAgent(config)
        
        self.logger = logging.getLogger(__name__)
    
    async def process(self, user_input: str, 
                     user_id: str = None,
                     conversation_history: List[Dict] = None) -> Dict:
        """
        Process user input through the agentic workflow
        
        Args:
            user_input: User's message
            user_id: User identifier for context management
            conversation_history: Previous conversation history
            
        Returns:
            Response dictionary with results
        """
        start_time = datetime.now()
        
        self.logger.info(f"Processing user input: {user_input[:50]}...")
        
        # Step 1: Classify intent
        intent_result = await self._classify_intent(user_input)
        intent = intent_result['intent']
        confidence = intent_result['confidence']
        
        self.logger.info(f"Intent: {intent} (confidence: {confidence:.2f})")
        
        # Step 2: Get context
        context = self.context_manager.get_context(user_id, conversation_history)
        
        # Step 3: Select workflow
        workflow = self._select_workflow(intent)
        
        # Step 4: Execute workflow with parallel processing [citation:4]
        if self.config['optimization']['parallel_agents']:
            result = await self._execute_parallel_workflow(workflow, user_input, context)
        else:
            result = await self._execute_sequential_workflow(workflow, user_input, context)
        
        # Step 5: Update context
        self.context_manager.update_context(user_id, user_input, result['response'])
        
        # Step 6: Calculate metrics
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            'response': result['response'],
            'intent': intent,
            'confidence': confidence,
            'agents_used': result.get('agents_used', []),
            'latency_ms': round(elapsed_ms, 2),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _classify_intent(self, user_input: str) -> Dict:
        """Classify user intent using fast routing [citation:9]"""
        # Fast path for trivial queries [citation:9]
        fast_intents = ['greeting', 'farewell', 'simple_question']
        
        # Use minimal reasoning for classification [citation:9]
        response = await self.openai_client.classify_intent(
            user_input,
            reasoning_effort="minimal"
        )
        
        return {
            'intent': response.get('intent', 'general'),
            'confidence': response.get('confidence', 0.8)
        }
    
    def _select_workflow(self, intent: str) -> str:
        """Select appropriate workflow based on intent"""
        workflows = {
            'technical_assistance': 'technical_assistance',
            'customer_support': 'customer_support',
            'information_retrieval': 'information_retrieval',
            'task_execution': 'task_execution',
            'general': 'general_conversation'
        }
        return workflows.get(intent, 'general_conversation')
    
    async def _execute_parallel_workflow(self, workflow: str, 
                                        user_input: str,
                                        context: Dict) -> Dict:
        """Execute workflow with parallel agent processing [citation:4]"""
        
        if workflow == 'technical_assistance':
            # Run research and analysis in parallel
            research_task = asyncio.create_task(
                self.research_agent.process(user_input, context)
            )
            analysis_task = asyncio.create_task(
                self.analysis_agent.process(user_input, context)
            )
            
            # Wait for both to complete
            research_result, analysis_result = await asyncio.gather(
                research_task, analysis_task
            )
            
            # Generate response using results
            generation_result = await self.generation_agent.process(
                user_input, context, {
                    'research': research_result,
                    'analysis': analysis_result
                }
            )
            
            # Format response
            execution_result = await self.execution_agent.process(
                generation_result
            )
            
            return {
                'response': execution_result['response'],
                'agents_used': ['research', 'analysis', 'generation', 'execution']
            }
        
        else:
            # Default sequential for simple workflows
            return await self._execute_sequential_workflow(workflow, user_input, context)
    
    async def _execute_sequential_workflow(self, workflow: str,
                                         user_input: str,
                                         context: Dict) -> Dict:
        """Execute workflow sequentially"""
        # Research
        research_result = await self.research_agent.process(user_input, context)
        
        # Analysis
        analysis_result = await self.analysis_agent.process(
            user_input, context, research_result
        )
        
        # Generation
        generation_result = await self.generation_agent.process(
            user_input, context, analysis_result
        )
        
        # Execution
        execution_result = await self.execution_agent.process(generation_result)
        
        return {
            'response': execution_result['response'],
            'agents_used': ['research', 'analysis', 'generation', 'execution']
        }
