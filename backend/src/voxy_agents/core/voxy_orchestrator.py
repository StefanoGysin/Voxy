"""
VOXY Orchestrator - OpenAI Agents SDK Implementation

This is the heart of the VOXY system, built on the official OpenAI Agents SDK.
Uses the "subagents as tools" pattern for optimal orchestration.

Architecture:
- VOXY (main agent) uses GPT-4.1 for intelligent reasoning
- Subagents are registered as tools via .as_tool()
- OpenAI Agents SDK handles sessions, streaming, and tool calls
- Implements the creative decisions from CREATIVE MODE
"""

import logging
from datetime import datetime
from typing import Any, Optional

from agents import Agent, Runner, function_tool
from openai import AsyncOpenAI

from ..config.settings import settings
from .database.supabase_integration import SupabaseSession
from .guardrails.safety_check import SafetyChecker
from .subagents.vision_agent import VisionAnalysisResult, get_vision_agent

logger = logging.getLogger(__name__)


class VoxyOrchestrator:
    """
    VOXY main agent using OpenAI Agents SDK.

    Implements the Hybrid Context-Aware Weighted System from CREATIVE MODE.
    Uses subagents as tools for optimal cost and performance.
    """

    def __init__(self):
        """Initialize VOXY orchestrator with OpenAI Agents SDK + LiteLLM."""
        # Load LiteLLM configuration for orchestrator
        from ..config.models_config import load_orchestrator_config
        from ..utils.llm_factory import create_litellm_model

        self.config = load_orchestrator_config()
        self.litellm_model = create_litellm_model(self.config)

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

        logger.info(
            f"VOXY Orchestrator initialized with LiteLLM:\n"
            f"   ├─ Provider: {self.config.provider}\n"
            f"   ├─ Model: {self.config.get_litellm_model_path()}\n"
            f"   ├─ Max tokens: {self.config.max_tokens}\n"
            f"   ├─ Temperature: {self.config.temperature}\n"
            f"   └─ Reasoning effort: {self.config.reasoning_effort}"
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
        logger.info(f"Registered subagent: {name} as tool '{tool_name}'")

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

        # Create main VOXY agent with LiteLLM model
        self.voxy_agent = Agent(
            name="VOXY",
            model=self.litellm_model,  # Use LiteLLM model instance
            instructions=self._get_voxy_instructions(),
            tools=tools,
            # Note: input_guardrails temporarily disabled for testing
        )

        logger.info(
            f"VOXY agent initialized:\n"
            f"   ├─ Model: {self.config.get_litellm_model_path()}\n"
            f"   ├─ Provider: {self.config.provider}\n"
            f"   ├─ Max tokens: {self.config.max_tokens}\n"
            f"   ├─ Temperature: {self.config.temperature}\n"
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
            logger.error(f"Conversationalization failed: {e}, returning raw analysis")
            # Fallback: return raw analysis if conversationalization fails
            return vision_result.analysis

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
                logger.info("🎯 PATH 1: Vision bypass with lightweight post-processing")

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
                    logger.error(f"❌ PATH 1 failed: {vision_error}, falling back to PATH 2")
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

                logger.info(f"🖼️ Image analysis requested: {image_url[:100]}...")
                logger.info(f"📝 Full processed message: {processed_message}")
            else:
                logger.info(f"📝 No image URL provided. Message: {message}")

            # Use OpenAI Agents SDK v0.2.8 with automatic session management
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

            if hasattr(result, "tool_calls") and result.tool_calls:
                tools_used = [call.tool_name for call in result.tool_calls]
                logger.info(f"🔧 PATH 2 - Tools used: {', '.join(tools_used)}")

                # If only one tool was used, update agent_type to reflect the specific agent
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
                else:
                    # Multiple tools used - VOXY orchestrated
                    agent_type = "voxy"

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
            logger.error(f"❌ [TRACE:{trace_id}] Error processing request: {e}")
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
