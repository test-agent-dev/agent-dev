"""
API Usage Examples for TESTIA AI Agent
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional


class TestiaAPIClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        async with self.session.get(f"{self.base_url}/api/status") as response:
            return await response.json()
    
    async def list_agents(self) -> Dict[str, Any]:
        """List all agents"""
        async with self.session.get(f"{self.base_url}/api/agents") as response:
            return await response.json()
    
    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get specific agent details"""
        async with self.session.get(f"{self.base_url}/api/agents/{agent_id}") as response:
            return await response.json()
    
    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent"""
        async with self.session.post(
            f"{self.base_url}/api/agents",
            json=agent_data
        ) as response:
            return await response.json()
    
    async def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an agent"""
        async with self.session.put(
            f"{self.base_url}/api/agents/{agent_id}",
            json=update_data
        ) as response:
            return await response.json()
    
    async def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """Delete an agent"""
        async with self.session.delete(f"{self.base_url}/api/agents/{agent_id}") as response:
            return await response.json()
    
    async def chat(self, agent_id: str, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a chat message"""
        data = {
            "agent_id": agent_id,
            "message": message,
            "conversation_id": conversation_id,
            "stream": False
        }
        async with self.session.post(f"{self.base_url}/api/chat", json=data) as response:
            return await response.json()
    
    async def list_models(self) -> Dict[str, Any]:
        """List all models"""
        async with self.session.get(f"{self.base_url}/api/models") as response:
            return await response.json()
    
    async def get_conversations(self, agent_id: str) -> Dict[str, Any]:
        """List conversations for an agent"""
        async with self.session.get(f"{self.base_url}/api/conversations/{agent_id}") as response:
            return await response.json()
    
    async def get_conversation(self, agent_id: str, conversation_id: str) -> Dict[str, Any]:
        """Get specific conversation"""
        async with self.session.get(
            f"{self.base_url}/api/conversations/{agent_id}/{conversation_id}"
        ) as response:
            return await response.json()


async def example_system_overview():
    """Example: Get system overview"""
    print("🔍 System Overview Example")
    
    async with TestiaAPIClient() as client:
        # Get system status
        status = await client.get_status()
        print(f"System Status: {json.dumps(status, indent=2)}")
        
        # List agents
        agents = await client.list_agents()
        print(f"\nAvailable Agents: {len(agents['agents'])}")
        for agent in agents['agents']:
            print(f"  - {agent['name']}: {agent['description']}")
        
        # List models
        models = await client.list_models()
        print(f"\nAvailable Models: {len(models['models'])}")
        for name, model in models['models'].items():
            print(f"  - {name}: {model['provider']} ({model['model_id']})")


async def example_agent_management():
    """Example: Agent management operations"""
    print("\n🤖 Agent Management Example")
    
    async with TestiaAPIClient() as client:
        # Create a custom agent
        new_agent = {
            "name": "example-agent",
            "description": "Example agent for testing",
            "model_name": "gpt-3.5-turbo",
            "instructions": "You are a helpful example agent for testing purposes.",
            "temperature": 0.8
        }
        
        print("Creating new agent...")
        result = await client.create_agent(new_agent)
        print(f"Created: {result}")
        
        # Get agent details
        print("\nGetting agent details...")
        agent_details = await client.get_agent("example-agent")
        print(f"Agent details: {json.dumps(agent_details, indent=2)}")
        
        # Update agent
        print("\nUpdating agent...")
        update_data = {
            "instructions": "You are an updated example agent with new instructions.",
            "temperature": 0.5
        }
        update_result = await client.update_agent("example-agent", update_data)
        print(f"Updated: {update_result}")
        
        # Chat with agent
        print("\nChatting with agent...")
        chat_response = await client.chat(
            "example-agent", 
            "Hello! Can you introduce yourself?"
        )
        print(f"Chat response: {chat_response['response']}")
        
        # Delete agent
        print("\nDeleting agent...")
        delete_result = await client.delete_agent("example-agent")
        print(f"Deleted: {delete_result}")


async def example_conversation_flow():
    """Example: Multi-turn conversation"""
    print("\n💬 Conversation Flow Example")
    
    async with TestiaAPIClient() as client:
        agent_id = "general-assistant"
        conversation_id = None
        
        messages = [
            "Hola, ¿puedes ayudarme con Docker?",
            "¿Cuál es la diferencia entre una imagen y un contenedor?",
            "¿Puedes mostrarme un ejemplo de Dockerfile?",
            "Gracias por la ayuda!"
        ]
        
        print(f"Starting conversation with {agent_id}...")
        
        for i, message in enumerate(messages, 1):
            print(f"\n[Turn {i}] User: {message}")
            
            response = await client.chat(agent_id, message, conversation_id)
            print(f"[Turn {i}] Assistant: {response['response'][:100]}...")
            
            # Extract conversation ID from first response
            if conversation_id is None:
                # In a real implementation, you'd get this from the response
                # For this example, we'll simulate it
                conversation_id = f"conv_{response['timestamp']}"
        
        print(f"\nConversation completed with ID: {conversation_id}")


async def example_model_testing():
    """Example: Test different models"""
    print("\n🧠 Model Testing Example")
    
    async with TestiaAPIClient() as client:
        # Get available models
        models = await client.list_models()
        available_models = list(models['models'].keys())
        
        test_message = "Explain quantum computing in simple terms."
        
        print(f"Testing message: '{test_message}'\n")
        
        # Test with different agents (which use different models)
        agents_to_test = ["general-assistant", "code-assistant"]
        
        for agent_id in agents_to_test:
            try:
                print(f"Testing with {agent_id}...")
                response = await client.chat(agent_id, test_message)
                print(f"Response length: {len(response['response'])} characters")
                print(f"First 100 chars: {response['response'][:100]}...\n")
            except Exception as e:
                print(f"Error testing {agent_id}: {e}\n")


async def example_performance_test():
    """Example: Simple performance test"""
    print("\n⚡ Performance Test Example")
    
    import time
    
    async with TestiaAPIClient() as client:
        agent_id = "general-assistant"
        test_messages = [
            "Hello!",
            "What's the weather like?",
            "Tell me a joke.",
            "Explain machine learning.",
            "Goodbye!"
        ]
        
        print(f"Sending {len(test_messages)} messages to {agent_id}...")
        
        start_time = time.time()
        
        for i, message in enumerate(test_messages, 1):
            msg_start = time.time()
            response = await client.chat(agent_id, message)
            msg_duration = time.time() - msg_start
            
            print(f"Message {i}: {msg_duration:.2f}s - {len(response['response'])} chars")
        
        total_duration = time.time() - start_time
        avg_duration = total_duration / len(test_messages)
        
        print(f"\nTotal time: {total_duration:.2f}s")
        print(f"Average per message: {avg_duration:.2f}s")


async def main():
    """Run all examples"""
    try:
        await example_system_overview()
        await example_agent_management()
        await example_conversation_flow()
        await example_model_testing()
        await example_performance_test()
        
    except aiohttp.ClientError as e:
        print(f"❌ Connection error: {e}")
        print("Make sure TESTIA server is running on http://localhost:8080")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
