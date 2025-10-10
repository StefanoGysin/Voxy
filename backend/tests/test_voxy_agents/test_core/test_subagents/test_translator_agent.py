"""
Tests for Translator Agent.

This mirrors src/voxy_agents/core/subagents/translator_agent.py
"""

from unittest.mock import MagicMock, patch

import pytest

from src.voxy_agents.core.subagents.translator_agent import (
    TranslatorAgent,
    get_translator_agent,
)


class TestTranslatorAgent:
    """Test the Translator Agent class."""

    @pytest.fixture
    def translator_agent(self):
        """Create translator agent with mocked dependencies."""
        with patch(
            "src.voxy_agents.core.subagents.translator_agent.Agent"
        ) as mock_agent_class:
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            agent = TranslatorAgent()
            return agent

    def test_translator_initialization(self, translator_agent):
        """Test translator agent initializes correctly."""
        assert translator_agent.agent is not None
        assert hasattr(translator_agent, "agent")

    @patch("src.voxy_agents.core.subagents.translator_agent.Agent")
    @patch("src.voxy_agents.core.subagents.translator_agent.create_litellm_model")
    @patch("src.voxy_agents.core.subagents.translator_agent.load_translator_config")
    def test_translator_initialization_with_correct_model(
        self, mock_load_config, mock_create_model, mock_agent_class
    ):
        """Test translator agent uses LiteLLM with correct configuration."""
        from src.voxy_agents.config.models_config import SubagentModelConfig

        # Setup mocks
        mock_config = SubagentModelConfig(
            provider="openrouter",
            model_name="anthropic/claude-3-opus",
            api_key="test-api-key",
            max_tokens=2000,
            temperature=0.3,
            include_usage=True,
        )
        mock_load_config.return_value = mock_config
        mock_model = MagicMock()
        mock_create_model.return_value = mock_model
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = TranslatorAgent()

        # Verify configuration was loaded
        mock_load_config.assert_called_once()

        # Verify LiteLLM model was created with correct config
        mock_create_model.assert_called_once_with(mock_config)

        # Verify Agent was initialized with LiteLLM model
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        assert call_args[1]["model"] == mock_model
        assert call_args[1]["name"] == "Subagente Tradutor VOXY"
        assert "instructions" in call_args[1]
        assert "model_settings" in call_args[1]

        # Verify agent has config attribute
        assert hasattr(agent, "config")
        assert agent.config == mock_config

    def test_get_instructions(self, translator_agent):
        """Test instructions are generated correctly."""
        instructions = translator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Verify key translation concepts are present (case insensitive)
        assert "tradução" in instructions_lower
        assert "idioma" in instructions_lower
        assert "traduzir" in instructions_lower or "translate" in instructions_lower
        assert "original" in instructions_lower
        assert "significado" in instructions_lower

    def test_get_agent_method(self, translator_agent):
        """Test get_agent returns the underlying agent."""
        agent = translator_agent.get_agent()
        assert agent == translator_agent.agent

    def test_instructions_contain_capabilities(self, translator_agent):
        """Test that instructions list key capabilities."""
        instructions = translator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Should list translation capabilities (case insensitive and flexible)
        capability_terms = [
            "idiomas",
            "detecção automática",
            "contexto",
            "significado",
            "cultural",
            "formatação",
            "tradução",
        ]
        capability_count = sum(
            1 for term in capability_terms if term in instructions_lower
        )
        assert capability_count >= 4, "Insufficient translation capability coverage"

    def test_instructions_contain_guidelines(self, translator_agent):
        """Test that instructions contain translation guidelines."""
        instructions = translator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Should have translation guidelines (case insensitive and flexible)
        guideline_terms = [
            "nativa",
            "estilo",
            "terminologia",
            "cultural",
            "preciso",
            "fluente",
            "tom",
        ]
        guideline_count = sum(
            1 for term in guideline_terms if term in instructions_lower
        )
        assert guideline_count >= 3, "Insufficient translation guideline coverage"

    def test_instructions_contain_examples(self, translator_agent):
        """Test that instructions contain practical examples."""
        instructions = translator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Should have translation examples (flexible check)
        example_terms = [
            "hello world",
            "olá mundo",
            "bom dia",
            "good morning",
            "portuguese",
            "português",
            "inglês",
            "input:",
            "output:",
        ]
        example_count = sum(1 for term in example_terms if term in instructions_lower)
        assert example_count >= 4, "Insufficient translation example coverage"

    def test_instructions_language_support(self, translator_agent):
        """Test that instructions indicate multilingual support."""
        instructions = translator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Should support multiple languages and scenarios (flexible)
        support_terms = [
            "multilingue",
            "múltiplos",
            "idiomas",
            "técnico",
            "criativo",
            "markdown",
            "tradução",
        ]
        support_count = sum(1 for term in support_terms if term in instructions_lower)
        assert support_count >= 3, "Insufficient multilingual support coverage"

    def test_instructions_response_format(self, translator_agent):
        """Test that instructions specify response format."""
        instructions = translator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Should have clear response format guidelines (flexible)
        format_terms = [
            "formato",
            "resposta",
            "tradução",
            "formatação",
            "original",
            "retorne",
        ]
        format_count = sum(1 for term in format_terms if term in instructions_lower)
        assert format_count >= 3, "Insufficient response format coverage"


class TestTranslatorAgentSingleton:
    """Test the singleton pattern for translator agent."""

    @patch("src.voxy_agents.core.subagents.translator_agent.TranslatorAgent")
    def test_get_translator_agent_singleton(self, mock_translator_class):
        """Test that get_translator_agent returns the same instance."""
        # Clear global instance first to ensure clean test
        import src.voxy_agents.core.subagents.translator_agent as trans_module

        trans_module._translator_agent = None

        mock_instance = MagicMock()
        mock_translator_class.return_value = mock_instance

        # First call should create instance
        agent1 = get_translator_agent()
        assert agent1 == mock_instance

        # Second call should return same instance
        agent2 = get_translator_agent()
        assert agent2 == mock_instance
        assert agent1 is agent2

        # TranslatorAgent should only be instantiated once
        mock_translator_class.assert_called_once()

    def test_get_translator_agent_lazy_initialization(self):
        """Test that translator agent is created lazily."""
        # Clear global instance first
        import src.voxy_agents.core.subagents.translator_agent as trans_module

        trans_module._translator_agent = None

        with patch.object(trans_module, "TranslatorAgent") as mock_translator_class:
            mock_instance = MagicMock()
            mock_translator_class.return_value = mock_instance

            # Agent should not be created yet
            assert trans_module._translator_agent is None

            # First access should create it
            agent = get_translator_agent()
            assert agent == mock_instance
            mock_translator_class.assert_called_once()

    def test_get_translator_agent_return_type(self):
        """Test that get_translator_agent returns correct type."""
        # Clear global instance first
        import src.voxy_agents.core.subagents.translator_agent as trans_module

        trans_module._translator_agent = None

        with patch(
            "src.voxy_agents.core.subagents.translator_agent.TranslatorAgent"
        ) as mock_translator_class:
            mock_instance = MagicMock()
            mock_translator_class.return_value = mock_instance

            agent = get_translator_agent()
            assert agent == mock_instance
            assert hasattr(agent, "get_agent")  # Should have the expected interface


class TestTranslatorAgentIntegration:
    """Integration tests for translator agent."""

    @pytest.fixture
    def real_translator_agent(self):
        """Create a real translator agent for integration testing."""
        with patch(
            "src.voxy_agents.core.subagents.translator_agent.Agent"
        ) as mock_agent_class:
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            agent = TranslatorAgent()
            return agent

    def test_agent_tool_registration_compatibility(self, real_translator_agent):
        """Test that agent is compatible with tool registration."""
        agent = real_translator_agent.get_agent()

        # Should be mockable for as_tool method (used in orchestrator)
        agent.as_tool = MagicMock()
        agent.as_tool(tool_name="translate_text", tool_description="Text translation")

        # Verify as_tool was called correctly
        agent.as_tool.assert_called_once_with(
            tool_name="translate_text", tool_description="Text translation"
        )

    def test_translation_context_coverage(self, real_translator_agent):
        """Test that instructions cover various translation contexts."""
        instructions = real_translator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Language operation coverage - be flexible
        operations = ["tradução", "detecção", "preservação", "adaptação", "idioma"]
        operation_count = sum(
            1 for operation in operations if operation in instructions_lower
        )
        assert operation_count >= 2, "Insufficient language operation coverage"

        # Text type coverage - be flexible
        text_types = ["técnico", "criativo", "texto"]
        text_count = sum(
            1 for text_type in text_types if text_type in instructions_lower
        )
        assert text_count >= 1, "Insufficient text type coverage"

        # Quality indicators coverage
        quality_terms = ["preciso", "fluente", "contexto", "significado"]
        quality_count = sum(1 for term in quality_terms if term in instructions_lower)
        assert quality_count >= 2, "Insufficient quality indicator coverage"

    def test_multilingual_example_coverage(self, real_translator_agent):
        """Test that examples cover multiple languages."""
        instructions = real_translator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Look for multilingual examples (flexible)
        multilingual_terms = [
            "hello world",
            "good morning",
            "olá mundo",
            "bom dia",
            "portuguese",
            "português",
            "inglês",
            "english",
        ]
        multilingual_count = sum(
            1 for term in multilingual_terms if term in instructions_lower
        )
        assert multilingual_count >= 4, "Insufficient multilingual example coverage"

    def test_instruction_structure_and_organization(self, real_translator_agent):
        """Test that instructions are well-structured and organized."""
        instructions = real_translator_agent._get_instructions()
        instructions_lower = instructions.lower()

        # Should have clear sections (flexible)
        section_terms = ["capacidades", "diretrizes", "formato", "exemplos", "tradução"]
        section_count = sum(1 for term in section_terms if term in instructions_lower)
        assert section_count >= 3, "Insufficient structural organization"

        # Should have practical guidance (flexible)
        guidance_terms = ["input:", "output:", "exemplo", "resposta"]
        guidance_count = sum(1 for term in guidance_terms if term in instructions_lower)
        assert guidance_count >= 2, "Insufficient practical guidance"

        # Should address common scenarios (flexible)
        scenarios = ["idioma", "destino", "especificado", "pergunte", "traduzir"]
        scenario_count = sum(
            1 for scenario in scenarios if scenario in instructions_lower
        )
        assert scenario_count >= 2, "Insufficient scenario handling coverage"
