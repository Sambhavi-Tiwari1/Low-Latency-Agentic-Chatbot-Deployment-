#!/usr/bin/env python
"""
Main CLI Application
"""
import os
import sys
import argparse
import asyncio
import logging
from typing import Optional

from src.agents.orchestrator import OrchestratorAgent
from src.utils.helpers import load_config, create_directories
from src.middleware.monitoring import MetricsCollector

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def interactive_mode():
    """Interactive CLI mode"""
    print("\n" + "="*60)
    print("🤖 Welcome to Agentic Chatbot!")
    print("   Type 'quit' to exit, 'clear' to clear context")
    print("="*60 + "\n")
    
    config = load_config()
    orchestrator = OrchestratorAgent(config)
    user_id = "cli_user"
    
    while True:
        try:
            user_input = input("\nUser: ").strip()
            
            if user_input.lower() == 'quit':
                print("Goodbye! 👋")
                break
            
            if user_input.lower() == 'clear':
                orchestrator.context_manager.clear_context(user_id)
                print("Context cleared!")
                continue
            
            if not user_input:
                continue
            
            # Process with latency tracking
            start_time = __import__('time').time()
            result = await orchestrator.process(user_input, user_id)
            elapsed_ms = (__import__('time').time() - start_time) * 1000
            
            # Display response
            print(f"\n🤖 Assistant: {result['response']}")
            print(f"\n💡 Intent: {result['intent']} (Confidence: {result['confidence']:.2f})")
            print(f"⏱️  Latency: {result['latency_ms']:.0f}ms")
            print(f"🧠 Agents: {', '.join(result.get('agents_used', []))}")
            
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Agentic Chatbot')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--query', '-q', type=str,
                       help='Send a single query')
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='Path to config file')
    
    args = parser.parse_args()
    
    create_directories()
    
    if args.interactive:
        asyncio.run(interactive_mode())
    elif args.query:
        # Single query mode
        config = load_config(args.config)
        orchestrator = OrchestratorAgent(config)
        
        result = asyncio.run(orchestrator.process(args.query, "cli_user"))
        print(f"\n🤖 Assistant: {result['response']}")
        print(f"\n⏱️  Latency: {result['latency_ms']:.0f}ms")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
