"""
Model Manager - Handles different AI model providers and configurations
"""
import os
import re
import json
import logging
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum

import openai
import anthropic

logger = logging.getLogger(__name__)

# Optional imports for Hugging Face
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers library not available. HuggingFace models will be disabled.")


def expand_env_vars(value: str) -> str:
    """Expand environment variables in string format ${VAR_NAME}"""
    if not isinstance(value, str):
        return value
    
    def replace_var(match):
        var_name = match.group(1)
        return os.getenv(var_name, match.group(0))  # Return original if not found
    
    return re.sub(r'\$\{([^}]+)\}', replace_var, value)


class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class ModelConfig:
    name: str
    provider: ModelProvider
    model_id: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    instructions: Optional[str] = None
    context_window: int = 8192
    enabled: bool = True
    custom_parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_parameters is None:
            self.custom_parameters = {}


class BaseModelProvider(ABC):
    """Abstract base class for model providers"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = None
        
    @abstractmethod
    async def initialize(self):
        """Initialize the model provider"""
        pass
    
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the model"""
        pass
    
    @abstractmethod
    async def stream_response(self, messages: List[Dict[str, str]], **kwargs):
        """Stream a response from the model"""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        return {
            "name": self.config.name,
            "provider": self.config.provider.value,
            "model_id": self.config.model_id,
            "max_tokens": self.config.max_tokens,
            "context_window": self.config.context_window
        }


class OpenAIProvider(BaseModelProvider):
    """OpenAI model provider (supports both OpenAI and Azure OpenAI)"""
    
    async def initialize(self):
        # Check if this is Azure OpenAI
        if self.config.api_base and "azure" in self.config.api_base.lower():
            # Azure OpenAI configuration
            api_version = self.config.custom_parameters.get("api-version", "2024-02-01")
            # Use the api_base directly as azure_endpoint
            azure_endpoint = self.config.api_base
            self.client = openai.AsyncAzureOpenAI(
                api_key=self.config.api_key or os.getenv("AZURE_OPENAI_API_KEY"),
                azure_endpoint=azure_endpoint,
                api_version=api_version
            )
            logger.info(f"Initialized Azure OpenAI provider for model {self.config.model_id} with endpoint {azure_endpoint}")
        else:
            # Regular OpenAI configuration
            self.client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv("OPENAI_API_KEY"),
                base_url=self.config.api_base
            )
            logger.info(f"Initialized OpenAI provider for model {self.config.model_id}")
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            # Use the model_id directly (for Azure it should be the deployment name)
            model_name = self.config.model_id
            
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                **{k: v for k, v in self.config.custom_parameters.items() if k != "api-version"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            raise
    
    async def stream_response(self, messages: List[Dict[str, str]], **kwargs):
        try:
            # For Azure OpenAI, use the deployment name as model
            model_name = self.config.model_id
            if self.config.api_base and "azure" in self.config.api_base.lower():
                # Extract deployment name from api_base if available
                if "/deployments/" in self.config.api_base:
                    model_name = self.config.api_base.split("/deployments/")[1].split("/")[0]
            
            stream = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                stream=True,
                **{k: v for k, v in self.config.custom_parameters.items() if k != "api-version"}
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error streaming OpenAI response: {e}")
            raise


class AnthropicProvider(BaseModelProvider):
    """Anthropic model provider"""
    
    async def initialize(self):
        self.client = anthropic.AsyncAnthropic(
            api_key=self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        logger.info(f"Initialized Anthropic provider for model {self.config.model_id}")
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            # Convert messages to Anthropic format
            system_message = None
            formatted_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    formatted_messages.append(msg)
            
            response = await self.client.messages.create(
                model=self.config.model_id,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                system=system_message or self.config.system_prompt,
                messages=formatted_messages,
                **self.config.custom_parameters
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating Anthropic response: {e}")
            raise
    
    async def stream_response(self, messages: List[Dict[str, str]], **kwargs):
        try:
            # Convert messages to Anthropic format
            system_message = None
            formatted_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    formatted_messages.append(msg)
            
            stream = await self.client.messages.create(
                model=self.config.model_id,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                system=system_message or self.config.system_prompt,
                messages=formatted_messages,
                stream=True,
                **self.config.custom_parameters
            )
            
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield chunk.delta.text
        except Exception as e:
            logger.error(f"Error streaming Anthropic response: {e}")
            raise


class HuggingFaceProvider(BaseModelProvider):
    """HuggingFace model provider"""
    
    async def initialize(self):
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers library not available. Please install transformers to use HuggingFace models.")
        
        # This is a simplified implementation
        # In production, you'd want to use more sophisticated loading
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(self.config.model_id)
        logger.info(f"Initialized HuggingFace provider for model {self.config.model_id}")
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers library not available.")
            
        try:
            # Convert messages to text
            text = self._messages_to_text(messages)
            
            inputs = self.tokenizer.encode(text, return_tensors="pt")
            max_length = len(inputs[0]) + kwargs.get("max_tokens", self.config.max_tokens)
            
            outputs = self.model.generate(
                inputs,
                max_length=max_length,
                temperature=kwargs.get("temperature", self.config.temperature),
                do_sample=True,
                **self.config.custom_parameters
            )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response[len(text):].strip()
        except Exception as e:
            logger.error(f"Error generating HuggingFace response: {e}")
            raise
    
    async def stream_response(self, messages: List[Dict[str, str]], **kwargs):
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers library not available.")
            
        # Simplified streaming - in production you'd implement proper streaming
        response = await self.generate_response(messages, **kwargs)
        for word in response.split():
            yield word + " "
    
    def _messages_to_text(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to plain text"""
        text_parts = []
        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"]
            text_parts.append(f"{role}: {content}")
        return "\n".join(text_parts) + "\nAssistant: "


class ModelManager:
    """Manages multiple AI models and providers"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.providers: Dict[str, BaseModelProvider] = {}
        self.configs: Dict[str, ModelConfig] = {}
        self.config_path = config_path or "config/models.json"
        
    async def load_models(self):
        """Load model configurations from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                for model_name, model_data in data.get("models", {}).items():
                    config = ModelConfig(
                        name=model_name,
                        provider=ModelProvider(model_data["provider"]),
                        model_id=expand_env_vars(model_data["model_id"]),
                        api_key=expand_env_vars(model_data.get("api_key")),
                        api_base=expand_env_vars(model_data.get("api_base")),
                        max_tokens=model_data.get("max_tokens", 4000),
                        temperature=model_data.get("temperature", 0.7),
                        system_prompt=expand_env_vars(model_data.get("system_prompt")),
                        instructions=expand_env_vars(model_data.get("instructions")),
                        context_window=model_data.get("context_window", 8192),
                        enabled=model_data.get("enabled", True),
                        custom_parameters={
                            k: expand_env_vars(v) if isinstance(v, str) else v 
                            for k, v in model_data.get("custom_parameters", {}).items()
                        }
                    )
                    
                    await self.add_model(model_name, config)
                
                logger.info(f"Loaded {len(self.configs)} model configurations")
            else:
                logger.warning(f"Model config file not found: {self.config_path}")
                await self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading model configurations: {e}")
            raise
    
    async def add_model(self, model_name: str, config: ModelConfig):
        """Add a new model configuration"""
        self.configs[model_name] = config
        
        if config.enabled:
            provider = self._create_provider(config)
            await provider.initialize()
            self.providers[model_name] = provider
            logger.info(f"Added model: {model_name}")
    
    async def remove_model(self, model_name: str):
        """Remove a model configuration"""
        if model_name in self.providers:
            del self.providers[model_name]
        if model_name in self.configs:
            del self.configs[model_name]
        logger.info(f"Removed model: {model_name}")
    
    def _create_provider(self, config: ModelConfig) -> BaseModelProvider:
        """Create a provider instance based on the model config"""
        if config.provider == ModelProvider.OPENAI:
            return OpenAIProvider(config)
        elif config.provider == ModelProvider.ANTHROPIC:
            return AnthropicProvider(config)
        elif config.provider == ModelProvider.HUGGINGFACE:
            return HuggingFaceProvider(config)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    async def generate_response(self, model_name: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response using a specific model"""
        if model_name not in self.providers:
            raise ValueError(f"Model not available: {model_name}")
        
        provider = self.providers[model_name]
        return await provider.generate_response(messages, **kwargs)
    
    async def stream_response(self, model_name: str, messages: List[Dict[str, str]], **kwargs):
        """Stream a response using a specific model"""
        if model_name not in self.providers:
            raise ValueError(f"Model not available: {model_name}")
        
        provider = self.providers[model_name]
        async for chunk in provider.stream_response(messages, **kwargs):
            yield chunk
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self.providers.keys())
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        if model_name in self.providers:
            return self.providers[model_name].get_model_info()
        return None
    
    def get_all_models_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all models"""
        return {
            name: provider.get_model_info()
            for name, provider in self.providers.items()
        }
    
    async def save_config(self):
        """Save current model configurations to file"""
        try:
            data = {
                "models": {
                    name: asdict(config)
                    for name, config in self.configs.items()
                }
            }
            
            # Convert enums to strings for JSON serialization
            for model_data in data["models"].values():
                model_data["provider"] = model_data["provider"].value
            
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Model configurations saved")
        except Exception as e:
            logger.error(f"Error saving model configurations: {e}")
            raise
    
    async def _create_default_config(self):
        """Create a default model configuration file"""
        default_config = {
            "models": {
                "gpt-4": {
                    "provider": "openai",
                    "model_id": "gpt-4",
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "enabled": True,
                    "instructions": "You are a helpful AI assistant."
                },
                "claude-3": {
                    "provider": "anthropic",
                    "model_id": "claude-3-sonnet-20240229",
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "enabled": False,
                    "instructions": "You are Claude, an AI assistant created by Anthropic."
                }
            }
        }
        
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Created default model configuration: {self.config_path}")
