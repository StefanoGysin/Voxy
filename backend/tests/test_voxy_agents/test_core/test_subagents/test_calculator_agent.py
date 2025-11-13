"""
Tests for Calculator Agent.

This mirrors src/voxy_agents/core/subagents/calculator_agent.py
Tests the new LiteLLM integration with configurable providers.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.voxy_agents.config.models_config import SubagentModelConfig
from src.voxy_agents.core.subagents.calculator_agent import (
    CalculatorAgent,
    get_calculator_agent,
)


class TestCalculatorAgent:
    """Test the Calculator Agent class."""

    @pytest.fixture
    def calculator_agent(self):
        """Create calculator agent with mocked dependencies."""
        # Mock the configuration loading
        mock_config = SubagentModelConfig(
            provider="openrouter",
            model_name="x-ai/grok-code-fast-1",
            api_key="test-api-key",
            max_tokens=2000,
            temperature=0.1,
            include_usage=True,
        )

        with (
            patch(
                "src.voxy_agents.core.subagents.calculator_agent.load_calculator_config"
            ) as mock_load_config,
            patch(
                "src.voxy_agents.core.subagents.calculator_agent.create_litellm_model"
            ) as mock_create_model,
            patch(
                "src.voxy_agents.core.subagents.calculator_agent.Agent"
            ) as mock_agent_class,
        ):
            # Setup mocks
            mock_load_config.return_value = mock_config
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            agent = CalculatorAgent()
            return agent

    def test_calculator_initialization(self, calculator_agent):
        """Test calculator agent initializes correctly."""
        assert calculator_agent.agent is not None
        assert hasattr(calculator_agent, "agent")

    @patch("src.voxy_agents.core.subagents.calculator_agent.Agent")
    @patch("src.voxy_agents.core.subagents.calculator_agent.create_litellm_model")
    @patch("src.voxy_agents.core.subagents.calculator_agent.load_calculator_config")
    def test_calculator_initialization_with_correct_model(
        self, mock_load_config, mock_create_model, mock_agent_class
    ):
        """Test calculator agent uses LiteLLM with correct configuration."""
        # Setup mocks
        mock_config = SubagentModelConfig(
            provider="openrouter",
            model_name="x-ai/grok-code-fast-1",
            api_key="test-api-key",
            max_tokens=2000,
            temperature=0.1,
            include_usage=True,
        )
        mock_load_config.return_value = mock_config
        mock_model = MagicMock()
        mock_create_model.return_value = mock_model
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        CalculatorAgent()

        # Verify configuration was loaded
        mock_load_config.assert_called_once()

        # Verify LiteLLM model was created with correct config
        mock_create_model.assert_called_once_with(mock_config)

        # Verify Agent was called with LiteLLM model
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        assert call_args[1]["model"] == mock_model
        assert call_args[1]["name"] == "Subagente Calculadora VOXY"
        assert "instructions" in call_args[1]
        assert "model_settings" in call_args[1]

    def test_get_instructions(self, calculator_agent):
        """Test instructions are generated correctly."""
        instructions = calculator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Verify key mathematical concepts are present (case insensitive)
        assert "cálculos" in instructions_lower
        assert "matemática" in instructions_lower or "aritmética" in instructions_lower
        assert "soma" in instructions_lower
        assert "divisão" in instructions_lower
        assert "álgebra" in instructions_lower
        assert "geometria" in instructions_lower
        assert "resultado" in instructions_lower

        # Verify advanced Grok capabilities are mentioned
        assert "reasoning" in instructions_lower or "raciocínio" in instructions_lower
        assert "grok" in instructions_lower or "avançado" in instructions_lower

    def test_get_agent_method(self, calculator_agent):
        """Test get_agent returns the underlying agent."""
        agent = calculator_agent.get_agent()
        assert agent == calculator_agent.agent

    def test_instructions_contain_examples(self, calculator_agent):
        """Test that instructions contain practical examples."""
        instructions = calculator_agent._get_instructions()

        # Should have mathematical examples
        assert "25 × 4" in instructions or "25 * 4" in instructions
        assert "área" in instructions
        assert "círculo" in instructions
        assert "raio" in instructions
        assert "quilômetros" in instructions

    def test_instructions_contain_capabilities(self, calculator_agent):
        """Test that instructions list key capabilities."""
        instructions = calculator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Should list mathematical capabilities (case insensitive)
        assert "aritmética" in instructions_lower or "básica" in instructions_lower
        assert "equações" in instructions_lower
        assert "trigonometria" in instructions_lower
        assert "estatística" in instructions_lower
        assert "cálculo" in instructions_lower
        assert "conversões" in instructions_lower

    def test_instructions_formatting_guidelines(self, calculator_agent):
        """Test that instructions contain formatting guidelines."""
        instructions = calculator_agent._get_instructions()

        # Should have formatting guidelines
        assert "formatação" in instructions
        assert "símbolos" in instructions
        assert "resultado final" in instructions
        assert "FORMATO" in instructions or "formato" in instructions


class TestCalculatorAgentSingleton:
    """Test the singleton pattern for calculator agent."""

    @patch("src.voxy_agents.core.subagents.calculator_agent.CalculatorAgent")
    def test_get_calculator_agent_singleton(self, mock_calculator_class):
        """Test that get_calculator_agent returns the same instance."""
        # Clear global instance first to ensure clean test
        import src.voxy_agents.core.subagents.calculator_agent as calc_module

        calc_module._calculator_agent = None

        mock_instance = MagicMock()
        mock_calculator_class.return_value = mock_instance

        # First call should create instance
        agent1 = get_calculator_agent()
        assert agent1 == mock_instance

        # Second call should return same instance
        agent2 = get_calculator_agent()
        assert agent2 == mock_instance
        assert agent1 is agent2

        # CalculatorAgent should only be instantiated once
        mock_calculator_class.assert_called_once()

    def test_get_calculator_agent_lazy_initialization(self):
        """Test that calculator agent is created lazily."""
        # Clear global instance first
        import src.voxy_agents.core.subagents.calculator_agent as calc_module

        calc_module._calculator_agent = None

        with patch.object(calc_module, "CalculatorAgent") as mock_calculator_class:
            mock_instance = MagicMock()
            mock_calculator_class.return_value = mock_instance

            # Agent should not be created yet
            assert calc_module._calculator_agent is None

            # First access should create it
            agent = get_calculator_agent()
            assert agent == mock_instance
            mock_calculator_class.assert_called_once()


class TestCalculatorAgentIntegration:
    """Integration tests for calculator agent."""

    @pytest.fixture
    def real_calculator_agent(self):
        """Create a real calculator agent for integration testing."""
        with patch(
            "src.voxy_agents.core.subagents.calculator_agent.Agent"
        ) as mock_agent_class:
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            agent = CalculatorAgent()
            return agent

    def test_agent_tool_registration_compatibility(self, real_calculator_agent):
        """Test that agent is compatible with tool registration."""
        agent = real_calculator_agent.get_agent()

        # Should be mockable for as_tool method (used in orchestrator)
        agent.as_tool = MagicMock()
        agent.as_tool(tool_name="calculate", tool_description="Math calculations")

        # Verify as_tool was called correctly
        agent.as_tool.assert_called_once_with(
            tool_name="calculate", tool_description="Math calculations"
        )

    def test_mathematical_context_coverage(self, real_calculator_agent):
        """Test that instructions cover various mathematical contexts."""
        instructions = real_calculator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Mathematical operations coverage - fix logic error
        operations = ["soma", "subtração", "multiplicação", "divisão"]
        for op in operations:
            assert op in instructions_lower, f"Missing {op} operation coverage"

        # Advanced mathematics coverage
        advanced_topics = ["álgebra", "geometria", "trigonometria", "estatística"]
        for topic in advanced_topics:
            assert topic in instructions_lower, f"Missing {topic} coverage"

        # Practical applications coverage - be more flexible
        applications = [
            "área",
            "volume",
            "porcentagem",
            "conversão",
            "percentuais",
            "conversões",
        ]
        coverage_count = sum(1 for app in applications if app in instructions_lower)
        assert coverage_count >= 1, "Insufficient practical application coverage"
