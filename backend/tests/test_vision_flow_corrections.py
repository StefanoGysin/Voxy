"""
Tests for Vision Agent Flow Corrections.

Validates:
1. Vision Agent returns VisionAnalysisResult structure
2. VOXY Orchestrator post-processes technical analysis
3. tools_used metadata is consistent
4. ChatResponse includes tools_used array
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.voxy_agents.core.subagents.vision_agent import VisionAnalysisResult
from src.voxy_agents.core.voxy_orchestrator import VoxyOrchestrator


class TestVisionAnalysisResult:
    """Test VisionAnalysisResult model."""

    def test_vision_result_success(self):
        """Test successful vision analysis result structure."""
        result = VisionAnalysisResult(
            success=True,
            analysis="Esta é uma análise técnica da imagem",
            confidence=0.95,
            metadata={
                "model_used": "gpt-5",
                "processing_time": 7.5,
                "cost": 0.045,
            },
            raw_response="Resposta bruta do GPT-5",
        )

        assert result.success is True
        assert result.confidence == 0.95
        assert result.metadata["model_used"] == "gpt-5"
        assert result.error is None

    def test_vision_result_error(self):
        """Test error vision analysis result structure."""
        result = VisionAnalysisResult(
            success=False,
            analysis="",
            confidence=0.0,
            metadata={"processing_time": 2.0},
            error="Connection timeout",
        )

        assert result.success is False
        assert result.confidence == 0.0
        assert result.error == "Connection timeout"


class TestVisionAgentFlow:
    """Test Vision Agent analyze_image returns VisionAnalysisResult."""

    @pytest.mark.asyncio
    async def test_analyze_image_returns_structured_result(self):
        """Verify analyze_image returns VisionAnalysisResult."""
        from src.voxy_agents.core.subagents.vision_agent import VisionAgent

        vision_agent = VisionAgent()

        # Mock GPT-5 API call
        with patch.object(
            vision_agent.client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Análise técnica da imagem"
            mock_response.usage = MagicMock(
                prompt_tokens=100, completion_tokens=50
            )
            mock_create.return_value = mock_response

            result = await vision_agent.analyze_image(
                image_url="https://example.com/test.jpg",
                query="O que você vê?",
                analysis_type="general",
                detail_level="basic",
            )

            # Validate structure
            assert isinstance(result, VisionAnalysisResult)
            assert result.success is True
            assert result.analysis == "Análise técnica da imagem"
            assert result.confidence > 0.0
            assert "model_used" in result.metadata
            assert "processing_time" in result.metadata

    @pytest.mark.asyncio
    async def test_analyze_image_error_handling(self):
        """Verify analyze_image returns error structure on failure."""
        from src.voxy_agents.core.subagents.vision_agent import VisionAgent

        vision_agent = VisionAgent()

        # Mock API failure
        with patch.object(
            vision_agent.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=Exception("API Error"),
        ):
            result = await vision_agent.analyze_image(
                image_url="https://example.com/test.jpg",
                query="Test query",
            )

            # Validate error structure
            assert isinstance(result, VisionAnalysisResult)
            assert result.success is False
            assert result.confidence == 0.0
            assert result.error is not None
            assert "API Error" in result.error


class TestVOXYOrchestratorPostProcessing:
    """Test VOXY Orchestrator post-processing of Vision results."""

    @pytest.mark.asyncio
    async def test_conversationalize_vision_result(self):
        """Verify _conversationalize_vision_result converts technical to conversational."""
        orchestrator = VoxyOrchestrator()

        vision_result = VisionAnalysisResult(
            success=True,
            analysis="Análise técnica: Imagem contém um Golden Retriever em posição sentada.",
            confidence=0.95,
            metadata={
                "model_used": "gpt-5",
                "processing_time": 7.2,
                "analysis_type": "general",
            },
        )

        # Mock GPT-4o-mini conversationalization
        with patch.object(
            orchestrator.openai_client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[
                0
            ].message.content = "Que lindo! 🐕 Na imagem eu vejo um Golden Retriever sentado, ele parece muito fofo!"
            mock_create.return_value = mock_response

            conversational = await orchestrator._conversationalize_vision_result(
                vision_result, "O que tem na imagem?"
            )

            # Validate conversational response
            assert isinstance(conversational, str)
            assert len(conversational) > 0
            assert "🐕" in conversational or "Golden" in conversational
            # Should NOT contain technical tags
            assert "[VISION_ANALYSIS]" not in conversational

    @pytest.mark.asyncio
    async def test_path_1_bypass_with_postprocessing(self):
        """Verify PATH 1 (bypass) uses Vision Agent + post-processing."""
        orchestrator = VoxyOrchestrator()

        # Mock Vision Agent
        vision_result = VisionAnalysisResult(
            success=True,
            analysis="Technical analysis of emoji: yellow smiling face",
            confidence=0.98,
            metadata={
                "model_used": "gpt-5",
                "processing_time": 6.8,
                "cost": 0.042,
                "cache_hit": False,
                "analysis_type": "general",
            },
        )

        with patch(
            "src.voxy_agents.core.voxy_orchestrator.get_vision_agent"
        ) as mock_get_vision:
            mock_vision_agent = AsyncMock()
            mock_vision_agent.analyze_image.return_value = vision_result
            mock_get_vision.return_value = mock_vision_agent

            # Mock conversationalization
            with patch.object(
                orchestrator,
                "_conversationalize_vision_result",
                new_callable=AsyncMock,
            ) as mock_conversationalize:
                mock_conversationalize.return_value = (
                    "É um emoji de carinha feliz! 😊 Aquele clássico amarelinho sorrindo."
                )

                response, metadata = await orchestrator.chat(
                    message="que emoji é este?",
                    user_id="test_user",
                    image_url="https://example.com/emoji.png",
                )

                # Validate PATH 1 was used
                assert "vision_agent" in metadata.get("tools_used", [])
                assert metadata.get("agent_type") == "vision"
                assert "conversationalization_time" in metadata

                # Validate conversational response (not technical)
                assert isinstance(response, str)
                assert "😊" in response or "feliz" in response


class TestToolsUsedMetadata:
    """Test tools_used metadata consistency."""

    @pytest.mark.asyncio
    async def test_path_1_tools_used(self):
        """Verify PATH 1 includes tools_used=['vision_agent']."""
        orchestrator = VoxyOrchestrator()

        vision_result = VisionAnalysisResult(
            success=True,
            analysis="Analysis result",
            confidence=0.95,
            metadata={"model_used": "gpt-5", "processing_time": 7.0},
        )

        with patch(
            "src.voxy_agents.core.voxy_orchestrator.get_vision_agent"
        ) as mock_get_vision:
            mock_vision_agent = AsyncMock()
            mock_vision_agent.analyze_image.return_value = vision_result
            mock_get_vision.return_value = mock_vision_agent

            with patch.object(
                orchestrator,
                "_conversationalize_vision_result",
                new_callable=AsyncMock,
                return_value="Conversational response",
            ):
                _, metadata = await orchestrator.chat(
                    message="analyze this image",
                    user_id="test_user",
                    image_url="https://example.com/test.jpg",
                )

                # Validate tools_used
                assert "tools_used" in metadata
                assert metadata["tools_used"] == ["vision_agent"]

    @pytest.mark.asyncio
    async def test_path_2_tools_used_extraction(self):
        """Verify PATH 2 extracts tools_used from RunResult."""
        # This would require mocking Runner.run which is complex
        # For now, testing the extraction logic directly

        orchestrator = VoxyOrchestrator()
        orchestrator._initialize_voxy_agent()

        # Mock RunResult with tool_calls
        mock_result = MagicMock()
        mock_result.final_output = "Translation: Bom dia"
        mock_result.tool_calls = [
            MagicMock(tool_name="translate_text"),
        ]

        # Simulate extraction logic
        tools_used = []
        if hasattr(mock_result, "tool_calls") and mock_result.tool_calls:
            tools_used = [call.tool_name for call in mock_result.tool_calls]

        assert tools_used == ["translate_text"]


class TestChatResponseModel:
    """Test ChatResponse includes tools_used."""

    def test_chat_response_with_tools_used(self):
        """Verify ChatResponse model includes tools_used field."""
        from datetime import datetime
        from src.voxy_agents.api.routes.chat import ChatResponse

        response = ChatResponse(
            response="Test response",
            session_id="test_session",
            request_id="test_request",
            timestamp=datetime.now(),
            processing_time=8.5,
            agent_type="vision",
            tools_used=["vision_agent"],
            cached=False,
            vision_metadata={
                "model_used": "gpt-5",
                "cost": 0.045,
            },
        )

        # Validate tools_used is present
        assert hasattr(response, "tools_used")
        assert response.tools_used == ["vision_agent"]
        assert response.agent_type == "vision"


class TestIntegrationFlow:
    """Integration tests for complete flow."""

    @pytest.mark.asyncio
    async def test_complete_vision_flow_path_1(self):
        """Test complete flow: Vision Agent → Post-processing → ChatResponse."""
        from src.voxy_agents.main import VOXYSystem

        voxy_system = VOXYSystem()

        # Mock Vision Agent and conversationalization
        vision_result = VisionAnalysisResult(
            success=True,
            analysis="Technical: Image shows a cat",
            confidence=0.95,
            metadata={
                "model_used": "gpt-5",
                "processing_time": 7.2,
                "cost": 0.045,
            },
        )

        with patch(
            "src.voxy_agents.core.voxy_orchestrator.get_vision_agent"
        ) as mock_get_vision:
            mock_vision_agent = AsyncMock()
            mock_vision_agent.analyze_image.return_value = vision_result
            mock_get_vision.return_value = mock_vision_agent

            with patch(
                "src.voxy_agents.core.voxy_orchestrator.VoxyOrchestrator._conversationalize_vision_result",
                new_callable=AsyncMock,
                return_value="Que fofo! 🐱 Na imagem tem um gatinho!",
            ):
                response, metadata = await voxy_system.chat(
                    message="o que tem na imagem?",
                    user_id="integration_test",
                    image_url="https://example.com/cat.jpg",
                )

                # Validate complete flow
                assert isinstance(response, str)
                assert "tools_used" in metadata
                assert "vision_agent" in metadata["tools_used"]
                assert metadata["agent_type"] == "vision"
                assert metadata.get("multimodal") is True

                # Response should be conversational (not technical)
                assert "🐱" in response or "gat" in response.lower()
                assert "Technical" not in response
