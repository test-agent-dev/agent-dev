import json
from pathlib import Path
from unittest import mock
import pytest

from src.llm_connector.factory import ModelFactory


sample_config = {
    "models": {
        "x": {
            "provider": "openai",
            "api_key": "sk-test",
            "endpoint": "https://api.example.com",
            "parameters": {"temperature": 0.5, "max_tokens": 10}
        }
    }
}


def test_load_config(tmp_path: Path):
    cfg_file = tmp_path / "models.json"
    cfg_file.write_text(json.dumps(sample_config))
    factory = ModelFactory(str(cfg_file))
    assert "x" in factory.configs
    cfg = factory.configs["x"]
    assert cfg.temperature == 0.5
    assert cfg.max_tokens == 10


@pytest.mark.asyncio
async def test_get_client_initializes(tmp_path: Path):
    cfg_file = tmp_path / "models.json"
    cfg_file.write_text(json.dumps(sample_config))
    factory = ModelFactory(str(cfg_file))
    with mock.patch("src.models.manager.OpenAIProvider.initialize") as init_mock:
        init_mock.return_value = None
        client = await factory.get_client("x")
        init_mock.assert_called_once()
        assert client is not None

