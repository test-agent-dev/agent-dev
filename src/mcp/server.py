"""
Model Context Protocol Server
Provides MCP-compliant interface for AI agents
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import websockets
from websockets.server import WebSocketServerProtocol

from ..models.manager import ModelManager
from ..agents.base import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class MCPConnection:
    websocket: WebSocketServerProtocol
    client_id: str
    agent_id: Optional[str] = None
    connected_at: datetime = None


@dataclass
class MCPTool:
    name: str
    description: str
    parameters: Dict[str, Any]


class SimpleMCPServer:
    """Simplified MCP Server implementation"""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.connections: Dict[str, MCPConnection] = {}
        self.agents: Dict[str, BaseAgent] = {}
        self.tools: Dict[str, MCPTool] = {}
        
        # Register MCP tools
        self._register_tools()
        
    def _register_tools(self):
        """Register available tools"""
        
        self.tools["chat"] = MCPTool(
            name="chat",
            description="Chat with an AI agent",
            parameters={
                "agent_id": {"type": "string", "required": True},
                "message": {"type": "string", "required": True},
                "context": {"type": "object", "required": False}
            }
        )
        
        self.tools["list_agents"] = MCPTool(
            name="list_agents",
            description="List available AI agents",
            parameters={}
        )
        
        self.tools["get_agent_config"] = MCPTool(
            name="get_agent_config",
            description="Get configuration for a specific agent",
            parameters={
                "agent_id": {"type": "string", "required": True}
            }
        )
        
        self.tools["update_agent_instructions"] = MCPTool(
            name="update_agent_instructions",
            description="Update instructions for an agent",
            parameters={
                "agent_id": {"type": "string", "required": True},
                "instructions": {"type": "string", "required": True}
            }
        )

    async def handle_message(self, websocket: WebSocketServerProtocol, message: str) -> str:
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            method = data.get("method")
            params = data.get("params", {})
            request_id = data.get("id", 1)
            
            if method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                result = await self._call_tool(tool_name, arguments)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            elif method == "tools/list":
                tools_list = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.parameters
                    }
                    for tool in self.tools.values()
                ]
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": tools_list}
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
            
            return json.dumps(response)
            
        except Exception as e:
            logger.error(f"Error handling MCP message: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": data.get("id", 1) if 'data' in locals() else 1,
                "error": {"code": -32603, "message": str(e)}
            }
            return json.dumps(error_response)

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        
        if tool_name == "chat":
            agent_id = arguments.get("agent_id")
            message = arguments.get("message")
            context = arguments.get("context", {})
            
            if not agent_id or not message:
                raise ValueError("agent_id and message are required")
            
            agent = self.agents.get(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            response = await agent.process_message(message, context)
            return {"content": [{"type": "text", "text": response}]}
            
        elif tool_name == "list_agents":
            agents_info = []
            for agent_id, agent in self.agents.items():
                agents_info.append({
                    "id": agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "model": agent.model_config.get("model", "unknown")
                })
            
            return {"content": [{"type": "text", "text": json.dumps(agents_info, indent=2)}]}
            
        elif tool_name == "get_agent_config":
            agent_id = arguments.get("agent_id")
            if not agent_id:
                raise ValueError("agent_id is required")
            
            agent = self.agents.get(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            config = {
                "id": agent_id,
                "name": agent.name,
                "description": agent.description,
                "instructions": agent.instructions,
                "model_config": agent.model_config
            }
            
            return {"content": [{"type": "text", "text": json.dumps(config, indent=2)}]}
            
        elif tool_name == "update_agent_instructions":
            agent_id = arguments.get("agent_id")
            instructions = arguments.get("instructions")
            
            if not agent_id or not instructions:
                raise ValueError("agent_id and instructions are required")
            
            agent = self.agents.get(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent.update_instructions(instructions)
            return {"content": [{"type": "text", "text": f"Instructions updated for agent {agent_id}"}]}
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def add_agent(self, agent_id: str, agent: BaseAgent):
        """Add an agent to the MCP server"""
        self.agents[agent_id] = agent
        logger.info(f"Added agent {agent_id} to MCP server")

    async def remove_agent(self, agent_id: str):
        """Remove an agent from the MCP server"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Removed agent {agent_id} from MCP server")

    async def start_server(self, host: str = "0.0.0.0", port: int = 3000):
        """Start the MCP WebSocket server"""
        async def handle_client(websocket: WebSocketServerProtocol, path: str):
            client_id = f"client_{len(self.connections)}"
            connection = MCPConnection(
                websocket=websocket,
                client_id=client_id,
                connected_at=datetime.now()
            )
            self.connections[client_id] = connection
            
            logger.info(f"MCP client {client_id} connected")
            
            try:
                async for message in websocket:
                    response = await self.handle_message(websocket, message)
                    await websocket.send(response)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"MCP client {client_id} disconnected")
            except Exception as e:
                logger.error(f"Error handling MCP client {client_id}: {e}")
            finally:
                if client_id in self.connections:
                    del self.connections[client_id]

        server = await websockets.serve(handle_client, host, port)
        logger.info(f"MCP server started on {host}:{port}")
        return server

    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        if not self.connections:
            return
        
        message_json = json.dumps(message)
        disconnected_clients = []
        
        for client_id, connection in self.connections.items():
            try:
                await connection.websocket.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            if client_id in self.connections:
                del self.connections[client_id]

    def get_connection_status(self) -> Dict[str, Any]:
        """Get status of all MCP connections"""
        return {
            "total_connections": len(self.connections),
            "connections": [
                {
                    "client_id": conn.client_id,
                    "agent_id": conn.agent_id,
                    "connected_at": conn.connected_at.isoformat() if conn.connected_at else None
                }
                for conn in self.connections.values()
            ],
            "available_agents": list(self.agents.keys())
        }


# Alias for backward compatibility
TestiaMCPServer = SimpleMCPServer
