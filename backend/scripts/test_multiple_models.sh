#!/bin/bash
# Script para testar Calculator Agent com múltiplos modelos OpenRouter

echo "🧪 Testing Calculator Agent with Multiple Models"
echo "================================================"

# Expressão de teste
EXPRESSION="887584 × 9"

# Lista de modelos para testar
MODELS=(
    "x-ai/grok-code-fast-1"
    "anthropic/claude-3.5-sonnet"
    "google/gemini-2.0-flash-exp"
    "openai/gpt-4o"
    "deepseek/deepseek-chat"
    "meta-llama/llama-3.1-70b-instruct"
)

# Testar cada modelo
for model in "${MODELS[@]}"; do
    echo ""
    echo "📊 Testing: $model"
    echo "---"

    CALCULATOR_MODEL=$model poetry run python scripts/test_agent.py calculator \
        --expression "$EXPRESSION" \
        --bypass-cache \
        2>&1 | grep -E "Model:|Response:|Processing Time:|Cost:"

    echo ""
done

echo "================================================"
echo "✅ All models tested!"
