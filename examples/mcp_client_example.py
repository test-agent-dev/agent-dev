"""
MCP Client Example - Demonstrates how to connect to TESTIA MCP server
"""
import asyncio
import websockets
import json
from typing import Dict, Any


class SimpleMCPClient:
    def __init__(self, server_url: str = "ws://localhost:3000"):
        self.server_url = server_url
        self.websocket = None
        
    async def connect(self):
        """Connect to MCP server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            print(f"✅ Connected to MCP server: {self.server_url}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.websocket:
            await self.websocket.close()
            print("👋 Disconnected from MCP server")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.websocket:
            raise ConnectionError("Not connected to MCP server")
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Send request
        await self.websocket.send(json.dumps(request))
        
        # Receive response
        response_raw = await self.websocket.recv()
        response = json.loads(response_raw)
        
        if "error" in response:
            raise Exception(f"MCP Error: {response['error']}")
        
        return response.get("result", {})


async def main():
    """Example usage of MCP client"""
    client = SimpleMCPClient()
    
    if not await client.connect():
        return
    
    try:
        # List available agents
        print("\n📋 Listing agents...")
        result = await client.call_tool("list_agents", {})
        print(f"Available agents: {result}")
        
        # Chat with an agent
        print("\n💬 Chatting with general-assistant...")
        result = await client.call_tool("chat", {
            "agent_id": "general-assistant",
            "message": "Hola, ¿puedes ayudarme con Docker?",
            "context": {"user": "example_user"}
        })
        print(f"Response: {result}")
        
        # Get agent configuration
        print("\n⚙️  Getting agent config...")
        result = await client.call_tool("get_agent_config", {
            "agent_id": "code-assistant"
        })
        print(f"Agent config: {result}")
        
        # Update agent instructions
        print("\n✏️  Updating agent instructions...")
        result = await client.call_tool("update_agent_instructions", {
            "agent_id": "general-assistant",
            "instructions": "Eres un asistente especializado en Docker y contenedores."
        })
        print(f"Update result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
