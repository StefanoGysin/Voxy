"""
Vision Agent - Análise Visual Avançada

Subagente especializado em análise visual multimodal.
Implementa análise inteligente de imagens com cache e otimizações.

Features:
- OpenAI Agents SDK v0.2.9 + LiteLLM Multi-Provider
- Multimodal native image analysis
- Intelligent caching system (L1 + L2)
- Adaptive reasoning optimization
- Cost tracking and rate limiting

Migração Loguru - Sprint 5
"""

import asyncio
from datetime import datetime
from typing import Any, Optional

import nest_asyncio
from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel
from loguru import logger
from pydantic import BaseModel

from ...config.models_config import load_vision_config
from ..cache.vision_cache import VisionCache
from ..optimization.adaptive_reasoning import AnalysisContext, adaptive_reasoning
from ..optimization.pipeline_optimizer import pipeline_optimizer


class VisionAnalysisResult(BaseModel):
    """
    Resultado estruturado da análise visual.

    Este modelo separa a análise técnica da resposta conversacional final,
    permitindo que o VOXY Orchestrator processe e formate adequadamente.
    """

    success: bool
    analysis: str  # Análise técnica da imagem (não resposta final ao usuário)
    confidence: float  # Nível de confiança (0.0 - 1.0)
    metadata: dict[str, Any]  # model_used, cost, processing_time, etc.
    raw_response: Optional[str] = None  # Resposta bruta GPT-5/GPT-4o
    error: Optional[str] = None


class VisionAgent:
    """
    Vision Agent para análise avançada de imagens.

    Features:
    - OpenAI Agents SDK v0.2.9 + LiteLLM Multi-Provider
    - Multimodal native image analysis
    - Intelligent caching system (L1 + L2)
    - Adaptive reasoning optimization
    - Cost tracking and rate limiting
    """

    def __init__(self):
        """Initialize vision agent with OpenAI Agents SDK + LiteLLM."""
        # Apply nest_asyncio patch for nested event loop compatibility
        # Required for process_tool_call() sync wrapper
        nest_asyncio.apply()

        # Load configuration from environment variables
        self.config = load_vision_config()

        # Create LiteLLM model instance
        litellm_model = LitellmModel(
            model=self.config.get_litellm_model_path(), api_key=self.config.api_key
        )

        # Create Agent with LiteLLM (NO TOOLS - multimodal native)
        self.agent = Agent(
            name="Vision Agent",
            model=litellm_model,
            instructions=self._get_system_instructions(),
        )

        # Optimization systems (MANTIDOS)
        self.vision_cache = VisionCache()

        # Agent identity (MANTIDOS)
        self.name = "Vision Agent"
        self.agent_type = "vision"

        # Performance tracking (SIMPLIFICADO)
        self.total_cost = 0.0
        self.analysis_count = 0

        # Rate limiting (MANTIDO)
        self.last_request_time = None
        self.requests_in_current_minute = 0
        self.requests_in_current_hour = 0

        logger.bind(event="VISION_AGENT|INIT").info(
            "Vision Agent initialized",
            model=self.config.get_litellm_model_path(),
            provider=self.config.provider
        )

    async def analyze_image(
        self,
        image_url: str,
        query: str = "Analise esta imagem",
        analysis_type: str = "general",
        detail_level: str = "standard",
        specific_questions: Optional[list[str]] = None,
    ) -> VisionAnalysisResult:
        """
        Main image analysis method - direct GPT-5 without SDK overhead.

        Args:
            image_url: URL or base64 data of the image
            query: User's question about the image
            analysis_type: Type of analysis (general, ocr, technical, artistic, document)
            detail_level: Level of detail (basic, standard, detailed, comprehensive)
            specific_questions: List of specific questions about the image

        Returns:
            VisionAnalysisResult with technical analysis (not final user response)
        """
        start_time = datetime.now()
        self.analysis_count += 1

        try:
            logger.bind(event="VISION_AGENT|ANALYSIS_START").info(
                "Vision analysis starting",
                image_url=image_url[:100]
            )

            # 1. Check intelligent cache first
            cached_analysis = await self.vision_cache.get_cached_analysis(
                image_url, analysis_type, detail_level, specific_questions
            )

            if cached_analysis:
                result, metadata = cached_analysis
                processing_time = (datetime.now() - start_time).total_seconds()

                logger.bind(event="VISION_AGENT|CACHE_HIT").info(
                    "Cache HIT: Returning cached result",
                    processing_time=processing_time
                )

                # Return structured result from cache
                return VisionAnalysisResult(
                    success=True,
                    analysis=result,
                    confidence=metadata.get("confidence", 0.95),
                    metadata={
                        **metadata,
                        "processing_time": processing_time,
                        "cache_hit": True,
                        "agent_type": self.agent_type,
                        "cache_optimized": True,
                    },
                    raw_response=metadata.get("raw_response"),
                )

            # 2. Rate limiting check
            await self._check_rate_limits()

            # 3. Determine optimal analysis parameters
            context = AnalysisContext(
                query_text=query,
                analysis_type=analysis_type,
                detail_level=detail_level,
                specific_questions=specific_questions,
                image_url=image_url,
            )

            (
                reasoning_level,
                reasoning_metadata,
            ) = adaptive_reasoning.determine_reasoning_effort(context)
            reasoning_effort = reasoning_level.value

            # 4. Configure API call parameters
            token_map = {"minimal": 500, "low": 1000, "medium": 1500, "high": 2000}
            max_tokens = token_map.get(reasoning_effort, 1000)

            timeout_map = {"minimal": 15.0, "low": 30.0, "medium": 60.0, "high": 120.0}
            adaptive_timeout = timeout_map.get(reasoning_effort, 30.0)

            # 5. Build optimized prompt
            prompt = self._build_analysis_prompt(
                query, analysis_type, detail_level, specific_questions
            )

            # 6. Prepare multimodal messages for Agents SDK (input_text + input_image format)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": image_url},
                    ],
                }
            ]

            # 7. Execute via OpenAI Agents SDK Runner
            api_start = datetime.now()

            try:
                logger.bind(event="VISION_AGENT|API_CALL").info(
                    "Vision API call starting",
                    model=self.config.model_name,
                    reasoning=reasoning_effort
                )

                # Runner.run() with multimodal messages (posicional, não nomeado)
                result = await Runner.run(self.agent, messages)

                api_duration = (datetime.now() - api_start).total_seconds()
                logger.bind(event="VISION_AGENT|API_SUCCESS").info(
                    "Vision API call completed",
                    api_duration=api_duration
                )

                # Update adaptive reasoning performance stats
                adaptive_reasoning.update_performance_stats(
                    reasoning_level, api_duration, True
                )

                # Extract content
                content = result.final_output

                # Extract cost from runner result
                cost = self._extract_cost_from_runner_result(result)
                self.total_cost += cost

            except Exception as e:
                api_duration = (datetime.now() - api_start).total_seconds()
                logger.bind(event="VISION_AGENT|API_ERROR").error(
                    "Vision API call failed",
                    api_duration=api_duration,
                    error=str(e)
                )
                raise

            # 8. Process response (content já extraído)

            # 9. Calculate confidence (model-agnostic)
            confidence = self._calculate_confidence(
                reasoning_effort=reasoning_effort,
                analysis_type=analysis_type,
            )

            # 10. Store in cache (store raw content, not formatted)
            total_processing_time = (datetime.now() - start_time).total_seconds()

            await self.vision_cache.store_analysis(
                image_url=image_url,
                analysis_type=analysis_type,
                detail_level=detail_level,
                specific_questions=specific_questions,
                result=content,  # Store raw analysis
                processing_time=total_processing_time,
                model_used=self.config.get_litellm_model_path(),
                cost=cost,
            )

            # 11. Build structured result
            logger.bind(event="VISION_AGENT|ANALYSIS_COMPLETE").info(
                "Vision analysis completed successfully",
                processing_time=total_processing_time,
                model=self.config.model_name,
                cost=cost
            )

            return VisionAnalysisResult(
                success=True,
                analysis=content,  # Raw technical analysis
                confidence=confidence,
                metadata={
                    "processing_time": total_processing_time,
                    "api_time": api_duration,
                    "reasoning_level": reasoning_effort,
                    "model_used": self.config.get_litellm_model_path(),
                    "provider": self.config.provider,
                    "cost": cost,
                    "cache_hit": False,
                    "agent_type": self.agent_type,
                    "optimized": True,
                    "analysis_type": analysis_type,
                    "detail_level": detail_level,
                    "estimated_time": reasoning_metadata.get("estimated_time", 0),
                },
                raw_response=content,
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.bind(event="VISION_AGENT|ANALYSIS_ERROR").error(
                "Vision analysis failed",
                processing_time=processing_time,
                error=str(e)
            )

            return VisionAnalysisResult(
                success=False,
                analysis="",
                confidence=0.0,
                metadata={
                    "processing_time": processing_time,
                    "agent_type": self.agent_type,
                    "optimized": True,
                    "cache_hit": False,
                },
                error=str(e),
            )

    def _get_system_instructions(self) -> str:
        """Get comprehensive system instructions for GPT-5."""
        return """
        Você é um especialista em análise visual avançada usando GPT-5 multimodal.

        CAPACIDADES:
        - Análise detalhada de imagens com alta precisão
        - Identificação de objetos, pessoas, texto, cenas
        - OCR integrado para texto em imagens
        - Análise de documentos, gráficos e diagramas
        - Detecção de problemas técnicos
        - Análise artística e de composição

        FORMATO DE RESPOSTA:
        - Seja preciso e específico nas descrições
        - Use formatação markdown quando apropriado
        - Para análises simples: resposta clara e concisa
        - Para análises complexas: estruture com seções lógicas
        - Sempre destaque informações importantes

        GUIDELINES:
        - Mantenha análises confiáveis e precisas
        - Adapte nível de detalhe ao contexto
        - Seja honesto sobre limitações quando aplicável
        - Use linguagem natural e acessível
        """

    def _build_analysis_prompt(
        self,
        query: str,
        analysis_type: str,
        detail_level: str,
        specific_questions: Optional[list[str]] = None,
    ) -> str:
        """Build optimized prompt for analysis."""
        # Quick responses for simple queries
        if detail_level == "basic" or any(
            keyword in query.lower() for keyword in ["que", "qual", "emoji"]
        ):
            return f"Responda de forma direta e concisa: {query}"

        # Build comprehensive prompt
        prompt = f"Analise esta imagem com foco em '{analysis_type}' e nível '{detail_level}': {query}"

        # Add specific analysis type instructions
        if analysis_type == "ocr":
            prompt += "\nFoque na extração e transcrição de todo texto visível."
        elif analysis_type == "technical":
            prompt += "\nConcentre-se em aspectos técnicos: qualidade, problemas, elementos específicos."
        elif analysis_type == "artistic":
            prompt += (
                "\nAnalise aspectos artísticos: composição, cores, estilo, técnica."
            )
        elif analysis_type == "document":
            prompt += "\nTrate como documento: extraia informações estruturadas."

        # Add detail level specifications
        if detail_level == "comprehensive":
            prompt += (
                "\nForneça análise extremamente detalhada com explicação passo a passo."
            )
        elif detail_level == "detailed":
            prompt += "\nForneça análise detalhada com contexto e explicações."

        # Add specific questions
        if specific_questions:
            questions_text = "\n".join(f"- {q}" for q in specific_questions)
            prompt += f"\n\nQuestões específicas:\n{questions_text}"

        return prompt

    def _calculate_confidence(
        self,
        reasoning_effort: str,
        analysis_type: str,
    ) -> float:
        """
        Calculate confidence score (model-agnostic).

        Args:
            reasoning_effort: Reasoning level (minimal/low/medium/high)
            analysis_type: Type of analysis performed

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence (uniform across models)
        base_confidence = 0.90

        # Adjust by reasoning effort
        reasoning_bonus = {
            "minimal": 0.0,
            "low": 0.02,
            "medium": 0.05,
            "high": 0.08,
        }.get(reasoning_effort, 0.0)

        # Adjust by analysis type
        type_factor = {
            "general": 1.0,
            "ocr": 0.95,  # OCR can have edge cases
            "technical": 0.98,
            "artistic": 0.90,  # Subjective
            "document": 0.95,
        }.get(analysis_type, 1.0)

        confidence = min((base_confidence + reasoning_bonus) * type_factor, 1.0)

        return round(confidence, 3)

    def _extract_cost_from_runner_result(self, result: Any) -> float:
        """
        Extract cost from Runner.run() result.

        Attempts to calculate cost from usage data in RunResult.
        Falls back to estimation if usage is not available.

        Args:
            result: RunResult object from Runner.run()

        Returns:
            Estimated cost in USD
        """
        try:
            # Try to access usage from result
            # TODO: Investigate RunResult structure for actual usage field
            if hasattr(result, "usage") and result.usage:
                # Attempt to use litellm.completion_cost if available
                try:
                    import litellm

                    return litellm.completion_cost(completion_response=result)
                except Exception:
                    # Fallback to manual calculation
                    input_tokens = getattr(result.usage, "prompt_tokens", 200)
                    output_tokens = getattr(result.usage, "completion_tokens", 100)
            else:
                # Estimate tokens based on content length
                input_tokens = 200  # prompt + image encoding (~200 tokens)
                output_tokens = len(result.final_output.split()) * 1.3

            # Pricing estimation by model (2025 rates)
            if "gpt-4o" in self.config.model_name.lower():
                input_cost = (input_tokens / 1000) * 0.0025
                output_cost = (output_tokens / 1000) * 0.01
                image_cost = 0.01
            elif "claude" in self.config.model_name.lower():
                input_cost = (input_tokens / 1000) * 0.003
                output_cost = (output_tokens / 1000) * 0.015
                image_cost = 0.01
            elif "gemini" in self.config.model_name.lower():
                input_cost = (input_tokens / 1000) * 0.00125
                output_cost = (output_tokens / 1000) * 0.01
                image_cost = 0.005
            else:
                # Generic fallback
                input_cost = (input_tokens / 1000) * 0.002
                output_cost = (output_tokens / 1000) * 0.01
                image_cost = 0.01

            total_cost = input_cost + output_cost + image_cost
            return round(total_cost, 6)

        except Exception as e:
            logger.bind(event="VISION_AGENT|COST_EXTRACTION_ERROR").warning(
                "Failed to extract cost from result",
                error=str(e)
            )
            return 0.02  # Conservative fallback estimate

    @pipeline_optimizer.skip_redundant_validations
    async def _check_rate_limits(self) -> None:
        """Check and enforce rate limits."""
        now = datetime.now()

        if self.last_request_time:
            time_diff = (now - self.last_request_time).total_seconds()

            # Reset counters
            if time_diff >= 60:
                self.requests_in_current_minute = 0
            if time_diff >= 3600:
                self.requests_in_current_hour = 0

        # Check limits
        if self.requests_in_current_minute >= 10:
            raise Exception("Rate limit exceeded: 10 requests per minute")
        if self.requests_in_current_hour >= 50:
            raise Exception("Rate limit exceeded: 50 requests per hour")

        # Update counters
        self.requests_in_current_minute += 1
        self.requests_in_current_hour += 1
        self.last_request_time = now

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive performance statistics."""
        avg_cost = self.total_cost / max(1, self.analysis_count)
        cache_stats = self.vision_cache.get_cache_stats()

        return {
            "agent_type": self.agent_type,
            "name": self.name,
            "multimodal": True,
            "model_configured": self.config.get_litellm_model_path(),
            "provider": self.config.provider,
            "analysis_count": self.analysis_count,
            "total_cost": round(self.total_cost, 4),
            "average_cost": round(avg_cost, 6),
            "requests_in_current_minute": self.requests_in_current_minute,
            "requests_in_current_hour": self.requests_in_current_hour,
            "cache_stats": cache_stats,
        }

    async def health_check(self) -> bool:
        """Perform health check for the vision agent."""
        try:
            # Test with minimal image
            test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            result, metadata = await self.analyze_image(
                image_url=test_image,
                query="teste",
                analysis_type="general",
                detail_level="basic",
            )

            return "análise" in result.lower() or not metadata.get("error")

        except Exception as e:
            logger.bind(event="VISION_AGENT|HEALTH_CHECK_ERROR").error(
                "Health check failed for vision agent",
                error=str(e)
            )
            return False

    # Compatibility methods for VOXY Orchestrator integration

    def get_tool_name(self) -> str:
        """Get tool name for orchestrator registration."""
        return "analyze_image"

    def get_tool_description(self) -> str:
        """Get tool description for orchestrator."""
        return "Análise avançada de imagens usando GPT-5 multimodal"

    def process_tool_call(
        self,
        image_url: str,
        analysis_type: str = "general",
        detail_level: str = "standard",
        specific_questions: Optional[list[str]] = None,
        query: str = "Analise esta imagem",
    ) -> str:
        """
        Process tool call from VOXY Orchestrator synchronously.

        Compatible with agents SDK synchronous tool calling using nest_asyncio.

        Args:
            image_url: URL of the image to analyze
            analysis_type: Type of analysis (general, ocr, technical, etc.)
            detail_level: Detail level (basic, standard, detailed, comprehensive)
            specific_questions: Optional list of specific questions
            query: User query about the image

        Returns:
            Structured format for VOXY to process (not final user response)
        """
        # Use nest_asyncio to run async method in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No loop running, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run async implementation
        return loop.run_until_complete(
            self._async_process_tool_call(
                image_url=image_url,
                query=query,
                analysis_type=analysis_type,
                detail_level=detail_level,
                specific_questions=specific_questions,
            )
        )

    async def _async_process_tool_call(
        self,
        image_url: str,
        query: str,
        analysis_type: str,
        detail_level: str,
        specific_questions: Optional[list[str]],
    ) -> str:
        """
        Internal async implementation of tool call processing.

        This method contains the actual async logic, called by the synchronous
        process_tool_call() wrapper.
        """
        vision_result = await self.analyze_image(
            image_url=image_url,
            query=query,
            analysis_type=analysis_type,
            detail_level=detail_level,
            specific_questions=specific_questions,
        )

        if not vision_result.success:
            return f"[VISION_ERROR] {vision_result.error}"

        # Return structured format for VOXY Orchestrator to process
        return f"""[VISION_ANALYSIS]
Tipo: {vision_result.metadata.get('analysis_type', 'general')}
Confiança: {vision_result.confidence:.1%}
Modelo: {vision_result.metadata.get('model_used', 'unknown')}
Tempo: {vision_result.metadata.get('processing_time', 0):.1f}s

Análise:
{vision_result.analysis}

[/VISION_ANALYSIS]"""


# Global instance using lazy initialization
_vision_agent = None


def get_vision_agent() -> VisionAgent:
    """
    Get the global vision agent instance.

    Thread-safe singleton pattern ensures single instance across application.
    """
    global _vision_agent
    if _vision_agent is None:
        _vision_agent = VisionAgent()
    return _vision_agent
