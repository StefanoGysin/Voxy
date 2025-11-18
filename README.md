# VOXY Agents - Sistema Multi-Agente Inteligente

Sistema conversacional multi-agente com VOXY Orchestrator (LiteLLM Multi-Provider, 400+ modelos) coordenando 4 subagentes especializados. Interface profissional com session management e dashboard em tempo real.

## Requisitos

- Python 3.12+ (minimo 3.12.3)
- Poetry 2.1.4
- LangGraph 0.6+
- LangChain Core 0.3+
- LiteLLM 1.75.7+
- FastAPI 0.115.14
- Next.js 15.4.6
- Node.js 18+ (para frontend)
- Redis 5.0+

## 🚀 Status Atual

**✅ Sistema 100% Funcional + LiteLLM Multi-Provider Support (2025-10-27)**
- ✅ Multi-agent backend operacional
- ✅ **🔧 LiteLLM Multi-Provider**: 4 Subagentes (Calculator, Corrector, Translator, Weather) com suporte a 400+ modelos via OpenRouter (NEW)
- ✅ **🧪 Isolated Subagent Testing**: Sistema completo para testes isolados de subagentes
  - CLI interativo + HTTP API + Python programático
  - Benchmark mode + Export (JSON/CSV) + 15+ test cases
  - 18x mais rápido (2s vs 37s) - Bypass VOXY overhead
- ✅ **Image Management System**: Sistema completo de gerenciamento de imagens integrado
- ✅ API consolidada e segura (7 módulos principais + Image Management + Testing)
- ✅ **VOXY Web OS**: Interface desktop com drag & drop profissional
- ✅ **Professional Drag & Drop**: Smart swapping + collision detection + grid responsivo
- ✅ Dashboard profissional + estatísticas de uso
- ✅ WebSocket seguro + REST híbrido estável
- ✅ Persistência de histórico + busca cross-session
- ✅ 100% endpoints com autenticação JWT (24-hour tokens)
- ✅ **Remember Me System**: Auto-login e persistência de credenciais (100% funcional)

## 🏗️ Arquitetura

### Backend (Python + LangGraph)
- **VOXY Orchestrator**: LangGraph StateGraph + LiteLLM Multi-Provider (400+ modelos configuráveis via .env)
- **5 Subagentes LangGraph**: Calculator, Corrector, Translator, Weather, Vision (Todos configuráveis via .env - 400+ modelos disponíveis)
- **Stack**: Python 3.12+ (minimo 3.12.3), Poetry 2.1.4, FastAPI 0.115.14, LangGraph 0.6+, LangChain Core 0.3+, Supabase, Redis
- **API Consolidada**: 7 módulos (/auth, /chat, /sessions, /messages, /images, /test) + Modelos centralizados
- **Isolated Testing**: SubagentTester para debug rápido (CLI + HTTP + Programático)
- **Arquitetura DRY**: Modelos Pydantic compartilhados em `api/models.py`
- **Segurança**: JWT + JTI (24-hour expiration) + Redis token blacklisting
- **Auth Avançado**: Remember Me + Real logout + Token invalidation

### Frontend (Next.js 15.4.6 + TypeScript)
- **VOXY Web OS**: Interface desktop completa com 13 wallpapers dinâmicos
- **Image Management System**: 5 componentes React + API client + página dedicada
- **Professional Drag & Drop**: Smart swapping, collision detection, grid responsivo
- **Session Management**: Sidebar com CRUD + busca temporal
- **Advanced Search**: Busca cross-session com filtros e relevance
- **Chat Interface**: Tempo real seguro com identificação por agente
- **Remember Me**: Auto-login, preenchimento automático, checkbox operacional
- **Stack**: Next.js 15.4.6, TypeScript, TailwindCSS, Zustand, Radix UI, @dnd-kit

## 🛠️ Instalação Rápida

### Pré-requisitos
- Node.js 18+
- Python 3.12+ (testado com 3.12.3)
- Poetry 2.1.4
- Redis 5.0+
- Contas: OpenAI/OpenRouter, Supabase, OpenWeatherMap

### 1. Backend
```bash
cd backend

# Instalar dependências
poetry install

# Configurar ambiente
cp .env.example .env
# Editar .env com suas credenciais

# Iniciar Redis
docker-compose up -d redis

# Executar servidor
poetry run uvicorn src.voxy_agents.api.fastapi_server:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend
```bash
cd frontend

# Instalar dependências  
npm install

# Configurar ambiente
cp .env.example .env.local
# Editar .env.local com suas credenciais

# Executar interface
npm run dev
```

### 3. Acessar Sistema
- **VOXY Web OS**: http://localhost:3000/ (interface desktop completa)
- **Chat**: http://localhost:3000/chat
- **Image Manager**: http://localhost:3000/images (sistema de gerenciamento de imagens)
- **Login**: http://localhost:3000/auth/login (Remember Me operacional)
- **API Docs**: http://localhost:8000/docs

## ⚙️ Configuração

### Backend (.env)
```bash
# OpenAI API (para VOXY Orchestrator e subagentes default)
OPENAI_API_KEY=sk-your-key

# OpenRouter API (para modelos alternativos - 400+ modelos disponíveis)
OPENROUTER_API_KEY=sk-or-your-key

# Calculator Agent Configuration (LiteLLM Multi-Provider)
CALCULATOR_PROVIDER=openrouter              # openrouter | openai | anthropic | google
CALCULATOR_MODEL=deepseek/deepseek-chat     # Modelo do OpenRouter
CALCULATOR_MAX_TOKENS=2000
CALCULATOR_TEMPERATURE=0.1
CALCULATOR_INCLUDE_USAGE=true

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_JWT_EXPIRATION_HOURS=24

# Redis
REDIS_URL=redis://localhost:6379

# Weather API (opcional)
OPENWEATHER_API_KEY=your-weather-key
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000
```

## 🎯 Funcionalidades

### 🖥️ VOXY Web OS - Professional Desktop Interface (2025-09-28)

#### **Professional Drag & Drop System**
- **Smart Position Swapping**: Arraste um ícone sobre outro - troca automática de posições
- **Multi-Level Collision Detection**: `pointerWithin` → `rectIntersection` → `closestCenter`
- **Grid Responsivo**: 6 breakpoints adaptativos (mobile portrait/landscape, tablet, desktop, large)
- **Dynamic Protected Areas**: DateTime widget protegido automaticamente (sem hardcoding)
- **100% Grid Movement**: Movimentação livre em toda a área (incluindo linhas 1-2)
- **Professional Animations**: Cubic-bezier easing para movimento natural
- **Touch Optimization**: Configurações específicas para mobile/tablet/desktop

#### **Sistema de Wallpapers Dinâmicos**
- **13 presets categorizados**: Paisagens, espaço, gradientes, abstratos
- **Navegação**: Atalho 'W' para próximo wallpaper
- **Customização**: Opacity, blur, URLs personalizadas

#### **Grid System Responsivo**
- **Adaptação automática**: Grid se reconfigura conforme tamanho da tela
- **Persistência inteligente**: Posições salvas com adaptação responsiva
- **Categorização**: Main, tools, settings, admin apps

#### **Atalhos de Teclado Profissionais**
- **E**: Toggle edit mode | **W**: Next wallpaper | **R**: Reset layout
- **H**: Help overlay | **Escape**: Exit edit mode
- **Context Protection**: Não interfere com inputs, chat ou modals

### 🔐 Remember Me System (100% Operacional)
- **Auto-login**: Credenciais persistentes por 7 dias
- **Auto-preenchimento**: Email pré-preenchido automaticamente  
- **Checkbox Inteligente**: "Remember me for 7 days" operacional
- **Segurança Aprimorada**: Credenciais salvas APÓS login bem-sucedido
- **Tratamento Inteligente**: Diferencia erros de credenciais vs. rede
- **Logout Real**: Invalidação efetiva de tokens no servidor via Redis
- **Cross-browser**: Funcionamento garantido em todos os navegadores
- **Zero Breaking Changes**: Compatibilidade total mantida

### Dashboard Profissional + Estatísticas
- Status dos 4 agentes em tempo real
- **Novo**: Métricas detalhadas de uso e engajamento
- **Novo**: Top agents por utilização com percentuais
- **Novo**: Insights de atividade e response rate
- Interface corporativa responsiva
- Quick actions para funcionalidades

### Session Management Avançado
- Sidebar com lista de conversas
- CRUD completo (criar, renomear, deletar)
- Navegação entre sessões
- Busca e agrupamento temporal
- **Novo**: Search dentro de sessões específicas
- Histórico preservado após F5

### Advanced Search (Implementado)
- **Busca Global**: Cross-session em todas as mensagens
- **Filtros Avançados**: Por role, agente, período
- **Relevance Scoring**: Ranking inteligente dos resultados
- **Highlighting**: Destaque visual dos termos buscados
- **Context-Aware**: Mensagens anteriores/posteriores para contexto

### 🖼️ Image Management System (Implementado 2025-09-30)

**Sistema completo de gerenciamento de imagens integrado ao VOXY Web OS**

#### **Frontend Architecture**
- **5 Componentes React**: ImageCard, ImageGrid, ImageUpload, ImageModal, EditImageForm
- **Página Principal**: `/images` com interface completa de gerenciamento
- **API Client**: Integração completa com backend via `/lib/api/images.ts`
- **TypeScript**: 100% type safety com interfaces bem definidas

#### **Funcionalidades Principais**
- **Upload Avançado**: Drag & drop com validação de tipos e tamanhos
- **Grid Responsivo**: 6 breakpoints adaptativos (mobile → desktop)
- **Modal Full-Screen**: Visualização profissional de imagens
- **Sistema de Busca**: Filtros por nome, descrição e tags
- **Metadata Editing**: Descrição, tags e controle de visibilidade
- **Public/Private**: Sistema de controle de acesso às imagens

#### **Backend Integration**
- **Upload Seguro**: Integração com Supabase Storage
- **Validação Robusta**: 4 camadas de segurança (tipo, tamanho, conteúdo, extensão)
- **Formatos Suportados**: JPEG, PNG, WebP (1KB - 10MB)
- **Tags Flexíveis**: JSON array, comma-separated, ou tag única
- **Organização**: Estrutura automática por usuário/data
- **URLs Públicas**: Opcionais por imagem
- **Metadados Completos**: Descrição, tags, visibilidade

#### **VOXY Web OS Integration**
- **Ícone Integrado**: Ícone "Images" (cor laranja) no grid do Web OS
- **Rota Dedicada**: `/images` acessível via clique no ícone
- **Autenticação**: JWT integration com sistema existente
- **Drag & Drop**: Funciona perfeitamente com o grid system

### Multi-Agent Chat
- **Translator** (LangGraph Node): 50+ idiomas (100% configurável via `.env`)
  - Recomendado: Gemini 2.5 Pro para máxima qualidade multilíngue
  - Alternativas: Claude 3.7 Sonnet, DeepSeek V3.1, modelos gratuitos
- **Corrector** (LangGraph Node): Gramática e estilo (100% configurável via `.env`)
  - Recomendado: Gemini 2.5 Flash Preview para gramática PT-BR
  - Alternativas: Claude 3.7 Sonnet, Gemini 2.0 Flash Experimental (grátis)
- **Weather** (LangGraph Node): Dados meteorológicos em tempo real (100% configurável via `.env`)
  - Recomendado: GPT-4.1 Nano para tool calling eficiente
  - Alternativas: Gemini 2.5 Flash Preview, GPT-4o-mini
- **Calculator** (LangGraph Node): Cálculos matemáticos complexos (100% configurável via `.env`)
  - Recomendado: DeepSeek V3.1 para raciocínio matemático + baixo custo
  - Alternativas: Claude Sonnet 4.5, GPT-4.1-mini, DeepSeek V3 0324 (grátis)
- **Vision** (LangGraph Node): Análise multimodal avançada (100% configurável via `.env`)
  - Recomendado: GPT-4o para análise de imagens
  - Alternativas: Claude 3.7 Sonnet, Gemini 2.5 Pro (vision-capable models)
- **Todos os subagentes**: Arquitetura LangGraph + LiteLLM Multi-Provider (400+ modelos, zero hardcoding)
- **VOXY Orchestrator**: LangGraph StateGraph (100% configurável via ORCHESTRATOR_MODEL - ver .env.example)

### Comunicação Real-time Segura
- **WebSocket Seguro**: JWT **obrigatório** via query parameter (código 1008 se ausente/inválido)
- **Validação User ID**: URL user_id deve corresponder ao token JWT (previne spoofing)
- **Fallback REST**: Autenticação Bearer em todos endpoints
- Indicadores de typing/processing
- Reconnection automática com validação
- Latency < 100ms

## 🔧 LiteLLM Multi-Provider Support

### Visão Geral

**4 Subagentes** (Calculator, Corrector, Translator, Weather) foram migrados para usar **LiteLLM**, permitindo acesso a **400+ modelos de IA** de diferentes provedores sem necessidade de alteração de código. Basta configurar o `.env` e escolher o modelo desejado!

### Arquitetura

```
4 Subagentes Configuráveis
├── Calculator Agent
├── Corrector Agent
├── Translator Agent
└── Weather Agent
    └── LiteLLM (camada de abstração)
        ├── OpenRouter (400+ modelos)
        │   ├── Claude 3.5 Sonnet (Anthropic)
        │   ├── Claude 3 Opus (Anthropic)
        │   ├── Grok Code Fast 1 (X.AI)
        │   ├── Gemini 2.0 Flash (Google)
        │   ├── DeepSeek V3 (DeepSeek)
        │   ├── GPT-4o (OpenAI)
        │   └── Llama 3.1 70B (Meta)
        ├── OpenAI direto
        ├── Anthropic direto
        └── Google direto
```

### Modelos Recomendados

> **💡 Nota sobre Modelos**: Todos os modelos listados abaixo são **sugestões baseadas em custo-benefício (2025)**.
> O sistema suporta **400+ modelos** via LiteLLM. Configure qualquer modelo através das variáveis
> `*_MODEL` no arquivo `.env`. Consulte `.env.example` para ver a configuração atual do seu projeto.

#### Para Matemática e Raciocínio (Calculator Agent)

| Modelo | ID OpenRouter | Custo (in/out 1M tokens) | Características |
|--------|---------------|--------------------------|-----------------|
| **DeepSeek V3.1 (2025)** | `deepseek/deepseek-chat-v3.1` | $0.20 / $0.80 | 🏆 **Top 2025** - Math reasoning + baixo custo |
| **Claude Sonnet 4.5** | `anthropic/claude-sonnet-4.5` | $3.00 / $15.00 | 🧠 **Premium 2025** - Raciocínio avançado |
| **Gemini 2.0 Flash** | `google/gemini-2.0-flash-exp` | **GRÁTIS** | 💰 **Grátis** - Rápido, boa matemática (preview) |
| **Grok Code Fast 1** | `x-ai/grok-code-fast-1` | $0.20 / $1.50 | ⚡ **Especializado** - Coding + matemática + 256k context |
| **GPT-4o** | `openai/gpt-4o` | $2.50 / $10.00 | ⚖️ **Balanceado** - Confiável, versátil |
| **Llama 3.1 70B** | `meta-llama/llama-3.1-70b-instruct` | $0.35 / $0.40 | 🌐 **Open Source** - Barato, boa performance |

#### Para Correção Gramatical (Corrector Agent)

| Modelo | ID OpenRouter | Custo (in/out 1M tokens) | Características |
|--------|---------------|--------------------------|-----------------|
| **Gemini 2.5 Flash** | `google/gemini-2.5-flash-preview` | $0.30 / $2.50 | 🏆 **Top 2025** - PT-BR grammar + cost-effective |
| **Claude 3.7 Sonnet** | `anthropic/claude-3.7-sonnet` | $3.00 / $15.00 | 💎 **Premium** - Precisão máxima |
| **Gemini 2.0 Flash** | `google/gemini-2.0-flash-exp` | **GRÁTIS** | 💰 **Grátis** - Boa qualidade (preview) |

#### Para Tradução (Translator Agent)

| Modelo | ID OpenRouter | Custo (in/out 1M tokens) | Características |
|--------|---------------|--------------------------|-----------------|
| **Gemini 2.5 Pro** | `google/gemini-2.5-pro` | $1.25 / $10.00 | 🏆 **Top 2025** - Multilingual quality |
| **Claude 3.7 Sonnet** | `anthropic/claude-3.7-sonnet` | $3.00 / $15.00 | 💎 **Premium** - Nuances culturais |
| **Gemini 2.5 Flash** | `google/gemini-2.5-flash-preview` | $0.30 / $2.50 | ⚡ **Rápido** - Cost-effective |
| **DeepSeek V3 (free)** | `deepseek/deepseek-chat-v3-0324:free` | **GRÁTIS** | 💰 **Grátis** - 50+ idiomas |

#### Para Informações Meteorológicas (Weather Agent)

| Modelo | ID OpenRouter | Custo (in/out 1M tokens) | Características |
|--------|---------------|--------------------------|-----------------|
| **GPT-4.1 Nano (2025)** | `openai/gpt-4.1-nano` | $0.10 / $0.40 | 🏆 **Top 2025** - Tool calling + baixa latência |
| **Gemini 2.5 Flash** | `google/gemini-2.5-flash-preview` | $0.30 / $2.50 | ⚡ **Rápido** - Ótimo custo-benefício |
| **GPT-4o-mini** | `openai/gpt-4o-mini` | $0.15 / $0.60 | 📊 **Estável** - Opção consolidada |
| **Gemini 2.0 Flash** | `google/gemini-2.0-flash-exp` | **GRÁTIS** | 💰 **Grátis** - Bom com APIs |

### Como Trocar Modelos

#### Método 1: Editar `.env` (Permanente)

```bash
# 1. Abrir arquivo .env
nano backend/.env

# 2. Alterar modelos desejados (2025):

# Calculator Agent
CALCULATOR_MODEL=deepseek/deepseek-chat-v3.1      # DeepSeek V3.1 (recomendado 2025)
# CALCULATOR_MODEL=anthropic/claude-sonnet-4.5    # Claude Sonnet 4.5 (premium)
# CALCULATOR_MODEL=deepseek/deepseek-chat-v3-0324:free  # DeepSeek V3 (GRÁTIS)

# Corrector Agent
CORRECTOR_MODEL=google/gemini-2.5-flash-preview   # Gemini 2.5 Flash (recomendado 2025)
# CORRECTOR_MODEL=anthropic/claude-3.7-sonnet     # Claude 3.7 Sonnet (premium)
# CORRECTOR_MODEL=google/gemini-2.0-flash-exp     # Gemini 2.0 Flash (GRÁTIS)

# Translator Agent
TRANSLATOR_MODEL=google/gemini-2.5-pro            # Gemini 2.5 Pro (recomendado 2025)
# TRANSLATOR_MODEL=anthropic/claude-3.7-sonnet    # Claude 3.7 Sonnet (premium)
# TRANSLATOR_MODEL=deepseek/deepseek-chat-v3-0324:free  # DeepSeek V3 (GRÁTIS)

# Weather Agent (2025)
WEATHER_MODEL=openai/gpt-4.1-nano                 # GPT-4.1 Nano (recomendado 2025)
# WEATHER_MODEL=google/gemini-2.5-flash-preview   # Gemini 2.5 Flash (rápido)
# WEATHER_MODEL=openai/gpt-4o-mini                # GPT-4o-mini (estável)
# WEATHER_MODEL=google/gemini-2.0-flash-exp       # Gemini 2.0 Flash (GRÁTIS)

# 3. Salvar e reiniciar backend
poetry run uvicorn src.voxy_agents.api.fastapi_server:app --reload
```

#### Método 2: Teste Rápido (Sem Modificar `.env`)

```bash
# Calculator Agent - Testar diferentes modelos (2025)
CALCULATOR_MODEL=deepseek/deepseek-chat-v3.1 poetry run python scripts/test_agent.py calculator --expression "8*8"
CALCULATOR_MODEL=anthropic/claude-sonnet-4.5 poetry run python scripts/test_agent.py calculator --expression "25 × 4"
CALCULATOR_MODEL=deepseek/deepseek-chat-v3-0324:free poetry run python scripts/test_agent.py calculator --expression "100 / 5"

# Corrector Agent - Testar correção gramatical (2025)
CORRECTOR_MODEL=google/gemini-2.5-flash-preview poetry run python scripts/test_agent.py corrector --text "Eu foi na loja ontem"
CORRECTOR_MODEL=anthropic/claude-3.7-sonnet poetry run python scripts/test_agent.py corrector --text "Os menino está brincando"

# Translator Agent - Testar tradução (2025)
TRANSLATOR_MODEL=google/gemini-2.5-pro poetry run python scripts/test_agent.py translator --text "Hello world" --target-language "pt-BR"
TRANSLATOR_MODEL=anthropic/claude-3.7-sonnet poetry run python scripts/test_agent.py translator --text "Bom dia" --target-language "en"

# Weather Agent - Testar consulta de clima (2025 models)
WEATHER_MODEL=openai/gpt-4.1-nano poetry run python scripts/test_agent.py weather --city "São Paulo"
WEATHER_MODEL=google/gemini-2.5-flash-preview poetry run python scripts/test_agent.py weather --city "Londres"
```

#### Método 3: Comparar Múltiplos Modelos

```bash
# Script automático que testa vários modelos
cd backend
./scripts/test_multiple_models.sh
```

### Adicionar Novo Provider

O sistema suporta qualquer provider compatível com LiteLLM:

```bash
# OpenRouter (recomendado - acesso a 400+ modelos)
CALCULATOR_PROVIDER=openrouter
CALCULATOR_MODEL=meta-llama/llama-3.1-70b-instruct

# Anthropic direto (2025)
CALCULATOR_PROVIDER=anthropic
CALCULATOR_MODEL=claude-3-7-sonnet-20250219
ANTHROPIC_API_KEY=sk-ant-sua-chave

# Google direto (2025)
CALCULATOR_PROVIDER=google
CALCULATOR_MODEL=gemini-2.5-pro
GOOGLE_API_KEY=sua-chave
```

### Benefícios

✅ **Flexibilidade Total**: Trocar modelos sem código (apenas `.env`)
✅ **400+ Modelos**: Acesso via OpenRouter
✅ **Cost Optimization**: Escolha modelos mais baratos
✅ **Multi-Provider**: OpenRouter, OpenAI, Anthropic, Google, etc.
✅ **Zero Lock-in**: Não depende de um único fornecedor
✅ **Template Reutilizável**: Padrão pronto para outros subagents
✅ **Type Safety**: Configuração validada com dataclasses

### Catálogo Completo de Modelos

Acesse: https://openrouter.ai/models

Filtre por:
- **Preço** (grátis, barato, premium)
- **Capacidades** (raciocínio, código, visão)
- **Provider** (OpenAI, Anthropic, Google, Meta, X.AI, etc.)
- **Context length** (até 2M tokens disponíveis)

### Status da Migração

✅ **Todos os 4 subagentes migrados com sucesso para LiteLLM**:
- Calculator Agent ✅ (2025-10-03)
- Corrector Agent ✅ (2025-10-04)
- Translator Agent ✅ (2025-10-04)
- Weather Agent ✅ (2025-10-04)

Ver **CLAUDE.md** seção "LiteLLM Migration Pattern" para detalhes técnicos da implementação.

## 📊 Performance

- **Mensagem Simples**: 1.47s
- **Com API Externa**: 7.23s (Weather)
- **Remember Me Auto-login**: < 2s
- **TTI Frontend**: < 3s
- **WebSocket Latency**: < 100ms
- **Session Restoration**: < 200ms
- **Drag & Drop Snap**: < 50ms
- **Smart Swapping**: < 100ms animation
- **Grid Adaptation**: < 200ms breakpoint change
- **Professional Easing**: Cubic-bezier smooth movement

## 📁 Estrutura do Projeto

```
voxy/
├── README.md                 # Este arquivo
├── CLAUDE.md                 # Memory bank principal
├── memory-bank/             # Memory bank estruturado
├── backend/                 # Sistema multi-agente Python
│   ├── src/voxy_agents/
│   │   ├── api/
│   │   │   ├── models.py    # Modelos compartilhados (DRY)
│   │   │   └── routes/      # Rotas da API
│   │   │       └── test.py  # 🆕 Endpoints de teste isolado
│   │   ├── core/            # Lógica de negócio
│   │   ├── utils/           # Utilitários
│   │   │   └── test_subagents.py  # 🆕 SubagentTester (400 linhas)
│   │   └── config/          # Configurações
│   ├── scripts/             # 🆕 Scripts CLI
│   │   └── test_agent.py    # 🆕 CLI interativo (200 linhas)
│   ├── tests/               # Testes (estrutura espelhada)
│   │   └── test_subagent_tester.py  # 🆕 15+ test cases (500 linhas)
│   ├── pyproject.toml       # Configuração Poetry
│   └── README.md            # Documentação backend
└── frontend/                # Interface Next.js
    ├── src/                 # Código fonte
    ├── package.json         # Dependências Node.js
    └── README.md            # Documentação frontend
```

## 🧪 Testes

### Sistema de Testes Isolados para Subagentes (NEW - 2025-10-03)

**Teste cada subagente individualmente sem passar pelo VOXY Orchestrator!**

O sistema permite validar rapidamente cada agente (Translator, Corrector, Weather, Calculator, Vision) de forma isolada, economizando tempo de debug e permitindo testes mais eficientes.

#### 🚀 Benefícios

- ⚡ **18x mais rápido**: Debug em 2s vs 37s (bypass VOXY overhead)
- 🔬 **Isolamento total**: Teste sem interferência do orchestrator
- 🧪 **CI/CD ready**: Testes automatizados por agente
- 📊 **Métricas detalhadas**: Tempo, custo, cache hit/miss, confiança
- 💰 **Cost tracking**: Monitoramento de custos por teste

#### 📋 Métodos de Teste Disponíveis

### 1️⃣ CLI (Mais Fácil e Interativo)

#### Modo Interativo (Recomendado para exploração)
```bash
cd backend
poetry run python scripts/test_agent.py --interactive
```

Exemplo de sessão interativa:
```
Available agents: translator, corrector, weather, calculator, vision
Enter agent name: corrector
  text: era uma vez uma menina que gostava de anda na mato

✅ TEST SUCCESS
💬 Response: Era uma vez uma menina que gostava de andar no mato.
📊 Processing Time: 1.5s | Model: google/gemini-2.5-flash-preview | Cost: $0.0002
```

#### Testes Diretos por Agente

**Translator**
```bash
poetry run python scripts/test_agent.py translator \
  --text "Hello world" \
  --target-language "pt-BR"

# Com idioma de origem
poetry run python scripts/test_agent.py translator \
  --text "Bonjour" \
  --source-language "fr" \
  --target-language "en"
```

**Corrector**
```bash
poetry run python scripts/test_agent.py corrector \
  --text "Eu foi na loja ontem"
```

**Weather**
```bash
poetry run python scripts/test_agent.py weather \
  --city "São Paulo"

# Com país específico
poetry run python scripts/test_agent.py weather \
  --city "Zurich" \
  --country "CH"
```

**Calculator**
```bash
poetry run python scripts/test_agent.py calculator \
  --expression "25 × 4 + 10"

# Problemas lógicos básicos
poetry run python scripts/test_agent.py calculator \
  --expression "Há um pato entre dois patos. Quantos patos?"

# Problemas lógicos avançados e desafiadores
poetry run python scripts/test_agent.py calculator \
  --expression "Em uma prisão há 100 celas numeradas de 1 a 100. Inicialmente todas estão fechadas. Um guarda passa e abre todas. O segundo guarda passa e fecha todas as celas de número par. O terceiro guarda muda o estado (abre se fechada, fecha se aberta) de todas as celas múltiplas de 3. Isso continua até o 100º guarda. Quantas celas ficam abertas?"

poetry run python scripts/test_agent.py calculator \
  --expression "Três amigos A, B e C têm idades que são números inteiros. A soma das idades é 72. A idade de A multiplicada pela idade de B é igual à idade de C. Se A tem 8 anos a mais que B, quais são as três idades?"

poetry run python scripts/test_agent.py calculator \
  --expression "Um trem de 200m de comprimento atravessa uma ponte de 300m em 25 segundos. Quanto tempo levará para atravessar um túnel de 500m?"

poetry run python scripts/test_agent.py calculator \
  --expression "Em um torneio de xadrez, cada jogador joga contra todos os outros exatamente uma vez. Se foram jogadas 45 partidas no total, quantos jogadores participaram?"

poetry run python scripts/test_agent.py calculator \
  --expression "Uma escada de 10 metros está apoiada em uma parede. O pé da escada está a 6 metros da parede. Se a escada deslizar 1 metro para baixo na parede, quanto o pé da escada se afastará da parede?"

poetry run python scripts/test_agent.py calculator \
  --expression "Dois relógios mostram a mesma hora ao meio-dia. Um ganha 2 minutos por hora e o outro perde 3 minutos por hora. Depois de quantas horas eles mostrarão novamente a mesma hora?"

poetry run python scripts/test_agent.py calculator \
  --expression "Uma formiga está em um cubo de açúcar de 3x3x3cm. Ela quer ir do vértice inferior esquerdo da face frontal ao vértice superior direito da face traseira. Qual é o menor caminho possível caminhando apenas pelas faces do cubo?"

poetry run python scripts/test_agent.py calculator \
  --expression "Em uma ilha há 100 pessoas: algumas sempre mentem e outras sempre falam a verdade. Cada pessoa diz: 'Pelo menos uma das outras 99 pessoas é mentirosa'. Quantas pessoas são mentirosas?"

poetry run python scripts/test_agent.py calculator \
  --expression "Um pai tem 3 vezes a idade do filho. Há 15 anos, ele tinha 9 vezes a idade do filho. Daqui a quantos anos o pai terá o dobro da idade do filho?"

poetry run python scripts/test_agent.py calculator \
  --expression "Cinco piratas encontram 100 moedas de ouro. O pirata mais velho propõe uma divisão. Se mais da metade concordar, a divisão é aceita. Senão, ele é morto e o próximo mais velho propõe. Todos são perfeitamente lógicos e querem maximizar suas moedas. Qual será a proposta vencedora do primeiro pirata?"
```

**Vision Agent**
```bash
poetry run python scripts/test_agent.py vision \
  --image-url "https://example.com/image.jpg" \
  --query "O que você vê?" \
  --analysis-type "general" \
  --detail-level "standard"

# Tipos de análise: general, ocr, technical, artistic, document
# Níveis de detalhe: basic, standard, detailed, comprehensive
```

#### Features Avançadas do CLI

**Listar agentes disponíveis**
```bash
poetry run python scripts/test_agent.py --list
```

**Benchmark de performance**
```bash
poetry run python scripts/test_agent.py calculator \
  --expression "2+2" \
  --benchmark --iterations 5

# Output: Min, Max, Average, Total time + Cost statistics
```

**Exportar resultados**
```bash
# JSON
poetry run python scripts/test_agent.py translator \
  --text "Hello" \
  --target-language "pt-BR" \
  --export results.json

# CSV
poetry run python scripts/test_agent.py weather \
  --city "London" \
  --export weather_test.csv
```

### 2️⃣ API HTTP (Postman/Insomnia/cURL)

**Testar subagente via HTTP**
```bash
POST http://localhost:8000/api/test/subagent
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN  # Opcional para testes

{
  "agent_name": "translator",
  "input_data": {
    "text": "Hello world",
    "target_language": "pt-BR"
  },
  "bypass_cache": true,
  "bypass_rate_limit": true
}
```

**Listar agentes disponíveis**
```bash
GET http://localhost:8000/api/test/agents
```

**Obter informações de um agente**
```bash
GET http://localhost:8000/api/test/agents/vision

# Response:
# {
#   "name": "vision",
#   "model": "gpt-5/gpt-4o",
#   "test_strategy": "direct",
#   "capabilities": ["GPT-5 multimodal", "OCR", ...],
#   "required_params": ["image_url"],
#   "optional_params": ["query", "analysis_type", ...]
# }
```

**Testes em lote (batch)**
```bash
POST http://localhost:8000/api/test/batch
Content-Type: application/json

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
```

**Health check**
```bash
GET http://localhost:8000/api/test/health
```

### 3️⃣ Programático (Python Code)

```python
from voxy_agents.utils.test_subagents import SubagentTester

# Criar tester com configuração
tester = SubagentTester(
    bypass_cache=True,      # Limpa cache antes de testar
    bypass_rate_limit=True  # Desabilita rate limiting
)

# Testar tradutor
result = await tester.test_subagent(
    "translator",
    {"text": "Hello world", "target_language": "pt-BR"}
)
print(f"✅ {result.response}")
print(f"⏱️  {result.metadata.processing_time:.2f}s")
print(f"💰 ${result.metadata.cost:.6f}")

# Testar Vision Agent
result = await tester.test_subagent(
    "vision",
    {
        "image_url": "https://example.com/image.jpg",
        "query": "O que você vê?",
        "analysis_type": "general"
    }
)
print(f"🖼️ {result.response}")
print(f"🎯 Confiança: {result.metadata.confidence:.1%}")
print(f"🔧 Modelo: {result.metadata.model_used}")

# Listar agentes disponíveis
agents = tester.get_available_agents()
print(f"📋 Agentes: {', '.join(agents)}")

# Obter informações de um agente
info = tester.get_agent_info("translator")
print(f"🤖 Modelo: {info['model']}")
print(f"📖 Capacidades: {info['capabilities']}")
```

### 4️⃣ Testes Unitários (pytest)

**Executar todos os testes**
```bash
cd backend
poetry run pytest tests/test_subagent_tester.py -v
```

**Executar teste específico**
```bash
poetry run pytest tests/test_subagent_tester.py::test_translator_pt_to_en -v
```

**Com coverage**
```bash
poetry run pytest tests/test_subagent_tester.py \
  --cov=src.voxy_agents.utils.test_subagents \
  --cov-report=html
```

**Testes disponíveis** (15+ test cases):
- `test_translator_pt_to_en` - Tradução PT→EN
- `test_corrector_grammar_fix` - Correção gramatical
- `test_weather_valid_city` - Weather API real
- `test_calculator_complex_expression` - Matemática avançada
- `test_vision_general_analysis` - Análise de imagem GPT-5
- `test_vision_cache_hit` - Validação de cache L1/L2
- E mais...

#### 📊 Performance Esperada (Modelos 2025)

| Agent | Tempo Médio | Modelo Recomendado | Custo/Request (2025) |
|-------|-------------|-------------------|----------------------|
| **Translator** | ~1.8s | Gemini 2.5 Pro | $0.0005 |
| ↳ Budget | ~1.6s | Gemini 2.5 Flash Preview | $0.0002 |
| ↳ Free | ~1.8s | DeepSeek V3 0324 (grátis) | **$0** |
| **Corrector** | ~1.5s | Gemini 2.5 Flash Preview | $0.0002 |
| ↳ Premium | ~1.8s | Claude 3.7 Sonnet | $0.0003 |
| ↳ Free | ~1.7s | Gemini 2.0 Flash Exp (grátis) | **$0** |
| **Weather** | ~1.3s | GPT-4.1 Nano | $0.0001 |
| ↳ Budget | ~1.5s | Gemini 2.5 Flash Preview | $0.0002 |
| **Calculator** | ~1.2s | DeepSeek V3.1 | $0.0001 |
| ↳ Premium | ~1.5s | Claude Sonnet 4.5 | $0.0003 |
| ↳ Free | ~1.5s | DeepSeek V3 0324 (grátis) | **$0** |
| **Vision (cache hit)** | <1s | cached | $0 |
| Vision (cache miss) | 7-8s | gpt-5/gpt-4o | $0.02 |

*Métricas baseadas nos modelos default do `.env.example`. Performance varia por modelo escolhido.*

#### 🔧 Configuração de Flags

**Bypass de Cache** (Vision Agent)
```python
tester = SubagentTester(bypass_cache=True)
# ✅ Limpa cache L1 antes de testar
# ✅ Garante teste com API call real
```

**Bypass de Rate Limiting** (Vision Agent)
```python
tester = SubagentTester(bypass_rate_limit=True)
# ✅ Desabilita limite de 10/min, 50/hour
# ✅ Permite testes intensivos sem bloqueio
```

#### 🐛 Troubleshooting

**Problema**: Vision Agent sempre retorna cache hit
```bash
# Solução: Use bypass_cache=True
poetry run python scripts/test_agent.py vision \
  --image-url "..." \
  --bypass-cache
```

**Problema**: Rate limiting bloqueando testes
```bash
# Solução: bypass_rate_limit já é padrão no CLI
# Programático: SubagentTester(bypass_rate_limit=true)
```

**Problema**: Weather retorna "API não configurada"
```bash
# Solução: Configure OPENWEATHER_API_KEY no .env
OPENWEATHER_API_KEY=your-key-here
```

**Problema**: ImportError ao executar testes
```bash
# Solução: Use Poetry para garantir ambiente correto
cd backend
poetry run python scripts/test_agent.py --list
```

### Testes Gerais do Sistema

**Backend**
```bash
cd backend
poetry run pytest --cov=src --cov-report=html
```

**Frontend**
```bash
cd frontend
npm run lint
npm run type-check
npm run build
```

## 🏛️ Arquitetura de Modelos API

### Modelos Centralizados (api/models.py)

O sistema utiliza **Single Source of Truth** para modelos compartilhados:

```python
# backend/src/voxy_agents/api/models.py

MessageResponse          # Mensagem individual de chat
MessagesListResponse     # Lista paginada de mensagens
SearchRequest           # Requisição de busca avançada
SearchResultItem        # Item de resultado com relevance scoring
SearchResponse          # Resposta de busca com metadata
```

### Boas Práticas

**✅ Criar em api/models.py quando:**
- Modelo usado por 2+ routers
- Representa contrato de API compartilhado
- Tem potencial de evolução futura

**✅ Manter local no router quando:**
- Usado por apenas 1 endpoint
- Específico de uma funcionalidade
- Sem dependências de outros routers

### Benefícios
- 🎯 **Manutenção simplificada**: Mudanças em um único lugar
- 🔒 **Type safety**: Contratos API consistentes
- 🚫 **Zero duplicação**: DRY principle aplicado
- 📚 **Documentação central**: Uma fonte de verdade

## 🔧 Desenvolvimento

### Comandos Essenciais
```bash
# Backend (a partir da raiz)
cd backend && poetry run uvicorn src.voxy_agents.api.fastapi_server:app --host 0.0.0.0 --port 8000 --reload

# Frontend (a partir da raiz)  
cd frontend && npm run dev

# Testes (a partir da raiz)
cd backend && poetry run pytest --cov=src --cov-report=html
```

### Issues Resolvidos Recentemente
- ✅ Backend raw_content variable error (2025-08-26)
- ✅ Session isolation bug (WebSocket) (2025-08-26)
- ✅ Message formatting (JSON bruto) (2025-08-26)
- ✅ History persistence (perda após F5) (2025-08-26)
- ✅ OpenAI SDK structured content processing (2025-08-26)

### Refatorações Críticas Executadas

#### Consolidação de Modelos API (2025-10-01)
- ✅ **DRY Principle**: Eliminação de 160 linhas duplicadas
- ✅ **Módulo Central**: Criação de `api/models.py` (5 modelos compartilhados)
- ✅ **Single Source of Truth**: MessageResponse, MessagesListResponse, SearchRequest, etc.
- ✅ **Zero Breaking Changes**: Compatibilidade total mantida
- ✅ **Type Safety**: Contratos de API unificados e consistentes

#### Segurança e Arquitetura (2025-08-31)
- ✅ **Vulnerabilidade**: Eliminação endpoint /no-auth inseguro
- ✅ **Duplicações**: Remoção módulos redundantes chat_history + chat_message
- ✅ **Consolidação**: API organizada em 6 módulos principais
- ✅ **Segurança**: JWT obrigatório em 100% dos endpoints
- ✅ **Funcionalidades**: +4 endpoints de busca avançada e estatísticas

## 🎪 Demo

### Exemplos de Conversação
```
👤 "Olá VOXY! Como está o tempo em Zurich?"
🤖 "Em Zurich, o tempo está agradável: 15°C, céu limpo..."

👤 "Traduza: Hello World para português"  
🤖 "A tradução de 'Hello World' para português é: 'Olá Mundo'"

👤 "Corrija: Eu vai na casa"
🤖 "A correção é: 'Eu vou à casa' ou 'Eu irei para casa'"
```

### Exemplo de Upload
```bash
curl -X POST "http://localhost:8000/api/images/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@minha-foto.jpg" \
  -F "description=Primeira foto no sistema" \
  -F "tags=test,foto" \
  -F "public=false"

# Response: 
# {
#   "id": "44bf2ec4-a595-4387-8881-c905213d691c",
#   "url": "https://supabase.../user-images/users/.../image.jpg",
#   "file_size": 224713,
#   "tags": ["test", "foto"],
#   "message": "Image uploaded successfully"
# }
```

### URLs Funcionais
- **VOXY Web OS**: http://localhost:3000/ (interface desktop completa)
- **Chat Integrado**: http://localhost:3000/chat (sistema multi-agente)
- **Image Manager**: http://localhost:3000/images (gerenciamento de imagens)
- **Login com Remember Me**: http://localhost:3000/auth/login
- **API Documentation**: http://localhost:8000/docs
- **Test API**: http://localhost:8000/api/test/agents (sistema de testes isolados)

### 🎮 Fluxo de Teste Drag & Drop
```bash
1. Acesse http://localhost:3000/ (Web OS principal)
2. Pressione 'E' para ativar modo de edição
3. Arraste ícones livremente por toda a grade (100% disponível)
4. Teste smart swapping: arraste um ícone sobre outro
5. Pressione 'W' para mudar wallpapers dinamicamente
6. Redimensione janela - grid adapta automaticamente
7. Pressione 'H' para ver todos os atalhos
```

### 🧪 Fluxo de Teste Remember Me
```bash
1. Navegue para http://localhost:3000/auth/login
2. Insira credenciais válidas
3. Marque "Remember me for 7 days"
4. Faça login (credenciais salvas APÓS sucesso)
5. Logout (token invalidado no Redis)
6. Retorne ao login - auto-preenchimento funcionando
7. Auto-login automático em <2s
```

### 🖼️ Fluxo de Teste Image Manager
```bash
1. Navegue para http://localhost:3000/ (VOXY Web OS)
2. Clique no ícone "Images" (cor laranja) no grid
3. Faça upload de imagens via drag & drop
4. Use filtros "All Images" vs "Public Only"
5. Clique em imagens para visualização full-screen
6. Edite metadata, tags e visibilidade
7. Teste busca por nome/descrição/tags
8. Verifique responsividade em diferentes tamanhos
```

### 🧪 Fluxo de Teste - Isolated Subagent Testing (NEW)
```bash
# 1. Modo Interativo (Mais fácil para começar)
cd backend
poetry run python scripts/test_agent.py --interactive

# 2. Listar agentes disponíveis
poetry run python scripts/test_agent.py --list

# 3. Testar agente específico
poetry run python scripts/test_agent.py corrector \
  --text "Eu foi na loja ontem"

# 4. Testar Vision Agent
poetry run python scripts/test_agent.py vision \
  --image-url "https://example.com/image.jpg" \
  --query "O que você vê?"

# 5. Benchmark de performance
poetry run python scripts/test_agent.py calculator \
  --expression "2+2" \
  --benchmark --iterations 5

# 6. Exportar resultados
poetry run python scripts/test_agent.py translator \
  --text "Hello" \
  --target-language "pt-BR" \
  --export results.json

# 7. Via HTTP API
curl -X POST http://localhost:8000/api/test/subagent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "weather",
    "input_data": {"city": "São Paulo"}
  }'

# 8. Executar testes unitários
poetry run pytest tests/test_subagent_tester.py -v
```

### Autenticação JWT Avançada
- **Token Expiration**: 24 horas (configurável via `SUPABASE_JWT_EXPIRATION_HOURS`)
- **JTI Tracking**: Tokens únicos com UUID para blacklisting
- **Redis Blacklisting**: Invalidação real de tokens no logout
- **API Endpoints**: `/api/auth/login` (+ Remember Me), `/api/auth/signup`, `/api/auth/logout` (+ blacklisting), `/api/auth/me`, `/api/auth/validate` (+ blacklist check)
- **Token Management**: Frontend com auto-refresh, monitoring inteligente e Remember Me integration

## 📈 Roadmap Opcional

- ~~Histórico expandido com busca avançada~~ ✅ **Implementado (2025-08-31)**
- ~~Monitoring e analytics~~ ✅ **Implementado (2025-08-31)**  
- Novos subagentes especializados
- Deploy para produção
- Mobile app (React Native)
- Rate limiting e throttling
- Webhook notifications

## 🔗 Links

- **Frontend README**: [frontend/README.md](./frontend/README.md)
- **Memory Bank**: [CLAUDE.md](./CLAUDE.md)
- **API Models**: [backend/src/voxy_agents/api/models.py](./backend/src/voxy_agents/api/models.py)
- **Testing System**: [backend/src/voxy_agents/utils/test_subagents.py](./backend/src/voxy_agents/utils/test_subagents.py)
- **Test CLI**: [backend/scripts/test_agent.py](./backend/scripts/test_agent.py)

---

**VOXY Agents** - Sistema multi-agente inteligente 100% operacional com **LiteLLM Multi-Provider Support** (acesso a 400+ modelos de IA), Isolated Subagent Testing, Image Management System, Professional Drag & Drop, smart swapping, grid responsivo, Remember Me System, API Architecture DRY-compliant e funcionalidades enterprise (2025-10-03)
