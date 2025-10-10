"""
Tests for VOXY Orchestrator.

This mirrors src/voxy_agents/core/voxy_orchestrator.py
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.voxy_agents.core.voxy_orchestrator import (
    VoxyOrchestrator,
    get_voxy_orchestrator,
)


class TestVoxyOrchestrator:
    """Test the VOXY Orchestrator class."""

    @pytest.fixture
    def mock_orchestrator_config(self):
        """Mock orchestrator LiteLLM configuration."""
        mock_config = MagicMock()
        mock_config.provider = "openrouter"
        mock_config.model_name = "anthropic/claude-sonnet-4.5"
        mock_config.max_tokens = 4000
        mock_config.temperature = 0.3
        mock_config.reasoning_effort = "medium"
        mock_config.enable_streaming = False
        mock_config.get_litellm_model_path.return_value = (
            "openrouter/anthropic/claude-sonnet-4.5"
        )
        return mock_config

    @pytest.fixture
    def mock_litellm_model(self):
        """Mock LiteLLM model instance (using string for Agent SDK compatibility)."""
        # Agent SDK accepts strings, Model instances, or None
        # For tests, we use a string representing the model path
        return "openrouter/anthropic/claude-sonnet-4.5"

    @pytest.fixture
    def mock_agent_wrapper(self):
        """Create a mock agent wrapper."""
        wrapper = MagicMock()
        mock_agent = MagicMock()
        wrapper.get_agent.return_value = mock_agent
        return wrapper, mock_agent

    @pytest.fixture
    def orchestrator(self, mock_orchestrator_config, mock_litellm_model):
        """Create orchestrator with mocked dependencies."""
        with (
            patch(
                "src.voxy_agents.core.voxy_orchestrator.SafetyChecker"
            ) as mock_safety,
            patch(
                "src.voxy_agents.config.models_config.load_orchestrator_config"
            ) as mock_load_config,
            patch(
                "src.voxy_agents.utils.llm_factory.create_litellm_model"
            ) as mock_create_model,
        ):
            mock_safety_instance = mock_safety.return_value
            mock_safety_instance.is_safe = AsyncMock(return_value=True)

            # Mock config and model loading
            mock_load_config.return_value = mock_orchestrator_config
            mock_create_model.return_value = mock_litellm_model

            orchestrator = VoxyOrchestrator()
            return orchestrator

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes correctly."""
        assert orchestrator.subagents == {}
        assert orchestrator.total_cost == 0.0
        assert orchestrator.request_count == 0
        assert orchestrator.voxy_agent is None
        assert hasattr(orchestrator, "safety_checker")

    def test_register_subagent(self, orchestrator, mock_agent_wrapper):
        """Test registering a subagent."""
        wrapper, mock_agent = mock_agent_wrapper

        orchestrator.register_subagent(
            name="translator",
            agent=mock_agent,
            tool_name="translate_text",
            description="Test translator",
        )

        assert "translator" in orchestrator.subagents
        assert orchestrator.subagents["translator"]["agent"] == mock_agent
        assert orchestrator.subagents["translator"]["tool_name"] == "translate_text"
        assert orchestrator.subagents["translator"]["description"] == "Test translator"

    @pytest.mark.asyncio
    async def test_chat_basic_flow(self, orchestrator):
        """Test basic chat flow."""
        with (
            patch("src.voxy_agents.core.voxy_orchestrator.Runner") as mock_runner_class,
            patch(
                "src.voxy_agents.core.voxy_orchestrator.SupabaseSession"
            ) as mock_session_class,
        ):
            # Setup mock response
            mock_result = MagicMock()
            mock_result.final_output = "Test response from VOXY"
            mock_runner_class.run = AsyncMock(return_value=mock_result)

            mock_session_instance = MagicMock()
            mock_session_class.return_value = mock_session_instance

            # Test
            response, metadata = await orchestrator.chat("Hello", "user123")

            # Verify
            assert "Test response from VOXY" in response
            assert metadata["agent_type"] == "voxy"  # Default agent_type
            assert metadata["user_id"] == "user123"
            assert "session_id" in metadata
            assert "processing_time" in metadata

    @pytest.mark.asyncio
    async def test_chat_with_session_id(self, orchestrator):
        """Test chat with existing session ID."""
        with (
            patch("src.voxy_agents.core.voxy_orchestrator.Runner") as mock_runner_class,
            patch(
                "src.voxy_agents.core.voxy_orchestrator.SupabaseSession"
            ) as mock_session_class,
        ):
            # Setup mock response
            mock_result = MagicMock()
            mock_result.final_output = "Test response with session"
            mock_runner_class.run = AsyncMock(return_value=mock_result)

            mock_session_instance = MagicMock()
            mock_session_class.return_value = mock_session_instance

            # Test with existing session
            response, metadata = await orchestrator.chat(
                "Hello", "user123", "existing_session"
            )

            # Verify
            assert "Test response with session" in response
            assert metadata["session_id"] == "existing_session"
            assert metadata["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_chat_error_handling(self, orchestrator):
        """Test chat error handling."""
        with patch(
            "src.voxy_agents.core.voxy_orchestrator.Runner"
        ) as mock_runner_class:
            # Setup mock to raise exception
            mock_runner_class.run = AsyncMock(side_effect=Exception("Runner failed"))

            # Test
            response, metadata = await orchestrator.chat("Hello", "user123")

            # Verify error handling
            assert "erro" in response.lower()
            assert metadata["agent_type"] == "error"
            assert "error" in metadata

    def test_get_stats(self, orchestrator):
        """Test getting orchestrator statistics."""
        # Set some test data
        orchestrator.request_count = 15
        orchestrator.subagents = {
            "translator": {"tool_name": "translate", "description": "Translator"},
            "calculator": {"tool_name": "calculate", "description": "Calculator"},
        }

        # Get stats
        stats = orchestrator.get_stats()

        # Verify based on actual implementation
        assert stats["request_count"] == 15
        assert stats["registered_subagents"] == ["translator", "calculator"]
        assert stats["voxy_initialized"] == (orchestrator.voxy_agent is not None)

    def test_setup_voxy_agent(self, orchestrator, mock_agent_wrapper):
        """Test VOXY agent initialization."""
        wrapper, mock_agent = mock_agent_wrapper

        # Setup mock agent with as_tool method
        mock_agent.as_tool = MagicMock(return_value=MagicMock())

        # Register some subagents first
        orchestrator.register_subagent("translator", mock_agent, "translate", "Test")
        orchestrator.register_subagent("calculator", mock_agent, "calculate", "Test")

        with (
            patch("src.voxy_agents.core.voxy_orchestrator.Agent") as mock_agent_class,
            patch(
                "src.voxy_agents.core.voxy_orchestrator.function_tool"
            ) as mock_function_tool,
        ):
            mock_voxy_instance = MagicMock()
            mock_agent_class.return_value = mock_voxy_instance
            mock_function_tool.return_value = MagicMock()

            # Test initialization
            orchestrator._initialize_voxy_agent()

            # Verify VOXY agent was created
            assert orchestrator.voxy_agent == mock_voxy_instance
            mock_agent_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_voxy_agent_initialization_multiple_calls(self, orchestrator):
        """Test that multiple initialization calls don't recreate the agent."""
        with patch("src.voxy_agents.core.voxy_orchestrator.Agent") as mock_agent_class:
            mock_voxy_instance = MagicMock()
            mock_agent_class.return_value = mock_voxy_instance

            # First call should create agent
            orchestrator._initialize_voxy_agent()
            assert orchestrator.voxy_agent == mock_voxy_instance

            # Second call should not recreate
            orchestrator._initialize_voxy_agent()
            assert orchestrator.voxy_agent == mock_voxy_instance
            mock_agent_class.assert_called_once()  # Only called once

    def test_get_voxy_instructions(self, orchestrator):
        """Test VOXY instructions generation."""
        instructions = orchestrator._get_voxy_instructions()

        # Verify key elements are present
        assert "VOXY" in instructions
        assert "subagentes" in instructions
        assert "translate_text" in instructions
        assert "correct_text" in instructions
        assert "get_weather" in instructions
        assert "calculate" in instructions

    def test_web_search_tool_execution(self, orchestrator):
        """Test that web_search tool is executed and returns formatted result (Line 92)."""
        with (
            patch(
                "src.voxy_agents.core.voxy_orchestrator.function_tool"
            ) as mock_function_tool,
            patch("src.voxy_agents.core.voxy_orchestrator.Agent") as mock_agent_class,
        ):
            # Capture the web_search function when it's created
            captured_web_search = None

            def capture_function_tool(func):
                nonlocal captured_web_search
                captured_web_search = func
                return func

            mock_function_tool.side_effect = capture_function_tool
            mock_agent_class.return_value = MagicMock()

            # Initialize agent to create the web_search tool
            orchestrator._initialize_voxy_agent()

            # Test the web_search function directly (Line 92)
            assert captured_web_search is not None
            result = captured_web_search("test query")
            assert result == "Web search results for: test query"

    @pytest.mark.asyncio
    async def test_create_safety_guardrail(self, orchestrator):
        """Test safety guardrail creation and execution (Lines 146-155)."""
        # Mock the safety checker
        orchestrator.safety_checker.is_safe = AsyncMock(return_value=True)

        # Mock the dynamic imports inside the method
        with (
            patch("agents.GuardrailFunctionOutput") as mock_output,
            patch("agents.InputGuardrail") as mock_guardrail,
        ):
            mock_output_instance = MagicMock()
            mock_output.return_value = mock_output_instance
            mock_guardrail_instance = MagicMock()
            mock_guardrail.return_value = mock_guardrail_instance

            # Test guardrail creation
            guardrail = await orchestrator._create_safety_guardrail()

            # Verify InputGuardrail was created
            mock_guardrail.assert_called_once()
            assert guardrail == mock_guardrail_instance

            # Test the safety check function inside the guardrail
            guardrail_function = mock_guardrail.call_args[1]["guardrail_function"]

            # Mock context and agent
            mock_ctx = MagicMock()
            mock_agent = MagicMock()
            test_input = "test input"

            # Call the safety check function (tests lines 148-155)
            await guardrail_function(mock_ctx, mock_agent, test_input)

            # Verify safety checker was called
            orchestrator.safety_checker.is_safe.assert_called_once_with(test_input)

            # Verify output was created correctly
            mock_output.assert_called_once_with(
                tripwire_triggered=False,  # not is_safe (True) = False
                output_info={"safe": True},
            )

    @pytest.mark.asyncio
    async def test_create_safety_guardrail_unsafe_input(self, orchestrator):
        """Test safety guardrail with unsafe input."""
        # Mock the safety checker to return False (unsafe)
        orchestrator.safety_checker.is_safe = AsyncMock(return_value=False)

        # Mock the dynamic imports inside the method
        with (
            patch("agents.GuardrailFunctionOutput") as mock_output,
            patch("agents.InputGuardrail") as mock_guardrail,
        ):
            mock_guardrail.return_value = MagicMock()

            # Create guardrail
            await orchestrator._create_safety_guardrail()

            # Get the safety check function
            guardrail_function = mock_guardrail.call_args[1]["guardrail_function"]

            # Test with unsafe input
            await guardrail_function(MagicMock(), MagicMock(), "unsafe input")

            # Verify unsafe input triggers the guardrail
            mock_output.assert_called_once_with(
                tripwire_triggered=True,  # not is_safe (False) = True
                output_info={"safe": False},
            )

    @pytest.mark.asyncio
    async def test_chat_response_list_handling(self, orchestrator):
        """Test chat handling when result is a list (Line 207)."""
        with (
            patch("src.voxy_agents.core.voxy_orchestrator.Runner") as mock_runner_class,
            patch("src.voxy_agents.core.voxy_orchestrator.SupabaseSession"),
        ):
            # Setup mock response as list
            mock_result = MagicMock()
            mock_result.final_output = ["First part", "Second part", "Third part"]
            mock_runner_class.run = AsyncMock(return_value=mock_result)

            # Test
            response, metadata = await orchestrator.chat("Hello", "user123")

            # Verify list was joined into string (Line 207)
            assert response == "First part Second part Third part"
            assert metadata["agent_type"] == "voxy"

    @pytest.mark.asyncio
    async def test_chat_response_non_string_handling(self, orchestrator):
        """Test chat handling when result is not a string (Line 209)."""
        with (
            patch("src.voxy_agents.core.voxy_orchestrator.Runner") as mock_runner_class,
            patch("src.voxy_agents.core.voxy_orchestrator.SupabaseSession"),
        ):
            # Setup mock response as non-string object
            mock_result = MagicMock()
            mock_result.final_output = {"message": "response", "status": "success"}
            mock_runner_class.run = AsyncMock(return_value=mock_result)

            # Test
            response, metadata = await orchestrator.chat("Hello", "user123")

            # Verify non-string was converted to string (Line 209)
            assert isinstance(response, str)
            assert "message" in response  # Dictionary should be stringified
            assert metadata["agent_type"] == "voxy"

    @pytest.mark.asyncio
    async def test_chat_single_tool_agent_type_mapping(self, orchestrator):
        """Test agent_type mapping when single tool is used (Lines 225-233)."""
        with (
            patch("src.voxy_agents.core.voxy_orchestrator.Runner") as mock_runner_class,
            patch("src.voxy_agents.core.voxy_orchestrator.SupabaseSession"),
        ):
            # Test each tool mapping
            tool_mappings = [
                ("translate_text", "translator"),
                ("correct_text", "corrector"),
                ("get_weather", "weather"),
                ("calculate", "calculator"),
                ("web_search", "web_search"),
                ("unknown_tool", "voxy"),  # Default case
            ]

            for tool_name, expected_agent_type in tool_mappings:
                # Setup mock response with single tool call
                mock_result = MagicMock()
                mock_result.final_output = f"Response from {tool_name}"
                mock_result.tool_calls = [MagicMock(tool_name=tool_name)]
                mock_runner_class.run = AsyncMock(return_value=mock_result)

                # Test
                response, metadata = await orchestrator.chat("Hello", "user123")

                # Verify correct agent_type mapping (Lines 225-233)
                assert metadata["agent_type"] == expected_agent_type
                assert metadata["tools_used"] == [tool_name]

    @pytest.mark.asyncio
    async def test_chat_multiple_tools_agent_type(self, orchestrator):
        """Test agent_type remains 'voxy' when multiple tools are used."""
        with (
            patch("src.voxy_agents.core.voxy_orchestrator.Runner") as mock_runner_class,
            patch("src.voxy_agents.core.voxy_orchestrator.SupabaseSession"),
        ):
            # Setup mock response with multiple tool calls
            mock_result = MagicMock()
            mock_result.final_output = "Response using multiple tools"
            mock_result.tool_calls = [
                MagicMock(tool_name="translate_text"),
                MagicMock(tool_name="calculate"),
            ]
            mock_runner_class.run = AsyncMock(return_value=mock_result)

            # Test
            response, metadata = await orchestrator.chat("Hello", "user123")

            # Verify agent_type remains 'voxy' for multiple tools
            assert metadata["agent_type"] == "voxy"
            assert metadata["tools_used"] == ["translate_text", "calculate"]

    @pytest.mark.asyncio
    async def test_chat_no_tools_used(self, orchestrator):
        """Test chat when no tools are used."""
        with (
            patch("src.voxy_agents.core.voxy_orchestrator.Runner") as mock_runner_class,
            patch("src.voxy_agents.core.voxy_orchestrator.SupabaseSession"),
        ):
            # Setup mock response with no tool calls
            mock_result = MagicMock()
            mock_result.final_output = "Direct response from VOXY"
            mock_result.tool_calls = []  # No tools used
            mock_runner_class.run = AsyncMock(return_value=mock_result)

            # Test
            response, metadata = await orchestrator.chat("Hello", "user123")

            # Verify defaults when no tools are used
            assert metadata["agent_type"] == "voxy"
            assert metadata["tools_used"] == []

    @pytest.mark.asyncio
    async def test_chat_result_without_tool_calls_attribute(self, orchestrator):
        """Test chat when result doesn't have tool_calls attribute."""
        with (
            patch("src.voxy_agents.core.voxy_orchestrator.Runner") as mock_runner_class,
            patch("src.voxy_agents.core.voxy_orchestrator.SupabaseSession"),
        ):
            # Setup mock response without tool_calls attribute
            mock_result = MagicMock()
            mock_result.final_output = "Response without tool calls"
            # Don't set tool_calls attribute at all
            if hasattr(mock_result, "tool_calls"):
                delattr(mock_result, "tool_calls")

            mock_runner_class.run = AsyncMock(return_value=mock_result)

            # Test
            response, metadata = await orchestrator.chat("Hello", "user123")

            # Verify defaults when no tool_calls attribute
            assert metadata["agent_type"] == "voxy"
            assert metadata["tools_used"] == []

    @pytest.mark.asyncio
    async def test_vision_bypass_integration(self, orchestrator):
        """Test Vision Agent Agents SDK Bypass integration."""
        with patch(
            "src.voxy_agents.core.voxy_orchestrator.direct_vision_processor"
        ) as mock_processor:
            # Setup mock for DirectVisionProcessor
            mock_result = "**🔍 Análise Visual (general)**\n\nEste é um emoji sorridente.\n\n---\n*Análise direta GPT-5 em 2.3s (custo: $0.0250)*"
            mock_metadata = {
                "processing_time": 2.3,
                "api_time": 1.8,
                "reasoning_level": "minimal",
                "cost": 0.0250,
                "bypass_used": True,
                "cache_hit": False,
            }
            mock_processor.analyze_image_direct = AsyncMock(
                return_value=(mock_result, mock_metadata)
            )
            mock_processor.get_bypass_stats.return_value = {
                "total_calls": 5,
                "total_time_saved": "185.0s",
                "success_rate": "100.0%",
                "overhead_eliminated": "~37s per call (Agents SDK bypassed)",
            }

            # Test vision request with image
            response, metadata = await orchestrator.chat(
                "que emoji é este?",
                "user123",
                image_url="https://example.com/emoji.png",
            )

            # Verify bypass was used
            assert "Análise direta GPT-5" in response
            assert metadata["agent_type"] == "vision"
            assert metadata["tools_used"] == ["direct_vision_processor"]
            assert metadata["bypass_used"] is True
            assert metadata["agents_sdk_bypassed"] is True
            assert metadata["overhead_eliminated"] == "~37s"
            assert "bypass_stats" in metadata["vision_metadata"]

            # Verify DirectVisionProcessor was called correctly
            mock_processor.analyze_image_direct.assert_called_once_with(
                image_url="https://example.com/emoji.png",
                query="que emoji é este?",
                analysis_type="general",
                detail_level="basic",
            )

    def test_is_vision_request_detection(self, orchestrator):
        """Test vision request detection logic."""
        # Vision requests
        assert orchestrator._is_vision_request("que emoji é este?") is True
        assert orchestrator._is_vision_request("analise esta imagem") is True
        assert orchestrator._is_vision_request("o que vejo na foto?") is True
        assert orchestrator._is_vision_request("identifique este objeto") is True
        assert orchestrator._is_vision_request("qual a cor do cabelo?") is True

        # Non-vision requests
        assert orchestrator._is_vision_request("como está o tempo?") is False
        assert orchestrator._is_vision_request("traduza hello para português") is False
        assert orchestrator._is_vision_request("calcule 2 + 2") is False

    def test_determine_analysis_type(self, orchestrator):
        """Test analysis type determination from message."""
        assert orchestrator._determine_analysis_type("ler o texto da imagem") == "ocr"
        assert (
            orchestrator._determine_analysis_type("análise técnica detalhada")
            == "technical"
        )
        assert (
            orchestrator._determine_analysis_type("composição artística") == "artistic"
        )
        assert orchestrator._determine_analysis_type("dados do gráfico") == "document"
        assert orchestrator._determine_analysis_type("que emoji é este?") == "general"

    def test_determine_detail_level(self, orchestrator):
        """Test detail level determination from message."""
        assert orchestrator._determine_detail_level("que emoji é este?") == "basic"
        assert orchestrator._determine_detail_level("análise rápida simples") == "basic"
        assert (
            orchestrator._determine_detail_level("análise detalhada completa")
            == "detailed"
        )
        assert (
            orchestrator._determine_detail_level("análise comprehensive")
            == "comprehensive"
        )
        assert orchestrator._determine_detail_level("descreva a imagem") == "standard"

    @pytest.mark.asyncio
    async def test_vision_bypass_not_triggered_without_image(self, orchestrator):
        """Test that bypass is not triggered when no image is provided."""
        with (
            patch(
                "src.voxy_agents.core.voxy_orchestrator.direct_vision_processor"
            ) as mock_processor,
            patch("src.voxy_agents.core.voxy_orchestrator.Runner") as mock_runner_class,
            patch("src.voxy_agents.core.voxy_orchestrator.SupabaseSession"),
        ):
            # Setup regular SDK response
            mock_result = MagicMock()
            mock_result.final_output = "Regular response without image"
            mock_runner_class.run = AsyncMock(return_value=mock_result)

            # Test vision-like request without image
            response, metadata = await orchestrator.chat("que emoji é este?", "user123")

            # Verify bypass was NOT used
            mock_processor.analyze_image_direct.assert_not_called()
            assert metadata["agent_type"] == "voxy"  # Regular flow
            assert "bypass_used" not in metadata

    @pytest.mark.asyncio
    async def test_vision_bypass_not_triggered_for_non_vision_with_image(
        self, orchestrator
    ):
        """Test that bypass is not triggered for non-vision requests even with image."""
        with (
            patch(
                "src.voxy_agents.core.voxy_orchestrator.direct_vision_processor"
            ) as mock_processor,
            patch("src.voxy_agents.core.voxy_orchestrator.Runner") as mock_runner_class,
            patch("src.voxy_agents.core.voxy_orchestrator.SupabaseSession"),
        ):
            # Setup regular SDK response
            mock_result = MagicMock()
            mock_result.final_output = "Weather response"
            mock_runner_class.run = AsyncMock(return_value=mock_result)

            # Test non-vision request with image (should use regular flow)
            response, metadata = await orchestrator.chat(
                "como está o tempo?",
                "user123",
                image_url="https://example.com/image.png",
            )

            # Verify bypass was NOT used (non-vision request)
            mock_processor.analyze_image_direct.assert_not_called()
            assert "bypass_used" not in metadata


class TestGetVoxyOrchestrator:
    """Test the get_voxy_orchestrator singleton function."""

    def test_get_voxy_orchestrator_singleton(self):
        """Test that get_voxy_orchestrator returns singleton instance (Lines 291-293)."""
        with patch(
            "src.voxy_agents.core.voxy_orchestrator.VoxyOrchestrator"
        ) as mock_orchestrator_class:
            # Clear any existing global instance
            import src.voxy_agents.core.voxy_orchestrator as orchestrator_module

            orchestrator_module._voxy_orchestrator = None

            mock_instance = MagicMock()
            mock_orchestrator_class.return_value = mock_instance

            # First call should create new instance
            orchestrator1 = get_voxy_orchestrator()

            # Second call should return same instance
            orchestrator2 = get_voxy_orchestrator()

            # Should be the same instance
            assert orchestrator1 is orchestrator2
            assert orchestrator1 is mock_instance

            # VoxyOrchestrator should only be instantiated once (line 292)
            mock_orchestrator_class.assert_called_once()

    def test_get_voxy_orchestrator_existing_instance(self):
        """Test get_voxy_orchestrator when instance already exists."""
        with patch(
            "src.voxy_agents.core.voxy_orchestrator.VoxyOrchestrator"
        ) as mock_orchestrator_class:
            # Set up existing global instance
            import src.voxy_agents.core.voxy_orchestrator as orchestrator_module

            existing_instance = MagicMock()
            orchestrator_module._voxy_orchestrator = existing_instance

            # Call get_voxy_orchestrator
            result = get_voxy_orchestrator()

            # Should return existing instance without creating new one
            assert result is existing_instance
            mock_orchestrator_class.assert_not_called()

            # Clean up
            orchestrator_module._voxy_orchestrator = None
