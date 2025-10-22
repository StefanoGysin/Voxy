"""
Sistema de Teste Isolado para Subagentes VOXY

Permite testar individualmente cada subagente (Translator, Corrector, Weather,
Calculator, Vision) sem passar pelo fluxo completo do VOXY Orchestrator.

Características:
- Teste direto sem overhead do VOXY (economia de ~37s no Vision)
- Bypass de autenticação, cache e rate limiting (configurável)
- Suporte assíncrono completo
- Resposta padronizada com metadata detalhado
- Compatível com CI/CD e testes automatizados

Uso Básico:
    tester = SubagentTester()
    result = await tester.test_subagent(
        agent_name="translator",
        input_data={"text": "Hello world", "target_language": "pt-BR"}
    )
    print(f"Success: {result.success}, Response: {result.response}")
"""

import logging
from datetime import datetime
from typing import Any, Optional

from agents import Runner
from pydantic import BaseModel

from ..config.models_config import load_orchestrator_config
from ..core.subagents import (
    get_calculator_agent,
    get_corrector_agent,
    get_translator_agent,
    get_weather_agent,
)
from ..core.subagents.vision_agent import VisionAgent, get_vision_agent
from ..main import VOXYSystem

logger = logging.getLogger(__name__)


class TestMetadata(BaseModel):
    """Metadados detalhados da execução do teste."""

    processing_time: float
    model_used: str
    tokens_used: Optional[dict] = None
    cost: Optional[float] = None
    cache_hit: bool = False
    bypassed_auth: bool = True
    test_mode: bool = True

    # Vision-specific metadata
    confidence: Optional[float] = None
    analysis_type: Optional[str] = None
    reasoning_level: Optional[str] = None
    detail_level: Optional[str] = None
    api_time: Optional[float] = None

    # Test configuration
    bypass_cache: bool = False
    bypass_rate_limit: bool = False
    tools_used: Optional[list[str]] = None
    subagents_invoked: Optional[list[str]] = None
    raw_metadata: Optional[dict[str, Any]] = None


class TestResult(BaseModel):
    """Resposta padronizada de teste de subagente."""

    success: bool
    agent_name: str
    response: str  # Resposta do subagente
    metadata: TestMetadata
    error: Optional[str] = None


class SubagentTester:
    """
    Gerenciador de testes isolados para subagentes VOXY.

    Permite testar cada subagente individualmente sem passar pelo VOXY Orchestrator,
    economizando tempo e permitindo debug mais eficiente.

    Estratégia:
    - Vision Agent: Teste direto via analyze_image() (interface pública assíncrona)
    - Standard Agents: Teste via SDK Runner.run() (simula como VOXY os usa)

    Args:
        bypass_cache: Se True, limpa cache antes de testar Vision Agent
        bypass_rate_limit: Se True, desabilita rate limiting (apenas Vision)

    Example:
        >>> tester = SubagentTester(bypass_cache=True)
        >>> result = await tester.test_subagent(
        ...     "translator",
        ...     {"text": "Hello", "target_language": "pt-BR"}
        ... )
        >>> print(result.response)  # "Olá"
    """

    # Mapeamento de nomes de agentes para getters
    AGENT_GETTERS = {
        "translator": get_translator_agent,
        "corrector": get_corrector_agent,
        "weather": get_weather_agent,
        "calculator": get_calculator_agent,
        "vision": get_vision_agent,
    }

    def __init__(
        self,
        bypass_cache: bool = False,
        bypass_rate_limit: bool = True,
    ):
        """
        Initialize subagent tester.

        Args:
            bypass_cache: Se True, limpa cache L1 do Vision Agent antes de testar
            bypass_rate_limit: Se True, desabilita verificação de rate limiting
        """
        self.bypass_cache = bypass_cache
        self.bypass_rate_limit = bypass_rate_limit

        # Load agent models dynamically from config
        self.AGENT_MODELS = self._get_agent_models()

        logger.info(
            f"SubagentTester initialized (bypass_cache={bypass_cache}, "
            f"bypass_rate_limit={bypass_rate_limit})"
        )

    @staticmethod
    def _get_agent_models() -> dict[str, str]:
        """
        Get model names from agent configurations dynamically.

        Returns:
            Dict mapping agent names to their configured model names
        """
        from ..config.models_config import (
            load_calculator_config,
            load_corrector_config,
            load_translator_config,
            load_vision_config,
            load_weather_config,
        )

        # Vision Agent (via LiteLLM)
        models = {}
        try:
            vision_config = load_vision_config()
            models["vision"] = vision_config.get_litellm_model_path()
        except Exception:
            models["vision"] = "openrouter/openai/gpt-4o"  # Fallback

        # Calculator Agent
        try:
            calc_config = load_calculator_config()
            models["calculator"] = f"{calc_config.provider}/{calc_config.model_name}"
        except Exception as e:
            logger.warning(f"Failed to load calculator config: {e}")
            models["calculator"] = "gpt-4o-mini (fallback)"

        # Corrector Agent
        try:
            corr_config = load_corrector_config()
            models["corrector"] = f"{corr_config.provider}/{corr_config.model_name}"
        except Exception as e:
            logger.warning(f"Failed to load corrector config: {e}")
            models["corrector"] = "gpt-4o-mini (fallback)"

        # Weather Agent
        try:
            weather_config = load_weather_config()
            models["weather"] = f"{weather_config.provider}/{weather_config.model_name}"
        except Exception as e:
            logger.warning(f"Failed to load weather config: {e}")
            models["weather"] = "gpt-4o-mini (fallback)"

        # Translator Agent
        try:
            trans_config = load_translator_config()
            models["translator"] = f"{trans_config.provider}/{trans_config.model_name}"
        except Exception as e:
            logger.warning(f"Failed to load translator config: {e}")
            models["translator"] = "gpt-4o-mini (fallback)"

        return models

    async def test_subagent(
        self,
        agent_name: str,
        input_data: dict[str, Any],
    ) -> TestResult:
        """
        Testa um subagente individualmente.

        Args:
            agent_name: Nome do subagente (translator, corrector, weather, calculator, vision)
            input_data: Dados de entrada específicos para o agente

        Returns:
            TestResult com resposta e metadata detalhado

        Raises:
            ValueError: Se agent_name não for reconhecido

        Example:
            # Testar tradutor
            result = await tester.test_subagent(
                "translator",
                {"text": "Hello world", "target_language": "pt-BR"}
            )

            # Testar Vision Agent
            result = await tester.test_subagent(
                "vision",
                {
                    "image_url": "https://example.com/image.jpg",
                    "query": "O que você vê?",
                    "analysis_type": "general",
                    "detail_level": "standard"
                }
            )
        """
        start_time = datetime.now()

        # Validar nome do agente
        if agent_name not in self.AGENT_GETTERS:
            available = ", ".join(self.AGENT_GETTERS.keys())
            raise ValueError(f"Unknown agent: {agent_name}. Available: {available}")

        logger.info(f"🧪 Testing {agent_name} agent...")

        try:
            # Rota especial para Vision Agent
            if agent_name == "vision":
                return await self._test_vision_agent(input_data, start_time)

            # Rota padrão para outros agentes via SDK Runner
            return await self._test_standard_agent(agent_name, input_data, start_time)

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Test failed for {agent_name}: {e}")

            return TestResult(
                success=False,
                agent_name=agent_name,
                response="",
                error=str(e),
                metadata=TestMetadata(
                    processing_time=processing_time,
                    model_used=self.AGENT_MODELS[agent_name],
                    bypass_cache=self.bypass_cache,
                    bypass_rate_limit=self.bypass_rate_limit,
                ),
            )

    async def _test_vision_agent(
        self,
        input_data: dict[str, Any],
        start_time: datetime,
    ) -> TestResult:
        """
        Testa Vision Agent diretamente via analyze_image().

        Estratégia: Bypass completo do SDK e VOXY Orchestrator para máxima velocidade.

        Args:
            input_data: Dict com image_url, query, analysis_type, detail_level
            start_time: Timestamp de início do teste

        Returns:
            TestResult com análise visual e metadata
        """
        # Obter instância do Vision Agent
        vision_agent: VisionAgent = get_vision_agent()

        # Bypass de cache se configurado
        if self.bypass_cache:
            vision_agent.vision_cache.local_cache.clear()
            logger.info("🗑️ Vision Agent cache cleared")

        # Bypass de rate limiting se configurado
        if self.bypass_rate_limit:
            vision_agent.requests_in_current_minute = 0
            vision_agent.requests_in_current_hour = 0
            logger.info("⚡ Rate limiting bypassed")

        # Extrair parâmetros
        image_url = input_data.get("image_url")
        if not image_url:
            raise ValueError("image_url is required for vision agent")

        query = input_data.get("query", "Analise esta imagem")
        analysis_type = input_data.get("analysis_type", "general")
        detail_level = input_data.get("detail_level", "standard")
        specific_questions = input_data.get("specific_questions")

        # Chamar Vision Agent diretamente
        vision_result = await vision_agent.analyze_image(
            image_url=image_url,
            query=query,
            analysis_type=analysis_type,
            detail_level=detail_level,
            specific_questions=specific_questions,
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        # Construir TestResult
        return TestResult(
            success=vision_result.success,
            agent_name="vision",
            response=vision_result.analysis,
            error=vision_result.error,
            metadata=TestMetadata(
                processing_time=processing_time,
                model_used=vision_result.metadata.get("model_used", "unknown"),
                cost=vision_result.metadata.get("cost", 0.0),
                cache_hit=vision_result.metadata.get("cache_hit", False),
                confidence=vision_result.confidence,
                analysis_type=analysis_type,
                detail_level=detail_level,
                reasoning_level=vision_result.metadata.get("reasoning_level"),
                api_time=vision_result.metadata.get("api_time"),
                bypass_cache=self.bypass_cache,
                bypass_rate_limit=self.bypass_rate_limit,
            ),
        )

    async def _test_standard_agent(
        self,
        agent_name: str,
        input_data: dict[str, Any],
        start_time: datetime,
    ) -> TestResult:
        """
        Testa subagente padrão usando SDK Runner.run().

        Estratégia: Usa Runner.run() para simular como VOXY Orchestrator chama os agentes.

        Args:
            agent_name: Nome do agente (translator, corrector, weather, calculator)
            input_data: Dados de entrada específicos do agente
            start_time: Timestamp de início do teste

        Returns:
            TestResult com resposta do agente
        """
        # Obter agente
        agent_getter = self.AGENT_GETTERS[agent_name]
        agent_wrapper = agent_getter()
        agent = agent_wrapper.get_agent()

        # Formatar entrada para o agente
        formatted_input = self._format_input(agent_name, input_data)

        logger.info(f"📝 Formatted input: {formatted_input[:100]}...")

        # Executar via SDK Runner (sem session para testes)
        result = await Runner.run(
            agent,
            formatted_input,
            session=None,  # No session needed for isolated tests
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        # Extrair resposta
        response_text = (
            result.final_output if hasattr(result, "final_output") else str(result)
        )

        if isinstance(response_text, list):
            response_text = " ".join(str(x) for x in response_text)
        elif not isinstance(response_text, str):
            response_text = str(response_text)

        # Extrair tokens_used se disponível
        tokens_used = None
        if hasattr(result, "usage") and result.usage:
            tokens_used = {
                "prompt_tokens": result.usage.prompt_tokens,
                "completion_tokens": result.usage.completion_tokens,
                "total_tokens": result.usage.total_tokens,
            }

        # Calcular custo estimado (GPT-4o-mini pricing)
        cost = None
        if tokens_used:
            # GPT-4o-mini: $0.15/$0.60 per 1M tokens (input/output)
            input_cost = (tokens_used["prompt_tokens"] / 1_000_000) * 0.15
            output_cost = (tokens_used["completion_tokens"] / 1_000_000) * 0.60
            cost = input_cost + output_cost

        logger.info(
            f"✅ {agent_name} completed in {processing_time:.2f}s "
            f"(cost: ${cost:.6f})"
            if cost
            else ""
        )

        return TestResult(
            success=True,
            agent_name=agent_name,
            response=response_text,
            metadata=TestMetadata(
                processing_time=processing_time,
                model_used=self.AGENT_MODELS[agent_name],
                tokens_used=tokens_used,
                cost=cost,
                bypass_cache=self.bypass_cache,
                bypass_rate_limit=self.bypass_rate_limit,
            ),
        )

    def _format_input(
        self,
        agent_name: str,
        input_data: dict[str, Any],
    ) -> str:
        """
        Formata entrada para o agente específico.

        Cada agente espera formato diferente de entrada (natural language prompt).

        Args:
            agent_name: Nome do agente
            input_data: Dados brutos de entrada

        Returns:
            String formatada para o agente processar

        Example:
            # Translator
            input_data = {"text": "Hello", "target_language": "pt-BR"}
            formatted = "Traduza 'Hello' para pt-BR"

            # Weather
            input_data = {"city": "São Paulo"}
            formatted = "Qual o clima em São Paulo?"
        """
        if agent_name == "translator":
            text = input_data.get("text", "")
            target_lang = input_data.get("target_language", "")
            source_lang = input_data.get("source_language", "")

            if source_lang:
                return f"Traduza '{text}' de {source_lang} para {target_lang}"
            else:
                return f"Traduza '{text}' para {target_lang}"

        elif agent_name == "corrector":
            text = input_data.get("text", "")
            return f"Corrija este texto: '{text}'"

        elif agent_name == "weather":
            city = input_data.get("city", "")
            country = input_data.get("country", "BR")
            return f"Qual o clima em {city}, {country}?"

        elif agent_name == "calculator":
            expression = input_data.get("expression", "")
            return f"Calcule: {expression}"

        else:
            # Fallback genérico
            return str(input_data)

    def get_available_agents(self) -> list[str]:
        """
        Retorna lista de agentes disponíveis para teste.

        Returns:
            Lista de nomes de agentes (5 subagentes + voxy orchestrator)
        """
        # Include 5 subagents + voxy orchestrator
        return list(self.AGENT_GETTERS.keys()) + ["voxy"]

    def get_agent_info(self, agent_name: str) -> dict[str, Any]:
        """
        Retorna informações sobre um agente específico.

        Args:
            agent_name: Nome do agente

        Returns:
            Dict com model_used, capabilities, etc.

        Raises:
            ValueError: Se agent_name não for reconhecido
        """
        # Special case for VOXY Orchestrator
        if agent_name == "voxy":
            from ..config.models_config import load_orchestrator_config

            try:
                config = load_orchestrator_config()
                model_path = config.get_litellm_model_path()
            except Exception:
                model_path = "openrouter/anthropic/claude-sonnet-4.5"  # Fallback

            return {
                "name": "voxy",
                "model": model_path,
                "test_strategy": "orchestrator_direct",
                "capabilities": [
                    "Multi-agent orchestration",
                    "Intelligent tool selection",
                    "Context-aware decision making",
                    "Vision + Standard agents coordination",
                    "Session management via Agents SDK",
                    "Adaptive reasoning (LiteLLM)",
                    "Lightweight post-processing",
                ],
                "required_params": ["message"],
                "optional_params": [
                    "image_url",
                    "session_id",
                    "user_id",
                    "bypass_cache",
                    "bypass_rate_limit",
                ],
            }

        if agent_name not in self.AGENT_GETTERS:
            raise ValueError(f"Unknown agent: {agent_name}")

        info: dict[str, Any] = {
            "name": agent_name,
            "model": self.AGENT_MODELS[agent_name],
            "test_strategy": ("direct" if agent_name == "vision" else "sdk_runner"),
        }

        # Adicionar informações específicas por agente
        if agent_name == "translator":
            info["capabilities"] = [
                "Translation between languages",
                "Auto-detect source language",
                "Native model translation",
            ]
            info["required_params"] = ["text", "target_language"]
            info["optional_params"] = ["source_language"]

        elif agent_name == "corrector":
            info["capabilities"] = [
                "Grammar correction",
                "Spelling correction",
                "Preserve original meaning",
            ]
            info["required_params"] = ["text"]

        elif agent_name == "weather":
            info["capabilities"] = [
                "Real-time weather data",
                "OpenWeatherMap API integration",
                "Global city support",
            ]
            info["required_params"] = ["city"]
            info["optional_params"] = ["country"]

        elif agent_name == "calculator":
            info["capabilities"] = [
                "Basic arithmetic",
                "Complex expressions",
                "Natural language math",
            ]
            info["required_params"] = ["expression"]

        elif agent_name == "vision":
            info["capabilities"] = [
                "GPT-5 multimodal analysis",
                "OCR text extraction",
                "Technical/artistic analysis",
                "Document understanding",
                "Cache L1/L2",
                "Adaptive reasoning",
            ]
            info["required_params"] = ["image_url"]
            info["optional_params"] = [
                "query",
                "analysis_type",
                "detail_level",
                "specific_questions",
            ]

        return info


# =============================================================================
# VOXY Orchestrator Test Harness
# =============================================================================


async def test_voxy_orchestrator(
    message: str,
    *,
    image_url: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    bypass_cache: bool = False,
    bypass_rate_limit: bool = False,
    include_tools_metadata: bool = True,
) -> TestResult:
    """
    Executa o VOXY Orchestrator diretamente (sem FastAPI) e coleta métricas detalhadas.

    Args:
        message: Texto a ser enviado ao orquestrador
        image_url: URL de imagem opcional (ativa fluxo multimodal)
        user_id: UUID do usuário (default: None, usa UUID do usuário de desenvolvimento)
        session_id: Session ID reutilizado ou None para gerar automaticamente
        bypass_cache: Se True, limpa caches locais (visão) antes do teste
        bypass_rate_limit: Se True, reinicia contadores de rate limit da visão
        include_tools_metadata: Se False, remove informações de tools/subagentes do metadata

    Returns:
        TestResult com sucesso, resposta e metadados (tokens, custo, ferramentas utilizadas)

    Note:
        O user_id padrão é do usuário de desenvolvimento (stefanogysin@hotmail.com),
        garantindo que CLI tests funcionem com o mesmo sistema de auth do Supabase
        que o frontend usa. Isso permite persistência correta de sessions e messages.
    """

    config = load_orchestrator_config()
    start_time = datetime.now()

    # Use development user UUID if user_id not provided
    # This ensures CLI tests work with the same Supabase auth system as frontend
    if user_id is None:
        user_id = "4a82fdef-cc14-4471-b9b9-9f1238bdd222"  # stefanogysin@hotmail.com (dev user)
        logger.info(f"Using default dev user_id: {user_id[:8]}...")

    vision_agent: Optional[VisionAgent] = None
    if image_url or bypass_cache or bypass_rate_limit:
        try:
            vision_agent = get_vision_agent()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Não foi possível inicializar Vision Agent para teste do orquestrador: %s",
                exc,
            )
            vision_agent = None

        if vision_agent is not None:
            if bypass_cache and hasattr(vision_agent, "vision_cache"):
                try:
                    vision_agent.vision_cache.local_cache.clear()
                    if hasattr(vision_agent.vision_cache, "cache_hits"):
                        vision_agent.vision_cache.cache_hits = 0
                        vision_agent.vision_cache.cache_misses = 0
                except Exception as cache_error:  # pragma: no cover
                    logger.debug(
                        "Falha ao limpar cache do Vision Agent durante teste: %s",
                        cache_error,
                    )

            if bypass_rate_limit:
                if hasattr(vision_agent, "requests_in_current_minute"):
                    vision_agent.requests_in_current_minute = 0
                if hasattr(vision_agent, "requests_in_current_hour"):
                    vision_agent.requests_in_current_hour = 0

    voxy_system = VOXYSystem()

    try:
        response, metadata = await voxy_system.chat(
            message=message,
            user_id=user_id,
            session_id=session_id,
            image_url=image_url,
        )
    except Exception as exc:
        processing_time = (datetime.now() - start_time).total_seconds()
        error_message = str(exc)
        logger.exception("Erro ao executar teste do VOXY Orchestrator: %s", exc)

        error_metadata = {
            "agent_type": "error",
            "tools_used": [],
            "cache_hit": False,
            "processing_time": processing_time,
            "error": error_message,
        }

        failure_metadata = TestMetadata(
            processing_time=processing_time,
            model_used=config.get_litellm_model_path(),
            cache_hit=False,
            bypass_cache=bypass_cache,
            bypass_rate_limit=bypass_rate_limit,
            tools_used=[] if include_tools_metadata else None,
            subagents_invoked=[] if include_tools_metadata else None,
            raw_metadata=error_metadata if include_tools_metadata else None,
        )

        return TestResult(
            success=False,
            agent_name="error",
            response=error_message,
            metadata=failure_metadata,
            error=error_message,
        )

    processing_time = (datetime.now() - start_time).total_seconds()
    agent_type = metadata.get("agent_type", "voxy")
    error_from_metadata: Optional[str] = metadata.get("error")
    success = agent_type != "error" and not error_from_metadata

    tokens_used = metadata.get("tokens_used")
    cost = metadata.get("cost")

    # Note: Cost calculation requires cost_per_million fields which are not in OrchestratorModelConfig
    # Rely on cost from metadata if available, otherwise set to 0.0
    if cost is None:
        cost = 0.0

    tools_used_raw = metadata.get("tools_used", []) or []
    if not isinstance(tools_used_raw, list):
        tools_used_raw = [tools_used_raw]

    tool_map = {
        "translate_text": "translator",
        "correct_text": "corrector",
        "get_weather": "weather",
        "calculate": "calculator",
        "analyze_image": "vision",
        "vision_agent": "vision",
        "web_search": "web_search",
    }
    subagents_invoked = (
        [tool_map.get(tool, tool) for tool in tools_used_raw]
        if include_tools_metadata and tools_used_raw
        else ([] if include_tools_metadata else None)
    )

    tools_for_metadata: Optional[list[str]]
    if include_tools_metadata:
        tools_for_metadata = tools_used_raw
    else:
        tools_for_metadata = None

    orchestrator_model = metadata.get(
        "orchestrator_model", config.get_litellm_model_path()
    )
    cache_hit = metadata.get("cache_hit", False)

    raw_metadata = metadata if include_tools_metadata else None

    # Determine the actual model used based on which subagent was invoked
    metadata_model = orchestrator_model or config.get_litellm_model_path()

    # If a subagent was invoked, use its model instead of orchestrator's
    if subagents_invoked and len(subagents_invoked) > 0:
        from ..config.models_config import (
            load_calculator_config,
            load_corrector_config,
            load_translator_config,
            load_vision_config,
            load_weather_config,
        )

        # Get the first subagent invoked (primary agent for this request)
        primary_subagent = subagents_invoked[0]

        # Load the appropriate config
        subagent_configs = {
            "calculator": load_calculator_config,
            "corrector": load_corrector_config,
            "translator": load_translator_config,
            "weather": load_weather_config,
            "vision": load_vision_config,
        }

        if primary_subagent in subagent_configs:
            try:
                subagent_config = subagent_configs[primary_subagent]()
                metadata_model = subagent_config.get_litellm_model_path()
            except Exception:
                # Fallback to orchestrator model if config loading fails
                pass

    test_metadata = TestMetadata(
        processing_time=processing_time,
        model_used=metadata_model,
        tokens_used=tokens_used,
        cost=cost,
        cache_hit=cache_hit,
        bypass_cache=bypass_cache,
        bypass_rate_limit=bypass_rate_limit,
        tools_used=tools_for_metadata,
        subagents_invoked=subagents_invoked,
        raw_metadata=raw_metadata,
    )

    return TestResult(
        success=bool(success),
        agent_name=agent_type,
        response=response,
        metadata=test_metadata,
        error=error_message,
    )


# Singleton global para uso conveniente
_subagent_tester = None


def get_subagent_tester(
    bypass_cache: bool = False,
    bypass_rate_limit: bool = True,
) -> SubagentTester:
    """
    Get global SubagentTester instance (lazy initialization).

    Args:
        bypass_cache: Se True, limpa cache antes de testar Vision Agent
        bypass_rate_limit: Se True, desabilita rate limiting

    Returns:
        SubagentTester instance configurada

    Example:
        >>> tester = get_subagent_tester()
        >>> result = await tester.test_subagent("calculator", {"expression": "2+2"})
    """
    global _subagent_tester
    if _subagent_tester is None:
        _subagent_tester = SubagentTester(
            bypass_cache=bypass_cache,
            bypass_rate_limit=bypass_rate_limit,
        )
    return _subagent_tester
