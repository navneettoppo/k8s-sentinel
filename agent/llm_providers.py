"""
LLM Provider Module for K3s-Sentinel Agent.

Supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google Gemini
- Azure OpenAI
- Ollama (local)
- Local models (via transformers)
- Custom OpenAI-compatible APIs
"""

import asyncio
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import aiohttp

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class LLMProviderType(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"
    LOCAL = "local"
    CUSTOM = "custom"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    usage: Dict[str, int]
    raw_response: Dict[str, Any]


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)
        self.extra_params = kwargs

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from LLM."""
        pass

    @abstractmethod
    async def generate_batch(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        """Generate responses for multiple prompts."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider (GPT-4, GPT-3.5)."""

    def __init__(self, api_key: str, model: str = "gpt-4", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")
        self.organization = kwargs.get("organization", None)
        self.client = None

    async def _get_client(self):
        """Get or create OpenAI client."""
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed")

        if self.client is None:
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                organization=self.organization
            )
        return self.client

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using OpenAI."""
        client = await self._get_client()

        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        system_prompt = kwargs.get("system_prompt", "You are a Kubernetes expert helping with root cause analysis.")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                raw_response=response.model_dump()
            )
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise

    async def generate_batch(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        """Generate responses for multiple prompts."""
        tasks = [self.generate(p, **kwargs) for p in prompts]
        return await asyncio.gather(*tasks)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic LLM provider (Claude)."""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = None

    async def _get_client(self):
        """Get or create Anthropic client."""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not installed")

        if self.client is None:
            self.client = anthropic.AsyncAnthropic(
                api_key=self.api_key
            )
        return self.client

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Anthropic."""
        client = await self._get_client()

        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        system_prompt = kwargs.get("system_prompt", "You are a Kubernetes expert helping with root cause analysis.")

        try:
            response = await client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            content = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    content += block.text

            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                raw_response=response.model_dump()
            )
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise

    async def generate_batch(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        """Generate responses for multiple prompts."""
        tasks = [self.generate(p, **kwargs) for p in prompts]
        return await asyncio.gather(*tasks)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self, api_key: str, model: str = "gemini-pro", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get("base_url", "https://generativelanguage.googleapis.com/v1")

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Google Gemini."""
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)

        url = f"{self.base_url}/models/{self.model}:generateContent"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": kwargs.get("top_p", 0.95),
                "topK": kwargs.get("top_k", 40)
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    params={"key": self.api_key}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Gemini API error: {error_text}")

                    data = await response.json()

                    content = ""
                    if "candidates" in data and len(data["candidates"]) > 0:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            for part in candidate["content"]["parts"]:
                                if "text" in part:
                                    content += part["text"]

                    return LLMResponse(
                        content=content,
                        model=self.model,
                        usage={"total_tokens": data.get("usageMetadata", {}).get("totalTokenCount", 0)},
                        raw_response=data
                    )
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            raise

    async def generate_batch(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        """Generate responses for multiple prompts."""
        tasks = [self.generate(p, **kwargs) for p in prompts]
        return await asyncio.gather(*tasks)


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI LLM provider."""

    def __init__(self, api_key: str, model: str, endpoint: str, api_version: str = "2024-02-01", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.endpoint = endpoint
        self.api_version = api_version
        self.client = None

    async def _get_client(self):
        """Get or create Azure OpenAI client."""
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed")

        if self.client is None:
            self.client = openai.AsyncAzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version
            )
        return self.client

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Azure OpenAI."""
        client = await self._get_client()

        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        system_prompt = kwargs.get("system_prompt", "You are a Kubernetes expert helping with root cause analysis.")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                raw_response=response.model_dump()
            )
        except Exception as e:
            self.logger.error(f"Azure OpenAI API error: {e}")
            raise

    async def generate_batch(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        """Generate responses for multiple prompts."""
        tasks = [self.generate(p, **kwargs) for p in prompts]
        return await asyncio.gather(*tasks)


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, api_key: str = "", model: str = "llama2", base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.base_url = base_url

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Ollama."""
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "options": {
                "num_predict": max_tokens
            },
            "stream": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {error_text}")

                    data = await response.json()

                    return LLMResponse(
                        content=data.get("response", ""),
                        model=self.model,
                        usage={"prompt_tokens": 0, "completion_tokens": 0},
                        raw_response=data
                    )
        except Exception as e:
            self.logger.error(f"Ollama API error: {e}")
            raise

    async def generate_batch(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        """Generate responses for multiple prompts."""
        tasks = [self.generate(p, **kwargs) for p in prompts]
        return await asyncio.gather(*tasks)


class LocalProvider(BaseLLMProvider):
    """Local model provider using transformers or similar."""

    def __init__(self, api_key: str = "", model: str = "microsoft/Phi-3-mini-4k-instruct", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.model_path = kwargs.get("model_path", None)
        self.device = kwargs.get("device", "auto")
        self.pipeline = None

    async def _get_pipeline(self):
        """Get or create local pipeline."""
        try:
            from transformers import pipeline
        except ImportError:
            raise ImportError("transformers package not installed")

        if self.pipeline is None:
            self.pipeline = await asyncio.to_thread(
                pipeline,
                "text-generation",
                model=self.model,
                device=self.device,
                model_kwargs={"torch_dtype": "auto"}
            )
        return self.pipeline

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using local model."""
        pipeline = await self._get_pipeline()

        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)

        try:
            result = await asyncio.to_thread(
                pipeline,
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                **kwargs
            )

            content = result[0]["generated_text"]

            return LLMResponse(
                content=content,
                model=self.model,
                usage={"prompt_tokens": 0, "completion_tokens": 0},
                raw_response=result
            )
        except Exception as e:
            self.logger.error(f"Local model error: {e}")
            raise

    async def generate_batch(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        """Generate responses for multiple prompts."""
        tasks = [self.generate(p, **kwargs) for p in prompts]
        return await asyncio.gather(*tasks)


class CustomProvider(BaseLLMProvider):
    """Custom OpenAI-compatible API provider."""

    def __init__(self, api_key: str, model: str, base_url: str, **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.client = None

    async def _get_client(self):
        """Get or create custom client."""
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed")

        if self.client is None:
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=f"{self.base_url}/v1"
            )
        return self.client

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using custom API."""
        client = await self._get_client()

        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)

        messages = [{"role": "user", "content": prompt}]

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                raw_response=response.model_dump()
            )
        except Exception as e:
            self.logger.error(f"Custom API error: {e}")
            raise

    async def generate_batch(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        """Generate responses for multiple prompts."""
        tasks = [self.generate(p, **kwargs) for p in prompts]
        return await asyncio.gather(*tasks)


class LLMProviderFactory:
    """Factory for creating LLM providers."""

    _providers = {
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.ANTHROPIC: AnthropicProvider,
        LLMProviderType.GEMINI: GeminiProvider,
        LLMProviderType.AZURE_OPENAI: AzureOpenAIProvider,
        LLMProviderType.OLLAMA: OllamaProvider,
        LLMProviderType.LOCAL: LocalProvider,
        LLMProviderType.CUSTOM: CustomProvider,
    }

    @classmethod
    def create_provider(
        cls,
        provider_type: str,
        api_key: str,
        model: str,
        **kwargs
    ) -> BaseLLMProvider:
        """Create an LLM provider instance."""
        try:
            provider_enum = LLMProviderType(provider_type.lower())
        except ValueError:
            raise ValueError(f"Unknown provider type: {provider_type}")

        provider_class = cls._providers.get(provider_enum)
        if provider_class is None:
            raise ValueError(f"Provider not implemented: {provider_type}")

        return provider_class(api_key=api_key, model=model, **kwargs)

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider types."""
        return [p.value for p in LLMProviderType]


class LLMManager:
    """Manager for LLM providers with fallback support."""

    def __init__(self, settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.providers: List[BaseLLMProvider] = []
        self.current_provider_index = 0

    async def initialize(self):
        """Initialize LLM providers."""
        primary_provider = self._create_provider_from_settings()
        if primary_provider:
            self.providers.append(primary_provider)
            self.logger.info(f"Primary LLM provider initialized: {self.settings.llm_provider}")

        # Add fallback providers if configured
        for fallback in self.settings.llm_fallback_providers or []:
            try:
                provider = self._create_provider_from_settings(fallback)
                if provider:
                    self.providers.append(provider)
                    self.logger.info(f"Fallback provider initialized: {fallback.get('provider')}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize fallback provider: {e}")

    def _create_provider_from_settings(self, config: Dict = None) -> Optional[BaseLLMProvider]:
        """Create provider from settings."""
        config = config or {}

        provider_type = config.get("provider", self.settings.llm_provider)
        api_key = config.get("api_key", self.settings.llm_api_key)
        model = config.get("model", self.settings.llm_model)

        if not api_key and provider_type not in ["ollama", "local"]:
            self.logger.warning(f"No API key provided for {provider_type}")
            return None

        extra_params = {}
        if provider_type == "azure_openai":
            extra_params["endpoint"] = config.get("azure_endpoint", self.settings.llm_azure_endpoint)
            extra_params["api_version"] = config.get("azure_api_version", self.settings.llm_azure_api_version)
        elif provider_type == "custom":
            extra_params["base_url"] = config.get("base_url", self.settings.llm_custom_base_url)
        elif provider_type == "ollama":
            extra_params["base_url"] = config.get("base_url", self.settings.llm_ollama_base_url)
        elif provider_type == "local":
            extra_params["model_path"] = config.get("model_path")
            extra_params["device"] = config.get("device", "auto")

        try:
            return LLMProviderFactory.create_provider(
                provider_type=provider_type,
                api_key=api_key,
                model=model,
                **extra_params
            )
        except Exception as e:
            self.logger.error(f"Failed to create provider: {e}")
            return None

    async def generate(self, prompt: str, **kwargs) -> Optional[LLMResponse]:
        """Generate response with fallback support."""
        if not self.providers:
            return None

        # Try primary provider first
        for i in range(len(self.providers)):
            provider = self.providers[self.current_provider_index]
            try:
                response = await provider.generate(prompt, **kwargs)
                return response
            except Exception as e:
                self.logger.warning(f"Provider {type(provider).__name__} failed: {e}")
                self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)

        self.logger.error("All LLM providers failed")
        return None

    async def generate_batch(self, prompts: List[str], **kwargs) -> List[LLMResponse]:
        """Generate responses for multiple prompts."""
        if not self.providers:
            return []

        provider = self.providers[self.current_provider_index]
        try:
            return await provider.generate_batch(prompts, **kwargs)
        except Exception as e:
            self.logger.error(f"Batch generation failed: {e}")
            return []
