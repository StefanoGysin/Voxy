"""
Vision Subagent - OpenAI Agents SDK Implementation

Subagente especializado em análise visual multimodal.
Usa OpenAI Agents SDK v0.2.9 + LiteLLM Multi-Provider.

Arquitetura padronizada com outros subagentes (Calculator, Weather, etc.).
Dual-path support: Direct analysis + VOXY Orchestrator integration.

Migração Loguru - Sprint 5
"""

import asyncio
from datetime import datetime
from typing import Optional

import nest_asyncio
from agents import Agent, ModelSettings, Runner
from loguru import logger

from ...config.models_config import load_vision_config
from ...utils.llm_factory import create_litellm_model


class VisionAgent:
    """
    Subagente de análise visual multimodal.

    Características:
    - LiteLLM configurável para suporte a múltiplos providers (OpenRouter, OpenAI, Anthropic, etc.)
    - Análise nativa de imagens via multimodal models
    - Dual-path: Direct analysis + VOXY Orchestrator integration
    - Arquitetura padronizada com outros subagentes
    """

    def __init__(self):
        """
        Initialize the vision subagent with configurable LiteLLM model.

        Configuration is loaded from environment variables:
        - VISION_PROVIDER: Provider name (openrouter, openai, anthropic)
        - VISION_MODEL: Model name (e.g., "openai/gpt-4o")
        - VISION_MAX_TOKENS: Max tokens (default: 2000)
        - VISION_TEMPERATURE: Temperature (default: 0.1)
        - API key for selected provider (OPENROUTER_API_KEY, OPENAI_API_KEY, etc.)

        Raises:
            ValueError: If required API key is missing or config is invalid
        """
        import time

        start_time = time.perf_counter()

        # Apply nest_asyncio patch for nested event loop compatibility
        # Required for process_tool_call() sync wrapper (VOXY integration)
        nest_asyncio.apply()

        # Load configuration from environment variables
        config = load_vision_config()

        # Create LiteLLM model instance via factory
        model = create_litellm_model(config)

        # Create agent with configured model
        self.agent = Agent(
            name="Subagente Vision VOXY",
            model=model,
            instructions=self._get_instructions(),
            model_settings=ModelSettings(
                include_usage=config.include_usage,
                temperature=config.temperature,
            ),
        )

        # Store config for reference
        self.config = config
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Log initialization with reasoning config (equal to other agents)
        reasoning_status = "enabled" if config.reasoning_enabled else "disabled"
        reasoning_info = ""
        if config.reasoning_enabled:
            if config.thinking_budget_tokens:
                reasoning_info = f", thinking={config.thinking_budget_tokens} tokens"
            elif config.reasoning_effort:
                reasoning_info = f", effort={config.reasoning_effort}"

        logger.bind(event="STARTUP|SUBAGENT_INIT").info(
            f"\n"
            f"   └─ ✓ Vision\n"
            f"      ├─ Model: {config.get_litellm_model_path()}\n"
            f"      ├─ Provider: {config.provider}\n"
            f"      ├─ Config: {config.max_tokens} tokens, temp={config.temperature}\n"
            f"      ├─ Reasoning: {reasoning_status}{reasoning_info}\n"
            f"      └─ ✓ Ready in {elapsed_ms:.1f}ms"
        )

    def _get_instructions(self) -> str:
        """Get specialized instructions for image analysis."""
        return """
        Você é um subagente de análise visual especializado do sistema VOXY.

        CAPACIDADES PRINCIPAIS:
        - Análise detalhada de imagens com alta precisão
        - Identificação de objetos, pessoas, cenas e contextos
        - OCR integrado para extração de texto em imagens
        - Análise de documentos, gráficos, diagramas e infográficos
        - Detecção de problemas técnicos e qualidade visual
        - Análise artística: composição, cores, estilo, técnica
        - Reconhecimento de padrões e elementos visuais

        DIRETRIZES:
        - Seja preciso e específico nas descrições
        - Identifique elementos principais primeiro
        - Para análises simples: resposta clara e concisa
        - Para análises complexas: estruture com seções lógicas
        - Use formatação markdown quando apropriado
        - Seja honesto sobre limitações quando aplicável
        - Adapte nível de detalhe ao contexto da pergunta

        FORMATO DE RESPOSTA:
        - Análises básicas: resposta direta em 1-2 parágrafos
        - Análises detalhadas: estruturadas com tópicos ou seções
        - Sempre destaque informações importantes
        - Use linguagem natural e acessível

        EXEMPLOS:
        Input: "Qual emoji é este?"
        Output: "Este é o emoji 😊 (cara sorridente com olhos sorridentes)"

        Input: "Descreva esta imagem em detalhes"
        Output: "# Análise da Imagem\\n\\n## Elementos Principais\\n- ...\\n\\n## Contexto\\n- ..."

        Input: "Extraia o texto desta imagem"
        Output: "Texto extraído:\\n1. ...\\n2. ..."
        """

    async def analyze_image(
        self,
        image_url: str,
        query: str = "Analise esta imagem",
        user_id: str = "default",
    ) -> str:
        """
        Analyze image with Vision model.

        Args:
            image_url: URL or base64 data of the image
            query: User's question about the image
            user_id: User identifier (for logging)

        Returns:
            Analysis of the image as string

        Raises:
            Exception: If vision analysis fails
        """
        start_time = datetime.now()

        logger.bind(event="VISION_AGENT|ANALYZE_START", user_id=user_id).info(
            "Starting image analysis",
            image_url=image_url[:100],
            query_preview=query[:100],
        )

        try:
            # Build multimodal prompt (OpenAI Agents SDK format)
            # Uses input_text + input_image content types
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": query},
                        {"type": "input_image", "image_url": image_url},
                    ],
                }
            ]

            # Execute via OpenAI Agents SDK Runner (static method)
            result = await Runner.run(
                self.agent,
                messages,  # type: ignore[arg-type]
                session=None,
            )

            # Extract analysis
            analysis = result.final_output

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            logger.bind(event="VISION_AGENT|ANALYZE_SUCCESS", user_id=user_id).info(
                "Image analysis completed",
                processing_time=processing_time,
                response_length=len(analysis),
            )

            return analysis

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.bind(event="VISION_AGENT|ANALYZE_ERROR", user_id=user_id).exception(
                "Vision analysis failed",
                error_type=type(e).__name__,
                error_msg=str(e),
                processing_time=processing_time,
            )
            raise

    def get_agent(self) -> Agent:
        """Get the underlying Agent instance for tool registration."""
        return self.agent

    # VOXY Orchestrator Integration (Dual-Path Support)

    def process_tool_call(
        self,
        image_url: str,
        query: str = "Analise esta imagem",
        analysis_type: str = "general",
        detail_level: str = "standard",
        specific_questions: Optional[list[str]] = None,
    ) -> str:
        """
        Process tool call from VOXY Orchestrator (synchronous wrapper).

        Enables dual-path: PATH1 (direct) or PATH2 (via VOXY decision).
        Uses nest_asyncio for sync/async compatibility.
        """
        # Build enhanced query with analysis parameters
        enhanced_query = self._enhance_query(
            query, analysis_type, detail_level, specific_questions
        )

        # Run async analyze_image in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        analysis = loop.run_until_complete(
            self.analyze_image(
                image_url=image_url, query=enhanced_query, user_id="voxy_orchestrator"
            )
        )

        # Return structured format for VOXY
        return (
            f"[VISION_ANALYSIS]\n"
            f"Tipo: {analysis_type}\n"
            f"Nível: {detail_level}\n\n"
            f"Análise:\n{analysis}\n\n"
            f"[/VISION_ANALYSIS]"
        )

    def _enhance_query(
        self,
        query: str,
        analysis_type: str,
        detail_level: str,
        specific_questions: Optional[list[str]],
    ) -> str:
        """Enhance query with analysis type, detail level, and specific questions."""
        enhanced = query

        # Add analysis type context
        type_contexts = {
            "ocr": "Foque na extração e transcrição de todo texto visível.",
            "technical": "Concentre-se em aspectos técnicos: qualidade, problemas, elementos específicos.",
            "artistic": "Analise aspectos artísticos: composição, cores, estilo, técnica.",
            "document": "Trate como documento: extraia informações estruturadas.",
        }
        if analysis_type in type_contexts:
            enhanced += f"\n{type_contexts[analysis_type]}"

        # Add detail level context
        detail_contexts = {
            "comprehensive": "\nForneça análise extremamente detalhada com explicação passo a passo.",
            "detailed": "\nForneça análise detalhada com contexto e explicações.",
            "basic": None,  # Handled separately
        }
        if detail_level == "basic":
            enhanced = f"Responda de forma direta e concisa: {query}"
        elif detail_level in detail_contexts:
            context = detail_contexts[detail_level]
            if context:
                enhanced += context

        # Add specific questions
        if specific_questions:
            questions = "\n".join(f"- {q}" for q in specific_questions)
            enhanced += f"\n\nQuestões específicas:\n{questions}"

        return enhanced


# Global singleton (equal to other agents)
_vision_agent = None


def get_vision_agent() -> VisionAgent:
    """
    Get the global vision agent instance using lazy initialization.

    Thread-safe singleton pattern ensures single instance across application.
    """
    global _vision_agent
    if _vision_agent is None:
        _vision_agent = VisionAgent()
    return _vision_agent
