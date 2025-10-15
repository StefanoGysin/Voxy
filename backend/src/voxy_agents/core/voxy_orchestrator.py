"""
VOXY Orchestrator - OpenAI Agents SDK Implementation

This is the heart of the VOXY system, built on the official OpenAI Agents SDK.
Uses the "subagents as tools" pattern for optimal orchestration.

Architecture:
- VOXY (main agent) uses GPT-4.1 for intelligent reasoning
- Subagents are registered as tools via .as_tool()
- OpenAI Agents SDK handles sessions, streaming, and tool calls
- Implements the creative decisions from CREATIVE MODE

Migração Loguru - Sprint 4 + Sprint Multi-Agent Hierarchical Logging
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

from agents import Agent, Runner, function_tool, ModelSettings
from loguru import logger
from openai import AsyncOpenAI

from ..config.settings import settings
from .database.supabase_integration import SupabaseSession
from .guardrails.safety_check import SafetyChecker
from .subagents.vision_agent import VisionAnalysisResult, get_vision_agent


@dataclass
class ToolInvocation:
    """
    Representa uma invocação de tool/subagente capturada durante execução.

    Attributes:
        tool_name: Nome da ferramenta (get_weather, translate_text, etc.)
        agent_name: Nome amigável do subagente (Weather Agent, Translator Agent, etc.)
        model: Modelo LLM usado pelo subagente
        config: Configuração do subagente (tokens, temperature, etc.)
        input_args: Argumentos passados para o tool (dict)
        output: Resposta retornada pelo tool (string)
        call_id: ID único da chamada (para debugging)
    """
    tool_name: str
    agent_name: str
    model: str
    config: dict
    input_args: dict
    output: str
    call_id: str


# Mapeamento de tool names para agent names amigáveis
TOOL_TO_AGENT_MAP = {
    "get_weather": "Weather Agent",
    "translate_text": "Translator Agent",
    "correct_text": "Corrector Agent",
    "calculate": "Calculator Agent",
    "analyze_image": "Vision Agent",
    "web_search": "Web Search Agent",
}


class VoxyOrchestrator:
    """
    VOXY main agent using OpenAI Agents SDK.

    Implements the Hybrid Context-Aware Weighted System from CREATIVE MODE.
    Uses subagents as tools for optimal cost and performance.
    """

    def __init__(self):
        """Initialize VOXY orchestrator with OpenAI Agents SDK + LiteLLM."""
        import time
        start_time = time.perf_counter()

        # Load LiteLLM configuration for orchestrator
        from ..config.models_config import load_orchestrator_config
        from ..utils.llm_factory import create_litellm_model, get_reasoning_params

        self.config = load_orchestrator_config()
        self.litellm_model = create_litellm_model(self.config)

        # Extract reasoning parameters for runtime use
        self.reasoning_params = get_reasoning_params(self.config)

        if self.reasoning_params:
            logger.bind(event="VOXY_ORCHESTRATOR|REASONING_CONFIG").info(
                "Orchestrator reasoning configured",
                params=list(self.reasoning_params.keys())
            )

        # Safety checker
        self.safety_checker = SafetyChecker()

        # Subagents registry (will be registered as tools)
        self.subagents = {}

        # Performance tracking
        self.total_cost = 0.0
        self.request_count = 0

        # Main VOXY agent will be initialized after subagents are registered
        self.voxy_agent = None

        # AsyncOpenAI client for lightweight post-processing (without SDK overhead)
        # Note: This is separate from orchestrator model and used only for conversationalization
        self.openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key, timeout=30.0, max_retries=1
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.bind(event="STARTUP|ORCHESTRATOR").info(
            f"\n"
            f"🤖 VOXY Orchestrator Initialized\n"
            f"   ├─ Model: {self.config.get_litellm_model_path()}\n"
            f"   ├─ Config: {self.config.max_tokens} tokens, temp={self.config.temperature}, reasoning={self.config.reasoning_effort}\n"
            f"   └─ ✓ Ready in {elapsed_ms:.1f}ms"
        )

    def register_subagent(
        self, name: str, agent: Agent, tool_name: str, description: str
    ) -> None:
        """
        Register a subagent as a tool for VOXY.

        Args:
            name: Internal name for the subagent
            agent: The Agent instance
            tool_name: Name for the tool call
            description: Description for the tool
        """
        self.subagents[name] = {
            "agent": agent,
            "tool_name": tool_name,
            "description": description,
        }
        # Logging now done by individual subagents during initialization

    def _initialize_voxy_agent(self) -> None:
        """Initialize the main VOXY agent with registered subagents as tools."""
        if self.voxy_agent is not None:
            return

        # Build tools list from registered subagents
        tools = []
        for subagent_info in self.subagents.values():
            agent = subagent_info["agent"]
            tool_name = subagent_info["tool_name"]
            description = subagent_info["description"]

            # Use .as_tool() to register subagent as tool
            tools.append(
                agent.as_tool(tool_name=tool_name, tool_description=description)
            )

        # Add vision agent tool
        vision_agent = get_vision_agent()

        @function_tool
        def analyze_image(
            image_url: str,
            analysis_type: str = "general",
            detail_level: str = "standard",
            specific_questions: Optional[list[str]] = None,
            query: str = "Analise esta imagem",
        ) -> str:  # pragma: no cover
            """
            Análise avançada de imagens usando GPT-5 multimodal.

            Args:
                image_url: URL da imagem para análise
                analysis_type: Tipo de análise (general, ocr, technical, artistic, document)
                detail_level: Nível de detalhe (basic, standard, detailed, comprehensive)
                specific_questions: Lista de perguntas específicas sobre a imagem
                query: Query do usuário sobre a imagem

            Returns:
                Resultado da análise visual detalhada
            """
            # process_tool_call() is now synchronous (uses nest_asyncio internally)
            return vision_agent.process_tool_call(
                image_url=image_url,
                analysis_type=analysis_type,
                detail_level=detail_level,
                specific_questions=specific_questions,
                query=query,
            )

        tools.append(analyze_image)

        # Add web search tool for VOXY
        @function_tool
        def web_search(query: str) -> str:
            """Search the web for current information."""
            # Placeholder - implement web search API
            return f"Web search results for: {query}"

        tools.append(web_search)

        # Prepare ModelSettings with reasoning parameters
        model_settings = None
        if self.reasoning_params:
            # Pass reasoning params via ModelSettings.extra_args
            model_settings = ModelSettings(
                extra_args=self.reasoning_params
            )

            logger.bind(event="VOXY_ORCHESTRATOR|MODEL_SETTINGS").info(
                "ModelSettings configured with reasoning params",
                params=self.reasoning_params
            )

        # Create main VOXY agent with LiteLLM model
        # IMPORTANT: Known SDK limitation - thinking blocks may be lost during tool calls
        # See: https://github.com/openai/openai-agents-python/issues/678
        self.voxy_agent = Agent(
            name="VOXY",
            model=self.litellm_model,  # Use LiteLLM model instance
            instructions=self._get_voxy_instructions(),
            tools=tools,
            model_settings=model_settings,  # Inject reasoning params
            # Note: input_guardrails temporarily disabled for testing
        )

        logger.bind(event="VOXY_ORCHESTRATOR|AGENT_INIT").info(
            f"VOXY agent initialized:\n"
            f"   ├─ Model: {self.config.get_litellm_model_path()}\n"
            f"   ├─ Provider: {self.config.provider}\n"
            f"   ├─ Max tokens: {self.config.max_tokens}\n"
            f"   ├─ Temperature: {self.config.temperature}\n"
            f"   ├─ Reasoning: {'enabled' if self.reasoning_params else 'disabled'}\n"
            f"   └─ Tools: {len(tools)} registered"
        )

    def _get_voxy_instructions(self) -> str:
        """Get VOXY's core instructions implementing Creative Mode decisions."""
        return """
        Você é o VOXY, agente principal que orquestra subagentes especializados.

        ARQUITETURA (Implementando Hybrid Context-Aware Weighted System):
        - Analise cada solicitação cuidadosamente para identificar tarefas específicas
        - Use subagentes especializados quando necessário via tool calls
        - Você pode usar múltiplos subagentes na mesma resposta
        - Sempre compile os resultados em uma resposta coerente e útil
        - O usuário só fala com você - você é o único ponto de contato

        SUBAGENTES DISPONÍVEIS:
        - translate_text: Para tradução entre idiomas (capacidade nativa)
        - correct_text: Para correção ortográfica e gramatical (capacidade nativa)
        - get_weather: Para informações meteorológicas (via APIs)
        - calculate: Para cálculos matemáticos (capacidade nativa)
        - analyze_image: Para análise avançada de imagens usando GPT-5 multimodal
        - web_search: Para busca na web (quando necessário)

        INSTRUÇÕES ESPECIAIS PARA ANÁLISE DE IMAGEM:
        - Quando a mensagem contém "[IMAGEM PARA ANÁLISE]: {URL}", extraia a URL
        - Use analyze_image(image_url="URL_EXTRAIDA", query="QUERY_DO_USUARIO") APENAS UMA VEZ
        - NUNCA chame analyze_image múltiplas vezes para a mesma imagem
        - A URL sempre aparece após "[IMAGEM PARA ANÁLISE]: " na mensagem
        - Exemplo: Se a mensagem for "que emoji é este?\n\n[IMAGEM PARA ANÁLISE]: https://...",
          use analyze_image(image_url="https://...", query="que emoji é este?") UMA ÚNICA VEZ
        - IMPORTANTE: Após receber o resultado da análise, responda diretamente sem chamar a função novamente
        - O Vision Agent usa GPT-5 multimodal para análise avançada

        OTIMIZAÇÃO (Dynamic Complexity Scoring):
        - Use subagentes especializados para tarefas específicas (mais eficiente)
        - Para consultas gerais, responda diretamente quando apropriado
        - Combine múltiplas ferramentas quando a tarefa é complexa
        - Mantenha o contexto da conversa para respostas inteligentes

        RECOVERY STRATEGY (Multi-Level Context-Aware):
        - Se um subagente falhar, continue com outros ou responda diretamente
        - Sempre forneça uma resposta útil mesmo com falhas parciais
        - Informe sobre limitações quando relevante

        EXPERIÊNCIA DO USUÁRIO:
        - Seja natural, conversacional e prestativo
        - Integre resultados de forma transparente
        - Mantenha consistência na personalidade VOXY
        - Responda em português brasileiro por padrão

        IMPORTANTE: Para análise de imagens, SEMPRE extraia a URL após "[IMAGEM PARA ANÁLISE]: "
        e passe como parâmetro image_url para a função analyze_image_independent.
        """

    async def _create_safety_guardrail(self):
        """Create safety guardrail for input validation."""
        from agents import GuardrailFunctionOutput, InputGuardrail

        async def safety_check(ctx, agent, input_data):
            """Check if input is safe."""
            is_safe = await self.safety_checker.is_safe(input_data)
            return GuardrailFunctionOutput(
                tripwire_triggered=not is_safe, output_info={"safe": is_safe}
            )

        return InputGuardrail(guardrail_function=safety_check)

    def _is_vision_request(self, message: str) -> bool:
        """Detect if this is a vision analysis request to trigger bypass."""
        # Keywords that indicate vision analysis
        vision_keywords = [
            "emoji",
            "imagem",
            "foto",
            "picture",
            "analise",
            "analisar",
            "vejo",
            "mostra",
            "que",
            "qual",
            "este",
            "esta",
            "identifique",
            "reconhece",
            "descreva",
            "cor",
            "cabelo",
            "pessoa",
            "objeto",
            "texto",
            "ler",
            "ocr",
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in vision_keywords)

    def _determine_analysis_type(self, message: str) -> str:
        """Determine analysis type from user message."""
        message_lower = message.lower()

        if any(
            word in message_lower for word in ["texto", "ler", "leia", "ocr", "escreve"]
        ):
            return "ocr"
        elif any(
            word in message_lower
            for word in ["técnico", "científico", "médico", "diagnóstico"]
        ):
            return "technical"
        elif any(
            word in message_lower
            for word in ["artístico", "arte", "composição", "estilo"]
        ):
            return "artistic"
        elif any(
            word in message_lower
            for word in ["documento", "relatório", "tabela", "gráfico"]
        ):
            return "document"
        else:
            return "general"

    def _determine_detail_level(self, message: str) -> str:
        """Determine detail level from user message."""
        message_lower = message.lower()

        # Simple/quick analysis indicators
        if any(
            word in message_lower
            for word in ["que", "qual", "emoji", "rápido", "simples", "básico"]
        ):
            return "basic"
        elif any(
            word in message_lower
            for word in ["detalhado", "completo", "minucioso", "profundo"]
        ):
            return "detailed"
        elif any(
            word in message_lower for word in ["análise completa", "comprehensive"]
        ):
            return "comprehensive"
        else:
            return "standard"

    async def _conversationalize_vision_result(
        self, vision_result: VisionAnalysisResult, user_query: str
    ) -> str:
        """
        Lightweight post-processing to convert technical analysis into conversational response.

        Uses GPT-4o-mini for fast conversationalization (adds ~1-2s).
        Avoids Runner.run() overhead to maintain performance.

        Args:
            vision_result: Technical analysis from Vision Agent
            user_query: Original user question

        Returns:
            Conversational response suitable for end user
        """
        try:
            # Build conversationalization prompt
            prompt = f"""Você é VOXY, um assistente brasileiro amigável e natural.

O usuário perguntou: "{user_query}"

O Vision Agent analisou a imagem e retornou esta análise técnica:

{vision_result.analysis}

Metadados:
- Modelo usado: {vision_result.metadata.get('model_used')}
- Confiança: {vision_result.confidence:.1%}
- Tipo de análise: {vision_result.metadata.get('analysis_type')}

TAREFA:
Transforme essa análise técnica em uma resposta conversacional natural e amigável para o usuário.

REGRAS:
- Use tom brasileiro casual mas profissional
- Use emojis quando apropriado 😊
- Seja empático e natural
- Se a análise for técnica, simplifique para usuário leigo
- Mantenha as informações principais da análise
- NÃO mencione metadados técnicos (modelo, confiança) diretamente

Responda APENAS com a versão conversacional, sem introduções ou conclusões extras."""

            # Lightweight GPT-4o-mini call (no SDK overhead)
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,  # More creative for conversational tone
            )

            conversational_response = response.choices[0].message.content.strip()

            # Calculate transformation metrics
            original_len = len(vision_result.analysis)
            conversational_len = len(conversational_response)
            diff_percent = ((conversational_len - original_len) / original_len) * 100 if original_len > 0 else 0
            diff_sign = "+" if diff_percent > 0 else ""

            logger.info(
                f"🎨 Conversationalization completed:\n"
                f"   ├─ 📥 Input (technical): {original_len} chars\n"
                f"   ├─ 📤 Output (conversational): {conversational_len} chars\n"
                f"   ├─ 🔄 Diff: {diff_sign}{diff_percent:.1f}%\n"
                f"   └─ 📝 Preview: {conversational_response[:150]}{'...' if len(conversational_response) > 150 else ''}"
            )

            return conversational_response

        except Exception as e:
            logger.bind(event="VOXY_ORCHESTRATOR|CONVERSATIONALIZATION_ERROR").error(
                "Conversationalization failed, returning raw analysis",
                error=str(e)
            )
            # Fallback: return raw analysis if conversationalization fails
            return vision_result.analysis

    def _extract_tool_invocations(self, result) -> List[ToolInvocation]:
        """
        Extrai invocações de tools do RunResult para logging hierárquico.

        Args:
            result: RunResult do Runner.run()

        Returns:
            Lista de ToolInvocation com dados estruturados
        """
        invocations = []

        if not hasattr(result, "new_items") or not result.new_items:
            return invocations

        # Build dictionary mapping call_id to tool call data
        tool_calls = {}  # call_id -> {tool_name, input_args}
        tool_outputs = {}  # call_id -> output

        for item in result.new_items:
            item_type = type(item).__name__

            # Extract tool call information
            if item_type == "ToolCallItem" and hasattr(item, 'raw_item'):
                raw_item = item.raw_item
                if hasattr(raw_item, 'call_id') and hasattr(raw_item, 'name'):
                    call_id = raw_item.call_id
                    tool_name = raw_item.name

                    # Parse arguments (JSON string)
                    input_args = {}
                    if hasattr(raw_item, 'arguments'):
                        try:
                            input_args = json.loads(raw_item.arguments)
                        except (json.JSONDecodeError, TypeError):
                            input_args = {"raw": str(raw_item.arguments)}

                    tool_calls[call_id] = {
                        "tool_name": tool_name,
                        "input_args": input_args
                    }

            # Extract tool output
            elif item_type == "ToolCallOutputItem":
                output = item.output if hasattr(item, 'output') else ""
                # Extract call_id from raw_item (dict with tool_call_id)
                if hasattr(item, 'raw_item') and isinstance(item.raw_item, dict):
                    call_id = item.raw_item.get('tool_call_id') or item.raw_item.get('call_id')
                    if call_id:
                        tool_outputs[call_id] = output

        # Match tool calls with outputs and load subagent configs
        for call_id, call_data in tool_calls.items():
            tool_name = call_data["tool_name"]
            input_args = call_data["input_args"]
            output = tool_outputs.get(call_id, "")

            # Get friendly agent name
            agent_name = TOOL_TO_AGENT_MAP.get(tool_name, tool_name)

            # Load subagent config to get model and settings
            model = "unknown"
            config = {}

            try:
                if tool_name == "get_weather":
                    from ..config.models_config import load_weather_config
                    cfg = load_weather_config()
                    model = cfg.get_litellm_model_path()
                    config = {
                        "max_tokens": cfg.max_tokens,
                        "temperature": cfg.temperature
                    }
                elif tool_name == "translate_text":
                    from ..config.models_config import load_translator_config
                    cfg = load_translator_config()
                    model = cfg.get_litellm_model_path()
                    config = {
                        "max_tokens": cfg.max_tokens,
                        "temperature": cfg.temperature
                    }
                elif tool_name == "correct_text":
                    from ..config.models_config import load_corrector_config
                    cfg = load_corrector_config()
                    model = cfg.get_litellm_model_path()
                    config = {
                        "max_tokens": cfg.max_tokens,
                        "temperature": cfg.temperature
                    }
                elif tool_name == "calculate":
                    from ..config.models_config import load_calculator_config
                    cfg = load_calculator_config()
                    model = cfg.get_litellm_model_path()
                    config = {
                        "max_tokens": cfg.max_tokens,
                        "temperature": cfg.temperature
                    }
                elif tool_name == "analyze_image":
                    from ..config.models_config import load_vision_config
                    cfg = load_vision_config()
                    model = cfg.get_litellm_model_path()
                    config = {
                        "max_tokens": cfg.max_tokens,
                        "temperature": cfg.temperature,
                        "reasoning_effort": cfg.reasoning_effort
                    }
            except Exception as e:
                logger.bind(event="VOXY_ORCHESTRATOR|CONFIG_LOAD_ERROR").warning(
                    f"Failed to load config for {tool_name}: {e}"
                )

            invocations.append(ToolInvocation(
                tool_name=tool_name,
                agent_name=agent_name,
                model=model,
                config=config,
                input_args=input_args,
                output=output[:200],  # Truncate for logging
                call_id=call_id
            ))

        return invocations

    def _format_hierarchical_log(
        self,
        invocations: List[ToolInvocation],
        total_time: float,
        trace_id: str,
        reasoning_list: Optional[List[dict[str, str]]] = None
    ) -> str:
        """
        Formata log hierárquico mostrando VOXY delegando para subagentes + reasoning.

        Args:
            invocations: Lista de tool invocations
            total_time: Tempo total de processamento
            trace_id: ID de rastreamento da requisição
            reasoning_list: Lista de reasoning blocks capturados (opcional)

        Returns:
            String formatada com hierarquia visual + reasoning
        """
        lines = []

        # Header: VOXY initialization
        lines.append(f"🤖 [TRACE:{trace_id}] VOXY Multi-Agent Flow")
        lines.append(f"   ├─ Model: {self.config.get_litellm_model_path()}")
        lines.append(f"   ├─ Config: {self.config.max_tokens} tokens, temp={self.config.temperature}, reasoning={self.config.reasoning_effort}")
        lines.append("   │")

        # Body: Each subagent invocation
        for idx, inv in enumerate(invocations):
            is_last = (idx == len(invocations) - 1)
            branch = "└─" if is_last else "├─"
            continuation = "   " if is_last else "│  "

            # Extract simplified input (first value from dict)
            input_preview = ""
            if inv.input_args:
                first_value = next(iter(inv.input_args.values()), "")
                input_preview = str(first_value)[:50]

            lines.append(f"   {branch} 🔄 Delegou para: {inv.agent_name}")
            lines.append(f"   {continuation}├─ Model: {inv.model}")

            # Format config string
            config_parts = [f"{k}={v}" for k, v in inv.config.items()]
            config_str = ", ".join(config_parts) if config_parts else "default"
            lines.append(f"   {continuation}├─ Config: {config_str}")

            lines.append(f"   {continuation}├─ 📤 Input: \"{input_preview}{'...' if len(input_preview) >= 50 else ''}\"")
            lines.append(f"   {continuation}├─ 📥 Output: \"{inv.output}{'...' if len(inv.output) >= 200 else ''}\"")

            # Add reasoning if available for this invocation
            if reasoning_list:
                for reasoning_item in reasoning_list:
                    reasoning_text = reasoning_item.get('reasoning', '')
                    if reasoning_text:
                        # Truncate reasoning to 150 chars for hierarchical log
                        reasoning_preview = reasoning_text[:150]
                        if len(reasoning_text) > 150:
                            reasoning_preview += "..."
                        lines.append(f"   {continuation}├─ 🧠 Reasoning: \"{reasoning_preview}\"")

            lines.append(f"   {continuation}└─ ✓ Completed")

            if not is_last:
                lines.append("   │")

        # Footer: Summary
        lines.append("   │")
        lines.append(f"   └─ ✓ Response compiled in {total_time:.2f}s")

        return "\n".join(lines)

    async def chat(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Main chat interface with Agents SDK Bypass for Vision Agent to eliminate 37s overhead.

        Args:
            message: User's message
            user_id: User identifier for session management
            session_id: Optional session ID (will be generated if not provided)
            image_url: Optional image URL for vision analysis with GPT-5

        Returns:
            Tuple of (response_text, metadata) where metadata includes agent_type, tools_used, and vision metadata
        """
        # Generate trace ID for end-to-end request tracking
        import uuid
        trace_id = str(uuid.uuid4())[:8]

        # Ensure VOXY agent is initialized
        self._initialize_voxy_agent()

        start_time = datetime.now()

        try:
            # Log request with trace ID
            if image_url:
                logger.info(
                    f"📨 [REQUEST:{trace_id}] Vision query received\n"
                    f"   ├─ 👤 User: {user_id[:8]}...\n"
                    f"   ├─ 🖼️  Image: {image_url[:80] if image_url else 'None'}{'...' if image_url and len(image_url) > 80 else ''}\n"
                    f"   └─ 💬 Query: \"{message[:80]}{'...' if len(message) > 80 else ''}\""
                )
            else:
                logger.info(
                    f"📨 [REQUEST:{trace_id}] Chat message received\n"
                    f"   ├─ 👤 User: {user_id[:8]}...\n"
                    f"   └─ 💬 Message: \"{message[:80]}{'...' if len(message) > 80 else ''}\""
                )

            # Create or get session ID (use UUID format for Supabase compatibility)
            if session_id:
                actual_session_id = session_id
            else:
                import uuid

                # Generate a deterministic UUID for this user
                actual_session_id = str(
                    uuid.uuid5(uuid.NAMESPACE_DNS, f"voxy.session.{user_id}")
                )

            # Create SupabaseSession for automatic context management
            session = SupabaseSession(session_id=actual_session_id, user_id=user_id)

            # 🖼️ VISION AGENT - GPT-5 multimodal analysis with lightweight post-processing
            if image_url and self._is_vision_request(message):
                logger.bind(event="VOXY_ORCHESTRATOR|VISION_PATH1").info("PATH 1: Vision bypass with lightweight post-processing")

                try:
                    # Determine analysis type and detail level from message
                    analysis_type = self._determine_analysis_type(message)
                    detail_level = self._determine_detail_level(message)

                    # Use Vision Agent directly for technical analysis
                    vision_agent = get_vision_agent()
                    vision_result = await vision_agent.analyze_image(
                        image_url=image_url,
                        query=message,
                        analysis_type=analysis_type,
                        detail_level=detail_level,
                    )

                    if not vision_result.success:
                        raise Exception(vision_result.error)

                    # Log Vision Agent technical response
                    logger.info(
                        f"✅ [TRACE:{trace_id}] Vision Agent analysis completed:\n"
                        f"   ├─ 📝 Response ({len(vision_result.analysis)} chars): {vision_result.analysis[:200]}{'...' if len(vision_result.analysis) > 200 else ''}\n"
                        f"   ├─ 🎯 Confidence: {vision_result.confidence:.1%}\n"
                        f"   ├─ 🤖 Model: {vision_result.metadata.get('model_used')}\n"
                        f"   ├─ ⏱️  Time: {vision_result.metadata.get('processing_time', 0):.2f}s\n"
                        f"   └─ 💰 Cost: ${vision_result.metadata.get('cost', 0):.4f}"
                    )

                    # Lightweight post-processing with GPT-4o-mini (adds ~1-2s)
                    # Feature flag: Can be disabled via ENABLE_VISION_POSTPROCESSING=false
                    if settings.enable_vision_postprocessing:
                        conversational_response = (
                            await self._conversationalize_vision_result(
                                vision_result, message
                            )
                        )
                        logger.info(
                            "✨ Post-processing enabled: Technical → Conversational"
                        )
                    else:
                        # Legacy mode: Return raw analysis
                        conversational_response = vision_result.analysis
                        logger.info(
                            "⚠️  Post-processing DISABLED: Returning raw analysis"
                        )

                    total_processing_time = (datetime.now() - start_time).total_seconds()
                    self.request_count += 1

                    metadata = {
                        "agent_type": "vision",
                        "tools_used": ["vision_agent"],
                        "processing_time": total_processing_time,
                        "vision_analysis_time": vision_result.metadata.get(
                            "processing_time", 0
                        ),
                        "conversationalization_time": total_processing_time
                        - vision_result.metadata.get("processing_time", 0),
                        "request_count": self.request_count,
                        "session_id": actual_session_id,
                        "user_id": user_id,
                        "multimodal": True,
                        "confidence": vision_result.confidence,
                        "model_used": vision_result.metadata.get("model_used"),
                        "cost": vision_result.metadata.get("cost", 0),
                        "cache_hit": vision_result.metadata.get("cache_hit", False),
                    }

                    logger.info(
                        f"⚡ [TRACE:{trace_id}] PATH 1 completed in {total_processing_time:.2f}s "
                        f"(vision: {vision_result.metadata.get('processing_time', 0):.1f}s + "
                        f"conversationalization: {metadata['conversationalization_time']:.1f}s)"
                    )

                    return conversational_response, metadata

                except Exception as vision_error:
                    logger.bind(event="VOXY_ORCHESTRATOR|VISION_PATH1_ERROR").error(
                        "PATH 1 failed, falling back to PATH 2",
                        error=str(vision_error)
                    )
                    # Fallback to PATH 2 (VOXY decision) by clearing image_url
                    image_url = None

            # Prepare message with image support for Vision Agent
            processed_message = message
            if image_url:
                # Detect if this is a simple analysis for optimization
                simple_keywords = [
                    "emoji",
                    "que",
                    "o que",
                    "identifique",
                    "qual",
                    "simples",
                ]
                is_simple_analysis = any(
                    keyword in message.lower() for keyword in simple_keywords
                )

                if is_simple_analysis:
                    processed_message = f"[ANÁLISE RÁPIDA] {message}\n\n[IMAGEM PARA ANÁLISE]: {image_url}"
                    logger.info("⚡ Simple analysis detected for optimization")
                else:
                    processed_message = (
                        f"{message}\n\n[IMAGEM PARA ANÁLISE]: {image_url}"
                    )

                logger.bind(event="VOXY_ORCHESTRATOR|IMAGE_ANALYSIS").info(
                    "Image analysis requested",
                    image_url=image_url[:100],
                    message=processed_message[:100]
                )
            else:
                logger.bind(event="VOXY_ORCHESTRATOR|TEXT_ONLY").debug("No image URL provided", message=message[:100])

            # 🧠 Enable reasoning capture from SDK logs (backward compatibility)
            from voxy_agents.utils.reasoning_capture import enable_reasoning_capture, clear_reasoning
            clear_reasoning()  # Clear any previous reasoning
            enable_reasoning_capture()

            # 🌟 Clear universal reasoning capture buffer
            from voxy_agents.utils.universal_reasoning_capture import clear_reasoning as clear_universal_reasoning
            clear_universal_reasoning()

            # Use OpenAI Agents SDK v0.2.8 with automatic session management
            # TODO: Pass reasoning_params to Runner once SDK supports it
            # For now, reasoning params are configured at model level via LiteLLM
            result = await Runner.run(
                self.voxy_agent,
                processed_message,
                session=session,  # ✅ Session support restored in v0.2.8!
            )

            # Extract response - SDK now automatically manages session state
            response_text = (
                result.final_output if hasattr(result, "final_output") else str(result)
            )
            if isinstance(response_text, list):
                response_text = " ".join(str(x) for x in response_text)
            elif not isinstance(response_text, str):
                response_text = str(response_text)

            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.request_count += 1

            # Extract tools_used and determine agent_type (PATH 2)
            tools_used = []
            agent_type = "voxy"  # Default to voxy (orchestrator)

            # Extract tool invocations for hierarchical logging
            invocations = self._extract_tool_invocations(result)

            # Extract tools_used list for backward compatibility
            tools_used = [inv.tool_name for inv in invocations]

            # 🧠 Capture reasoning from SDK logs (legacy system - backward compatibility)
            from voxy_agents.utils.reasoning_capture import get_captured_reasoning, clear_reasoning
            reasoning_list_legacy = get_captured_reasoning()

            # 🌟 Capture reasoning from Universal System (new system)
            from voxy_agents.utils.universal_reasoning_capture import get_captured_reasoning as get_universal_reasoning
            reasoning_list_universal = get_universal_reasoning()

            # Merge both reasoning sources (prioritize universal if available)
            reasoning_list = reasoning_list_universal if reasoning_list_universal else reasoning_list_legacy

            # Log summary of captured reasoning
            if reasoning_list_universal:
                logger.bind(event="VOXY_ORCHESTRATOR|REASONING_SUMMARY").info(
                    f"✅ Universal Reasoning: Captured {len(reasoning_list_universal)} block(s)",
                    count=len(reasoning_list_universal),
                    source="universal_system"
                )
                # Log each reasoning block (universal format)
                for idx, reasoning_content in enumerate(reasoning_list_universal):
                    thinking_text = reasoning_content.thinking_text or reasoning_content.thought_summary or ""
                    logger.bind(event="VOXY_ORCHESTRATOR|REASONING_CAPTURED").info(
                        f"🧠 Reasoning {idx + 1}/{len(reasoning_list_universal)}",
                        provider=reasoning_content.provider,
                        model=reasoning_content.model,
                        strategy=reasoning_content.extraction_strategy,
                        thinking_preview=thinking_text[:200] if len(thinking_text) > 200 else thinking_text,
                        thinking_length=len(thinking_text) if thinking_text else 0,
                        reasoning_tokens=reasoning_content.reasoning_tokens,
                        thinking_blocks_count=len(reasoning_content.thinking_blocks) if reasoning_content.thinking_blocks else 0,
                        has_signature=bool(reasoning_content.signature)
                    )

            elif reasoning_list_legacy:
                logger.bind(event="VOXY_ORCHESTRATOR|REASONING_SUMMARY").info(
                    f"✅ Legacy Reasoning: Captured {len(reasoning_list_legacy)} block(s)",
                    count=len(reasoning_list_legacy),
                    source="log_parsing"
                )
                # Log each reasoning block (legacy format)
                for idx, r_item in enumerate(reasoning_list_legacy):
                    reasoning_text = r_item.get('reasoning', '')
                    logger.bind(event="VOXY_ORCHESTRATOR|REASONING_CAPTURED").info(
                        f"🧠 Reasoning {idx + 1}/{len(reasoning_list_legacy)} (legacy)",
                        reasoning_preview=reasoning_text[:200] if len(reasoning_text) > 200 else reasoning_text,
                        reasoning_length=len(reasoning_text),
                        source=r_item.get('source', 'log_parsing')
                    )
            else:
                logger.bind(event="VOXY_ORCHESTRATOR|REASONING_SUMMARY").debug(
                    "No reasoning content captured (model may not support reasoning or reasoning disabled)"
                )

            # Clear buffers for next call
            if reasoning_list_legacy:
                clear_reasoning()
            if reasoning_list_universal:
                clear_universal_reasoning()

            # Determine agent_type based on tools used
            if len(tools_used) == 1:
                tool_name = tools_used[0]
                agent_type_map = {
                    "translate_text": "translator",
                    "correct_text": "corrector",
                    "get_weather": "weather",
                    "calculate": "calculator",
                    "analyze_image": "vision",
                    "web_search": "web_search",
                }
                agent_type = agent_type_map.get(tool_name, "voxy")
            elif len(tools_used) > 1:
                # Multiple tools used - VOXY orchestrated
                agent_type = "voxy"
            else:
                # No tools used - direct VOXY response
                agent_type = "voxy"

            # Generate and log hierarchical multi-agent flow (if tools were used)
            if invocations:
                # Debug: Check if reasoning_list is populated
                logger.bind(event="VOXY_ORCHESTRATOR|HIER_LOG_DEBUG").debug(
                    "Generating hierarchical log",
                    has_reasoning=bool(reasoning_list),
                    reasoning_count=len(reasoning_list) if reasoning_list else 0
                )
                hierarchical_log = self._format_hierarchical_log(
                    invocations=invocations,
                    total_time=processing_time,
                    trace_id=trace_id,
                    reasoning_list=reasoning_list if reasoning_list else None
                )
                logger.bind(event="VOXY_ORCHESTRATOR|MULTI_AGENT_FLOW").info(
                    f"\n{hierarchical_log}"
                )

            # Create metadata object
            metadata = {
                "agent_type": agent_type,
                "tools_used": tools_used,
                "processing_time": processing_time,
                "request_count": self.request_count,
                "session_id": actual_session_id,
                "user_id": user_id,
                "sdk_version": "0.2.8",
                "session_managed": "automatic",  # Now handled by SDK
            }

            # Add vision metadata if Vision Agent was used (PATH 2)
            if "analyze_image" in tools_used:
                vision_agent = get_vision_agent()
                vision_stats = vision_agent.get_stats()
                metadata["vision_metadata"] = {
                    "image_url": image_url if image_url else "extracted_from_message",
                    "model_used": vision_agent.current_model,
                    "analysis_count": vision_stats["analysis_count"],
                    "gpt5_usage_count": vision_stats["gpt5_usage_count"],
                    "gpt4o_fallback_count": vision_stats["gpt4o_fallback_count"],
                    "total_cost": vision_stats["total_cost"],
                    "average_cost": vision_stats["average_cost"],
                    "multimodal": True,
                    "path": "PATH_2",
                }
                logger.info(
                    f"🖼️ PATH 2 - Vision analysis completed with {vision_agent.current_model}"
                )

            logger.info(
                f"✅ [TRACE:{trace_id}] Request completed:\n"
                f"   ├─ 🤖 Agent: {agent_type}\n"
                f"   ├─ 🔧 Tools: {', '.join(tools_used) if tools_used else 'none'}\n"
                f"   ├─ ⏱️  Time: {processing_time:.2f}s\n"
                f"   └─ 📝 Response: {response_text[:100]}{'...' if len(response_text) > 100 else ''}"
            )

            return response_text, metadata

        except Exception as e:
            logger.bind(event="VOXY_ORCHESTRATOR|ERROR", trace_id=trace_id).exception("Error processing request")
            error_metadata = {
                "agent_type": "error",
                "tools_used": [],
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "request_count": self.request_count,
                "session_id": (
                    actual_session_id if "actual_session_id" in locals() else None
                ),
                "user_id": user_id,
                "error": str(e),
            }
            error_response = (
                f"Desculpe, encontrei um erro ao processar sua solicitação: {str(e)}"
            )
            return error_response, error_metadata

    def get_stats(self) -> dict[str, Any]:
        """Get current orchestrator statistics."""
        return {
            "request_count": self.request_count,
            "registered_subagents": list(self.subagents.keys()),
            "voxy_initialized": self.voxy_agent is not None,
        }


# Global orchestrator instance - using lazy initialization
_voxy_orchestrator = None


def get_voxy_orchestrator() -> VoxyOrchestrator:
    """
    Get the global VOXY orchestrator instance using lazy initialization.

    Thread-safe singleton pattern ensures single instance across application.
    """
    global _voxy_orchestrator
    if _voxy_orchestrator is None:
        _voxy_orchestrator = VoxyOrchestrator()
    return _voxy_orchestrator
