"""
Testes para Sistema de Teste Isolado de Subagentes

Valida funcionamento de todos os 5 subagentes (Translator, Corrector,
Weather, Calculator, Vision) em modo de teste isolado.

Coverage Target: 90%+
"""

import pytest
from src.voxy_agents.utils.test_subagents import (
    SubagentTester,
    TestMetadata,
    TestResult,
    get_subagent_tester,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def tester():
    """SubagentTester instance com configuração padrão."""
    return SubagentTester(bypass_cache=True, bypass_rate_limit=True)


@pytest.fixture
def tester_no_bypass():
    """SubagentTester instance sem bypasses (para testar cache)."""
    return SubagentTester(bypass_cache=False, bypass_rate_limit=False)


# ============================================================================
# Tests: Pydantic Models
# ============================================================================


def test_test_metadata_model():
    """Testa criação de TestMetadata model."""
    metadata = TestMetadata(
        processing_time=1.234,
        model_used="gpt-4o-mini",
        tokens_used={"prompt": 100, "completion": 50},
        cost=0.001,
        cache_hit=False,
    )

    assert metadata.processing_time == 1.234
    assert metadata.model_used == "gpt-4o-mini"
    assert metadata.cache_hit is False
    assert metadata.bypassed_auth is True  # Default
    assert metadata.test_mode is True  # Default


def test_test_result_model():
    """Testa criação de TestResult model."""
    metadata = TestMetadata(
        processing_time=1.5,
        model_used="gpt-4o-mini",
    )

    result = TestResult(
        success=True,
        agent_name="translator",
        response="Olá mundo",
        metadata=metadata,
    )

    assert result.success is True
    assert result.agent_name == "translator"
    assert result.response == "Olá mundo"
    assert result.error is None


# ============================================================================
# Tests: SubagentTester Initialization
# ============================================================================


def test_subagent_tester_init():
    """Testa inicialização do SubagentTester."""
    tester = SubagentTester(bypass_cache=True, bypass_rate_limit=True)

    assert tester.bypass_cache is True
    assert tester.bypass_rate_limit is True
    assert "translator" in tester.AGENT_GETTERS
    assert "vision" in tester.AGENT_GETTERS
    assert len(tester.AGENT_GETTERS) == 5


def test_get_subagent_tester_singleton():
    """Testa singleton global get_subagent_tester()."""
    tester1 = get_subagent_tester()
    tester2 = get_subagent_tester()

    # Deve retornar mesma instância
    assert tester1 is tester2


# ============================================================================
# Tests: Translator Agent
# ============================================================================


@pytest.mark.asyncio
async def test_translator_pt_to_en(tester):
    """Testa tradução PT → EN."""
    result = await tester.test_subagent(
        "translator",
        {
            "text": "Olá mundo",
            "target_language": "en",
        },
    )

    assert result.success is True
    assert result.agent_name == "translator"
    assert "hello" in result.response.lower() or "hi" in result.response.lower()
    assert result.metadata.model_used == "gpt-4o-mini"
    assert result.metadata.processing_time > 0
    assert result.error is None


@pytest.mark.asyncio
async def test_translator_en_to_pt(tester):
    """Testa tradução EN → PT."""
    result = await tester.test_subagent(
        "translator",
        {
            "text": "Hello world",
            "target_language": "pt-BR",
        },
    )

    assert result.success is True
    assert "olá" in result.response.lower() or "oi" in result.response.lower()
    assert result.metadata.processing_time > 0


@pytest.mark.asyncio
async def test_translator_with_source_language(tester):
    """Testa tradução com idioma de origem especificado."""
    result = await tester.test_subagent(
        "translator",
        {
            "text": "Bonjour",
            "source_language": "fr",
            "target_language": "en",
        },
    )

    assert result.success is True
    assert "hello" in result.response.lower() or "hi" in result.response.lower()


# ============================================================================
# Tests: Corrector Agent
# ============================================================================


@pytest.mark.asyncio
async def test_corrector_grammar_fix(tester):
    """Testa correção gramatical."""
    result = await tester.test_subagent(
        "corrector",
        {
            "text": "Eu foi na loja ontem",
        },
    )

    assert result.success is True
    assert result.agent_name == "corrector"
    # Deve corrigir "foi" para "fui"
    assert "fui" in result.response.lower()
    assert result.metadata.processing_time > 0


@pytest.mark.asyncio
async def test_corrector_spelling_fix(tester):
    """Testa correção ortográfica."""
    result = await tester.test_subagent(
        "corrector",
        {
            "text": "Ocê está bem?",  # Você
        },
    )

    assert result.success is True
    # Deve ter corrigido para "Você"
    assert "você" in result.response.lower() or "voce" in result.response.lower()


@pytest.mark.asyncio
async def test_corrector_no_errors(tester):
    """Testa correção de texto sem erros."""
    result = await tester.test_subagent(
        "corrector",
        {
            "text": "Este texto está correto.",
        },
    )

    assert result.success is True
    # Deve retornar texto similar ao original
    assert "correto" in result.response.lower() or "texto" in result.response.lower()


# ============================================================================
# Tests: Weather Agent
# ============================================================================


@pytest.mark.asyncio
async def test_weather_valid_city(tester):
    """Testa busca de clima para cidade válida."""
    result = await tester.test_subagent(
        "weather",
        {
            "city": "São Paulo",
            "country": "BR",
        },
    )

    assert result.success is True
    assert result.agent_name == "weather"
    # Deve conter informações de clima ou mensagem de API não configurada
    assert (
        "°C" in result.response
        or "clima" in result.response.lower()
        or "API" in result.response
    )


@pytest.mark.asyncio
async def test_weather_invalid_city(tester):
    """Testa busca de clima para cidade inválida."""
    result = await tester.test_subagent(
        "weather",
        {
            "city": "CidadeInexistente123",
        },
    )

    # Pode ser sucesso com mensagem de erro ou falha
    assert result.success is True  # Agent processa mesmo que cidade não exista
    # Deve conter mensagem de erro ou aviso
    assert (
        "não encontrada" in result.response.lower()
        or "erro" in result.response.lower()
        or "API" in result.response
    )


@pytest.mark.asyncio
async def test_weather_default_country(tester):
    """Testa busca de clima com país padrão (BR)."""
    result = await tester.test_subagent(
        "weather",
        {
            "city": "Rio de Janeiro",
        },
    )

    assert result.success is True
    # Deve funcionar com país padrão BR
    assert len(result.response) > 0


# ============================================================================
# Tests: Calculator Agent
# ============================================================================


@pytest.mark.asyncio
async def test_calculator_basic_math(tester):
    """Testa cálculo matemático básico."""
    result = await tester.test_subagent(
        "calculator",
        {
            "expression": "2 + 2",
        },
    )

    assert result.success is True
    assert result.agent_name == "calculator"
    assert "4" in result.response


@pytest.mark.asyncio
async def test_calculator_complex_expression(tester):
    """Testa expressão matemática complexa."""
    result = await tester.test_subagent(
        "calculator",
        {
            "expression": "25 × 4 + 10",
        },
    )

    assert result.success is True
    # 25 * 4 + 10 = 110
    assert "110" in result.response


@pytest.mark.asyncio
async def test_calculator_with_parentheses(tester):
    """Testa cálculo com parênteses."""
    result = await tester.test_subagent(
        "calculator",
        {
            "expression": "(10 + 5) * 2",
        },
    )

    assert result.success is True
    # (10 + 5) * 2 = 30
    assert "30" in result.response


# ============================================================================
# Tests: Vision Agent
# ============================================================================


@pytest.mark.asyncio
async def test_vision_general_analysis(tester):
    """Testa análise visual geral."""
    # Imagem mínima 1x1 pixel PNG (base64)
    test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    result = await tester.test_subagent(
        "vision",
        {
            "image_url": test_image,
            "query": "O que você vê nesta imagem?",
            "analysis_type": "general",
            "detail_level": "basic",
        },
    )

    assert result.success is True
    assert result.agent_name == "vision"
    assert len(result.response) > 0  # Deve ter alguma análise
    assert result.metadata.model_used in ["gpt-5", "gpt-4o"]
    assert result.metadata.confidence is not None
    assert result.metadata.analysis_type == "general"
    assert result.metadata.detail_level == "basic"


@pytest.mark.asyncio
async def test_vision_cache_bypass(tester):
    """Testa bypass de cache no Vision Agent."""
    test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    # Primeiro teste (cache miss)
    result1 = await tester.test_subagent(
        "vision",
        {
            "image_url": test_image,
            "query": "teste cache",
            "analysis_type": "general",
            "detail_level": "basic",
        },
    )

    assert result1.success is True
    # Com bypass_cache=True, sempre cache_hit=False no primeiro teste
    # (porque limpa cache antes)


@pytest.mark.asyncio
async def test_vision_cache_hit(tester_no_bypass):
    """Testa cache hit no Vision Agent."""
    test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    # Primeiro teste (cache miss)
    result1 = await tester_no_bypass.test_subagent(
        "vision",
        {
            "image_url": test_image,
            "query": "teste cache hit",
            "analysis_type": "general",
            "detail_level": "basic",
        },
    )

    # Segundo teste (deve ter cache hit)
    result2 = await tester_no_bypass.test_subagent(
        "vision",
        {
            "image_url": test_image,
            "query": "teste cache hit",
            "analysis_type": "general",
            "detail_level": "basic",
        },
    )

    assert result2.success is True
    assert result2.metadata.cache_hit is True
    # Tempo de processamento do segundo deve ser menor
    assert result2.metadata.processing_time < result1.metadata.processing_time


@pytest.mark.asyncio
async def test_vision_different_analysis_types(tester):
    """Testa diferentes tipos de análise."""
    test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    analysis_types = ["general", "ocr", "technical"]

    for analysis_type in analysis_types:
        result = await tester.test_subagent(
            "vision",
            {
                "image_url": test_image,
                "query": f"Análise tipo {analysis_type}",
                "analysis_type": analysis_type,
                "detail_level": "basic",
            },
        )

        assert result.success is True
        assert result.metadata.analysis_type == analysis_type


# ============================================================================
# Tests: Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_unknown_agent_error(tester):
    """Testa erro ao tentar testar agente desconhecido."""
    with pytest.raises(ValueError, match="Unknown agent"):
        await tester.test_subagent(
            "unknown_agent",
            {"data": "test"},
        )


@pytest.mark.asyncio
async def test_vision_missing_image_url(tester):
    """Testa erro quando image_url não é fornecida para Vision Agent."""
    with pytest.raises(ValueError, match="image_url is required"):
        await tester.test_subagent(
            "vision",
            {"query": "Teste sem imagem"},
        )


# ============================================================================
# Tests: Helper Methods
# ============================================================================


def test_format_input_translator(tester):
    """Testa formatação de entrada para translator."""
    formatted = tester._format_input(
        "translator",
        {"text": "Hello", "target_language": "pt-BR"},
    )

    assert "Hello" in formatted
    assert "pt-BR" in formatted
    assert "traduza" in formatted.lower()


def test_format_input_corrector(tester):
    """Testa formatação de entrada para corrector."""
    formatted = tester._format_input(
        "corrector",
        {"text": "Texto com erros"},
    )

    assert "Texto com erros" in formatted
    assert "corrija" in formatted.lower()


def test_format_input_weather(tester):
    """Testa formatação de entrada para weather."""
    formatted = tester._format_input(
        "weather",
        {"city": "São Paulo", "country": "BR"},
    )

    assert "São Paulo" in formatted
    assert "clima" in formatted.lower()


def test_format_input_calculator(tester):
    """Testa formatação de entrada para calculator."""
    formatted = tester._format_input(
        "calculator",
        {"expression": "2 + 2"},
    )

    assert "2 + 2" in formatted
    assert "calcule" in formatted.lower()


def test_get_available_agents(tester):
    """Testa listagem de agentes disponíveis."""
    agents = tester.get_available_agents()

    assert isinstance(agents, list)
    assert len(agents) == 5
    assert "translator" in agents
    assert "vision" in agents


def test_get_agent_info_translator(tester):
    """Testa obtenção de informações do translator."""
    info = tester.get_agent_info("translator")

    assert info["name"] == "translator"
    assert info["model"] == "gpt-4o-mini"
    assert info["test_strategy"] == "sdk_runner"
    assert "text" in info["required_params"]
    assert "target_language" in info["required_params"]


def test_get_agent_info_vision(tester):
    """Testa obtenção de informações do Vision Agent."""
    info = tester.get_agent_info("vision")

    assert info["name"] == "vision"
    assert "gpt-5" in info["model"]
    assert info["test_strategy"] == "direct"
    assert "image_url" in info["required_params"]
    assert "query" in info["optional_params"]


def test_get_agent_info_unknown(tester):
    """Testa erro ao buscar informações de agente desconhecido."""
    with pytest.raises(ValueError, match="Unknown agent"):
        tester.get_agent_info("unknown_agent")


# ============================================================================
# Tests: Metadata Validation
# ============================================================================


@pytest.mark.asyncio
async def test_metadata_has_required_fields(tester):
    """Testa se metadata contém todos os campos obrigatórios."""
    result = await tester.test_subagent(
        "calculator",
        {"expression": "1 + 1"},
    )

    metadata = result.metadata

    # Campos obrigatórios
    assert hasattr(metadata, "processing_time")
    assert hasattr(metadata, "model_used")
    assert hasattr(metadata, "bypassed_auth")
    assert hasattr(metadata, "test_mode")
    assert hasattr(metadata, "cache_hit")

    # Valores corretos
    assert metadata.bypassed_auth is True
    assert metadata.test_mode is True
    assert metadata.processing_time > 0


@pytest.mark.asyncio
async def test_vision_metadata_has_extra_fields(tester):
    """Testa se Vision Agent metadata contém campos extras."""
    test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    result = await tester.test_subagent(
        "vision",
        {
            "image_url": test_image,
            "query": "teste",
            "analysis_type": "general",
            "detail_level": "basic",
        },
    )

    metadata = result.metadata

    # Campos específicos do Vision Agent
    assert metadata.confidence is not None
    assert metadata.analysis_type == "general"
    assert metadata.detail_level == "basic"
    assert metadata.reasoning_level is not None


# ============================================================================
# Tests: Performance & Cost
# ============================================================================


@pytest.mark.asyncio
async def test_standard_agent_performance(tester):
    """Testa se agentes padrão completam em tempo razoável (<5s)."""
    result = await tester.test_subagent(
        "calculator",
        {"expression": "10 * 5"},
    )

    assert result.success is True
    # Deve completar em menos de 5 segundos
    assert result.metadata.processing_time < 5.0


@pytest.mark.asyncio
async def test_vision_agent_performance(tester):
    """Testa se Vision Agent completa em tempo esperado (~7-8s)."""
    test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    result = await tester.test_subagent(
        "vision",
        {
            "image_url": test_image,
            "query": "teste performance",
            "analysis_type": "general",
            "detail_level": "basic",
        },
    )

    assert result.success is True
    # Vision Agent deve completar em menos de 15 segundos
    # (7-8s normal + margem para fallback)
    assert result.metadata.processing_time < 15.0


@pytest.mark.asyncio
async def test_cost_tracking(tester):
    """Testa se custo é rastreado corretamente."""
    result = await tester.test_subagent(
        "translator",
        {"text": "Hello", "target_language": "pt-BR"},
    )

    assert result.success is True
    # Custo deve ser calculado para agentes padrão
    assert result.metadata.cost is not None
    assert result.metadata.cost > 0
    assert result.metadata.tokens_used is not None
