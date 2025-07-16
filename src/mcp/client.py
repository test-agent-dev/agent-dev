"""
Model Context Protocol Client
Provides client interface for MCP connections
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable

import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class SimpleMCPClient:
    """Simplified MCP Client implementation"""
    
    def __init__(self, client_id: str = "testia-client"):
        self.client_id = client_id
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.connected = False
        self.request_id = 0
        self.pending_requests: Dict[int, asyncio.Future] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
    async def connect(self, uri: str = "ws://localhost:3000"):
        """Connect to MCP server"""
        try:
            self.websocket = await websockets.connect(uri)
            self.connected = True
            logger.info(f"MCP client {self.client_id} connected to {uri}")
            
            # Start message handler task
            asyncio.create_task(self._handle_messages())
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info(f"MCP client {self.client_id} disconnected")

    async def _handle_messages(self):
        """Handle incoming messages from server"""
        try:
            while self.connected and self.websocket:
                message = await self.websocket.recv()
                await self._process_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            logger.info("MCP server connection closed")
        except Exception as e:
            logger.error(f"Error handling MCP messages: {e}")
            self.connected = False

    async def _process_message(self, message: str):
        """Process incoming message"""
        try:
            data = json.loads(message)
            
            # Handle response to our request
            if "id" in data and data["id"] in self.pending_requests:
                future = self.pending_requests.pop(data["id"])
                if "error" in data:
                    future.set_exception(Exception(data["error"]["message"]))
                else:
                    future.set_result(data.get("result"))
            
            # Handle notifications/events
            elif "method" in data:
                method = data["method"]
                params = data.get("params", {})
                
                if method in self.message_handlers:
                    await self.message_handlers[method](params)
                else:
                    logger.debug(f"Unhandled MCP method: {method}")
                    
        except Exception as e:
            logger.error(f"Error processing MCP message: {e}")

    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Any:
        """Send a request to the MCP server"""
        if not self.connected or not self.websocket:
            raise Exception("Not connected to MCP server")
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        future = asyncio.Future()
        self.pending_requests[self.request_id] = future
        
        await self.websocket.send(json.dumps(request))
        
        try:
            result = await asyncio.wait_for(future, timeout=30.0)
            return result
        except asyncio.TimeoutError:
            if self.request_id in self.pending_requests:
                del self.pending_requests[self.request_id]
            raise Exception("Request timeout")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server"""
        result = await self._send_request("tools/list")
        return result.get("tools", [])

    async def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a tool on the MCP server"""
        params = {
            "name": name,
            "arguments": arguments or {}
        }
        return await self._send_request("tools/call", params)

    async def chat(self, agent_id: str, message: str, context: Dict[str, Any] = None) -> str:
        """Chat with an agent via MCP"""
        result = await self.call_tool("chat", {
            "agent_id": agent_id,
            "message": message,
            "context": context or {}
        })
        
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", "")
        
        return str(result)

    async def list_agents(self) -> List[Dict[str, Any]]:
        """List available agents"""
        result = await self.call_tool("list_agents")
        
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "[]")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return []
        
        return []

    async def get_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """Get agent configuration"""
        result = await self.call_tool("get_agent_config", {"agent_id": agent_id})
        
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "{}")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {}
        
        return {}

    async def update_agent_instructions(self, agent_id: str, instructions: str) -> str:
        """Update agent instructions"""
        result = await self.call_tool("update_agent_instructions", {
            "agent_id": agent_id,
            "instructions": instructions
        })
        
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", "")
        
        return str(result)

    def on_message(self, method: str, handler: Callable):
        """Register a message handler for specific method"""
        self.message_handlers[method] = handler

    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.connected and self.websocket is not None


# Alias for backward compatibility
TestiaMCPClient = SimpleMCPClient
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self.connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self.server_configs: Dict[str, MCPServerConfig] = {}
        
    async def add_server(self, config: MCPServerConfig):
        """Add a new MCP server configuration"""
        self.server_configs[config.name] = config
        
        if config.enabled:
            await self.connect_to_server(config.name)
    
    async def connect_to_server(self, server_name: str) -> bool:
        """Connect to an MCP server"""
        if server_name not in self.server_configs:
            logger.error(f"Server config for {server_name} not found")
            return False
        
        config = self.server_configs[server_name]
        
        try:
            # Create WebSocket connection
            headers = {}
            if config.auth_token:
                headers["Authorization"] = f"Bearer {config.auth_token}"
            
            websocket = await websockets.connect(config.url, extra_headers=headers)
            self.connections[server_name] = websocket
            
            # Create MCP client
            client = MCPClient(server_name)
            await client.connect(websocket)
            self.clients[server_name] = client
            
            logger.info(f"Connected to MCP server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_name}: {e}")
            return False
    
    async def disconnect_from_server(self, server_name: str):
        """Disconnect from an MCP server"""
        if server_name in self.clients:
            try:
                await self.clients[server_name].disconnect()
                del self.clients[server_name]
            except Exception as e:
                logger.error(f"Error disconnecting from {server_name}: {e}")
        
        if server_name in self.connections:
            try:
                await self.connections[server_name].close()
                del self.connections[server_name]
            except Exception as e:
                logger.error(f"Error closing connection to {server_name}: {e}")
        
        logger.info(f"Disconnected from MCP server: {server_name}")
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on a specific MCP server"""
        if server_name not in self.clients:
            raise ValueError(f"Not connected to server: {server_name}")
        
        client = self.clients[server_name]
        request = CallToolRequest(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )
        
        try:
            response = await client.call_tool(request)
            return response
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on {server_name}: {e}")
            raise
    
    async def get_resource(self, server_name: str, resource_uri: str) -> Any:
        """Get a resource from a specific MCP server"""
        if server_name not in self.clients:
            raise ValueError(f"Not connected to server: {server_name}")
        
        client = self.clients[server_name]
        request = GetResourceRequest(
            method="resources/read",
            params={
                "uri": resource_uri
            }
        )
        
        try:
            response = await client.get_resource(request)
            return response
        except Exception as e:
            logger.error(f"Error getting resource {resource_uri} from {server_name}: {e}")
            raise
    
    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools on a server"""
        if server_name not in self.clients:
            raise ValueError(f"Not connected to server: {server_name}")
        
        client = self.clients[server_name]
        
        try:
            tools = await client.list_tools()
            return tools
        except Exception as e:
            logger.error(f"Error listing tools on {server_name}: {e}")
            raise
    
    async def list_resources(self, server_name: str) -> List[Dict[str, Any]]:
        """List available resources on a server"""
        if server_name not in self.clients:
            raise ValueError(f"Not connected to server: {server_name}")
        
        client = self.clients[server_name]
        
        try:
            resources = await client.list_resources()
            return resources
        except Exception as e:
            logger.error(f"Error listing resources on {server_name}: {e}")
            raise
    
    def get_connected_servers(self) -> List[str]:
        """Get list of connected server names"""
        return list(self.clients.keys())
    
    def is_connected(self, server_name: str) -> bool:
        """Check if connected to a specific server"""
        return server_name in self.clients
    
    async def disconnect_all(self):
        """Disconnect from all MCP servers"""
        server_names = list(self.clients.keys())
        for server_name in server_names:
            await self.disconnect_from_server(server_name)
    
    def get_status(self) -> Dict[str, Any]:
        """Get connection status for all servers"""
        status = {}
        for name, config in self.server_configs.items():
            status[name] = {
                "config": {
                    "url": config.url,
                    "description": config.description,
                    "enabled": config.enabled
                },
                "connected": self.is_connected(name)
            }
        return status
