"""
Universal Reasoning Capture System

Sistema universal para capturar reasoning/thinking de múltiplos provedores LLM.
Suporta diferentes estratégias de extração conforme a arquitetura de cada provedor.

Providers Suportados (all configurable via .env):
- Claude (e.g., Sonnet 4.5): Extended Thinking API (thinking blocks)
- Gemini (e.g., 2.5): Thinking Config API (thought summaries)
- OpenAI (e.g., GPT-5/o1): Reasoning tokens (usage statistics only)
- Grok/DeepSeek: reasoning_content field
- Generic: Log parsing (fallback)

Author: VOXY System
Date: 2025-10-14
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from loguru import logger

# ============================================================================
# Data Models
# ============================================================================


@dataclass
class ReasoningContent:
    """Modelo unificado para conteúdo de reasoning capturado."""

    # Metadata
    provider: str  # claude, openai, gemini, grok, deepseek, generic
    model: str
    timestamp: datetime
    extraction_strategy: str  # api, response_field, logs, stats

    # Content (pelo menos um deve estar presente)
    thinking_text: Optional[str] = None  # Texto do reasoning/thinking
    thinking_blocks: Optional[list[dict[str, Any]]] = (
        None  # Blocos estruturados (Claude)
    )
    thought_summary: Optional[str] = None  # Resumo (Gemini)

    # Usage Statistics
    reasoning_tokens: Optional[int] = None  # Token count (OpenAI)
    reasoning_effort: Optional[str] = None  # Effort level usado

    # Technical Metadata
    signature: Optional[str] = None  # Assinatura criptográfica (Claude)
    redacted: bool = False  # Se foi redacted por safety
    cache_hit: bool = False

    # Performance
    extraction_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário para logging/storage."""
        return {
            "provider": self.provider,
            "model": self.model,
            "timestamp": self.timestamp.isoformat(),
            "extraction_strategy": self.extraction_strategy,
            "thinking_text": self.thinking_text,
            "thinking_blocks": self.thinking_blocks,
            "thought_summary": self.thought_summary,
            "reasoning_tokens": self.reasoning_tokens,
            "reasoning_effort": self.reasoning_effort,
            "signature": self.signature,
            "redacted": self.redacted,
            "cache_hit": self.cache_hit,
            "extraction_time_ms": self.extraction_time_ms,
        }

    def has_content(self) -> bool:
        """Verifica se há conteúdo de reasoning capturado."""
        return bool(
            self.thinking_text
            or self.thinking_blocks
            or self.thought_summary
            or self.reasoning_tokens
        )


# ============================================================================
# Abstract Base Class
# ============================================================================


class ReasoningExtractor(ABC):
    """Interface abstrata para extratores de reasoning específicos por provedor."""

    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model
        self.logger = logger.bind(component="ReasoningExtractor", provider=provider)

    @abstractmethod
    def extract(
        self, response: Any, metadata: Optional[dict[str, Any]] = None
    ) -> Optional[ReasoningContent]:
        """
        Extrai reasoning do response do LLM.

        Args:
            response: Response object do LiteLLM ou OpenAI Agents SDK
            metadata: Metadados adicionais (trace_id, agent_name, etc.)

        Returns:
            ReasoningContent se reasoning foi encontrado, None caso contrário
        """
        pass

    @abstractmethod
    def supports_provider(self, provider: str, model: str) -> bool:
        """Verifica se este extractor suporta o provider/model."""
        pass


# ============================================================================
# Claude Extended Thinking Extractor
# ============================================================================


class ClaudeThinkingExtractor(ReasoningExtractor):
    """Extrai thinking blocks da API Extended Thinking do Claude."""

    def __init__(self):
        super().__init__(
            provider="claude", model="claude"
        )  # Generic placeholder - actual model from config

    def supports_provider(self, provider: str, model: str) -> bool:
        """Suporta provedores Anthropic/Claude."""
        return provider in ["anthropic", "claude"] or "claude" in model.lower()

    def extract(
        self, response: Any, metadata: Optional[dict[str, Any]] = None
    ) -> Optional[ReasoningContent]:
        """
        Extrai thinking blocks do response do Claude.

        Response format esperado:
        {
            "content": [
                {
                    "type": "thinking",
                    "thinking": "Let me analyze this step by step...",
                    "signature": "WaUjzkypQ2mUEVM36O2TxuC06KN8xyfb..."
                },
                {
                    "type": "text",
                    "text": "Based on my analysis..."
                }
            ]
        }
        """
        start_time = datetime.now()

        try:
            thinking_blocks = []
            thinking_texts = []
            signature = None
            redacted = False

            # Extrair do response.message.content (lista de blocos)
            content_blocks = self._get_content_blocks(response)

            for block in content_blocks:
                if not isinstance(block, dict):
                    continue

                block_type = block.get("type")

                # Thinking block
                if block_type == "thinking":
                    thinking_text = block.get("thinking", "")
                    thinking_texts.append(thinking_text)
                    thinking_blocks.append(block)

                    if not signature and "signature" in block:
                        signature = block["signature"]

                # Redacted thinking
                elif block_type == "redacted_thinking":
                    redacted = True
                    self.logger.bind(event="CLAUDE_THINKING|REDACTED").warning(
                        "Thinking was redacted by safety filter"
                    )

            # Se encontrou thinking, criar ReasoningContent
            if thinking_texts or thinking_blocks:
                combined_text = "\n\n".join(thinking_texts) if thinking_texts else None

                extraction_time = (datetime.now() - start_time).total_seconds() * 1000

                return ReasoningContent(
                    provider="claude",
                    model=self.model,
                    timestamp=datetime.now(),
                    extraction_strategy="api",
                    thinking_text=combined_text,
                    thinking_blocks=thinking_blocks,
                    signature=signature,
                    redacted=redacted,
                    extraction_time_ms=extraction_time,
                )

            return None

        except Exception as e:
            self.logger.bind(event="CLAUDE_THINKING|EXTRACT_ERROR").error(
                f"Failed to extract Claude thinking: {e}"
            )
            return None

    def _get_content_blocks(self, response: Any) -> list[dict[str, Any]]:
        """Extrai content blocks do response (compatível com diferentes formatos)."""
        # LiteLLM response format
        if hasattr(response, "choices") and response.choices:
            message = response.choices[0].message
            if hasattr(message, "content") and isinstance(message.content, list):
                return message.content

        # Dict format direto
        if isinstance(response, dict):
            if "content" in response and isinstance(response["content"], list):
                return response["content"]

            if "choices" in response and response["choices"]:
                message = response["choices"][0].get("message", {})
                content = message.get("content", [])
                if isinstance(content, list):
                    return content

        return []


# ============================================================================
# Gemini Thinking Config Extractor
# ============================================================================


class GeminiThinkingExtractor(ReasoningExtractor):
    """Extrai thought summaries da API Thinking Config do Gemini."""

    def __init__(self):
        super().__init__(provider="gemini", model="gemini-2.5")

    def supports_provider(self, provider: str, model: str) -> bool:
        """Suporta provedores Google/Gemini."""
        return provider in ["google", "gemini"] or "gemini" in model.lower()

    def extract(
        self, response: Any, metadata: Optional[dict[str, Any]] = None
    ) -> Optional[ReasoningContent]:
        """
        Extrai thought summary do response do Gemini.

        Response format esperado:
        {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "...",
                        "thought_summary": "Analyzed the input and determined..."
                    }]
                }
            }]
        }
        """
        start_time = datetime.now()

        try:
            thought_summary = None

            # Tentar extrair do formato LiteLLM
            if hasattr(response, "choices") and response.choices:
                message = response.choices[0].message

                # Verificar se há thought_summary no message
                if hasattr(message, "thought_summary"):
                    thought_summary = message.thought_summary
                elif hasattr(message, "metadata") and isinstance(
                    message.metadata, dict
                ):
                    thought_summary = message.metadata.get("thought_summary")

            # Tentar formato dict direto
            elif isinstance(response, dict):
                candidates = response.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])

                    for part in parts:
                        if isinstance(part, dict) and "thought_summary" in part:
                            thought_summary = part["thought_summary"]
                            break

            # Se encontrou thought summary, criar ReasoningContent
            if thought_summary:
                extraction_time = (datetime.now() - start_time).total_seconds() * 1000

                return ReasoningContent(
                    provider="gemini",
                    model=self.model,
                    timestamp=datetime.now(),
                    extraction_strategy="api",
                    thought_summary=thought_summary,
                    extraction_time_ms=extraction_time,
                )

            return None

        except Exception as e:
            self.logger.bind(event="GEMINI_THINKING|EXTRACT_ERROR").error(
                f"Failed to extract Gemini thinking: {e}"
            )
            return None


# ============================================================================
# Response Field Extractor (Grok, DeepSeek)
# ============================================================================


class ResponseFieldExtractor(ReasoningExtractor):
    """Extrai reasoning_content field de modelos que expõem diretamente (Grok, DeepSeek)."""

    def __init__(self):
        super().__init__(provider="generic", model="response-field")

    def supports_provider(self, provider: str, model: str) -> bool:
        """Suporta Grok, DeepSeek e qualquer modelo com reasoning_content."""
        supported = ["grok", "deepseek", "x-ai"]
        return any(
            name in provider.lower() or name in model.lower() for name in supported
        )

    def extract(
        self, response: Any, metadata: Optional[dict[str, Any]] = None
    ) -> Optional[ReasoningContent]:
        """
        Extrai reasoning_content field do response.

        Response format esperado (LiteLLM):
        {
            "message": {
                "reasoning_content": "The capital of France is Paris.",
                "content": "Paris"
            }
        }
        """
        start_time = datetime.now()

        try:
            reasoning_text = None

            # LiteLLM format
            if hasattr(response, "choices") and response.choices:
                message = response.choices[0].message

                # reasoning_content field
                if hasattr(message, "reasoning_content"):
                    reasoning_text = message.reasoning_content

            # Dict format
            elif isinstance(response, dict):
                if "choices" in response and response["choices"]:
                    message = response["choices"][0].get("message", {})
                    reasoning_text = message.get("reasoning_content")
                elif "message" in response:
                    reasoning_text = response["message"].get("reasoning_content")

            # Se encontrou reasoning_content, criar ReasoningContent
            if reasoning_text:
                extraction_time = (datetime.now() - start_time).total_seconds() * 1000

                # Detectar provider do metadata ou model name
                provider = (
                    metadata.get("provider", "generic") if metadata else "generic"
                )
                model = metadata.get("model", self.model) if metadata else self.model

                return ReasoningContent(
                    provider=provider,
                    model=model,
                    timestamp=datetime.now(),
                    extraction_strategy="response_field",
                    thinking_text=reasoning_text,
                    extraction_time_ms=extraction_time,
                )

            return None

        except Exception as e:
            self.logger.bind(event="RESPONSE_FIELD|EXTRACT_ERROR").error(
                f"Failed to extract reasoning_content: {e}"
            )
            return None


# ============================================================================
# OpenAI Stats Extractor
# ============================================================================


class OpenAIStatsExtractor(ReasoningExtractor):
    """Extrai reasoning token statistics do OpenAI (GPT-5, o1)."""

    def __init__(self):
        super().__init__(provider="openai", model="gpt-5")

    def supports_provider(self, provider: str, model: str) -> bool:
        """Suporta provedores OpenAI."""
        return (
            provider == "openai" or model.startswith("gpt-") or model.startswith("o1-")
        )

    def extract(
        self, response: Any, metadata: Optional[dict[str, Any]] = None
    ) -> Optional[ReasoningContent]:
        """
        Extrai reasoning tokens do response do OpenAI.

        Response format esperado:
        {
            "usage": {
                "completion_tokens": 150,
                "completion_tokens_details": {
                    "reasoning_tokens": 45
                }
            }
        }

        NOTA: OpenAI não expõe o conteúdo do reasoning, apenas o token count.
        """
        start_time = datetime.now()

        try:
            reasoning_tokens = None
            reasoning_effort = None

            # LiteLLM format
            if hasattr(response, "usage"):
                usage = response.usage

                # completion_tokens_details.reasoning_tokens
                if hasattr(usage, "completion_tokens_details"):
                    details = usage.completion_tokens_details
                    if hasattr(details, "reasoning_tokens"):
                        reasoning_tokens = details.reasoning_tokens

            # Dict format
            elif isinstance(response, dict):
                usage = response.get("usage", {})
                details = usage.get("completion_tokens_details", {})
                reasoning_tokens = details.get("reasoning_tokens")

            # Extrair reasoning_effort do metadata (se foi configurado no request)
            if metadata:
                reasoning_effort = metadata.get("reasoning_effort")

            # Se encontrou reasoning tokens, criar ReasoningContent
            if reasoning_tokens is not None and reasoning_tokens > 0:
                extraction_time = (datetime.now() - start_time).total_seconds() * 1000

                model = metadata.get("model", self.model) if metadata else self.model

                return ReasoningContent(
                    provider="openai",
                    model=model,
                    timestamp=datetime.now(),
                    extraction_strategy="stats",
                    reasoning_tokens=reasoning_tokens,
                    reasoning_effort=reasoning_effort,
                    extraction_time_ms=extraction_time,
                )

            return None

        except Exception as e:
            self.logger.bind(event="OPENAI_STATS|EXTRACT_ERROR").error(
                f"Failed to extract OpenAI reasoning stats: {e}"
            )
            return None


# ============================================================================
# SDK Reasoning Extractor (OpenRouter / OpenAI Agents SDK)
# ============================================================================


class SDKReasoningExtractor(ReasoningExtractor):
    """
    Extrai reasoning de RunResult items do OpenAI Agents SDK.

    Suporta formato OpenRouter/SDK:
    {
        'type': 'reasoning',
        'summary': [{'text': '...', 'type': 'summary_text'}]
    }

    Este é um fallback universal que processa items retornados pelo SDK.
    """

    def __init__(self):
        super().__init__(provider="sdk", model="universal")

    def supports_provider(self, provider: str, model: str) -> bool:
        """
        Suporta qualquer provider como fallback universal.

        Este extractor é executado por último e processa items do SDK
        independente do provider original.
        """
        return True

    def extract(
        self, response: Any, metadata: Optional[dict[str, Any]] = None
    ) -> Optional[ReasoningContent]:
        """
        Extrai reasoning de items do OpenAI Agents SDK RunResult.

        Formato esperado (item do SDK):
        {
            'id': '__fake_id__',
            'type': 'reasoning',
            'summary': [
                {'text': 'Texto do reasoning...', 'type': 'summary_text'}
            ]
        }
        """
        start_time = datetime.now()

        try:
            self.logger.bind(event="SDK_REASONING|EXTRACT_START").debug(
                "Starting SDK reasoning extraction",
                response_type=type(response).__name__,
                is_dict=isinstance(response, dict),
            )

            # Processar dict format (item do SDK)
            if not isinstance(response, dict):
                self.logger.bind(event="SDK_REASONING|NOT_DICT").debug(
                    "Response is not dict, skipping"
                )
                return None

            item_type = response.get("type")
            self.logger.bind(event="SDK_REASONING|TYPE_CHECK").debug(
                f"Item type: {item_type}"
            )

            # Verificar se é um reasoning item
            if item_type != "reasoning":
                self.logger.bind(event="SDK_REASONING|NOT_REASONING").debug(
                    f"Item type '{item_type}' is not reasoning, skipping"
                )
                return None

            # Extrair summary text
            summary = response.get("summary", [])
            self.logger.bind(event="SDK_REASONING|SUMMARY_CHECK").debug(
                "Checking summary",
                has_summary=bool(summary),
                is_list=isinstance(summary, list),
                summary_length=len(summary) if isinstance(summary, list) else 0,
            )

            if not summary or not isinstance(summary, list):
                self.logger.bind(event="SDK_REASONING|NO_SUMMARY").warning(
                    "No summary found or summary is not a list"
                )
                return None

            # Extrair texto do primeiro summary item
            thinking_text = None
            for idx, summary_item in enumerate(summary):
                # Suportar tanto dict quanto objetos SDK (Summary)
                text = None
                item_type = None

                if isinstance(summary_item, dict):
                    # Dict format
                    text = summary_item.get("text")
                    item_type = summary_item.get("type")
                elif hasattr(summary_item, "text") and hasattr(summary_item, "type"):
                    # Object format (OpenAI SDK Summary)
                    text = summary_item.text
                    item_type = summary_item.type

                self.logger.bind(event="SDK_REASONING|TEXT_CHECK").debug(
                    f"Summary item {idx}",
                    has_text=bool(text),
                    text_length=len(text) if text else 0,
                    item_type=item_type,
                    item_class=type(summary_item).__name__,
                )

                if text and item_type == "summary_text":
                    thinking_text = text
                    self.logger.bind(event="SDK_REASONING|TEXT_FOUND").info(
                        f"✅ Found thinking text in summary item {idx}",
                        text_length=len(text),
                    )
                    break

            if not thinking_text:
                self.logger.bind(event="SDK_REASONING|NO_TEXT").warning(
                    "No thinking text found in summary items"
                )
                return None

            # Extrair provider/model do metadata
            provider = (
                metadata.get("provider", "openrouter") if metadata else "openrouter"
            )
            model = metadata.get("model", "unknown") if metadata else "unknown"

            extraction_time = (datetime.now() - start_time).total_seconds() * 1000

            self.logger.bind(event="SDK_REASONING|EXTRACTED").info(
                "Reasoning extracted from SDK item",
                provider=provider,
                model=model,
                text_length=len(thinking_text),
            )

            return ReasoningContent(
                provider=provider,
                model=model,
                timestamp=datetime.now(),
                extraction_strategy="sdk_items",
                thinking_text=thinking_text,
                extraction_time_ms=extraction_time,
            )

        except Exception as e:
            self.logger.bind(event="SDK_REASONING|EXTRACT_ERROR").error(
                f"Failed to extract SDK reasoning: {e}"
            )
            return None


# ============================================================================
# Universal Reasoning Capture (Orchestrator)
# ============================================================================


class UniversalReasoningCapture:
    """
    Orquestrador universal de captura de reasoning.

    Detecta automaticamente o provider e aplica a estratégia apropriada.
    """

    def __init__(self):
        self.logger = logger.bind(component="UniversalReasoningCapture")

        # Registrar extractors
        # IMPORTANTE: SDKReasoningExtractor é fallback universal (último)
        self.extractors: list[ReasoningExtractor] = [
            ClaudeThinkingExtractor(),
            GeminiThinkingExtractor(),
            ResponseFieldExtractor(),
            OpenAIStatsExtractor(),
            SDKReasoningExtractor(),  # Fallback universal para SDK items
        ]

        # Buffer de reasoning capturado (thread-safe)
        self._buffer: list[ReasoningContent] = []

        self.logger.bind(event="UNIVERSAL_REASONING|INIT").info(
            f"Universal reasoning capture initialized with {len(self.extractors)} extractors"
        )

    def extract(
        self,
        response: Any,
        provider: str,
        model: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[ReasoningContent]:
        """
        Extrai reasoning do response usando o extractor apropriado.

        Args:
            response: Response object do LLM
            provider: Nome do provider (openai, anthropic, google, etc.)
            model: Nome do modelo
            metadata: Metadados adicionais

        Returns:
            ReasoningContent se reasoning foi capturado, None caso contrário
        """
        # Adicionar provider/model ao metadata
        if metadata is None:
            metadata = {}
        metadata.update({"provider": provider, "model": model})

        # Tentar cada extractor até encontrar um que suporte
        for extractor in self.extractors:
            if extractor.supports_provider(provider, model):
                self.logger.bind(event="UNIVERSAL_REASONING|TRYING_EXTRACTOR").debug(
                    f"Trying {extractor.__class__.__name__} for {provider}/{model}"
                )

                reasoning = extractor.extract(response, metadata)

                if reasoning and reasoning.has_content():
                    # Adicionar ao buffer
                    self._buffer.append(reasoning)

                    self.logger.bind(event="UNIVERSAL_REASONING|CAPTURED").info(
                        f"Reasoning captured via {extractor.__class__.__name__}",
                        provider=provider,
                        model=model,
                        strategy=reasoning.extraction_strategy,
                        has_text=bool(reasoning.thinking_text),
                        has_blocks=bool(reasoning.thinking_blocks),
                        tokens=reasoning.reasoning_tokens,
                    )

                    return reasoning

        self.logger.bind(event="UNIVERSAL_REASONING|NOT_FOUND").debug(
            f"No reasoning found for {provider}/{model}"
        )

        return None

    def get_captured(self) -> list[ReasoningContent]:
        """Retorna todo reasoning capturado."""
        return self._buffer.copy()

    def clear(self) -> None:
        """Limpa o buffer de reasoning."""
        count = len(self._buffer)
        self._buffer.clear()

        self.logger.bind(event="UNIVERSAL_REASONING|CLEAR").debug(
            f"Cleared {count} reasoning entries from buffer"
        )

    def get_latest(self) -> Optional[ReasoningContent]:
        """Retorna o reasoning mais recente capturado."""
        return self._buffer[-1] if self._buffer else None


# ============================================================================
# Global Instance & Convenience Functions
# ============================================================================

_global_capture: Optional[UniversalReasoningCapture] = None


def get_universal_capture() -> UniversalReasoningCapture:
    """Obtém a instância global do universal reasoning capture."""
    global _global_capture
    if _global_capture is None:
        _global_capture = UniversalReasoningCapture()
    return _global_capture


def capture_reasoning(
    response: Any, provider: str, model: str, metadata: Optional[dict[str, Any]] = None
) -> Optional[ReasoningContent]:
    """Convenience function para capturar reasoning."""
    capture = get_universal_capture()
    return capture.extract(response, provider, model, metadata)


def get_captured_reasoning() -> list[ReasoningContent]:
    """Convenience function para obter todo reasoning capturado."""
    capture = get_universal_capture()
    return capture.get_captured()


def clear_reasoning() -> None:
    """Convenience function para limpar buffer de reasoning."""
    capture = get_universal_capture()
    capture.clear()


def get_latest_reasoning() -> Optional[ReasoningContent]:
    """Convenience function para obter último reasoning capturado."""
    capture = get_universal_capture()
    return capture.get_latest()
