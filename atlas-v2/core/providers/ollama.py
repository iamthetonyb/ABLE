"""
Ollama Provider - Local LLM inference for privacy and offline operation.

Always-available fallback that runs on local hardware.
"""

import asyncio
import json
import logging
from typing import List, Dict, Optional, AsyncIterator

import aiohttp

from .base import (
    LLMProvider,
    ProviderConfig,
    ProviderError,
    Message,
    CompletionResult,
    UsageStats,
    ToolCall,
    Role,
)

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Ollama Provider for local LLM inference.

    Default model: llama3.2 (good balance of speed and quality)
    Alternative: mistral, codellama, phi3

    Benefits:
    - Free (runs locally)
    - Private (no data leaves machine)
    - Offline capable
    - No rate limits
    """

    DEFAULT_MODEL = "llama3.2"
    DEFAULT_URL = "http://localhost:11434"

    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        timeout: float = 300.0  # Local inference can be slow
    ):
        config = ProviderConfig(
            api_key="",  # Not needed for local
            base_url=base_url or self.DEFAULT_URL,
            model=model or self.DEFAULT_MODEL,
            timeout=timeout,
            cost_per_million_input=0.0,  # Free
            cost_per_million_output=0.0
        )
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def name(self) -> str:
        return "ollama"

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self._session

    def _convert_messages(self, messages: List[Message]) -> List[Dict]:
        """Convert to Ollama chat format"""
        converted = []
        for msg in messages:
            converted.append({
                "role": msg.role.value,
                "content": msg.content
            })
        return converted

    async def complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> CompletionResult:
        session = await self._get_session()

        payload = {
            "model": self.config.model,
            "messages": self._convert_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        # Ollama tool support is model-dependent
        if tools and self._model_supports_tools():
            payload["tools"] = tools

        try:
            async with session.post(
                f"{self.config.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status == 404:
                    raise ProviderError(
                        self.name,
                        f"Model '{self.config.model}' not found. Run: ollama pull {self.config.model}",
                        retryable=False
                    )
                elif response.status != 200:
                    text = await response.text()
                    raise ProviderError(
                        self.name,
                        f"API error {response.status}: {text}",
                        retryable=response.status >= 500
                    )

                data = await response.json()

                message = data.get("message", {})

                # Parse tool calls if present
                tool_calls = None
                if message.get("tool_calls"):
                    tool_calls = [
                        ToolCall(
                            id=f"call_{i}",
                            name=tc["function"]["name"],
                            arguments=tc["function"]["arguments"]
                        )
                        for i, tc in enumerate(message["tool_calls"])
                    ]

                # Ollama provides token counts
                prompt_eval_count = data.get("prompt_eval_count", 0)
                eval_count = data.get("eval_count", 0)

                result = CompletionResult(
                    content=message.get("content", ""),
                    finish_reason="stop" if data.get("done") else "length",
                    usage=UsageStats(
                        input_tokens=prompt_eval_count,
                        output_tokens=eval_count,
                        total_tokens=prompt_eval_count + eval_count
                    ),
                    provider=self.name,
                    model=data.get("model", self.config.model),
                    tool_calls=tool_calls,
                    cost=0.0,  # Free
                    raw_response=data
                )

                return result

        except aiohttp.ClientConnectorError:
            raise ProviderError(
                self.name,
                f"Cannot connect to Ollama at {self.config.base_url}. Is it running?",
                retryable=True
            )
        except aiohttp.ClientError as e:
            raise ProviderError(
                self.name,
                f"Connection error: {e}",
                retryable=True
            )

    async def stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncIterator[str]:
        session = await self._get_session()

        payload = {
            "model": self.config.model,
            "messages": self._convert_messages(messages),
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        try:
            async with session.post(
                f"{self.config.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise ProviderError(
                        self.name,
                        f"Stream error {response.status}: {text}",
                        retryable=response.status >= 500
                    )

                async for line in response.content:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if message := data.get("message", {}).get("content"):
                            yield message
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

        except aiohttp.ClientConnectorError:
            raise ProviderError(
                self.name,
                f"Cannot connect to Ollama at {self.config.base_url}",
                retryable=True
            )
        except aiohttp.ClientError as e:
            raise ProviderError(
                self.name,
                f"Stream connection error: {e}",
                retryable=True
            )

    def count_tokens(self, text: str) -> int:
        """Approximate token count"""
        return len(text) // 4

    def _model_supports_tools(self) -> bool:
        """Check if current model supports tool calling"""
        tool_capable = ['llama3', 'mistral', 'mixtral', 'command-r']
        return any(m in self.config.model.lower() for m in tool_capable)

    async def list_models(self) -> List[str]:
        """List available local models"""
        session = await self._get_session()
        try:
            async with session.get(f"{self.config.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry"""
        session = await self._get_session()
        try:
            async with session.post(
                f"{self.config.base_url}/api/pull",
                json={"name": model, "stream": False}
            ) as response:
                return response.status == 200
        except Exception:
            return False

    async def health_check(self) -> bool:
        """Check if Ollama is running and model is available"""
        session = await self._get_session()
        try:
            async with session.get(f"{self.config.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return self.config.model in models or any(
                        self.config.model in m for m in models
                    )
        except Exception:
            pass
        return False

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
