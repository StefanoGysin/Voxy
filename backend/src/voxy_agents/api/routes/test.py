"""
API Routes para Teste Isolado de Subagentes

Endpoints HTTP para testar subagentes individuais sem passar pelo VOXY Orchestrator.
Útil para testes via Postman, Insomnia ou integração com CI/CD.

Endpoints:
- POST /api/test/subagent - Testa um subagent específico
- GET /api/test/agents - Lista agentes disponíveis
- GET /api/test/agents/{agent_name} - Informações sobre agente específico
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...utils.test_subagents import SubagentTester, TestResult

logger = logging.getLogger(__name__)

router = APIRouter(tags=["testing"])


# ============================================================================
# Request/Response Models
# ============================================================================


class SubagentTestRequest(BaseModel):
    """Request para testar um subagente ou o VOXY Orchestrator."""

    agent_name: str = Field(
        ...,
        description="Nome do agente (translator, corrector, weather, calculator, vision, voxy)",
        example="translator",
    )
    input_data: dict[str, Any] = Field(
        ...,
        description="Dados de entrada específicos para o agente",
        example={"text": "Hello world", "target_language": "pt-BR"},
    )
    bypass_cache: bool = Field(
        default=True,
        description="Se True, limpa cache antes de testar (Vision Agent)",
    )
    bypass_rate_limit: bool = Field(
        default=True,
        description="Se True, desabilita rate limiting (Vision Agent)",
    )


class SubagentTestResponse(BaseModel):
    """Response do teste de subagente."""

    success: bool
    agent_name: str
    response: str
    metadata: dict[str, Any]
    error: Optional[str] = None


class AgentListResponse(BaseModel):
    """Lista de agentes disponíveis."""

    agents: list[str]
    total: int


class AgentInfoResponse(BaseModel):
    """Informações sobre um agente específico."""

    name: str
    model: str
    test_strategy: str
    capabilities: Optional[list[str]] = None
    required_params: Optional[list[str]] = None
    optional_params: Optional[list[str]] = None


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/test/subagent", response_model=SubagentTestResponse)
async def test_subagent(request: SubagentTestRequest):
    """
    Testa um subagente específico ou o VOXY Orchestrator com dados de entrada fornecidos.

    Este endpoint permite testar subagentes individuais (translator, corrector, weather,
    calculator, vision) ou o VOXY Orchestrator completo sem passar pelo fluxo de autenticação.
    Útil para debug e testes automatizados.

    Args:
        request: Dados de teste incluindo nome do agente e input_data

    Returns:
        TestResult com resposta e metadata detalhado

    Raises:
        HTTPException 400: Se agent_name for desconhecido ou input_data inválido
        HTTPException 500: Se o teste falhar por erro interno

    Examples:
        # Test translator
        POST /api/test/subagent
        {
            "agent_name": "translator",
            "input_data": {
                "text": "Hello world",
                "target_language": "pt-BR"
            },
            "bypass_cache": true
        }

        # Test VOXY Orchestrator
        POST /api/test/subagent
        {
            "agent_name": "voxy",
            "input_data": {
                "message": "Traduza 'Hello' para português"
            },
            "bypass_cache": true
        }

        Response 200:
        {
            "success": true,
            "agent_name": "translator",
            "response": "Olá mundo",
            "metadata": {
                "processing_time": 1.234,
                "model_used": "gpt-4o-mini",
                "cost": 0.0001,
                ...
            }
        }
    """
    try:
        # Special route for VOXY Orchestrator
        if request.agent_name == "voxy":
            from ...utils.test_subagents import test_voxy_orchestrator

            logger.info(
                f"🧪 Testing VOXY Orchestrator via HTTP API "
                f"(bypass_cache={request.bypass_cache})"
            )

            # Validate input_data
            message = request.input_data.get("message")
            if not message:
                raise ValueError(
                    "'message' is required in input_data for voxy agent. "
                    "Example: {'message': 'Traduza hello para português'}"
                )

            image_url = request.input_data.get("image_url")
            user_id = request.input_data.get("user_id", "test_user_http")
            session_id = request.input_data.get("session_id")

            # Execute VOXY Orchestrator test
            result = await test_voxy_orchestrator(
                message=message,
                image_url=image_url,
                user_id=user_id,
                session_id=session_id,
                bypass_cache=request.bypass_cache,
                bypass_rate_limit=request.bypass_rate_limit,
                include_tools_metadata=True,
            )

            return SubagentTestResponse(
                success=result.success,
                agent_name=result.agent_name,
                response=result.response,
                metadata=result.metadata.dict(),
                error=result.error,
            )

        # Standard route for 5 subagents
        tester = SubagentTester(
            bypass_cache=request.bypass_cache,
            bypass_rate_limit=request.bypass_rate_limit,
        )

        # Executar teste
        logger.info(
            f"🧪 Testing {request.agent_name} via HTTP API "
            f"(bypass_cache={request.bypass_cache})"
        )

        result: TestResult = await tester.test_subagent(
            agent_name=request.agent_name,
            input_data=request.input_data,
        )

        # Converter TestResult para dict para resposta
        return SubagentTestResponse(
            success=result.success,
            agent_name=result.agent_name,
            response=result.response,
            metadata=result.metadata.dict(),
            error=result.error,
        )

    except ValueError as e:
        # Agent name inválido ou input_data inválido
        logger.error(f"❌ Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Erro interno
        logger.error(f"❌ Test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal test error: {str(e)}",
        )


@router.get("/test/agents", response_model=AgentListResponse)
async def list_agents():
    """
    Lista todos os agentes disponíveis para teste.

    Returns:
        Lista de nomes de agentes e total

    Example:
        GET /api/test/agents

        Response 200:
        {
            "agents": ["translator", "corrector", "weather", "calculator", "vision"],
            "total": 5
        }
    """
    tester = SubagentTester()
    agents = tester.get_available_agents()

    return AgentListResponse(
        agents=agents,
        total=len(agents),
    )


@router.get("/test/agents/{agent_name}", response_model=AgentInfoResponse)
async def get_agent_info(agent_name: str):
    """
    Obtém informações detalhadas sobre um agente específico.

    Args:
        agent_name: Nome do agente (translator, corrector, weather, calculator, vision)

    Returns:
        Informações do agente incluindo modelo, capacidades e parâmetros

    Raises:
        HTTPException 404: Se agent_name não for encontrado

    Example:
        GET /api/test/agents/translator

        Response 200:
        {
            "name": "translator",
            "model": "gpt-4o-mini",
            "test_strategy": "sdk_runner",
            "capabilities": [
                "Translation between languages",
                "Auto-detect source language"
            ],
            "required_params": ["text", "target_language"],
            "optional_params": ["source_language"]
        }
    """
    try:
        tester = SubagentTester()
        info = tester.get_agent_info(agent_name)

        return AgentInfoResponse(
            name=info["name"],
            model=info["model"],
            test_strategy=info["test_strategy"],
            capabilities=info.get("capabilities"),
            required_params=info.get("required_params"),
            optional_params=info.get("optional_params"),
        )

    except ValueError as e:
        logger.error(f"❌ Agent not found: {agent_name}")
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Batch Testing (Bonus Feature)
# ============================================================================


class BatchTestRequest(BaseModel):
    """Request para testar múltiplos subagentes em lote."""

    tests: list[SubagentTestRequest] = Field(
        ...,
        description="Lista de testes a executar",
        min_items=1,
        max_items=10,  # Limite para prevenir abuse
    )


class BatchTestResponse(BaseModel):
    """Response de testes em lote."""

    results: list[SubagentTestResponse]
    total: int
    successful: int
    failed: int


@router.post("/test/batch", response_model=BatchTestResponse)
async def batch_test_subagents(request: BatchTestRequest):
    """
    Executa múltiplos testes de subagentes em lote.

    Útil para testes automatizados que precisam validar múltiplos cenários.
    Limita a 10 testes por request para prevenir abuse.

    Args:
        request: Lista de testes a executar

    Returns:
        Resultados de todos os testes com estatísticas

    Example:
        POST /api/test/batch
        {
            "tests": [
                {
                    "agent_name": "translator",
                    "input_data": {"text": "Hello", "target_language": "pt-BR"}
                },
                {
                    "agent_name": "calculator",
                    "input_data": {"expression": "2+2"}
                }
            ]
        }

        Response 200:
        {
            "results": [...],
            "total": 2,
            "successful": 2,
            "failed": 0
        }
    """
    results = []
    successful = 0
    failed = 0

    logger.info(f"🧪 Batch testing {len(request.tests)} subagents")

    # Executar testes sequencialmente
    for test_req in request.tests:
        try:
            result_response = await test_subagent(test_req)
            results.append(result_response)

            if result_response.success:
                successful += 1
            else:
                failed += 1

        except HTTPException as e:
            # Erro no teste individual
            logger.error(f"❌ Batch test failed for {test_req.agent_name}: {e.detail}")
            results.append(
                SubagentTestResponse(
                    success=False,
                    agent_name=test_req.agent_name,
                    response="",
                    metadata={},
                    error=e.detail,
                )
            )
            failed += 1

    logger.info(f"✅ Batch testing completed: {successful} successful, {failed} failed")

    return BatchTestResponse(
        results=results,
        total=len(results),
        successful=successful,
        failed=failed,
    )


# ============================================================================
# Health Check
# ============================================================================


@router.get("/test/health")
async def test_health_check():
    """
    Health check para o sistema de testes.

    Valida que o SubagentTester pode ser inicializado corretamente.

    Returns:
        Status de saúde do sistema de testes

    Example:
        GET /api/test/health

        Response 200:
        {
            "status": "healthy",
            "available_agents": 5,
            "message": "Subagent testing system operational"
        }
    """
    try:
        tester = SubagentTester()
        agents = tester.get_available_agents()

        return {
            "status": "healthy",
            "available_agents": len(agents),
            "message": "Subagent testing system operational",
        }

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Testing system unhealthy: {str(e)}",
        )
