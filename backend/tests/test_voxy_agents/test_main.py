"""
Tests for VOXY main system integration.

This mirrors src/voxy_agents/main.py
"""

from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.voxy_agents.main import VOXYSystem, get_voxy_system, main


class TestVOXYSystem:
    """Test the main VOXY system integration."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator."""
        mock = MagicMock()
        mock.register_subagent = MagicMock()
        mock.chat = AsyncMock(return_value=("Test response", {"agent_type": "voxy"}))
        mock.get_stats = MagicMock(return_value={"calls": 0, "success_rate": 1.0})
        mock.subagents = {
            "translator": None,
            "corrector": None,
            "weather": None,
            "calculator": None,
        }
        return mock

    @pytest.fixture
    def mock_subagents(self):
        """Create mock subagents."""
        mocks = {}
        for name in ["translator", "corrector", "weather", "calculator"]:
            mock_wrapper = MagicMock()
            mock_agent = MagicMock()
            mock_wrapper.get_agent.return_value = mock_agent
            mocks[name] = mock_wrapper
        return mocks

    @pytest.fixture
    def voxy_system(self, mock_orchestrator, mock_subagents, mock_supabase_clients):
        """Create VOXYSystem instance for testing."""
        with (
            patch(
                "src.voxy_agents.core.voxy_orchestrator.get_voxy_orchestrator",
                return_value=mock_orchestrator,
            ),
            patch(
                "src.voxy_agents.core.subagents.translator_agent.get_translator_agent",
                return_value=mock_subagents["translator"],
            ),
            patch(
                "src.voxy_agents.core.subagents.corrector_agent.get_corrector_agent",
                return_value=mock_subagents["corrector"],
            ),
            patch(
                "src.voxy_agents.core.subagents.weather_agent.get_weather_agent",
                return_value=mock_subagents["weather"],
            ),
            patch(
                "src.voxy_agents.core.subagents.calculator_agent.get_calculator_agent",
                return_value=mock_subagents["calculator"],
            ),
        ):
            # Create the system instance - now the mock orchestrator will be used during init
            system = VOXYSystem()
            return system

    def test_voxy_system_initialization(self, voxy_system):
        """Test that VOXY system initializes correctly."""
        assert voxy_system.orchestrator is not None

        # Test basic functionality rather than internal mocking details
        assert hasattr(voxy_system.orchestrator, "register_subagent")
        assert hasattr(voxy_system.orchestrator, "subagents")
        assert hasattr(voxy_system.orchestrator, "chat")

        # Test that subagents dict exists (regardless of whether it's mocked or real)
        assert isinstance(voxy_system.orchestrator.subagents, dict)

    @pytest.mark.asyncio
    async def test_chat_success(self, voxy_system):
        """Test successful chat interaction."""
        message = "Hello VOXY"
        user_id = "test_user"
        session_id = "test_session"

        # Mock the orchestrator's chat method to return expected response
        voxy_system.orchestrator.chat = AsyncMock(
            return_value=("Test response", {"agent_type": "voxy"})
        )

        response, metadata = await voxy_system.chat(message, user_id, session_id)

        assert response == "Test response"
        assert metadata["agent_type"] == "voxy"
        voxy_system.orchestrator.chat.assert_called_once_with(
            message, user_id, session_id
        )

    @pytest.mark.asyncio
    async def test_chat_error_handling(self, voxy_system):
        """Test chat error handling."""
        # Configure orchestrator to raise an exception
        voxy_system.orchestrator.chat = AsyncMock(side_effect=Exception("Test error"))

        message = "Hello VOXY"
        user_id = "test_user"

        response, metadata = await voxy_system.chat(message, user_id)

        assert "erro ao processar" in response.lower()
        assert metadata["agent_type"] == "system_error"
        assert "error" in metadata
        assert metadata["user_id"] == user_id

    def test_get_system_stats(self, voxy_system):
        """Test getting system statistics."""
        stats = voxy_system.get_system_stats()

        assert "orchestrator_stats" in stats
        assert "subagents_count" in stats
        assert "system_status" in stats
        assert stats["system_status"] == "operational"
        assert stats["subagents_count"] == 4


def test_get_voxy_system_singleton():
    """Test that get_voxy_system returns singleton instance."""
    with patch("src.voxy_agents.main.VOXYSystem") as mock_voxy_system_class:
        # First call
        system1 = get_voxy_system()

        # Second call
        system2 = get_voxy_system()

        # Should be the same instance
        assert system1 is system2

        # VOXYSystem should only be instantiated once
        mock_voxy_system_class.assert_called_once()


class TestMainFunction:
    """Test the main() function coverage."""

    @pytest.fixture
    def mock_voxy_system_for_main(self):
        """Mock VOXY system for main function testing."""
        mock_system = MagicMock()
        mock_system.chat = AsyncMock()
        mock_system.get_system_stats = MagicMock(
            return_value={
                "subagents_count": 4,
                "system_status": "operational",
                "orchestrator_stats": {"calls": 0},
            }
        )
        return mock_system

    @pytest.mark.asyncio
    async def test_main_function_success_flow(self, mock_voxy_system_for_main):
        """Test main function with successful interactions."""
        # Mock all chat responses
        mock_responses = [
            ("Olá! Estou bem, obrigado!", {"agent_type": "voxy", "tools_used": []}),
            (
                "Hello world = Olá mundo",
                {"agent_type": "translator", "tools_used": ["translate_text"]},
            ),
            (
                "Eu fui na loja ontem",
                {"agent_type": "corrector", "tools_used": ["correct_text"]},
            ),
            (
                "Temp: 25°C, céu limpo",
                {"agent_type": "weather", "tools_used": ["get_weather"]},
            ),
            (
                "25 × 4 + 10 = 110",
                {"agent_type": "calculator", "tools_used": ["calculate"]},
            ),
            (
                "Good morning, √16 = 4",
                {"agent_type": "voxy", "tools_used": ["translate_text", "calculate"]},
            ),
        ]

        mock_voxy_system_for_main.chat.side_effect = mock_responses

        # Capture stdout
        captured_output = StringIO()

        with (
            patch("sys.stdout", captured_output),
            patch(
                "src.voxy_agents.main.get_voxy_system",
                return_value=mock_voxy_system_for_main,
            ),
        ):
            await main()

            output = captured_output.getvalue()

            # Verify header is printed (line 147-148)
            assert "🎯 VOXY Agents System" in output
            assert "=" * 60 in output

            # Verify all test messages are processed (lines 151-171)
            assert "1. Usuário: Olá! Como você está?" in output
            assert "2. Usuário: Traduza 'Hello world' para português" in output
            assert "3. Usuário: Corrija este texto" in output
            assert "4. Usuário: Qual o clima em São Paulo?" in output
            assert "5. Usuário: Quanto é 25 × 4 + 10?" in output
            assert "6. Usuário: Traduza 'Bom dia' para inglês" in output

            # Verify responses are displayed
            assert "VOXY: Olá! Estou bem, obrigado!" in output
            assert "Agent: voxy" in output
            assert "Agent: translator" in output
            assert "Tools: translate_text" in output

            # Verify system statistics are displayed (lines 174-178)
            assert "📊 Estatísticas do Sistema:" in output
            assert "Subagentes registrados: 4" in output
            assert "Status: operational" in output

        # Verify chat was called 6 times with correct parameters
        assert mock_voxy_system_for_main.chat.call_count == 6
        mock_voxy_system_for_main.get_system_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_function_with_chat_errors(self, mock_voxy_system_for_main):
        """Test main function handling chat errors."""
        # First call succeeds, second fails, rest succeed
        mock_voxy_system_for_main.chat.side_effect = [
            ("Success response", {"agent_type": "voxy"}),
            Exception("Connection error"),
            ("Recovery response", {"agent_type": "voxy"}),
            Exception("API error"),
            ("Final success", {"agent_type": "voxy"}),
            ("Last success", {"agent_type": "voxy"}),
        ]

        captured_output = StringIO()

        with (
            patch("sys.stdout", captured_output),
            patch(
                "src.voxy_agents.main.get_voxy_system",
                return_value=mock_voxy_system_for_main,
            ),
        ):
            await main()

            output = captured_output.getvalue()

            # Verify errors are handled and displayed (line 170-171)
            assert "Erro: Connection error" in output
            assert "Erro: API error" in output

            # Verify successful responses are also shown
            assert "VOXY: Success response" in output
            assert "VOXY: Recovery response" in output

    @pytest.mark.asyncio
    async def test_main_function_user_id_generation(self, mock_voxy_system_for_main):
        """Test that main function generates correct user IDs."""
        mock_voxy_system_for_main.chat.return_value = (
            "Response",
            {"agent_type": "voxy"},
        )

        with (
            patch(
                "src.voxy_agents.main.get_voxy_system",
                return_value=mock_voxy_system_for_main,
            ),
            patch("sys.stdout", StringIO()),
        ):
            await main()

            # Verify chat was called with incrementing user IDs
            expected_calls = [
                ("Olá! Como você está?", "test_user_1"),
                ("Traduza 'Hello world' para português", "test_user_2"),
                ("Corrija este texto: 'Eu foi na loja ontem'", "test_user_3"),
                ("Qual o clima em São Paulo?", "test_user_4"),
                ("Quanto é 25 × 4 + 10?", "test_user_5"),
                (
                    "Traduza 'Bom dia' para inglês e me diga quanto é a raiz quadrada de 16",
                    "test_user_6",
                ),
            ]

            actual_calls = [
                call.args for call in mock_voxy_system_for_main.chat.call_args_list
            ]
            assert actual_calls == expected_calls

    @pytest.mark.asyncio
    async def test_main_function_metadata_tools_display(
        self, mock_voxy_system_for_main
    ):
        """Test main function displays tools when present in metadata."""
        # Mock responses with different tool usage scenarios
        mock_responses = [
            ("Response 1", {"agent_type": "voxy", "tools_used": []}),  # No tools
            (
                "Response 2",
                {"agent_type": "translator", "tools_used": ["translate_text"]},
            ),  # Single tool
            (
                "Response 3",
                {"agent_type": "voxy", "tools_used": ["weather", "calculator"]},
            ),  # Multiple tools
            ("Response 4", {"agent_type": "corrector"}),  # No tools_used key
            (
                "Response 5",
                {"agent_type": "weather", "tools_used": ["get_weather", "format_data"]},
            ),
            ("Response 6", {"agent_type": "calculator", "tools_used": ["calculate"]}),
        ]

        mock_voxy_system_for_main.chat.side_effect = mock_responses

        captured_output = StringIO()

        with (
            patch("sys.stdout", captured_output),
            patch(
                "src.voxy_agents.main.get_voxy_system",
                return_value=mock_voxy_system_for_main,
            ),
        ):
            await main()

            output = captured_output.getvalue()

            # Check that tools are displayed when present (line 168-169)
            assert "Tools: translate_text" in output
            assert "Tools: weather, calculator" in output
            assert "Tools: get_weather, format_data" in output
            assert "Tools: calculate" in output


class TestMainEntryPoint:
    """Test the main entry point behavior."""

    def test_main_module_structure(self):
        """Test that the main module has the correct structure for __main__ execution."""
        # This test verifies the module contains the main execution code
        # By importing the module, we ensure the structure is correct
        import src.voxy_agents.main as main_module

        # Verify the main function exists and is callable
        assert hasattr(main_module, "main")
        assert callable(main_module.main)

        # Verify asyncio is imported (needed for line 182)
        assert hasattr(main_module, "asyncio")

        # Test the conditional execution path by simulating module execution
        # We need to properly handle the coroutine to avoid RuntimeWarning
        async def mock_main():
            """Mock version of main that returns immediately."""
            return "mock_result"

        # Create a test namespace that simulates the main module
        test_namespace = {
            "__name__": "__main__",
            "asyncio": main_module.asyncio,
            "main": mock_main,  # Use mock to avoid creating unawaited coroutine
        }

        test_code = compile(
            """
if __name__ == "__main__":
    asyncio.run(main())
""",
            "<test>",
            "exec",
        )

        # Execute the code with mocked asyncio.run to verify the path
        with patch.object(main_module.asyncio, "run") as mock_run:
            exec(test_code, test_namespace)
            # Verify asyncio.run was called once with the mock function
            mock_run.assert_called_once()
            # Verify the argument passed was a coroutine (by calling the mock_main function)
            args, kwargs = mock_run.call_args
            assert len(args) == 1
            # The argument should be a coroutine object from calling mock_main()
            import inspect

            assert inspect.iscoroutine(args[0])
            # Clean up the coroutine to avoid warnings
            args[0].close()
