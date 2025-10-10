"""
Tests for Vision Agent.

This mirrors src/voxy_agents/core/subagents/vision_agent.py
Tests refactored for OpenAI Agents SDK + LiteLLM architecture.
"""

from unittest.mock import AsyncMock, MagicMock, patch

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
            mock_config.reasoning_effort = "medium"
            mock_config.enable_postprocessing = True
            mock_config.cache_ttl_base = 600
            mock_config.get_litellm_model_path.return_value = "openrouter/openai/gpt-4o"
            mock_config_loader.return_value = mock_config
            yield mock_config

    @pytest.fixture
    def mock_runner(self):
        """Create a mock Runner.run."""
        with patch("src.voxy_agents.core.subagents.vision_agent.Runner.run") as mock:
            result = MagicMock()
            result.final_output = "Test vision analysis result"
            result.usage = None  # Simula ausência de usage
            mock.return_value = result
            yield mock

    @pytest.fixture
    def mock_vision_cache(self):
        """Create a mock vision cache."""
        with patch(
            "src.voxy_agents.core.subagents.vision_agent.VisionCache"
        ) as mock_cache_class:
            mock_cache = AsyncMock()
            mock_cache_class.return_value = mock_cache

            # Mock cache methods
            mock_cache.get_cached_analysis = AsyncMock(
                return_value=None
            )  # Cache miss by default
            mock_cache.store_analysis = AsyncMock()
            mock_cache.get_cache_stats = MagicMock(
                return_value={"hit_rate": "0%", "total_hits": 0, "total_requests": 1}
            )

            yield mock_cache

    @pytest.fixture
    def mock_adaptive_reasoning(self):
        """Create a mock adaptive reasoning system."""
        with patch(
            "src.voxy_agents.core.subagents.vision_agent.adaptive_reasoning"
        ) as mock_reasoning:
            mock_reasoning.determine_reasoning_effort = MagicMock(
                return_value=(MagicMock(value="minimal"), {"estimated_time": 5.0})
            )
            mock_reasoning.update_performance_stats = MagicMock()
            yield mock_reasoning

    @pytest.fixture
    def agent(
        self, mock_vision_config, mock_runner, mock_vision_cache, mock_adaptive_reasoning
    ):
        """Create Vision Agent with mocked dependencies."""
        with patch("src.voxy_agents.core.subagents.vision_agent.LitellmModel"):
            with patch("src.voxy_agents.core.subagents.vision_agent.Agent"):
                agent = VisionAgent()
                return agent

    def test_agent_initialization(self, agent, mock_vision_config):
        """Test agent initializes correctly with SDK."""
        assert agent.name == "Vision Agent"
        assert agent.agent_type == "vision"
        assert agent.total_cost == 0.0
        assert agent.analysis_count == 0
        assert hasattr(agent, "config")
        assert hasattr(agent, "agent")
        assert hasattr(agent, "vision_cache")
        assert agent.config.provider == "openrouter"
        assert agent.config.model_name == "openai/gpt-4o"

    @pytest.mark.asyncio
    async def test_analyze_image_basic_flow(self, agent, mock_runner):
        """Test basic image analysis flow with Runner."""
        # Test input
        image_url = "https://example.com/test.jpg"
        query = "que emoji é este?"

        # Call analyze_image
        result = await agent.analyze_image(
            image_url=image_url,
            query=query,
            analysis_type="general",
            detail_level="basic",
        )

        # Verify result structure (VisionAnalysisResult)
        assert result.success is True
        assert "Test vision analysis result" in result.analysis
        assert result.confidence > 0.0
        assert result.metadata["agent_type"] == "vision"
        assert result.metadata["cache_hit"] is False
        assert "processing_time" in result.metadata
        assert "cost" in result.metadata
        assert result.metadata["model_used"] == "openrouter/openai/gpt-4o"

        # Verify Runner.run was called
        mock_runner.assert_called_once()

        # Verify agent stats updated
        assert agent.analysis_count == 1

    @pytest.mark.asyncio
    async def test_analyze_image_with_cache_hit(self, agent, mock_vision_cache):
        """Test image analysis with cache hit."""
        # Setup cache hit
        cached_result = "Cached analysis result"
        cached_metadata = {
            "processing_time": 0.5,
            "cost": 0.02,
            "cache_level": "L1",
            "confidence": 0.95,
        }
        mock_vision_cache.get_cached_analysis.return_value = (
            cached_result,
            cached_metadata,
        )

        # Call analyze_image
        result = await agent.analyze_image(
            image_url="https://example.com/test.jpg", query="analyze this image"
        )

        # Verify cache result (VisionAnalysisResult)
        assert result.success is True
        assert result.analysis == cached_result
        assert result.metadata["cache_hit"] is True
        assert result.metadata["agent_type"] == "vision"
        assert result.metadata["cache_optimized"] is True

        # Verify no API call was made
        assert agent.analysis_count == 1  # Counter still increments

    @pytest.mark.asyncio
    async def test_analyze_image_failure(self, agent, mock_runner):
        """Test handling of analysis failure."""
        # Setup Runner.run to fail
        mock_runner.side_effect = Exception("Model failed")

        # Call analyze_image
        result = await agent.analyze_image(
            image_url="https://example.com/test.jpg", query="analyze this image"
        )

        # Verify error handling (VisionAnalysisResult)
        assert result.success is False
        assert result.error == "Model failed"
        assert result.metadata["agent_type"] == "vision"
        assert result.metadata["cache_hit"] is False

    def test_rate_limiting_setup(self, agent):
        """Test rate limiting setup."""
        # Test basic rate limiting configuration
        assert agent.requests_in_current_minute == 0
        assert agent.requests_in_current_hour == 0
        assert agent.last_request_time is None

    def test_build_analysis_prompt_simple_query(self, agent):
        """Test prompt building for simple queries."""
        prompt = agent._build_analysis_prompt(
            query="que emoji é este?",
            analysis_type="general",
            detail_level="basic",
            specific_questions=None,
        )

        assert "Responda de forma direta e concisa" in prompt
        assert "que emoji é este?" in prompt

    def test_build_analysis_prompt_complex_query(self, agent):
        """Test prompt building for complex queries."""
        prompt = agent._build_analysis_prompt(
            query="análise detalhada desta imagem",
            analysis_type="technical",
            detail_level="detailed",
            specific_questions=["Qual a qualidade?", "Há problemas?"],
        )

        assert "Analise esta imagem com foco em 'technical'" in prompt
        assert "aspectos técnicos" in prompt
        assert "análise detalhada" in prompt
        assert "Qual a qualidade?" in prompt
        assert "Há problemas?" in prompt

    def test_get_stats(self, agent, mock_vision_config):
        """Test statistics retrieval (SDK version)."""
        # Set some test data
        agent.analysis_count = 10
        agent.total_cost = 0.25

        stats = agent.get_stats()

        assert stats["agent_type"] == "vision"
        assert stats["multimodal"] is True
        assert stats["model_configured"] == "openrouter/openai/gpt-4o"
        assert stats["provider"] == "openrouter"
        assert stats["analysis_count"] == 10
        assert stats["total_cost"] == 0.25
        assert stats["average_cost"] == 0.025
        assert "cache_stats" in stats
        # Removed: gpt5_usage_count, gpt4o_fallback_count, gpt5_success_rate

    def test_extract_cost_from_runner_result(self, agent):
        """Test cost extraction from Runner result."""
        # Mock result with usage
        mock_result = MagicMock()
        mock_result.final_output = "Test analysis with 20 words repeated " * 5
        mock_result.usage = None  # No usage available

        cost = agent._extract_cost_from_runner_result(mock_result)

        # Should return fallback estimate
        assert isinstance(cost, float)
        assert cost > 0.0
        assert cost <= 0.1  # Reasonable upper bound

    def test_health_check_configuration(self, agent):
        """Test health check configuration."""
        # Test health check method exists
        assert hasattr(agent, "health_check")
        assert callable(agent.health_check)

    def test_compatibility_methods(self, agent):
        """Test VOXY Orchestrator compatibility methods."""
        assert agent.get_tool_name() == "analyze_image"
        assert "multimodal" in agent.get_tool_description().lower()

    def test_process_tool_call_configuration(self, agent):
        """Test tool call configuration."""
        # Test tool call method exists
        assert hasattr(agent, "process_tool_call")
        assert callable(agent.process_tool_call)

    def test_multimodal_message_structure(self, agent):
        """Test that multimodal messages are built correctly."""
        # This is tested implicitly in analyze_image tests
        # Verify agent has necessary attributes
        assert hasattr(agent, "agent")  # SDK Agent
        assert hasattr(agent, "config")  # Model configuration


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
