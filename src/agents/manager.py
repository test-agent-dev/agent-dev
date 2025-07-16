"""
Agent Manager - Manages multiple AI agents
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Type
from datetime import datetime

from .base import BaseAgent, AgentConfig, GeneralAssistant, CodeAssistant, DataAnalyst
from ..models.manager import ModelManager

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages multiple AI agents"""
    
    def __init__(self, model_manager: ModelManager, config_path: str = "config/agents.json"):
        self.model_manager = model_manager
        self.config_path = config_path
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_classes: Dict[str, Type[BaseAgent]] = {
            "general-assistant": GeneralAssistant,
            "code-assistant": CodeAssistant,
            "data-analyst": DataAnalyst
        }
    
    async def load_agents(self):
        """Load agent configurations from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                for agent_data in data.get("agents", []):
                    await self.create_agent_from_config(agent_data)
                
                logger.info(f"Loaded {len(self.agents)} agents")
            else:
                logger.warning(f"Agent config file not found: {self.config_path}")
                await self._create_default_agents()
        except Exception as e:
            logger.error(f"Error loading agent configurations: {e}")
            raise
    
    async def create_agent_from_config(self, agent_data: Dict[str, Any]) -> BaseAgent:
        """Create an agent from configuration data"""
        agent_type = agent_data.get("type", "custom")
        agent_id = agent_data["name"]
        
        if agent_type in self.agent_classes:
            # Create predefined agent type
            agent_class = self.agent_classes[agent_type]
            model_name = agent_data.get("model_name", "gpt-4")
            agent = agent_class(self.model_manager, model_name)
            
            # Override with custom configuration
            if "instructions" in agent_data:
                agent.update_instructions(agent_data["instructions"])
        else:
            # Create custom agent
            config = AgentConfig(
                name=agent_data["name"],
                description=agent_data.get("description", "Custom AI agent"),
                model_name=agent_data.get("model_name", "gpt-4"),
                instructions=agent_data.get("instructions", "You are a helpful AI assistant."),
                system_prompt=agent_data.get("system_prompt"),
                max_context_length=agent_data.get("max_context_length", 8000),
                temperature=agent_data.get("temperature", 0.7),
                tools=agent_data.get("tools", []),
                enabled=agent_data.get("enabled", True),
                metadata=agent_data.get("metadata", {})
            )
            agent = BaseAgent(config, self.model_manager)
        
        self.agents[agent_id] = agent
        logger.info(f"Created agent: {agent_id}")
        return agent
    
    async def create_custom_agent(self, 
                                 name: str, 
                                 description: str,
                                 model_name: str,
                                 instructions: str,
                                 **kwargs) -> BaseAgent:
        """Create a custom agent with specified parameters"""
        config = AgentConfig(
            name=name,
            description=description,
            model_name=model_name,
            instructions=instructions,
            system_prompt=kwargs.get("system_prompt"),
            max_context_length=kwargs.get("max_context_length", 8000),
            temperature=kwargs.get("temperature", 0.7),
            tools=kwargs.get("tools", []),
            enabled=kwargs.get("enabled", True),
            metadata=kwargs.get("metadata", {})
        )
        
        agent = BaseAgent(config, self.model_manager)
        self.agents[name] = agent
        logger.info(f"Created custom agent: {name}")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """List all agent IDs"""
        return list(self.agents.keys())
    
    def get_enabled_agents(self) -> List[str]:
        """Get list of enabled agent IDs"""
        return [
            agent_id for agent_id, agent in self.agents.items()
            if agent.config.enabled
        ]
    
    async def remove_agent(self, agent_id: str):
        """Remove an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Removed agent: {agent_id}")
    
    def enable_agent(self, agent_id: str):
        """Enable an agent"""
        if agent_id in self.agents:
            self.agents[agent_id].config.enabled = True
            logger.info(f"Enabled agent: {agent_id}")
    
    def disable_agent(self, agent_id: str):
        """Disable an agent"""
        if agent_id in self.agents:
            self.agents[agent_id].config.enabled = False
            logger.info(f"Disabled agent: {agent_id}")
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent"""
        agent = self.get_agent(agent_id)
        return agent.get_status() if agent else None
    
    def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents"""
        return {
            agent_id: agent.get_status()
            for agent_id, agent in self.agents.items()
        }
    
    async def process_message(self, 
                             agent_id: str, 
                             message: str, 
                             context: Optional[Dict[str, Any]] = None,
                             conversation_id: Optional[str] = None,
                             stream: bool = False):
        """Process a message with a specific agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        if not agent.config.enabled:
            raise ValueError(f"Agent is disabled: {agent_id}")
        
        return await agent.process_message(message, context, conversation_id, stream)
    
    async def save_config(self):
        """Save current agent configurations to file"""
        try:
            agents_data = []
            for agent_id, agent in self.agents.items():
                agent_dict = agent.to_dict()
                # Determine agent type
                agent_type = "custom"
                for type_name, agent_class in self.agent_classes.items():
                    if isinstance(agent, agent_class):
                        agent_type = type_name
                        break
                
                agent_dict["type"] = agent_type
                agents_data.append(agent_dict)
            
            config_data = {"agents": agents_data}
            
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info("Agent configurations saved")
        except Exception as e:
            logger.error(f"Error saving agent configurations: {e}")
            raise
    
    async def _create_default_agents(self):
        """Create default agents"""
        default_agents = [
            {
                "type": "general-assistant",
                "name": "general-assistant",
                "description": "A helpful general-purpose AI assistant",
                "model_name": "gpt-4",
                "enabled": True
            },
            {
                "type": "code-assistant", 
                "name": "code-assistant",
                "description": "An AI assistant specialized in programming",
                "model_name": "gpt-4",
                "enabled": True
            },
            {
                "type": "data-analyst",
                "name": "data-analyst", 
                "description": "An AI assistant specialized in data analysis",
                "model_name": "gpt-4",
                "enabled": False
            }
        ]
        
        for agent_data in default_agents:
            await self.create_agent_from_config(agent_data)
        
        await self.save_config()
        logger.info("Created default agents")
    
    def get_conversation_history(self, agent_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation history for a specific agent and conversation"""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        conversation = agent.get_conversation(conversation_id)
        if not conversation:
            return None
        
        return {
            "id": conversation.id,
            "agent_id": conversation.agent_id,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "message_count": len(conversation.messages),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in conversation.messages
            ]
        }
    
    def clear_agent_conversations(self, agent_id: str):
        """Clear all conversations for a specific agent"""
        agent = self.get_agent(agent_id)
        if agent:
            agent.clear_all_conversations()
            logger.info(f"Cleared all conversations for agent: {agent_id}")
    
    def register_agent_class(self, type_name: str, agent_class: Type[BaseAgent]):
        """Register a new agent class type"""
        self.agent_classes[type_name] = agent_class
        logger.info(f"Registered agent class: {type_name}")
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about agents"""
        total_agents = len(self.agents)
        enabled_agents = len(self.get_enabled_agents())
        
        total_conversations = sum(
            len(agent.conversations) for agent in self.agents.values()
        )
        
        model_usage = {}
        for agent in self.agents.values():
            model = agent.config.model_name
            model_usage[model] = model_usage.get(model, 0) + 1
        
        return {
            "total_agents": total_agents,
            "enabled_agents": enabled_agents,
            "disabled_agents": total_agents - enabled_agents,
            "total_conversations": total_conversations,
            "model_usage": model_usage,
            "available_types": list(self.agent_classes.keys())
        }
