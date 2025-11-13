# VOXY Agents - Sistema Multi-Agente

Sistema multi-agente inteligente desenvolvido em Python com OpenAI Agents SDK v0.3.3. Implementa orquestração inteligente com VOXY coordenando subagentes especializados + Vision Agent GPT-5 integrado, apresentado através de uma interface **VOXY Web OS** completa.

> ⚠️ **OpenAI Agents SDK v0.4.2 disponível**: Requer migração (breaking changes). Ver [.safe-zone/migration-plan.md] para detalhes.

> 📚 Para histórico detalhado de implementações e features, consulte [@HISTORY.md](./HISTORY.md)

## 🎯 Status: 100% OPERACIONAL

- **5 Subagentes SDK**: Translator, Corrector, Weather, Calculator, Vision (LiteLLM - 400+ modelos configuráveis)
- **Vision Agent**: Análise multimodal com OpenAI Agents SDK + LiteLLM Multi-Provider
- **Token Usage Tracking**: Sistema centralizado de rastreamento de tokens + cost estimation (100% coverage)
- **Image Management System**: Sistema completo de gerenciamento de imagens integrado ao Web OS
- **VOXY Web OS**: Interface desktop completa com 13 wallpapers dinâmicos
- **Professional Drag & Drop**: Smart swapping, collision detection, grid responsivo (6 breakpoints)
- **VOXY Orchestrator**: OpenAI Agents SDK + LiteLLM Multi-Provider (400+ modelos configuráveis via .env)
- **Remember Me System**: Auto-login e persistência de credenciais (100% funcional)
- **Stack Completa**: FastAPI + Next.js 15 + Supabase + Redis
- **Performance**: 7-8s análise multimodal, <2s operações standard

## 🏗️ Arquitetura

### Core Components
```
VOXY Orchestrator (OpenAI Agents SDK + LiteLLM Multi-Provider)
├── Model Selection: 100% configurável via .env (ORCHESTRATOR_MODEL)
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

**Backend**: Python 3.12+ (min 3.12.3), Poetry 2.1.4, FastAPI, Uvicorn
**AI**: OpenAI Agents SDK 0.3.3, LiteLLM 1.75.7+ Multi-Provider (400+ modelos configuráveis via .env)
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
│   │   └── utils/              # llm_factory.py + usage_tracker.py + test_subagents.py
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

## 🔧 Consultando Configuração de Modelos Atual

**IMPORTANTE**: A documentação usa modelos como **exemplos** (defaults configurados em `.env.example`).
Para saber qual modelo está **realmente sendo usado** no ambiente atual:

1. **Verificar arquivo .env**:
   ```bash
   grep "ORCHESTRATOR_MODEL\|CALCULATOR_MODEL\|VISION_MODEL" backend/.env
   ```

2. **Consultar quando necessário**: Antes de assumir qual modelo está ativo, sempre consulte o `.env`
   ou pergunte ao usuário sobre a configuração atual.

3. **Flexibilidade**: Qualquer referência a "Claude Sonnet 4.5", "GPT-4o", etc. na documentação
   refere-se aos **defaults sugeridos**, não a requisitos fixos.

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

**IMPORTANTE - Sistema Model-Agnostic**:

O VOXY Agents é **100% configurável via variáveis de ambiente**. Não há modelos hardcoded no código.
Todos os modelos (VOXY Orchestrator + 5 Subagentes) são configurados através do arquivo `.env`.

**Para configurar seu ambiente**:

1. **Copie o template**:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **Edite `backend/.env`** com suas credenciais e preferências de modelos

3. **Consulte `.env.example`** para ver:
   - Variáveis obrigatórias vs. opcionais
   - Exemplos de configuração (não são requisitos!)
   - Comentários sobre cada parâmetro
   - Sugestões de modelos por caso de uso

**Categorias de Configuração**:

```bash
# 1. API Keys & Authentication
OPENROUTER_API_KEY=          # Para 400+ modelos via OpenRouter
OPENAI_API_KEY=              # Para modelos OpenAI diretos
ANTHROPIC_API_KEY=           # Para Claude direto
GOOGLE_API_KEY=              # Para Gemini direto

# 2. Database & Cache
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=
SUPABASE_JWT_SECRET=
REDIS_URL=

# 3. VOXY Orchestrator
ORCHESTRATOR_PROVIDER=       # openrouter | openai | anthropic | google
ORCHESTRATOR_MODEL=          # Qualquer modelo suportado pelo provider
ORCHESTRATOR_MAX_TOKENS=
ORCHESTRATOR_TEMPERATURE=
ORCHESTRATOR_REASONING_EFFORT=

# 4. Subagentes (Calculator, Corrector, Translator, Weather, Vision)
# Cada um configurável independentemente:
<AGENT>_PROVIDER=            # openrouter | openai | anthropic | google
<AGENT>_MODEL=               # Qualquer modelo do provider
<AGENT>_MAX_TOKENS=
<AGENT>_TEMPERATURE=

# 5. External APIs
OPENWEATHER_API_KEY=         # Para Weather Agent
```

**⚠️ Nenhuma Referência Hardcoded**:
- ❌ Código NÃO contém modelos específicos
- ✅ Tudo vem do `.env`
- ✅ Trocar modelos = apenas editar `.env` (zero mudanças de código)
- ✅ Suporta 400+ modelos via LiteLLM Multi-Provider

**Consulte sempre**:
- `backend/.env.example` - Template oficial com exemplos comentados
- [Seção "Consultando Configuração de Modelos Atual"](#🔧-consultando-configuração-de-modelos-atual) acima

## 📋 Comandos Essenciais

**Backend**:
```bash
# Rodar servidor
poetry run uvicorn src.voxy_agents.api.fastapi_server:app --reload

# Testes
poetry run pytest --cov=src --cov-report=html

# Testar subagente isolado
poetry run python scripts/test_agent.py <agent_name> [args]

# Quality Checks (executam automaticamente via pre-commit hooks)
poetry run ruff check .
poetry run black --check src/ tests/
poetry run mypy src/

# Pre-commit (validação completa antes de commit)
poetry run pre-commit run --all-files  # Ver docs/PRE_COMMIT_GUIDE.md
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

**Orchestrator LiteLLM**: VOXY totalmente configurável (400+ modelos via .env)
**Multi-Agent System**: 5 subagentes (OpenAI Agents SDK + LiteLLM) + Flow Corrections
**Token Usage Tracking**: Rastreamento centralizado de tokens + cost estimation via LiteLLM (100% tested)
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
- **Pre-commit hooks instalados**: Validação automática antes de cada commit (ver [`docs/PRE_COMMIT_GUIDE.md`](./docs/PRE_COMMIT_GUIDE.md))
- Sempre execute typecheck após mudanças: `npm run typecheck` (frontend), `poetry run mypy src/` (backend)
- Rode testes antes de commits: `poetry run pytest --cov=src`
- Use sistema de testes isolados para debug rápido de subagentes
- Commits devem passar pelo fluxo: **pre-commit hooks** → lint → typecheck → tests → commit
- Para features visuais, teste em todos os 6 breakpoints responsivos

## 📚 Documentation-First Approach (CRÍTICO!)

**Lição Aprendida**: Sempre consulte a documentação oficial ANTES de implementar qualquer feature.

### ⚠️ Regra de Ouro: Documente ANTES de Codificar

**SEMPRE use Context7 MCP para consultar documentações** antes de implementar:

1. **ANTES de criar qualquer código**, verifique se a funcionalidade já existe na biblioteca
2. **ANTES de implementar uma feature**, consulte docs oficiais via Context7
3. **ANTES de corrigir um bug**, confirme o comportamento esperado na documentação

### 🔍 Como Usar Context7 Corretamente

**Exemplo Real - Token Usage Tracking (2025-10-25)**:

❌ **ERRADO** (o que NÃO fazer):
```python
# Tentamos implementar token tracking manualmente
if hasattr(result, 'usage') and result.usage:  # ❌ Caminho ERRADO
    tokens = result.usage.total_tokens
```

✅ **CORRETO** (consultar documentação primeiro):
```bash
# 1. Resolver library ID
mcp__context7__resolve-library-id("openai agents sdk")

# 2. Buscar documentação sobre token usage
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/openai/openai-agents-python",
    topic="token usage RunResult response tracking"
)

# Descoberta: OpenAI Agents SDK usa result.context_wrapper.usage
if hasattr(result, 'context_wrapper') and result.context_wrapper.usage:  # ✅ CORRETO
    tokens = result.context_wrapper.usage.total_tokens
```

### 📖 Bibliotecas Principais para Consultar

**Sempre consulte via Context7 antes de usar**:

| Biblioteca | Library ID | Quando Consultar |
|------------|-----------|------------------|
| **LiteLLM** | `/berriai/litellm` | Token tracking, cost calculation, model usage |
| **OpenAI Agents SDK** | `/openai/openai-agents-python` | Agent patterns, Runner API, sessions, usage |
| **Next.js** | Context7 search | Routing, data fetching, app directory |
| **Supabase** | Context7 search | Auth, database, storage, realtime |
| **Radix UI** | Context7 search | Component APIs, accessibility |

### 🎯 Workflow Recomendado

```
1. 📋 User pede feature/fix
2. 🔍 PRIMEIRO: Consultar Context7 (library docs)
3. 📖 Ler padrões oficiais e best practices
4. 💡 Verificar se feature JÁ existe na lib
5. ⌨️  ENTÃO: Implementar usando padrões corretos
6. ✅ Testar e validar
```

### ⚡ Benefícios Comprovados

**Caso Real**: Token Usage Tracking Implementation

| Abordagem | Tempo | Resultado |
|-----------|-------|-----------|
| ❌ **Sem consultar docs** | 2h tentando `result.usage` | FALHA - caminho incorreto |
| ✅ **Com Context7 docs** | 30min | SUCESSO - `context_wrapper.usage` + testes 100% |

**Economia**: **75% menos tempo** + **solução correta** desde o início

### 🚨 Sinais de Alerta

**PARE e consulte documentação quando**:
- ❓ "Como faço X com biblioteca Y?"
- 🤔 "Esse atributo não existe..."
- 😕 "Por que não está funcionando?"
- 🔁 "Já tentei 3 formas diferentes..."

**Resposta**: 📚 **Abra Context7 e consulte a documentação oficial!**

### 💡 Exemplo Prático de Consulta

**Problema**: Implementar streaming com LiteLLM

**Workflow Correto**:
```typescript
// 1. Resolver library ID
const libraryId = await resolveLibraryId("litellm");

// 2. Consultar docs sobre streaming
const docs = await getLibraryDocs({
    libraryId: "/berriai/litellm",
    topic: "streaming responses token usage",
    tokens: 6000
});

// 3. Implementar seguindo padrão oficial descoberto
const response = completion({
    model: "gpt-4",
    messages: [...],
    stream: true,
    stream_options: { include_usage: true }  // ✅ Da documentação!
});
```

### ✅ Checklist Antes de Implementar

- [ ] Consultei Context7 para verificar se a funcionalidade existe?
- [ ] Li os exemplos oficiais da biblioteca?
- [ ] Verifiquei se minha abordagem está alinhada com os padrões da lib?
- [ ] Confirmei que não estou "reinventando a roda"?

**Se algum item for "NÃO"**: 🛑 **PARE e consulte a documentação primeiro!**

---

**Resumo**: Context7 é sua **primeira ferramenta**, não a última. Use-o **proativamente** para economizar tempo e implementar soluções corretas desde o início.

## 🔄 Summary Instructions

Quando usar auto-compact, foque em:
- Test output e código alterado
- Erros e warnings relevantes
- Decisões arquiteturais importantes
- Mudanças em modelos de dados
- Performance metrics críticos

---

**Sistema multi-agente enterprise-ready com VOXY Orchestrator (LiteLLM Multi-Provider) + 5 Subagentes SDK (OpenAI Agents + LiteLLM configuráveis) + Token Usage Tracking Centralizado + VOXY Web OS + Image Management System + API Architecture DRY-compliant + Pre-commit Quality Hooks + Documentation-First Approach completamente implementado e 100% operacional.**

*Última atualização: 2025-10-25 - Token Usage Tracking System + Documentation-First Approach via Context7*
