"""
Tests for Vision Agent.

This mirrors src/voxy_agents/core/subagents/vision_agent.py
Tests refactored for simplified SDK architecture (post-refactoring).
"""

from unittest.mock import MagicMock, patch

import pytest

from src.voxy_agents.core.subagents.vision_agent import VisionAgent, get_vision_agent


class TestVisionAgent:
    """Test the Vision Agent class."""

    @pytest.fixture
    def mock_vision_config(self):
        """Create a mock vision configuration."""
        with patch(
            "src.voxy_agents.core.subagents.vision_agent.load_vision_config"
        ) as mock_config_loader:
            mock_config = MagicMock()
            mock_config.provider = "openrouter"
            mock_config.model_name = "openai/gpt-4o"
            mock_config.api_key = "test-key"
            mock_config.temperature = 0.1
            mock_config.max_tokens = 2000
            mock_config.reasoning_enabled = True
            mock_config.reasoning_effort = "medium"
            mock_config.thinking_budget_tokens = None
            mock_config.include_usage = True
            mock_config.get_litellm_model_path.return_value = "openrouter/openai/gpt-4o"
            mock_config_loader.return_value = mock_config
            yield mock_config

    @pytest.fixture
    def mock_runner(self):
        """Create a mock Runner.run static method."""
        with patch(
            "src.voxy_agents.core.subagents.vision_agent.Runner.run"
        ) as mock_run:
            result = MagicMock()
            result.final_output = "Test vision analysis result"
            mock_run.return_value = result
            yield mock_run

    @pytest.fixture
    def mock_litellm_model(self):
        """Create a mock LiteLLM model."""
        with patch(
            "src.voxy_agents.core.subagents.vision_agent.create_litellm_model"
        ) as mock:
            mock.return_value = MagicMock()
            yield mock

    @pytest.fixture
    def mock_agent_sdk(self):
        """Create a mock Agent SDK."""
        with patch(
            "src.voxy_agents.core.subagents.vision_agent.Agent"
        ) as mock_agent_class:
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            yield mock_agent_instance

    @pytest.fixture
    def agent(
        self,
        mock_vision_config,
        mock_litellm_model,
        mock_agent_sdk,
    ):
        """Create Vision Agent with mocked dependencies."""
        with patch("src.voxy_agents.core.subagents.vision_agent.nest_asyncio"):
            agent = VisionAgent()
            return agent

    def test_agent_initialization(self, agent, mock_vision_config):
        """Test agent initializes correctly with SDK."""
        # Verify agent has required attributes
        assert hasattr(agent, "config")
        assert hasattr(agent, "agent")
        assert agent.config.provider == "openrouter"
        assert agent.config.model_name == "openai/gpt-4o"

        # Verify no custom complexity attributes exist
        assert not hasattr(agent, "total_cost")
        assert not hasattr(agent, "analysis_count")
        assert not hasattr(agent, "vision_cache")
        assert not hasattr(agent, "requests_in_current_minute")

    @pytest.mark.asyncio
    async def test_analyze_image_basic_flow(self, agent, mock_runner):
        """Test basic image analysis flow returns simple string."""
        # Test input
        image_url = "https://example.com/test.jpg"
        query = "que emoji é este?"

        # Call analyze_image
        result = await agent.analyze_image(
            image_url=image_url,
            query=query,
            user_id="test_user",
        )

        # Verify result is simple string (not VisionAnalysisResult)
        assert isinstance(result, str)
        assert "Test vision analysis result" in result

        # Verify Runner.run was called
        mock_runner.assert_called_once()

        # Verify messages structure (multimodal)
        call_args = mock_runner.call_args[0]
        # call_args[0] = agent, call_args[1] = messages, call_args[2] = session
        messages = call_args[1]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert len(messages[0]["content"]) == 2
        assert messages[0]["content"][0]["type"] == "input_text"
        assert messages[0]["content"][1]["type"] == "input_image"

    @pytest.mark.asyncio
    async def test_analyze_image_failure(self, agent, mock_runner):
        """Test handling of analysis failure."""
        # Setup Runner.run to fail
        mock_runner.side_effect = Exception("Model failed")

        # Call analyze_image should raise exception
        with pytest.raises(Exception) as exc_info:
            await agent.analyze_image(
                image_url="https://example.com/test.jpg",
                query="analyze this image",
                user_id="test_user",
            )

        assert "Model failed" in str(exc_info.value)

    def test_get_agent(self, agent):
        """Test get_agent returns underlying Agent instance."""
        underlying_agent = agent.get_agent()
        assert underlying_agent is not None

    def test_process_tool_call_sync_wrapper(self, agent, mock_runner):
        """Test process_tool_call is synchronous wrapper."""
        # Verify method exists
        assert hasattr(agent, "process_tool_call")
        assert callable(agent.process_tool_call)

        # Note: Full test would require asyncio event loop setup
        # This is tested in integration tests

    def test_enhance_query_basic(self, agent):
        """Test _enhance_query with basic parameters."""
        enhanced = agent._enhance_query(
            query="que emoji é este?",
            analysis_type="general",
            detail_level="basic",
            specific_questions=None,
        )

        assert "Responda de forma direta e concisa" in enhanced
        assert "que emoji é este?" in enhanced

    def test_enhance_query_with_analysis_type(self, agent):
        """Test _enhance_query with analysis type."""
        enhanced = agent._enhance_query(
            query="analyze image",
            analysis_type="ocr",
            detail_level="standard",
            specific_questions=None,
        )

        assert "extração e transcrição" in enhanced

    def test_enhance_query_with_detail_level(self, agent):
        """Test _enhance_query with detail level."""
        enhanced = agent._enhance_query(
            query="analyze image",
            analysis_type="general",
            detail_level="comprehensive",
            specific_questions=None,
        )

        assert "extremamente detalhada" in enhanced

    def test_enhance_query_with_specific_questions(self, agent):
        """Test _enhance_query with specific questions."""
        enhanced = agent._enhance_query(
            query="analyze image",
            analysis_type="general",
            detail_level="standard",
            specific_questions=["Qual a qualidade?", "Há problemas?"],
        )

        assert "Qual a qualidade?" in enhanced
        assert "Há problemas?" in enhanced

    def test_no_removed_methods(self, agent):
        """Test that removed methods no longer exist."""
        # These methods were removed in refactoring
        assert not hasattr(agent, "get_stats")
        assert not hasattr(agent, "_build_analysis_prompt")
        assert not hasattr(agent, "_extract_cost_from_runner_result")
        assert not hasattr(agent, "health_check")
        assert not hasattr(agent, "get_tool_name")
        assert not hasattr(agent, "get_tool_description")
        assert not hasattr(agent, "_check_rate_limits")


class TestGetVisionAgent:
    """Test the get_vision_agent singleton function."""

    def test_get_vision_agent_singleton(self):
        """Test that get_vision_agent returns singleton instance."""
        with patch(
            "src.voxy_agents.core.subagents.vision_agent.VisionAgent"
        ) as mock_agent_class:
            # Clear any existing global instance
            import src.voxy_agents.core.subagents.vision_agent as agent_module

            agent_module._vision_agent = None

            mock_instance = MagicMock()
            mock_agent_class.return_value = mock_instance

            # First call should create new instance
            agent1 = get_vision_agent()

            # Second call should return same instance
            agent2 = get_vision_agent()

            # Should be the same instance
            assert agent1 is agent2
            assert agent1 is mock_instance

            # VisionAgent should only be instantiated once
            mock_agent_class.assert_called_once()

    def test_get_vision_agent_existing_instance(self):
        """Test get_vision_agent when instance already exists."""
        with patch(
            "src.voxy_agents.core.subagents.vision_agent.VisionAgent"
        ) as mock_agent_class:
            # Set up existing global instance
            import src.voxy_agents.core.subagents.vision_agent as agent_module

            existing_instance = MagicMock()
            agent_module._vision_agent = existing_instance

            # Call get_vision_agent
            result = get_vision_agent()

            # Should return existing instance without creating new one
            assert result is existing_instance
            mock_agent_class.assert_not_called()

            # Clean up
            agent_module._vision_agent = None
