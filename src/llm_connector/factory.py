import json
import os
import logging
from typing import Any, Dict

from src.models.manager import (
    ModelProvider,
    ModelConfig,
    OpenAIProvider,
    AnthropicProvider,
    HuggingFaceProvider,
)

logger = logging.getLogger(__name__)


class ModelFactory:
    """Factory that builds model clients from a configuration file."""

    def __init__(self, config_path: str = "models.config.json"):
        """Initialize the factory and load model configurations."""
        self.config_path = config_path
        self.configs: Dict[str, ModelConfig] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load all model configurations from ``self.config_path``."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            data = json.load(f)

        for name, cfg in data.get("models", {}).items():
            parameters = cfg.get("parameters", {})
            model_cfg = ModelConfig(
                name=name,
                provider=ModelProvider(cfg["provider"]),
                model_id=cfg.get("model_id", name),
                api_key=cfg.get("api_key"),
                api_base=cfg.get("endpoint"),
                max_tokens=parameters.get("max_tokens", 4000),
                temperature=parameters.get("temperature", 0.7),
                custom_parameters={k: v for k, v in parameters.items() if k not in {"max_tokens", "temperature"}},
            )
            self.configs[name] = model_cfg
        logger.info("Loaded %s model configurations", len(self.configs))

    async def get_client(self, model_name: str):
        """Return an initialized provider for ``model_name``.

        Parameters
        ----------
        model_name: str
            Identifier of the model as defined in the configuration file.
        """
        if model_name not in self.configs:
            raise ValueError(f"Unknown model: {model_name}")

        config = self.configs[model_name]
        provider = self._create_provider(config)
        await provider.initialize()
        return provider

    def _create_provider(self, config: ModelConfig):
        """Instantiate the correct provider implementation."""
        if config.provider == ModelProvider.OPENAI:
            return OpenAIProvider(config)
        if config.provider == ModelProvider.ANTHROPIC:
            return AnthropicProvider(config)
        if config.provider == ModelProvider.HUGGINGFACE:
            return HuggingFaceProvider(config)
        # Custom/unknown provider handled as OpenAI-compatible HTTP API
        return OpenAIProvider(config)

