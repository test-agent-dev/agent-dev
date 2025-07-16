"""
Base Agent Class - Foundation for all AI agents
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import json

from ..models.manager import ModelManager

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    name: str
    description: str
    model_name: str
    instructions: str
    system_prompt: Optional[str] = None
    max_context_length: int = 8000
    temperature: float = 0.7
    tools: List[str] = field(default_factory=list)
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    id: str
    agent_id: str
    messages: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, config: AgentConfig, model_manager: ModelManager):
        self.config = config
        self.model_manager = model_manager
        self.conversations: Dict[str, Conversation] = {}
        self.tools: Dict[str, callable] = {}
        
        # Agent properties
        self.name = config.name
        self.description = config.description
        self.instructions = config.instructions
        self.model_config = {
            "model": config.model_name,
            "temperature": config.temperature,
            "max_tokens": config.max_context_length
        }
        
        logger.info(f"Initialized agent: {self.name}")
    
    async def process_message(self, 
                            user_message: str, 
                            context: Optional[Dict[str, Any]] = None,
                            conversation_id: Optional[str] = None,
                            stream: bool = False) -> Union[str, Any]:
        """Process a user message and return a response"""
        
        # Get or create conversation
        if conversation_id is None:
            conversation_id = f"conv_{datetime.now().timestamp()}"
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation(
                id=conversation_id,
                agent_id=self.name
            )
        
        conversation = self.conversations[conversation_id]
        
        # Add user message
        user_msg = Message(role="user", content=user_message)
        conversation.messages.append(user_msg)
        
        # Update context
        if context:
            conversation.context.update(context)
        
        try:
            # Prepare messages for the model
            messages = await self._prepare_messages(conversation)
            
            # Generate response
            if stream:
                return self._stream_response(conversation_id, messages)
            else:
                response = await self._generate_response(messages)
                
                # Add assistant message
                assistant_msg = Message(role="assistant", content=response)
                conversation.messages.append(assistant_msg)
                conversation.updated_at = datetime.now()
                
                return response
                
        except Exception as e:
            logger.error(f"Error processing message for agent {self.name}: {e}")
            error_response = "I apologize, but I encountered an error processing your request."
            
            # Add error message to conversation
            assistant_msg = Message(
                role="assistant", 
                content=error_response,
                metadata={"error": str(e)}
            )
            conversation.messages.append(assistant_msg)
            
            return error_response
    
    async def stream_response(
        self, 
        message: str, 
        conversation_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ):
        """Public method to stream responses"""
        try:
            # Create or get conversation
            if not conversation_id:
                conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.conversations)}"
            
            if conversation_id not in self.conversations:
                conversation = Conversation(id=conversation_id, agent_id=self.name)
                self.conversations[conversation_id] = conversation
            else:
                conversation = self.conversations[conversation_id]
            
            # Add user message
            user_msg = Message(role="user", content=message)
            conversation.messages.append(user_msg)
            conversation.updated_at = datetime.now()
            
            # Prepare messages for model
            messages = []
            
            # System prompt
            system_content = system_prompt or self.config.system_prompt or self.config.instructions
            if system_content:
                messages.append({"role": "system", "content": system_content})
            
            # Add conversation history
            for msg in conversation.messages:
                messages.append({"role": msg.role, "content": msg.content})
            
            # Stream response
            async for chunk in self._stream_response(conversation_id, messages, temperature, max_tokens):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in stream_response: {e}")
            yield f"Error: {str(e)}"

    def update_system_prompt(self, system_prompt: str):
        """Update the agent's system prompt"""
        self.config.system_prompt = system_prompt
        logger.info(f"Updated system prompt for agent {self.name}")
    
    def update_instructions(self, instructions: str):
        """Update the agent's instructions"""
        self.config.instructions = instructions
        logger.info(f"Updated instructions for agent {self.name}")
    
    def update_temperature(self, temperature: float):
        """Update the agent's temperature setting"""
        self.config.temperature = max(0.0, min(2.0, temperature))
        logger.info(f"Updated temperature for agent {self.name} to {self.config.temperature}")
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history as a list of dictionaries"""
        if conversation_id not in self.conversations:
            return []
        
        conversation = self.conversations[conversation_id]
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            }
            for msg in conversation.messages
        ]

    # Tool management methods (stub implementations)
    def register_tool(self, tool_name: str, tool_function):
        """Register a tool function for this agent"""
        pass
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools for this agent"""
        return self.config.tools.copy()

    async def _stream_response(
        self, 
        conversation_id: str, 
        messages: List[Dict[str, str]], 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """Stream response from the model"""
        conversation = self.conversations[conversation_id]
        response_chunks = []
        
        try:
            # Use provided temperature or default
            temp = temperature if temperature is not None else self.config.temperature
            
            async for chunk in self.model_manager.stream_response(
                self.config.model_name, 
                messages,
                temperature=temp,
                max_tokens=max_tokens
            ):
                response_chunks.append(chunk)
                yield chunk
            
            # Save complete response to conversation
            complete_response = "".join(response_chunks)
            assistant_msg = Message(role="assistant", content=complete_response)
            conversation.messages.append(assistant_msg)
            conversation.updated_at = datetime.now()
            
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield f"Error: {str(e)}"
    
    async def _generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a response from the model"""
        return await self.model_manager.generate_response(
            self.config.model_name,
            messages,
            temperature=self.config.temperature
        )
    
    async def _prepare_messages(self, conversation: Conversation) -> List[Dict[str, str]]:
        """Prepare messages for the model"""
        messages = []
        
        # Add system message with instructions
        system_content = self._build_system_message(conversation.context)
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history (with context window limit)
        for message in conversation.messages[-self._get_context_limit():]:
            messages.append({
                "role": message.role,
                "content": message.content
            })
        
        return messages
    
    def _build_system_message(self, context: Dict[str, Any]) -> str:
        """Build the system message with instructions and context"""
        system_parts = []
        
        # Base instructions
        if self.config.system_prompt:
            system_parts.append(self.config.system_prompt)
        
        system_parts.append(self.instructions)
        
        # Add context if available
        if context:
            system_parts.append(f"\nAdditional context: {json.dumps(context)}")
        
        return "\n\n".join(system_parts)
    
    def _get_context_limit(self) -> int:
        """Get the number of messages to include in context"""
        # Simple heuristic: assume ~100 tokens per message
        return min(50, self.config.max_context_length // 100)
    
    def update_instructions(self, new_instructions: str):
        """Update the agent's instructions"""
        self.instructions = new_instructions
        self.config.instructions = new_instructions
        logger.info(f"Updated instructions for agent {self.name}")
    
    def add_tool(self, tool_name: str, tool_function: callable):
        """Add a tool to the agent"""
        self.tools[tool_name] = tool_function
        if tool_name not in self.config.tools:
            self.config.tools.append(tool_name)
        logger.info(f"Added tool {tool_name} to agent {self.name}")
    
    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent"""
        if tool_name in self.tools:
            del self.tools[tool_name]
        if tool_name in self.config.tools:
            self.config.tools.remove(tool_name)
        logger.info(f"Removed tool {tool_name} from agent {self.name}")
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a specific conversation"""
        return self.conversations.get(conversation_id)
    
    def list_conversations(self) -> List[str]:
        """Get list of conversation IDs"""
        return list(self.conversations.keys())
    
    def clear_conversation(self, conversation_id: str):
        """Clear a specific conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Cleared conversation {conversation_id} for agent {self.name}")
    
    def clear_all_conversations(self):
        """Clear all conversations"""
        self.conversations.clear()
        logger.info(f"Cleared all conversations for agent {self.name}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            "name": self.name,
            "description": self.description,
            "model": self.config.model_name,
            "enabled": self.config.enabled,
            "active_conversations": len(self.conversations),
            "available_tools": list(self.tools.keys()),
            "instructions_length": len(self.instructions)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "model_name": self.config.model_name,
            "instructions": self.instructions,
            "system_prompt": self.config.system_prompt,
            "max_context_length": self.config.max_context_length,
            "temperature": self.config.temperature,
            "tools": self.config.tools,
            "enabled": self.config.enabled,
            "metadata": self.config.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], model_manager: ModelManager) -> 'BaseAgent':
        """Create agent from dictionary representation"""
        config = AgentConfig(
            name=data["name"],
            description=data["description"],
            model_name=data["model_name"],
            instructions=data["instructions"],
            system_prompt=data.get("system_prompt"),
            max_context_length=data.get("max_context_length", 8000),
            temperature=data.get("temperature", 0.7),
            tools=data.get("tools", []),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {})
        )
        return cls(config, model_manager)


class GeneralAssistant(BaseAgent):
    """General purpose AI assistant"""
    
    def __init__(self, model_manager: ModelManager, model_name: str = "gpt-4"):
        config = AgentConfig(
            name="general-assistant",
            description="A helpful general-purpose AI assistant",
            model_name=model_name,
            instructions="""You are a helpful, harmless, and honest AI assistant. 
            You provide accurate information and assistance across a wide range of topics.
            Always be respectful and professional in your responses."""
        )
        super().__init__(config, model_manager)


class CodeAssistant(BaseAgent):
    """Specialized coding assistant"""
    
    def __init__(self, model_manager: ModelManager, model_name: str = "gpt-4"):
        config = AgentConfig(
            name="code-assistant",
            description="An AI assistant specialized in programming and software development",
            model_name=model_name,
            instructions="""You are an expert programming assistant. You help with:
            - Writing and debugging code
            - Explaining programming concepts
            - Code reviews and optimization
            - Architecture and design patterns
            - Best practices and conventions
            
            Always provide clear, well-commented code examples and explanations."""
        )
        super().__init__(config, model_manager)


class DataAnalyst(BaseAgent):
    """Specialized data analysis assistant"""
    
    def __init__(self, model_manager: ModelManager, model_name: str = "gpt-4"):
        config = AgentConfig(
            name="data-analyst",
            description="An AI assistant specialized in data analysis and statistics",
            model_name=model_name,
            instructions="""You are a data analysis expert. You help with:
            - Data exploration and visualization
            - Statistical analysis and interpretation
            - Machine learning model selection
            - Data cleaning and preprocessing
            - Reporting and insights generation
            
            Always provide clear explanations of your analysis methods and findings."""
        )
        super().__init__(config, model_manager)
