# VOXY Agents - Backend Documentation

## 🎯 Visão Geral

**VOXY Agents Backend** é um sistema multi-agente inteligente desenvolvido em Python com OpenAI Agents SDK v0.3.3. Implementa orquestração inteligente com VOXY coordenando subagentes especializados através da arquitetura **LiteLLM Multi-Provider**.

## Requisitos

- Python 3.12+ (minimo 3.12.3)
- Poetry 2.1.4
- OpenAI Agents SDK 0.3.3
- LiteLLM 1.75.7+
- FastAPI 0.115.14
- Next.js 15.4.6
- Node.js 18+ (para frontend)
- Redis 5.0+

> Nota: OpenAI Agents SDK v0.4.2 esta disponivel, mas a migracao ainda nao foi realizada. Consulte `.safe-zone/migration-plan.md` para detalhes.

### ✨ Características Principais

- **Arquitetura LiteLLM**: Suporte a 400+ modelos via OpenRouter, OpenAI, Anthropic
- **4 Subagentes Especializados**: Calculator, Corrector, Translator, Weather
- **Vision Agent GPT-5**: Análise multimodal avançada integrada
- **Configuração Dinâmica**: Modelos configuráveis via variáveis de ambiente
- **Sistema de Cache**: Redis para otimização de performance
- **Autenticação Completa**: JWT + Remember Me + Token blacklisting
- **API RESTful**: FastAPI com WebSocket support

### 🏗️ Stack Tecnológico

- **Runtime**: Python 3.12+ (minimo 3.12.3)
- **Package Manager**: Poetry 2.1.4
- **Web Framework**: FastAPI 0.115.14 + Uvicorn
- **AI Framework**: OpenAI Agents SDK 0.3.3
- **LLM Gateway**: LiteLLM 1.75.7+ (400+ modelos)
- **Database**: Supabase (PostgreSQL + Auth + Storage)
- **Cache**: Redis 5.0+
- **Testing**: pytest + pytest-asyncio

---

## 🔧 LiteLLM Multi-Provider Architecture

### Visão Geral da Arquitetura

LiteLLM é uma camada de abstração que unifica o acesso a 400+ modelos LLM através de uma interface consistente. Cada subagente pode ser configurado independentemente via variáveis de ambiente.

```
┌─ VOXY Orchestrator (GPT-4o) ────────────────────┐
│                                                  │
├─ Calculator Agent ────> LiteLLM ──> OpenRouter ─┤
│  (Math reasoning)         ↓                      │
│                      [Model Router]              │
├─ Corrector Agent ────> LiteLLM ──> Anthropic ───┤
│  (Grammar correction)     ↓                      │
│                      [API Gateway]               │
├─ Translator Agent ───> LiteLLM ──> Google AI ───┤
│  (Multilingual)           ↓                      │
│                                                  │
├─ Weather Agent ───────> LiteLLM ──> OpenAI ─────┤
│  (Tool calling)           ↓                      │
│                                                  │
└─ Vision Agent (GPT-5) ──> Direct OpenAI ────────┘
```

### Benefícios da Arquitetura

- ✅ **Flexibilidade**: Troque modelos sem alterar código
- ✅ **Cost Control**: Escolha modelos por relação custo-benefício
- ✅ **Performance**: Otimize latência por caso de uso
- ✅ **Fallback**: Múltiplos providers para redundância
- ✅ **Zero Vendor Lock-in**: Migre entre providers facilmente

---

## ⚙️ Configuração de Modelos (2025)

### 🎯 Modelos Recomendados por Subagente

#### **1. Calculator Agent** (Raciocínio Matemático)

**Modelos Testados e Recomendados:**

| Tier | Modelo | Input/Output (1M tokens) | Latência | Precisão |
|------|--------|--------------------------|----------|----------|
| **Premium** | `anthropic/claude-sonnet-4.5` | $3/$15 | ~1.5s | 99%+ |
| **Balanced** | `openai/gpt-4.1-mini` | $0.10/$0.40 | ~1.2s | 98% |
| **Budget** | `deepseek/deepseek-chat-v3.1` | $0.20/$0.80 | ~1.3s | 97% |
| **Free** | `deepseek/deepseek-chat-v3-0324:free` | $0/$0 | ~1.5s | 95% |

**Configuração Recomendada:**
```bash
CALCULATOR_PROVIDER=openrouter
CALCULATOR_MODEL=deepseek/deepseek-chat-v3.1  # Melhor custo-benefício
CALCULATOR_MAX_TOKENS=2000
CALCULATOR_TEMPERATURE=0.1  # Baixa temperatura para precisão
CALCULATOR_INCLUDE_USAGE=true
```

#### **2. Corrector Agent** (Gramática Portuguesa)

**Modelos Testados e Recomendados:**

| Tier | Modelo | Input/Output (1M tokens) | Latência | Qualidade |
|------|--------|--------------------------|----------|-----------|
| **Premium** | `anthropic/claude-3.7-sonnet` | $3/$15 | ~1.8s | Excelente |
| **Balanced** | `google/gemini-2.5-flash-preview` | $0.30/$2.50 | ~1.5s | Muito Boa |
| **Budget** | `google/gemini-2.0-flash-exp` | $0/$0 (GRÁTIS) | ~1.7s | Boa |

**Configuração Recomendada:**
```bash
CORRECTOR_PROVIDER=openrouter
CORRECTOR_MODEL=google/gemini-2.5-flash-preview  # Otimizado PT-BR
CORRECTOR_MAX_TOKENS=2000
CORRECTOR_TEMPERATURE=0.1  # Baixa para consistência
CORRECTOR_INCLUDE_USAGE=true
```

#### **3. Translator Agent** (Tradução Multilíngue)

**Modelos Testados e Recomendados:**

| Tier | Modelo | Input/Output (1M tokens) | Latência | Idiomas |
|------|--------|--------------------------|----------|---------|
| **Premium** | `google/gemini-2.5-pro` | $1.25/$10 | ~2.0s | 100+ |
| **Balanced** | `anthropic/claude-3.7-sonnet` | $3/$15 | ~1.8s | 95+ |
| **Budget** | `google/gemini-2.5-flash-preview` | $0.30/$2.50 | ~1.6s | 90+ |
| **Free** | `deepseek/deepseek-chat-v3-0324:free` | $0/$0 | ~1.8s | 50+ |

**Configuração Recomendada:**
```bash
TRANSLATOR_PROVIDER=openrouter
TRANSLATOR_MODEL=google/gemini-2.5-pro  # Superior multilíngue
TRANSLATOR_MAX_TOKENS=2000
TRANSLATOR_TEMPERATURE=0.3  # Moderada para criatividade
TRANSLATOR_INCLUDE_USAGE=true
```

#### **4. Weather Agent** (Tool Calling + API Integration)

**Modelos Testados e Recomendados:**

| Tier | Modelo | Input/Output (1M tokens) | Latência | Tool Calling |
|------|--------|--------------------------|----------|--------------|
| **Premium** | `openai/gpt-4.1-nano` | $0.10/$0.40 | ~1.3s | Excelente |
| **Balanced** | `google/gemini-2.5-flash-preview` | $0.30/$2.50 | ~1.5s | Muito Bom |
| **Budget** | `openai/gpt-4o-mini` | $0.15/$0.60 | ~1.4s | Bom |

**Configuração Recomendada:**
```bash
WEATHER_PROVIDER=openrouter
WEATHER_MODEL=openai/gpt-4.1-nano  # Otimizado tool calling
WEATHER_MAX_TOKENS=1500
WEATHER_TEMPERATURE=0.1
WEATHER_INCLUDE_USAGE=true
```

### 🔑 Providers Suportados

#### **OpenRouter** (Recomendado)
```bash
OPENROUTER_API_KEY=sk-or-v1-...
# Acesso a 400+ modelos
# Pass-through pricing (sem markup)
# 5.5% platform fee apenas na compra de créditos
```

#### **OpenAI**
```bash
OPENAI_API_KEY=sk-proj-...
# Modelos GPT-4.1, GPT-4o, GPT-4o-mini
# Pricing direto da OpenAI
```

#### **Anthropic**
```bash
ANTHROPIC_API_KEY=sk-ant-...
# Modelos Claude 4.5 Sonnet, Claude 3.7 Sonnet
# Pricing direto da Anthropic
```

#### **Google AI**
```bash
GOOGLE_API_KEY=AIza...
# Modelos Gemini 2.5 Pro, Gemini 2.5 Flash
# Pricing direto do Google AI
```

---

## 📦 Estrutura do Projeto

```
backend/
├── src/voxy_agents/
│   ├── core/
│   │   ├── subagents/
│   │   │   ├── calculator_agent.py   # LiteLLM ✅
│   │   │   ├── corrector_agent.py    # LiteLLM ✅
│   │   │   ├── translator_agent.py   # LiteLLM ✅
│   │   │   ├── weather_agent.py      # LiteLLM ✅
│   │   │   └── vision_agent.py       # GPT-5 Direct
│   │   ├── voxy_orchestrator.py      # GPT-4o
│   │   ├── cache/                     # Redis caching
│   │   └── optimization/              # Performance
│   ├── config/
│   │   ├── models_config.py           # 🔧 Model configurations
│   │   └── settings.py
│   ├── utils/
│   │   ├── llm_factory.py             # LiteLLM factory
│   │   └── test_subagents.py          # Testing utilities
│   └── api/
│       ├── routes/                     # API endpoints
│       └── models.py                   # Pydantic models
├── tests/                              # 213+ test cases
├── pyproject.toml                      # Poetry config
└── .env                                # Environment variables
```

---

## 🛠️ Desenvolvimento

### Setup Inicial

```bash
# Clone e navegue
cd /mnt/d/Projeto-Voxy/voxy/backend

# Instale dependências com Poetry
poetry install

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas API keys

# Inicie servidor
poetry run uvicorn src.voxy_agents.api.fastapi_server:app --reload
```

### Variáveis de Ambiente Essenciais

```bash
# OpenRouter (Recomendado para todos os subagentes)
OPENROUTER_API_KEY=sk-or-v1-...

# Calculator Subagent
CALCULATOR_PROVIDER=openrouter
CALCULATOR_MODEL=deepseek/deepseek-chat-v3.1
CALCULATOR_MAX_TOKENS=2000
CALCULATOR_TEMPERATURE=0.1
CALCULATOR_INCLUDE_USAGE=true

# Corrector Subagent
CORRECTOR_PROVIDER=openrouter
CORRECTOR_MODEL=google/gemini-2.5-flash-preview
CORRECTOR_MAX_TOKENS=2000
CORRECTOR_TEMPERATURE=0.1
CORRECTOR_INCLUDE_USAGE=true

# Translator Subagent
TRANSLATOR_PROVIDER=openrouter
TRANSLATOR_MODEL=google/gemini-2.5-pro
TRANSLATOR_MAX_TOKENS=2000
TRANSLATOR_TEMPERATURE=0.3
TRANSLATOR_INCLUDE_USAGE=true

# Weather Subagent
WEATHER_PROVIDER=openrouter
WEATHER_MODEL=openai/gpt-4.1-nano
WEATHER_MAX_TOKENS=1500
WEATHER_TEMPERATURE=0.1
WEATHER_INCLUDE_USAGE=true

# Weather API (Opcional)
OPENWEATHER_API_KEY=...

# Database (Supabase)
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...

# Cache (Redis)
REDIS_URL=redis://localhost:6379
```

---

## 🧪 Sistema de Testes

### Executar Testes Completos

```bash
# Todos os testes (213+ test cases)
poetry run pytest

# Com coverage report
poetry run pytest --cov=src --cov-report=html

# Testes específicos
poetry run pytest tests/test_voxy_agents/test_core/test_subagents/
```

### Testar Subagentes Individualmente

```bash
# Via script CLI
poetry run python scripts/test_agent.py calculator --expression "25 × 4 + 10"
poetry run python scripts/test_agent.py translator --text "Hello" --target-language "pt-BR"
poetry run python scripts/test_agent.py corrector --text "Eu foi na loja ontem"
poetry run python scripts/test_agent.py weather --city "São Paulo"

# Via HTTP API
curl -X POST http://localhost:8000/api/test/subagent \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "calculator", "input_data": {"expression": "2+2"}}'
```

### Coverage Atual

- **Vision Agent**: 89% (19 testes unitários)
- **Core Modules**: 85%+ coverage
- **Total Tests**: 213+ testes passando
- **Integration Tests**: Subagentes isolados + End-to-end

---

## 📊 Performance & Custos (2025)

### Métricas de Performance

| Operação | Latência Média | Modelo Padrão | Custo/Request |
|----------|----------------|---------------|---------------|
| Cálculo matemático | ~1.2s | DeepSeek-V3.1 | $0.0001 |
| Correção gramática | ~1.5s | Gemini 2.5 Flash | $0.0002 |
| Tradução | ~1.8s | Gemini 2.5 Pro | $0.0005 |
| Clima (tool calling) | ~1.3s | GPT-4.1 Nano | $0.0001 |
| Vision análise GPT-5 | 7-8s | GPT-5 (Vision) | $0.02 |
| Vision cache hit | <1s | Cached | $0 |

### Otimizações Implementadas

- **Multi-level Caching**: L1 (memory) + L2 (Redis)
- **Rate Limiting**: 10/min, 50/hour para Vision Agent
- **Adaptive Reasoning**: Minimal/Low/Medium/High configs
- **Token Optimization**: Temperature tuning por subagente
- **Prompt Caching**: Até 90% economia em prompts repetidos

### Recomendações de Custo-Benefício

**Para Produção (Baixo Custo)**:
```bash
CALCULATOR_MODEL=deepseek/deepseek-chat-v3.1       # $0.20/$0.80
CORRECTOR_MODEL=google/gemini-2.5-flash-preview    # $0.30/$2.50
TRANSLATOR_MODEL=google/gemini-2.5-pro             # $1.25/$10
WEATHER_MODEL=openai/gpt-4.1-nano                  # $0.10/$0.40
```

**Para Desenvolvimento (GRÁTIS)**:
```bash
CALCULATOR_MODEL=deepseek/deepseek-chat-v3-0324:free    # $0/$0
CORRECTOR_MODEL=google/gemini-2.0-flash-exp             # $0/$0
TRANSLATOR_MODEL=deepseek/deepseek-chat-v3-0324:free    # $0/$0
WEATHER_MODEL=google/gemini-2.0-flash-exp               # $0/$0
```

**Para Máxima Qualidade**:
```bash
CALCULATOR_MODEL=anthropic/claude-sonnet-4.5       # $3/$15
CORRECTOR_MODEL=anthropic/claude-3.7-sonnet        # $3/$15
TRANSLATOR_MODEL=google/gemini-2.5-pro             # $1.25/$10
WEATHER_MODEL=openai/gpt-4.1-nano                  # $0.10/$0.40
```

---

## 🔐 Autenticação & Segurança

### Sistema JWT Avançado

- **Token Expiration**: 24 horas (configurável)
- **JTI Tracking**: Tokens únicos com UUID
- **Redis Blacklisting**: Invalidação real de tokens
- **Remember Me**: Persistência de credenciais por 7 dias
- **CORS**: Configurado para frontend Next.js

### Endpoints de Autenticação

- `POST /api/auth/login` - Login + Remember Me
- `POST /api/auth/signup` - Registro de usuário
- `POST /api/auth/logout` - Logout com token blacklisting
- `GET /api/auth/me` - Informações do usuário atual
- `GET /api/auth/validate` - Validação de token

---

## 🚀 API Endpoints

### Chat & Sessions

- `POST /api/chat` - Enviar mensagem (WebSocket ou HTTP)
- `GET /api/sessions` - Listar sessões do usuário
- `POST /api/sessions` - Criar nova sessão
- `GET /api/sessions/{id}` - Detalhes da sessão
- `DELETE /api/sessions/{id}` - Deletar sessão

### Mensagens

- `GET /api/messages` - Listar mensagens (paginado)
- `POST /api/messages/search` - Busca avançada
- `GET /api/messages/stats` - Estatísticas de uso

### Image Management

- `POST /api/images/upload` - Upload de imagem
- `GET /api/images/` - Listar imagens (com filtros)
- `PUT /api/images/{id}` - Atualizar metadata
- `DELETE /api/images/{id}` - Deletar imagem

### Testing (Desenvolvimento)

- `POST /api/test/subagent` - Testar subagente específico
- `GET /api/test/agents` - Listar agentes disponíveis
- `POST /api/test/batch` - Testes em lote

---

## 📈 Monitoramento

### Logs Estruturados

```python
# Configuração de logs
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
ENVIRONMENT=development  # development, staging, production
```

### Métricas Coletadas

- **Token Usage**: Rastreamento automático por subagente
- **Latency**: Tempo de resposta de cada agente
- **Cost Tracking**: Custo estimado por request
- **Cache Hit Rate**: Eficiência do sistema de cache
- **Error Rate**: Taxa de erros por endpoint

---

## 🔧 Troubleshooting

### Problemas Comuns

**1. Vision Agent sempre retorna cache hit**
```bash
# Solução: Bypass cache em testes
tester = SubagentTester(bypass_cache=True)
```

**2. Rate limiting bloqueando testes**
```bash
# Solução: Bypass rate limit em desenvolvimento
tester = SubagentTester(bypass_rate_limit=True)
```

**3. Weather Agent retorna "API não configurada"**
```bash
# Solução: Configure OpenWeather API key
OPENWEATHER_API_KEY=your_key_here
```

**4. LiteLLM modelo não encontrado**
```bash
# Verifique o model ID no OpenRouter
# Formato correto: provider/model-name
# Exemplo: anthropic/claude-sonnet-4.5
```

---

## 📚 Recursos Adicionais

### Documentação de Referência

- [OpenAI Agents SDK](https://github.com/openai/openai-agents-sdk)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [OpenRouter Models](https://openrouter.ai/models)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Links Úteis

- **Frontend Documentation**: `../frontend/README.md`
- **Memory Bank (CLAUDE.md)**: `../CLAUDE.md`
- **Root README**: `../README.md`
- **Testing Guide**: `tests/README.md`

---

**VOXY Agents Backend - Powered by LiteLLM Multi-Provider Architecture (2025)**
