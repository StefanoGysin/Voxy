# VOXY Agents - Sistema Multi-Agente

Sistema multi-agente inteligente desenvolvido em Python com OpenAI Agents SDK v0.3.3. Implementa orquestração inteligente com VOXY coordenando subagentes especializados, apresentado através de uma interface **VOXY Web OS** completa.

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
  └── Translator, Corrector, Weather, Calculator, vision (LiteLLM configuráveis)
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
- **PATH 1 (Bypass)**: `image_url + keywords` → Vision Agent direto 
- **PATH 2 (VOXY)**: URL no texto → VOXY decide → @function_tool. 

## 📋 Stack Tecnológico

**Backend**: Python 3.12+, Poetry 2.1.4, FastAPI, Uvicorn
**AI**: OpenAI Agents SDK 0.3.3, LiteLLM 1.75.7+ Multi-Provider (400+ modelos configuráveis via .env)
**Database**: Supabase (PostgreSQL + Auth + Storage)
**Cache**: Redis 5.0+ (Token blacklisting + Vision cache)
**Frontend**: Next.js 15.4.6, TypeScript, TailwindCSS, Radix UI
**Web OS**: EnhancedOSDashboard, WallpaperSystem, Professional Drag & Drop
**Security**: JWT + JTI (24-hour expiration), Remember Me, CORS, RLS policies


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

**Regra**: pode criar documentação livremente em `.safe-zone/` mas NUNCA em `docs/` sem autorização explícita.

## 📜 Git como Fonte de Verdade do Projeto

**IMPORTANTE - Histórico via Git History**:

Este projeto usa o **git como estrutura de informação** para rastrear toda a evolução do código e features.

**Como Claude Code deve entender o projeto**:

1. **Git History = Documentação Viva**:
   - Use `git log --oneline --graph` para ver a linha do tempo do projeto
   - Commits descrevem **o que** foi implementado e **por quê**
   - Mensagens de commit seguem padrão descritivo e informativo

2. **Branches indicam Contexto de Trabalho**:
   - `main`: Código estável e testado em produção
   - `feature/*`: Desenvolvimento de novas funcionalidades
   - Use `git branch` ou `git status` para saber onde está trabalhando

3. **Commits Informativos em Português**:
   - **OBRIGATÓRIO**: Todas as mensagens de commit devem ser em **português**
   - Cada commit deve descrever claramente o trabalho realizado
   - Exemplo: `feat(langgraph): Implementa Fase 2 - Supervisor Graph & Entry Router`
   - Formato sugerido: `<type>(<scope>): <descrição em português>`
   - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
   - Descrição sempre em português para facilitar leitura do histórico

4. **Como Consultar Histórico**:
   ```bash
   # Ver commits recentes com contexto
   git log --oneline --graph -n 20

   # Ver mudanças em um arquivo específico
   git log --follow -p -- <file_path>

   # Ver trabalho em uma branch específica
   git log main..feature/nome-da-feature

   # Ver commits por autor ou período
   git log --author="name" --since="2 weeks ago"
   ```

5. **Entendendo o Estado Atual**:
   - `git status`: O que está modificado agora
   - `git diff`: Mudanças não commitadas
   - `git diff main`: Diferença da branch atual com main
   - `git log -1`: Último commit (contexto atual)

**Para Claude Code**: Sempre que precisar entender o histórico de uma feature, mudança arquitetural ou decisão de design, consulte o git history. Os commits contêm o "porquê" e "como" de cada implementação.

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

## 🔐 Configurações de Ambiente

**IMPORTANTE - Sistema Model-Agnostic**:

O VOXY Agents é **100% configurável via variáveis de ambiente**. Não há modelos hardcoded no código.
Todos os modelos (VOXY Orchestrator + 5 Subagentes) são configurados através do arquivo `.env`.

**Setup rápido**:

1. Copie o template: `cp backend/.env.example backend/.env`
2. Edite `backend/.env` com suas credenciais
3. Consulte `backend/.env.example` para ver todas as variáveis disponíveis

**Principais categorias**: API Keys, Database (Supabase), Cache (Redis), VOXY Orchestrator, Subagentes (5), External APIs.

**Princípio Model-Agnostic**: Zero modelos hardcoded no código. Tudo configurável via `.env` - suporta 400+ modelos via LiteLLM Multi-Provider.

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

## 🧪 Sistema de Testes Isolados

Script para testar agentes individualmente (18x mais rápido que testes completos):

```bash
# Testar subagente específico
poetry run python scripts/test_agent.py translator --text "Hello" --target-language "pt-BR"

# Testar VOXY Orchestrator
poetry run python scripts/test_agent.py voxy --message "Traduza 'Hello' para português"

# Modo interativo
poetry run python scripts/test_agent.py --interactive
```

Use `--help` para ver todas as opções e agentes disponíveis.

## 📊 API Endpoints

Principais rotas organizadas em: **Auth**, **Chat**, **Images**, **Testing**.

Documentação completa disponível em `/docs` (FastAPI Swagger) ou veja `backend/src/voxy_agents/api/routes/`.

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

**Exemplo Real - Token Usage Tracking**:

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

### ✅ Checklist Antes de Implementar

- [ ] Consultei Context7 para verificar se a funcionalidade existe?
- [ ] Li os exemplos oficiais da biblioteca?
- [ ] Verifiquei se minha abordagem está alinhada com os padrões da lib?
- [ ] Confirmei que não estou "reinventando a roda"?

**Se algum item for "NÃO"**: 🛑 **PARE e consulte a documentação primeiro!**

---

**Resumo**: Context7 é sua **primeira ferramenta**, não a última. Use-o **proativamente** para economizar tempo e implementar soluções corretas desde o início.
