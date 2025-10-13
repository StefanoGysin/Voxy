#!/bin/bash
# Test trace_id propagation - Sprint 3 validation

echo "🧪 Testando propagação de trace_id..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"
SUCCESS_COUNT=0
TOTAL_TESTS=3

# Test 1: Request sem trace_id (deve gerar novo)
echo "1. Request sem X-Trace-ID header:"
RESPONSE=$(curl -s -i ${BASE_URL}/ 2>&1)
TRACE_ID=$(echo "$RESPONSE" | grep -i "x-trace-id" | cut -d':' -f2 | tr -d '[:space:]')

if [ ! -z "$TRACE_ID" ]; then
    echo -e "${GREEN}✅${NC} Header X-Trace-ID presente: $TRACE_ID"
    ((SUCCESS_COUNT++))
else
    echo -e "${RED}❌${NC} Header X-Trace-ID ausente"
fi

# Test 2: Request com trace_id customizado
echo ""
echo "2. Request com X-Trace-ID custom:"
CUSTOM_TRACE="my-test-123"
RESPONSE=$(curl -s -i -H "X-Trace-ID: ${CUSTOM_TRACE}" ${BASE_URL}/ 2>&1)
RETURNED_TRACE=$(echo "$RESPONSE" | grep -i "x-trace-id" | cut -d':' -f2 | tr -d '[:space:]')

if [ "$RETURNED_TRACE" = "$CUSTOM_TRACE" ]; then
    echo -e "${GREEN}✅${NC} Trace ID preservado: $RETURNED_TRACE"
    ((SUCCESS_COUNT++))
else
    echo -e "${RED}❌${NC} Trace ID diferente. Esperado: $CUSTOM_TRACE, Recebido: $RETURNED_TRACE"
fi

# Test 3: Verificar logs
echo ""
echo "3. Verificando logs (últimas 10 linhas com trace_id):"
if [ -f "logs/voxy_main.log" ]; then
    LOG_ENTRIES=$(grep "trace_id" logs/voxy_main.log 2>/dev/null | tail -5)
    if [ ! -z "$LOG_ENTRIES" ]; then
        echo -e "${GREEN}✅${NC} Logs com trace_id encontrados:"
        echo "$LOG_ENTRIES" | head -3
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}❌${NC} Nenhum log com trace_id encontrado"
    fi
else
    echo -e "${RED}❌${NC} Arquivo logs/voxy_main.log não encontrado"
fi

# Summary
echo ""
echo "======================================"
if [ $SUCCESS_COUNT -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}✅ SPRINT 3 VALIDADO${NC} ($SUCCESS_COUNT/$TOTAL_TESTS testes passaram)"
    exit 0
else
    echo -e "${RED}❌ SPRINT 3 FALHOU${NC} ($SUCCESS_COUNT/$TOTAL_TESTS testes passaram)"
    echo ""
    echo "Dicas de troubleshooting:"
    echo "  1. Certifique-se que o servidor está rodando: poetry run uvicorn src.voxy_agents.api.fastapi_server:app --reload"
    echo "  2. Verifique se LoggingContextMiddleware está registrado"
    echo "  3. Confira o diretório logs/ existe"
    exit 1
fi
