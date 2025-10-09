# VOXY Web OS - Frontend Documentation

Interface desktop completa desenvolvida para o sistema VOXY multi-agente. **VOXY Web OS** oferece uma experiência de sistema operacional web com 13 wallpapers dinâmicos, grid 4x6 inteligente e VOXY Chat integrado.

## 🖥️ Status do VOXY Web OS

**✅ 100% Funcional + Image Management System (Implementado 2025-09-30)**
- ✅ Build Next.js 15.4.6 com 0 erros
- ✅ **Image Management System**: 5 componentes React + API client + página dedicada
- ✅ Web OS completo com 13 wallpapers dinâmicos
- ✅ **Professional Drag & Drop**: Smart swapping + collision detection + grid responsivo
- ✅ **Grid Responsivo**: 6 breakpoints adaptativos com movimentação livre 100%
- ✅ 6 atalhos de teclado com feedback visual integrados
- ✅ VOXY Chat integrado ao sistema operacional
- ✅ Authentication + Remember Me system preservado

## 🛠️ Stack Tecnológico

- **Next.js 15.4.6** + App Router + TypeScript
- **VOXY Web OS**: EnhancedOSDashboard + WallpaperSystem + Professional Drag & Drop
- **TailwindCSS** + shadcn/ui + Radix UI (design system)
- **Zustand** + localStorage (persistência de estado OS)
- **@dnd-kit**: Professional drag & drop library (core, modifiers, sortable)
- **Responsive System**: 6 breakpoints adaptativos
- **Supabase** Auth (autenticação JWT 24-hour tokens)

## 🚀 Instalação

```bash
# Instalar dependências
npm install

# Configurar ambiente
cp .env.example .env.local
# Editar .env.local com suas credenciais

# Executar em desenvolvimento
npm run dev
```

## ⚙️ Configuração (.env.local)

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000
```

## 🎯 Funcionalidades Web OS

### 🖥️ VOXY Desktop Interface
- Interface desktop completa para usuários autenticados
- Experiência semelhante a sistemas operacionais modernos
- Substituição completa do dashboard legado
- Integração fluida com VOXY Chat

### 🎨 Sistema de Wallpapers Dinâmicos (13 Presets)
- **Paisagens**: mountain-sunset, ocean-waves, forest-morning, city-night
- **Espaço**: space-nebula, galaxy-spiral  
- **Gradientes**: gradient-blue, gradient-purple, gradient-ocean, gradient-forest
- **Abstratos**: abstract-purple, minimal-dark, minimal-light
- **Configuração**: Opacity, blur, custom URLs
- **Navegação**: Atalho 'W' para próximo wallpaper

### 📱 Professional Drag & Drop System (2025-09-28)

#### **Smart Position Swapping**
- **Troca automática**: Arraste um ícone sobre outro - troca de posições instantânea
- **Multi-level collision**: `pointerWithin` → `rectIntersection` → `closestCenter`
- **Haptic feedback**: Padrões distintos para sucesso, erro e swap
- **Screen reader support**: Anúncios automáticos para acessibilidade

#### **Grid Responsivo Profissional**
- **6 breakpoints adaptativos**: mobile-portrait, mobile-landscape, tablet-portrait, tablet-landscape, desktop, large-desktop
- **Adaptação automática**: Grid se reconfigura conforme tamanho da tela
- **Touch optimization**: Configurações específicas para mobile/tablet/desktop
- **Orientation support**: Suporte completo para mudanças de orientação

#### **Dynamic Protected Areas**
- **Zero hardcoding**: Substituiu restrições `row >= 3` por detecção inteligente
- **DateTime widget protection**: Protegido automaticamente via pixel detection
- **100% Grid Movement**: Movimentação livre em toda a área (incluindo linhas 1-2)
- **Container-aware calculations**: Medições baseadas no container real

#### **Professional Animations & Performance**
- **Cubic-bezier easing**: Movimento natural com curvas profissionais (0.92 damping)
- **High-precision snapping**: Cálculos matemáticos otimizados
- **Performance metrics**: <50ms snap time, <100ms swap animation
- **Container-aware**: Medições precisas baseadas no grid real

### ⌨️ Atalhos de Teclado
- **E**: Alternar modo de edição (com feedback toast)
- **Escape**: Sair do modo de edição
- **W**: Próximo wallpaper (com feedback toast)
- **R**: Reset layout (apenas em edit mode, com feedback toast)
- **H**: Mostrar/ocultar ajuda de atalhos
- **Enter/Space**: Abrir aplicativos

#### 🎯 Sistema de Feedback Visual
- **Toast Notifications**: Feedback instantâneo para todas as ações de teclado
- **Help Overlay**: Overlay completo com todos os atalhos (tecla H)
- **Context-Aware**: Diferencia modo de edição ativo/inativo

#### 🔒 Proteção Inteligente de Contexto
- **Inputs/Textareas**: Atalhos desabilitados em campos de texto
- **Modais**: Proteção em diálogos e overlays
- **Chat Interface**: Não interfere com a digitação no chat

### 🚀 Apps Integrados
- **VOXY Chat**: Sistema de conversação multiagente completo
- **Image Manager**: Sistema completo de gerenciamento de imagens
- **Settings**: Configurações do sistema operacional
- **Activity**: Monitor de atividade e estatísticas
- **Dashboard**: Analytics e métricas (quando aplicável)

### 🔐 Authentication & Security (Preservado)
- **JWT 24-hour Tokens**: Sistema de autenticação mantido
- **Remember Me System**: Auto-login funcional
- **Token Management**: Validação automática preservada
- **Zero Breaking Changes**: Compatibilidade total mantida

## 📱 URLs

- **VOXY Web OS**: http://localhost:3000/ (usuários autenticados)
- **VOXY Chat**: http://localhost:3000/chat (integrado ao OS)
- **Image Manager**: http://localhost:3000/images (sistema de gerenciamento de imagens)
- **Authentication**: http://localhost:3000/auth/login

## 🖼️ Image Management System (2025-09-30)

### ✨ **Sistema Completo Implementado**

**5 Componentes React Profissionais** integrados ao VOXY Web OS para gerenciamento completo de imagens com interface moderna e responsiva.

#### **Componentes Principais**
- **ImageCard.tsx**: Display individual de imagem com hover effects e actions
- **ImageGrid.tsx**: Grid responsivo com busca e filtros dinâmicos
- **ImageUpload.tsx**: Drag & drop upload com progress tracking
- **ImageModal.tsx**: Visualizador full-screen com navigation
- **EditImageForm.tsx**: Formulário de edição de metadata completo

#### **API Integration**
- **API Client**: `/lib/api/images.ts` com CRUD operations completas
- **TypeScript**: 100% type safety com interfaces bem definidas
- **Authentication**: JWT integration com sistema existente
- **Error Handling**: Loading states e error boundaries profissionais

#### **Funcionalidades UX**
- **Upload Avançado**: Drag & drop + validation + progress tracking
- **Grid Responsivo**: 6 breakpoints adaptativos (mobile → desktop)
- **Modal Professional**: Full-screen viewer + metadata display
- **Sistema de Busca**: Filtros por nome, descrição e tags
- **Metadata System**: Tags + descriptions + public/private control

#### **VOXY Web OS Integration**
- **Ícone Integrado**: "Images" (cor laranja #f59e0b) no grid do Web OS
- **Rota Dedicada**: `/images` acessível via clique no ícone
- **Drag & Drop**: Funciona perfeitamente com o grid system do OS
- **Store Management**: Integrado ao os-store.ts com persistência

## 🎨 Design System

### Paleta de Cores
- **Primary**: #0066cc (VOXY Blue)
- **Agents**: Emerald, Violet, Cyan, Amber
- **Dark Mode**: Suporte completo

### Componentes
- **shadcn/ui**: Button, Card, Dialog, Sheet
- **Custom**: ChatInterface, SessionSidebar, AgentStatusGrid
- **Responsive**: Mobile-first design

## 📊 Performance

- **TTI**: < 3s (Time to Interactive)
- **Bundle**: Otimizado com Next.js
- **WebSocket**: Latency < 100ms
- **Session Restoration**: < 200ms
- **Drag & Drop Snap**: < 50ms (high-precision)
- **Smart Swapping**: < 100ms animation
- **Grid Adaptation**: < 200ms breakpoint change
- **Professional Easing**: Cubic-bezier smooth movement

## 🏗️ Arquitetura Web OS

### Estrutura de Páginas
```
src/app/
├── page.tsx              # 🖥️ VOXY Web OS (main interface)
├── chat/
│   └── page.tsx         # VOXY Chat (integrado ao OS)
├── images/
│   └── page.tsx         # 🆕 Image Management main page
└── auth/
    └── login/page.tsx   # Sistema de autenticação
```

### 🖥️ Componentes Web OS + Professional Drag & Drop
```
src/components/os/
├── EnhancedOSDashboard.tsx # 🆕 Interface principal do OS com atalhos
├── WallpaperSystem.tsx     # 🆕 Sistema de 13 wallpapers (CSS otimizado)
├── ToastSystem.tsx         # 🆕 Sistema de notificações toast
├── HelpOverlay.tsx         # 🆕 Overlay de ajuda para atalhos
├── AppIcon.tsx            # 🆕 Ícones arrastáveis com smart collision
├── DraggableAppIcon.tsx   # 🆕 Professional draggable implementation
├── DroppableGridCell.tsx  # 🆕 Drop zones com collision detection
├── DateTimeWidget.tsx     # 🆕 Widget de data/hora
├── DragDropProvider.tsx   # 🆕 Advanced drag & drop system
├── GridModifiers.ts       # 🆕 Professional modifiers & easing
└── hooks/                 # 🆕 Professional drag & drop hooks
    ├── useResponsiveGrid.ts       # 6-breakpoint responsive system
    ├── useProtectedAreas.ts       # Dynamic protected zones
    └── useScreenReaderAnnouncements.ts # Accessibility
```

### 🖼️ Componentes Image Management System
```
src/components/images/
├── ImageCard.tsx           # 🆕 Individual image display
├── ImageGrid.tsx           # 🆕 Responsive image grid
├── ImageUpload.tsx         # 🆕 Drag & drop upload component
├── ImageModal.tsx          # 🆕 Full-screen image viewer
└── EditImageForm.tsx       # 🆕 Metadata editing form
```

### 💬 Componentes Chat (Integrados)
```
src/components/chat/
├── chat-container.tsx     # Interface principal do chat
├── message-bubble.tsx     # Bubbles de mensagem
├── session-sidebar.tsx    # Sidebar de sessões
├── session-list.tsx       # Lista virtualizada
└── advanced-search.tsx    # Busca avançada
```

### 📦 Stores (Zustand + Persistence)
```
src/lib/
├── api/
│   └── images.ts         # 🆕 Image Management API client
└── store/
    ├── os-store.ts       # 🆕 Estado do Web OS (grid, wallpapers)
    ├── session-store.ts  # Gerenciamento de sessões chat
    ├── auth-store.ts     # Autenticação + Remember Me
    └── chat-store.ts     # Estado do chat em tempo real
```

### 🔧 Hooks e Utilidades
```
src/lib/hooks/
├── use-websocket.ts      # WebSocket seguro com JWT
├── use-chat-api.ts       # REST API client
└── use-vision-api.ts     # Vision Agent integration
```

## 🔧 Scripts

```bash
# Desenvolvimento
npm run dev

# Build para produção
npm run build

# Iniciar produção
npm start

# Linting
npm run lint

# Type checking
npm run type-check
```

## 🚀 Professional Drag & Drop Implementation (2025-09-28)

### 🖥️ Advanced Architecture - VOXY Web OS + Professional Drag & Drop

**Professional System Implemented:**
```typescript
✅ Smart Position Swapping       // Automatic icon position exchange
✅ Multi-Level Collision         // pointerWithin → rectIntersection → closestCenter
✅ Responsive Grid System        // 6 adaptive breakpoints
✅ Dynamic Protected Areas       // Intelligent DateTime widget protection
✅ Professional Animations       // Cubic-bezier easing + container-aware
✅ Touch Optimization           // Device-specific configurations
✅ 100% Grid Movement           // Free movement across entire grid area
```

### 📦 Novos Componentes Web OS

**1. Sistema de Wallpapers:**
```typescript
// 13 presets categorizados
const wallpaperPresets = {
  'mountain-sunset': { type: 'image', ... },
  'gradient-blue': { type: 'gradient', ... },
  'minimal-dark': { type: 'gradient', ... },
  // + 10 outros presets
}
```

**2. Grid System 4x6:**
```typescript
// Layout com persistência
interface IconPosition {
  id: string
  x: number    // 0-3 (4 colunas)
  y: number    // 0-5 (6 linhas)  
  size: 'small' | 'medium' | 'large'
  category: 'main' | 'tools' | 'settings' | 'admin'
}
```

**3. Atalhos de Teclado:**
```typescript
// Implementação completa com feedback toast
E      → Toggle edit mode (toast feedback)
Escape → Exit edit mode  
W      → Next wallpaper (toast feedback)
R      → Reset layout (edit mode only, toast feedback)
H      → Show/hide help overlay
Enter/Space → Open apps

// Context Protection
- Smart detection for inputs/textareas/modals
- No interference with chat interface
- Protection against accidental triggers
```

### 🔄 Migração do Dashboard Legado

**Substituições Completas:**
```diff
- Dashboard components     → EnhancedOSDashboard
- Static interface        → Dynamic wallpaper system
- Fixed layout           → Drag & drop grid 4x6
- Basic navigation       → OS-like experience
+ 13 dynamic wallpapers  → Full visual customization
+ Keyboard shortcuts     → Power user features
+ Persistent state       → os-store.ts with localStorage
```

## 🐛 Issues Resolvidos & Quality

### Build & Performance (2025-09-26)
- ✅ **Next.js 15.4.6**: Build com 0 erros de produção
- ✅ **TypeScript Strict**: Compliance total sem warnings
- ✅ **Image Optimization**: `img` → `next/image` para performance
- ✅ **React Hooks**: Dependências otimizadas sem warnings
- ✅ **Code Quality**: Remoção de variáveis não utilizadas

### Professional Drag & Drop Implementation (2025-09-28)  
- ✅ **Smart Position Swapping**: Troca automática de posições entre ícones
- ✅ **Multi-Level Collision Detection**: pointerWithin → rectIntersection → closestCenter
- ✅ **Responsive Grid System**: 6 breakpoints adaptativos (mobile → large desktop)
- ✅ **Dynamic Protected Areas**: DateTime widget protegido automaticamente
- ✅ **Professional Animations**: Cubic-bezier easing para movimento natural
- ✅ **Container-Aware Calculations**: Medições precisas baseadas no grid real
- ✅ **100% Grid Movement**: Movimentação livre em toda a área (incluindo linhas 1-2)
- ✅ **Touch Optimization**: Configurações específicas por tipo de device
- ✅ **Zero Breaking Changes**: Chat + Auth preservados

## 🎯 Features Web OS

### 🖥️ Desktop Experience
- **OS-like Interface**: Experiência desktop completa
- **Dynamic Wallpapers**: 13 presets categorizados
- **App Icons**: Drag & drop com categorização
- **Edit Mode**: Reorganização visual intuitiva

### ⚡ Performance & UX
- **Optimized Rendering**: useMemo + useCallback otimizados
- **Persistent State**: localStorage + Zustand integration
- **Responsive Design**: Mobile + Desktop adaptive
- **Smooth Animations**: Transições CSS nativas

### 🔧 Technical Excellence
- **TypeScript**: Strict mode compliance
- **Error Boundaries**: Tratamento robusto de erros
- **Accessibility**: WCAG guidelines seguidas
- **Code Splitting**: Next.js optimização automática

## 🔗 Dependências Principais

```json
{
  "next": "15.4.6",
  "react": "19.1.0", 
  "typescript": "5.x",
  "tailwindcss": "4.x",
  "zustand": "5.0.7",
  "@dnd-kit/core": "latest",
  "@dnd-kit/modifiers": "latest", 
  "@dnd-kit/sortable": "latest",
  "@supabase/supabase-js": "2.55.0",
  "@radix-ui/react-*": "latest",
  "lucide-react": "latest"
}
```

---

**VOXY Web OS - Sistema operacional web completo com Image Management System, Professional Drag & Drop, smart swapping, grid responsivo, 13 wallpapers dinâmicos e VOXY Chat integrado.**

*Última atualização: 2025-09-30 - Image Management System Implementation*