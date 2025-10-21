# VOXY Agents - Sistema Multi-Agente

Sistema multi-agente inteligente desenvolvido em Python com OpenAI Agents SDK v0.2.8. Implementa orquestração inteligente com VOXY coordenando subagentes especializados + Vision Agent GPT-5 integrado, apresentado através de uma interface **VOXY Web OS** completa.

> 📚 Para histórico detalhado de implementações e features, consulte [@HISTORY.md](./HISTORY.md)

## 🎯 Status: 100% OPERACIONAL

- **5 Subagentes SDK**: Translator, Corrector, Weather, Calculator, Vision (LiteLLM - 400+ modelos configuráveis)
- **Vision Agent**: Análise multimodal com OpenAI Agents SDK + LiteLLM Multi-Provider
- **Image Management System**: Sistema completo de gerenciamento de imagens integrado ao Web OS
- **VOXY Web OS**: Interface desktop completa com 13 wallpapers dinâmicos
- **Professional Drag & Drop**: Smart swapping, collision detection, grid responsivo (6 breakpoints)
- **VOXY Orchestrator**: OpenAI Agents SDK + LiteLLM Multi-Provider (Claude Sonnet 4.5 default, 400+ modelos configuráveis)
- **Remember Me System**: Auto-login e persistência de credenciais (100% funcional)
- **Stack Completa**: FastAPI + Next.js 15 + Supabase + Redis
- **Performance**: 7-8s análise multimodal, <2s operações standard

## 🏗️ Arquitetura

### Core Components
```
VOXY Orchestrator (OpenAI Agents SDK + LiteLLM Multi-Provider)
├── Default Model: anthropic/claude-sonnet-4.5 via OpenRouter
├── Configuration: 100% via environment variables (ORCHESTRATOR_*)
├── Architecture: Factory pattern (models_config.py + llm_factory.py)
├── Flexibility: 400+ modelos disponíveis (OpenRouter, OpenAI, Anthropic, Google)
└── 5 Subagentes SDK (OpenAI Agents SDK + LiteLLM - 400+ modelos)
  ├── Translator, Corrector, Weather, Calculator (LiteLLM configuráveis)
  └── Vision Agent (OpenAI Agents SDK + LiteLLM Multi-Provider)
      ├── Dual-Path: Bypass direto + Decisão VOXY
      ├── Cache: L1 memory + L2 Redis
      ├── Provider: openrouter | openai | anthropic
      └── Features: Adaptive reasoning + Cost tracking
├── Image Management System
│   ├── Upload: Drag & drop + validation + progress tracking
│   ├── Storage: Supabase Storage + organized paths
│   ├── UI: 5 React components + responsive grid
│   └── Integration: VOXY Web OS icon + JWT auth
└── Authentication System
  ├── Remember Me: Auto-login + Credential persistence
  ├── JWT Tokens: 24h expiration + JTI tracking
  ├── Redis Blacklisting: Token invalidation system
  └── Security: Smart logout + Error handling
```

### Vision Agent Dual-Path
- **PATH 1 (Bypass)**: `image_url + keywords` → Vision Agent direto (7-8s)
- **PATH 2 (VOXY)**: URL no texto → VOXY decide → @function_tool (9-10s)

## 📋 Stack Tecnológico

**Backend**: Python 3.9+, Poetry 2.1.4, FastAPI, Uvicorn
**AI**: OpenAI Agents SDK 0.2.8, LiteLLM Multi-Provider (400+ modelos), Claude Sonnet 4.5 (Orchestrator default)
**Database**: Supabase (PostgreSQL + Auth + Storage)
**Cache**: Redis 5.0+ (Token blacklisting + Vision cache)
**Frontend**: Next.js 15.4.6, TypeScript, TailwindCSS, Radix UI
**Web OS**: EnhancedOSDashboard, WallpaperSystem, Professional Drag & Drop
**Security**: JWT + JTI (24-hour expiration), Remember Me, CORS, RLS policies

## 📁 Estrutura do Projeto

```
voxy/
├── CLAUDE.md                  # Este arquivo (instruções para Claude)
├── HISTORY.md                 # Histórico detalhado de implementações
├── backend/
│   ├── src/voxy_agents/
│   │   ├── core/
│   │   │   ├── subagents/      # 4 agentes + vision_agent.py
│   │   │   ├── voxy_orchestrator.py
│   │   │   ├── auth_token_manager.py # JWT + Redis blacklisting
│   │   │   ├── cache/          # Redis + Vision cache
│   │   │   └── optimization/   # Adaptive reasoning
│   │   ├── api/
│   │   │   ├── models.py       # Modelos compartilhados (DRY principle)
│   │   │   └── routes/         # 6 módulos API + auth
│   │   ├── config/             # models_config.py (LiteLLM)
│   │   └── utils/              # llm_factory.py + test_subagents.py
│   ├── tests/                  # 213+ testes (89% coverage)
│   ├── scripts/                # test_agent.py (CLI testing)
│   └── pyproject.toml          # Poetry config
└── frontend/
  ├── src/components/
  │   ├── os/                 # VOXY Web OS Components
  │   │   ├── EnhancedOSDashboard.tsx
  │   │   ├── WallpaperSystem.tsx (13 presets)
  │   │   ├── AppIcon.tsx (draggable)
  │   │   ├── DateTimeWidget.tsx
  │   │   ├── DragDropProvider.tsx (smart collision)
  │   │   └── hooks/          # useResponsiveGrid, useProtectedAreas
  │   ├── images/             # Image Management System (5 components)
  │   ├── ui/                 # Radix UI components
  │   ├── auth/               # Enhanced with Remember Me
  │   └── chat/               # Integrated VOXY Chat
  ├── lib/
  │   ├── api/images.ts       # Image Management API client
  │   └── store/              # os-store, auth-store, session-store
  └── src/app/
      ├── page.tsx            # VOXY Web OS main interface
      ├── chat/page.tsx       # Chat application
      └── images/page.tsx     # Image Management page
```

## 📁 Estrutura de Documentação

**IMPORTANTE - Organização de Documentação**:

- **`.safe-zone/`**: Área de desenvolvimento/rascunho (NÃO commitada ao git)
  - Use livremente para notas técnicas, planos de implementação, findings de auditoria
  - Conteúdo desta pasta NÃO entra no repositório
  - Ideal para documentação técnica temporária e trabalho em progresso

- **`docs/`**: Documentação oficial do projeto (commitada ao git)
  - **REQUER AUTORIZAÇÃO** do usuário antes de criar/modificar arquivos aqui
  - Contém documentação pública e permanente do projeto
  - Apenas documentação finalizada e aprovada

**Regra**: Claude pode criar documentação livremente em `.safe-zone/` mas NUNCA em `docs/` sem autorização explícita.

## 🧪 Testing & Quality

**Coverage**:
- Vision Agent: 74% (15 testes unitários - SDK pattern)
- Remember Me System: 100% funcional (integração completa)
- Auth System: JWT + Redis blacklisting operacional
- Core Modules: 85%+ coverage
- Total Tests: 213+ testes passando

**Performance Metrics**:
```
- Mensagem simples: ~1.5s
- Vision análise (cache miss): 7-8s
- Vision cache hit: <1s
- Remember Me auto-login: <2s
- Upload imagem: <3s
- WebSocket latency: <100ms
- Drag & Drop: <50ms snap time
- Grid adaptação: <200ms breakpoint change
```

## ⚙️ Configuração Desenvolvimento

### Backend Setup
```bash
cd /mnt/d/Projeto-Voxy/voxy/backend
poetry install
poetry run uvicorn src.voxy_agents.api.fastapi_server:app --reload
```

### Frontend Setup
```bash
cd /mnt/d/Projeto-Voxy/voxy/frontend
npm install
npm run dev
```

### Testing
```bash
# Backend tests
poetry run pytest --cov=src --cov-report=html

# Isolated subagent testing (18x mais rápido)
poetry run python scripts/test_agent.py translator --text "Hello" --target-language "pt-BR"
poetry run python scripts/test_agent.py --interactive
```

## 🚀 URLs de Teste

- **VOXY Web OS**: http://localhost:3000/ (usuários autenticados)
- **VOXY Chat**: http://localhost:3000/chat (integrado ao OS)
- **Image Manager**: http://localhost:3000/images (gerenciamento de imagens)
- **Authentication**: http://localhost:3000/auth/login
- **Remember Me Debug**: http://localhost:3000/test-remember-me

## 🔐 Configurações de Ambiente

**Essenciais (.env)**:
```bash
# JWT + Remember Me
SUPABASE_JWT_EXPIRATION_HOURS=24
SUPABASE_JWT_SECRET=your_jwt_secret_here
REDIS_URL=redis://localhost:6379

# OpenRouter API (LiteLLM)
OPENROUTER_API_KEY=sk-or-...
OR_SITE_URL=https://voxy.ai              # [OPTIONAL]
OR_APP_NAME=VOXY Agents                  # [OPTIONAL]

# VOXY Orchestrator (LiteLLM Multi-Provider)
ORCHESTRATOR_PROVIDER=openrouter                      # openrouter | openai | anthropic
ORCHESTRATOR_MODEL=anthropic/claude-sonnet-4.5       # Main orchestrator model
ORCHESTRATOR_MAX_TOKENS=4000
ORCHESTRATOR_TEMPERATURE=0.3                          # Moderate for reasoning
ORCHESTRATOR_REASONING_EFFORT=medium                  # minimal | low | medium | high
ORCHESTRATOR_INCLUDE_USAGE=true
ORCHESTRATOR_ENABLE_STREAMING=false                   # Future feature flag

# Calculator Agent (Grok Code Fast 1)
CALCULATOR_PROVIDER=openrouter
CALCULATOR_MODEL=x-ai/grok-code-fast-1
CALCULATOR_MAX_TOKENS=2000
CALCULATOR_TEMPERATURE=0.1

# Weather Agent
OPENWEATHER_API_KEY=your_openweather_key

# Vision Agent (LiteLLM Multi-Provider)
VISION_PROVIDER=openrouter                    # openrouter | openai | anthropic
VISION_MODEL=openai/gpt-4o                    # Multimodal model
VISION_MAX_TOKENS=2000
VISION_TEMPERATURE=0.1
VISION_REASONING_EFFORT=medium                # minimal | low | medium | high
VISION_CACHE_TTL=600                          # Cache TTL in seconds
VISION_INCLUDE_USAGE=true
ENABLE_VISION_POSTPROCESSING=true             # Feature flag
```

## 📋 Comandos Essenciais

**Backend**:
```bash
# Rodar servidor
poetry run uvicorn src.voxy_agents.api.fastapi_server:app --reload

# Testes
poetry run pytest --cov=src --cov-report=html

# Testar subagente isolado
poetry run python scripts/test_agent.py <agent_name> [args]

# Linting
poetry run ruff check .
poetry run mypy src/
```

**Frontend**:
```bash
# Development
npm run dev

# Build
npm run build

# Typecheck
npm run typecheck

# Lint
npm run lint
```

## 🏛️ Modelos Centralizados (DRY Principle)

**Arquivo**: `backend/src/voxy_agents/api/models.py`

5 modelos compartilhados entre rotas:
- `MessageResponse` - Mensagem de chat individual
- `MessagesListResponse` - Lista paginada de mensagens
- `SearchRequest` - Busca avançada unificada
- `SearchResultItem` - Item de resultado de busca
- `SearchResponse` - Resposta de busca com metadata

**Benefícios**: Manutenção simplificada, Type Safety, Prevenção de bugs, Evolução segura

## 🔧 LiteLLM Migration Pattern

**Padrão implementado** (Calculator Agent):
1. Configuração centralizada em `config/models_config.py`
2. Factory pattern em `utils/llm_factory.py`
3. Subagent refatorado para usar LiteLLM Model

**Como migrar outro subagente**:
1. Adicionar função `load_<subagent>_config()` em `models_config.py`
2. Refatorar subagent para importar config + factory
3. Adicionar env vars em `.env.example`
4. Atualizar testes para mockar `load_config` e `create_litellm_model`

**Modelos recomendados (2025)**:
- **Orchestrator**: `anthropic/claude-sonnet-4.5` ($3/$15 per 1M) - Advanced reasoning (DEFAULT)
- Calculator: `deepseek/deepseek-chat-v3.1` ($0.20/$0.80 per 1M)
- Corrector: `google/gemini-2.5-flash-preview` ($0.30/$2.50 per 1M)
- Weather: `openai/gpt-4.1-nano` ($0.10/$0.40 per 1M)
- Translator: `google/gemini-2.5-pro` ($1.25/$10.00 per 1M)
- Vision: `openai/gpt-4o` ($2.50/$10.00 per 1M) ou `anthropic/claude-3.5-sonnet` ($3/$15)

## 🧪 Sistema de Testes Isolados

**Bypass do VOXY Orchestrator** para debug rápido:
- Debug 18x mais rápido: 37s → 2s (standard agents)
- 4 componentes: Módulo principal, Testes unitários, CLI script, HTTP endpoints
- 6 agentes testáveis: 5 subagentes + VOXY Orchestrator
- 5 endpoints HTTP: `/api/test/subagent`, `/api/test/agents`, etc.
- CLI rico: ANSI colors, interactive mode, benchmark, export JSON/CSV

**Exemplo CLI (Subagentes)**:
```bash
# Testar tradutor
poetry run python scripts/test_agent.py translator \
--text "Hello world" \
--target-language "pt-BR"

# Testar Vision Agent
poetry run python scripts/test_agent.py vision \
--image-url "https://example.com/image.jpg" \
--query "O que você vê?"
```

**Exemplo CLI (VOXY Orchestrator)**:
```bash
# Teste simples
poetry run python scripts/test_agent.py voxy \
--message "Traduza 'Hello world' para português"

# Com imagem (análise multimodal via Vision Agent)
poetry run python scripts/test_agent.py voxy \
--message "Qual emoji é este?" \
--image-url "https://example.com/emoji.png"

# Benchmark mode
poetry run python scripts/test_agent.py voxy \
--message "Quanto é 2+2?" \
--benchmark --iterations 5

# Modo interativo
poetry run python scripts/test_agent.py --interactive
# Digite: voxy
# message: Traduza "Hello" para francês
```

## 📊 API Endpoints Principais

**Auth**:
- `POST /api/auth/login` - Login + Remember Me
- `POST /api/auth/logout` - Logout + Token blacklisting
- `GET /api/auth/me` - User info
- `GET /api/auth/validate` - Token validation

**Chat**:
- `POST /api/chat` - Send message (VOXY Orchestrator)
- `GET /api/sessions` - List sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}/messages` - Get messages

**Images**:
- `POST /api/images/upload` - Upload with metadata
- `GET /api/images/` - List with filters
- `PUT /api/images/{id}` - Update metadata
- `DELETE /api/images/{id}` - Delete image

**Testing**:
- `POST /api/test/subagent` - Test isolated subagent or VOXY Orchestrator
- `GET /api/test/agents` - List available agents (5 subagentes + voxy)
- `POST /api/test/batch` - Batch testing (up to 10)
- `GET /api/test/health` - Health check do sistema de testes

## 🎯 Features Principais

**Orchestrator LiteLLM**: VOXY com Claude Sonnet 4.5 + 400+ modelos configuráveis via factory pattern
**Multi-Agent System**: 5 subagentes (OpenAI Agents SDK + LiteLLM) + Flow Corrections
**Image Management**: Upload, grid responsivo, modal, busca, metadata editing
**VOXY Web OS**: Interface desktop com 13 wallpapers + Grid responsivo (6 breakpoints)
**Professional Drag & Drop**: Smart swapping + collision detection
**Remember Me**: Auto-login + persistência de credenciais (7 dias)
**JWT Advanced**: 24h tokens + JTI tracking + Redis blacklisting
**Isolated Testing**: Sistema completo para testar subagentes individualmente
**API DRY**: Modelos centralizados em `api/models.py`
**LiteLLM Support**: 400+ modelos configuráveis via `.env` (Orchestrator + 5 Subagentes)

## 📝 Code Style & Workflow

**Python**:
- Use Poetry para gerenciamento de dependências
- Siga PEP 8 (enforced by Ruff)
- Type hints obrigatórios (enforced by mypy)
- Async/await para operações IO-bound
- Pydantic models para validação de dados
- DRY principle: Centralize modelos compartilhados em `api/models.py`

**TypeScript/React**:
- Use ES modules (import/export), não CommonJS (require)
- Destructure imports quando possível: `import { foo } from 'bar'`
- TypeScript strict mode enabled
- Radix UI para componentes de UI
- Zustand para state management
- TailwindCSS para styling
- Next.js 15 App Router

**Workflow**:
- Sempre execute typecheck após mudanças: `npm run typecheck` (frontend), `poetry run mypy src/` (backend)
- Rode testes antes de commits: `poetry run pytest --cov=src`
- Use sistema de testes isolados para debug rápido de subagentes
- Commits devem passar pelo fluxo: lint → typecheck → tests → commit
- Para features visuais, teste em todos os 6 breakpoints responsivos

## 🔄 Summary Instructions

Quando usar auto-compact, foque em:
- Test output e código alterado
- Erros e warnings relevantes
- Decisões arquiteturais importantes
- Mudanças em modelos de dados
- Performance metrics críticos

---

**Sistema multi-agente enterprise-ready com VOXY Orchestrator (Claude Sonnet 4.5) + 5 Subagentes SDK (OpenAI Agents + LiteLLM) + VOXY Web OS + Image Management System + API Architecture DRY-compliant completamente implementado e 100% operacional.**

*Última atualização: 2025-10-09 - VOXY Orchestrator LiteLLM Migration (Claude Sonnet 4.5 default via OpenRouter)*
