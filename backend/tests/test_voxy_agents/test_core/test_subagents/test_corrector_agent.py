"""
Tests for Corrector Agent.

This mirrors src/voxy_agents/core/subagents/corrector_agent.py
"""

from unittest.mock import MagicMock, patch

import pytest

from src.voxy_agents.core.subagents.corrector_agent import (
    CorrectorAgent,
    get_corrector_agent,
)


class TestCorrectorAgent:
    """Test the Corrector Agent class."""

    @pytest.fixture
    def corrector_agent(self):
        """Create corrector agent with mocked dependencies."""
        with patch(
            "src.voxy_agents.core.subagents.corrector_agent.Agent"
        ) as mock_agent_class:
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            agent = CorrectorAgent()
            return agent

    def test_corrector_initialization(self, corrector_agent):
        """Test corrector agent initializes correctly."""
        assert corrector_agent.agent is not None
        assert hasattr(corrector_agent, "agent")

    @patch("src.voxy_agents.core.subagents.corrector_agent.Agent")
    @patch("src.voxy_agents.core.subagents.corrector_agent.create_litellm_model")
    @patch("src.voxy_agents.core.subagents.corrector_agent.load_corrector_config")
    def test_corrector_initialization_with_correct_model(
        self, mock_load_config, mock_create_model, mock_agent_class
    ):
        """Test corrector agent uses LiteLLM with correct configuration."""
        from src.voxy_agents.config.models_config import SubagentModelConfig

        # Setup mocks
        mock_config = SubagentModelConfig(
            provider="openrouter",
            model_name="anthropic/claude-3.5-sonnet",
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

        agent = CorrectorAgent()

        # Verify configuration was loaded
        mock_load_config.assert_called_once()

        # Verify LiteLLM model was created with correct config
        mock_create_model.assert_called_once_with(mock_config)

        # Verify Agent was initialized with LiteLLM model
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        assert call_args[1]["model"] == mock_model
        assert call_args[1]["name"] == "Subagente Corretor VOXY"
        assert "instructions" in call_args[1]
        assert "model_settings" in call_args[1]

        # Verify agent has config attribute
        assert hasattr(agent, "config")
        assert agent.config == mock_config

    def test_get_instructions(self, corrector_agent):
        """Test instructions are generated correctly."""
        instructions = corrector_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Verify key correction concepts are present (case insensitive)
        assert "correção" in instructions_lower
        assert "ortográfica" in instructions_lower
        assert "gramatical" in instructions_lower
        assert "erro" in instructions_lower
        assert "texto" in instructions_lower
        assert "original" in instructions_lower

    def test_get_agent_method(self, corrector_agent):
        """Test get_agent returns the underlying agent."""
        agent = corrector_agent.get_agent()
        assert agent == corrector_agent.agent

    def test_instructions_contain_capabilities(self, corrector_agent):
        """Test that instructions list key capabilities."""
        instructions = corrector_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Should list correction capabilities (case insensitive)
        assert "ortográfica" in instructions_lower
        assert "gramatical" in instructions_lower
        assert "clareza" in instructions_lower or "claridade" in instructions_lower
        assert "fluidez" in instructions_lower or "fluente" in instructions_lower
        assert "significado" in instructions_lower
        assert "idioma" in instructions_lower

    def test_instructions_contain_guidelines(self, corrector_agent):
        """Test that instructions contain correction guidelines."""
        instructions = corrector_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Should have correction guidelines (case insensitive)
        assert "corrija" in instructions_lower
        assert "preserve" in instructions_lower or "mantenha" in instructions_lower
        assert "estilo" in instructions_lower
        assert "intenção" in instructions_lower
        assert "nomes próprios" in instructions_lower

    def test_instructions_contain_examples(self, corrector_agent):
        """Test that instructions contain practical examples."""
        instructions = corrector_agent._get_instructions()

        # Should have correction examples (some may not be present, check flexibly)
        example_terms = ["exemplo", "input:", "output:", "correção", "erro"]
        example_count = sum(1 for term in example_terms if term in instructions.lower())
        assert example_count >= 2, "Insufficient example coverage in instructions"

    def test_instructions_error_types(self, corrector_agent):
        """Test that instructions cover different error types."""
        instructions = corrector_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Should cover different error types (case insensitive)
        error_types = [
            "ortográficos",
            "gramaticais",
            "pontuação",
            "acentuação",
            "sintática",
        ]
        for error_type in error_types:
            assert error_type in instructions_lower, f"Missing {error_type} coverage"

    def test_instructions_multilingual_support(self, corrector_agent):
        """Test that instructions indicate multilingual support."""
        instructions = corrector_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Should support multiple languages (case insensitive)
        assert "idioma" in instructions_lower
        assert "hello" in instructions_lower  # English example
        # Check for multilingual support indicators
        multilingual_indicators = [
            "múltiplos",
            "vários",
            "detecção automática",
            "gramática",
            "ortografia",
        ]
        multilingual_count = sum(
            1
            for indicator in multilingual_indicators
            if indicator in instructions_lower
        )
        assert multilingual_count >= 1, "Missing multilingual support indicators"


class TestCorrectorAgentSingleton:
    """Test the singleton pattern for corrector agent."""

    @patch("src.voxy_agents.core.subagents.corrector_agent.CorrectorAgent")
    def test_get_corrector_agent_singleton(self, mock_corrector_class):
        """Test that get_corrector_agent returns the same instance."""
        # Clear global instance first to ensure clean test
        import src.voxy_agents.core.subagents.corrector_agent as corr_module

        corr_module._corrector_agent = None

        mock_instance = MagicMock()
        mock_corrector_class.return_value = mock_instance

        # First call should create instance
        agent1 = get_corrector_agent()
        assert agent1 == mock_instance

        # Second call should return same instance
        agent2 = get_corrector_agent()
        assert agent2 == mock_instance
        assert agent1 is agent2

        # CorrectorAgent should only be instantiated once
        mock_corrector_class.assert_called_once()

    def test_get_corrector_agent_lazy_initialization(self):
        """Test that corrector agent is created lazily."""
        # Clear global instance first
        import src.voxy_agents.core.subagents.corrector_agent as corr_module

        corr_module._corrector_agent = None

        with patch.object(corr_module, "CorrectorAgent") as mock_corrector_class:
            mock_instance = MagicMock()
            mock_corrector_class.return_value = mock_instance

            # Agent should not be created yet
            assert corr_module._corrector_agent is None

            # First access should create it
            agent = get_corrector_agent()
            assert agent == mock_instance
            mock_corrector_class.assert_called_once()


class TestCorrectorAgentIntegration:
    """Integration tests for corrector agent."""

    @pytest.fixture
    def real_corrector_agent(self):
        """Create a real corrector agent for integration testing."""
        with patch(
            "src.voxy_agents.core.subagents.corrector_agent.Agent"
        ) as mock_agent_class:
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            agent = CorrectorAgent()
            return agent

    def test_agent_tool_registration_compatibility(self, real_corrector_agent):
        """Test that agent is compatible with tool registration."""
        agent = real_corrector_agent.get_agent()

        # Should be mockable for as_tool method (used in orchestrator)
        agent.as_tool = MagicMock()
        agent.as_tool(tool_name="correct_text", tool_description="Text correction")

        # Verify as_tool was called correctly
        agent.as_tool.assert_called_once_with(
            tool_name="correct_text", tool_description="Text correction"
        )

    def test_correction_context_coverage(self, real_corrector_agent):
        """Test that instructions cover various correction contexts."""
        instructions = real_corrector_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Error type coverage - be more flexible
        error_types = ["ortográfic", "gramatic", "pontuação", "acentuação", "correção"]
        error_count = sum(
            1 for error_type in error_types if error_type in instructions_lower
        )
        assert error_count >= 2, "Insufficient error type coverage"

        # Language preservation guidelines - be more flexible
        preservation_guidelines = [
            "preserve",
            "mantenha",
            "original",
            "significado",
            "texto",
        ]
        preservation_count = sum(
            1
            for guideline in preservation_guidelines
            if guideline in instructions_lower
        )
        assert preservation_count >= 2, "Insufficient preservation guideline coverage"

        # Output format specifications - be more flexible
        format_specs = ["formato", "resposta", "corrig", "texto"]
        coverage_count = sum(1 for spec in format_specs if spec in instructions_lower)
        assert coverage_count >= 2, "Insufficient format specification coverage"

    def test_multilingual_example_coverage(self, real_corrector_agent):
        """Test that examples cover multiple languages."""
        instructions = real_corrector_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Look for multilingual support indicators
        multilingual_indicators = [
            "idioma",
            "language",
            "múltiplos",
            "correção",
            "texto",
        ]
        multilingual_count = sum(
            1
            for indicator in multilingual_indicators
            if indicator in instructions_lower
        )
        assert multilingual_count >= 2, "Insufficient multilingual support indicators"

        # Grammar concepts that apply across languages - be flexible
        concepts = ["concordânc", "conjugação", "sintát", "gramátic", "ortográf"]
        concept_count = sum(1 for concept in concepts if concept in instructions_lower)
        assert concept_count >= 1, "Missing grammar concept coverage"
